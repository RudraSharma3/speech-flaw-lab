"""
FastAPI application for Contrastive Speech Analytics & Temporal Flaw Grounding.
Implements non-blocking async job queue, file SHA-256 caching, and pre-cached demo samples.
"""

import hashlib
import json
import os
import shutil
import uuid
from typing import Any

from backend.app.demo_samples import get_cached_result_by_id, get_demo_samples, get_reference_speeches
from backend.pipeline.orchestrator import run_speech_pipeline
from backend.schemas.api import (
    AnalysisResult,
    JobStatus,
    SampleRecording,
)
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(
    title="Contrastive Speech Analytics API",
    description="Multimodal temporal flaw grounding and contrastive speech analytics engine.",
    version="1.0.0",
)

# Enable CORS for frontend Vite dev server and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory and file-based state stores
JOBS_STORE: dict[str, dict[str, Any]] = {}
RESULTS_CACHE: dict[str, dict[str, Any]] = {}

import numpy as np

def json_serialize(obj):
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    return str(obj)

DATA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
CACHE_DIR = os.path.join(DATA_ROOT, "cached_results")
BENCHMARK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "results", "benchmark.json"))
os.makedirs(CACHE_DIR, exist_ok=True)

AUDIO_SEARCH_DIRS = [
    os.path.join(DATA_ROOT, "injected"),
    os.path.join(DATA_ROOT, "self_recordings"),
    os.path.join(DATA_ROOT, "demo_audio"),
    os.path.join(DATA_ROOT, "processed"),
    os.path.join(DATA_ROOT, "raw"),
]


def process_audio_job_async(job_id: str, audio_bytes: bytes, filename: str, transcript: str, reference_id: str | None):
    """Background task worker for audio pipeline processing with granular stage progress."""
    try:
        def on_progress(p: float, stage: str, msg: str):
            if job_id in JOBS_STORE:
                JOBS_STORE[job_id]["progress"] = p
                JOBS_STORE[job_id]["stage"] = stage
                JOBS_STORE[job_id]["message"] = msg

        JOBS_STORE[job_id]["status"] = "processing"
        on_progress(0.10, "Audio Ingestion", "Preprocessing audio and performing LUFS normalization...")

        # Check if already cached by SHA-256
        sha256 = hashlib.sha256(audio_bytes).hexdigest()
        cached_disk_path = os.path.join(CACHE_DIR, f"{sha256}.json")
        
        if os.path.exists(cached_disk_path):
            with open(cached_disk_path, encoding="utf-8") as f:
                result_data = json.load(f)
            JOBS_STORE[job_id]["progress"] = 1.0
            JOBS_STORE[job_id]["stage"] = "Completed"
            JOBS_STORE[job_id]["status"] = "completed"
            JOBS_STORE[job_id]["message"] = "Analysis retrieved from SHA-256 cache."
            JOBS_STORE[job_id]["result_id"] = result_data["meta"]["analysis_id"]
            RESULTS_CACHE[result_data["meta"]["analysis_id"]] = result_data
            return

        # Load reference baseline words if reference_id provided
        ref_words = None
        ref_sha256 = None
        if reference_id:
            cached_ref = get_cached_result_by_id(reference_id) or RESULTS_CACHE.get(reference_id)
            if cached_ref:
                ref_words = cached_ref.get("words")
                ref_sha256 = cached_ref.get("meta", {}).get("audio_sha256")

        # Execute pipeline with real-time stage progress reporting
        result_payload = run_speech_pipeline(
            audio_source=audio_bytes,
            transcript=transcript,
            filename=filename,
            reference_words=ref_words,
            reference_id=reference_id,
            reference_sha256=ref_sha256,
            progress_callback=on_progress,
        )

        analysis_id = result_payload["meta"]["analysis_id"]

        # Strip unneeded cached context before serialization
        result_payload.pop("_cached_context", None)

        # Cache in memory and on disk
        RESULTS_CACHE[analysis_id] = result_payload
        with open(cached_disk_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, default=json_serialize)

        JOBS_STORE[job_id]["progress"] = 1.0
        JOBS_STORE[job_id]["stage"] = "Completed"
        JOBS_STORE[job_id]["status"] = "completed"
        JOBS_STORE[job_id]["message"] = "Analysis completed successfully."
        JOBS_STORE[job_id]["result_id"] = analysis_id

    except Exception as e:
        JOBS_STORE[job_id]["status"] = "failed"
        JOBS_STORE[job_id]["stage"] = "Error"
        JOBS_STORE[job_id]["progress"] = 1.0
        JOBS_STORE[job_id]["message"] = "Processing failed."
        JOBS_STORE[job_id]["error"] = str(e)


@app.on_event("startup")
def startup_event():
    """Warms up MMS_FA aligner so live upload encounters zero cold-start delay."""
    try:
        from backend.pipeline.align import warmup_mms_fa
        warmup_mms_fa()
    except Exception as e:
        print(f"Aligner warmup notice: {e}")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    mfa_available = shutil.which("mfa") is not None
    return {
        "status": "healthy",
        "service": "Contrastive Speech Analytics",
        "mfa_available": mfa_available,
        "version": "1.0.0",
    }


@app.get("/samples", response_model=list[SampleRecording])
def list_demo_samples():
    """Returns catalog of pre-cached demo samples across all 5 quality levels."""
    return get_demo_samples()


@app.get("/api/references")
def list_reference_speeches():
    """Returns list of canonical reference takes for contrastive mode."""
    return get_reference_speeches()


@app.get("/api/benchmark")
def get_benchmark_results():
    """Returns official evaluation benchmark metrics from results/benchmark.json."""
    if os.path.exists(BENCHMARK_PATH):
        with open(BENCHMARK_PATH, encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="benchmark.json not yet generated")


@app.get("/api/audio/{filename}")
def stream_audio(filename: str):
    """Streams audio WAV files for browser waveform playback across data dirs."""
    for search_dir in AUDIO_SEARCH_DIRS:
        cand_path = os.path.join(search_dir, filename)
        if os.path.exists(cand_path):
            return FileResponse(cand_path, media_type="audio/wav")
    raise HTTPException(status_code=404, detail=f"Audio file '{filename}' not found")


@app.post("/analyze")
async def analyze_speech(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    transcript: str = Form(...),
    reference_id: str | None = Form(None),
):
    """
    Submits audio + transcript for asynchronous analysis.
    Returns a job_id immediately for polling.
    """
    if not transcript or not transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript is required for forced alignment.")

    audio_bytes = await audio.read()
    if len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Audio file is empty or too short.")

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    JOBS_STORE[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "message": "Job queued for processing...",
        "result_id": None,
        "error": None,
    }

    background_tasks.add_task(
        process_audio_job_async,
        job_id=job_id,
        audio_bytes=audio_bytes,
        filename=audio.filename or "upload.wav",
        transcript=transcript.strip(),
        reference_id=reference_id,
    )

    return {"job_id": job_id}


@app.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    """Polls progress status for an ongoing analysis job."""
    if job_id not in JOBS_STORE:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return JOBS_STORE[job_id]


def compute_iou(s1: float, e1: float, s2: float, e2: float) -> float:
    inter = max(0.0, min(e1, e2) - max(s1, s2))
    union = max(e1, e2) - min(s1, s2)
    return inter / union if union > 0 else 0.0


def enrich_with_ground_truth(result: dict[str, Any], rec_id: str) -> dict[str, Any]:
    if result.get("ground_truth_eval"):
        return result
    gt_path = os.path.join(DATA_ROOT, "injected", f"{rec_id}_flaws.json")
    if not os.path.exists(gt_path):
        return result
    try:
        with open(gt_path, encoding="utf-8") as f:
            gt_data = json.load(f)
        gt_flaws = gt_data.get("flaws", [])
        result["ground_truth_flaws"] = gt_flaws
        
        det_flaws = result.get("flaws", [])
        cost_matrix = []
        for d in det_flaws:
            row = []
            for g in gt_flaws:
                iou = compute_iou(d["start_s"], d["end_s"], g["start_s"], g["end_s"])
                row.append(1.0 - iou if iou >= 0.3 else 1.0)
            cost_matrix.append(row)
            
        eval_rows = []
        matched_det = set()
        matched_gt = set()
        if cost_matrix and len(cost_matrix[0]) > 0:
            from scipy.optimize import linear_sum_assignment
            d_ind, g_ind = linear_sum_assignment(cost_matrix)
            for d_i, g_i in zip(d_ind, g_ind):
                cost = cost_matrix[d_i][g_i]
                iou = 1.0 - cost
                if iou >= 0.3:
                    det = det_flaws[d_i]
                    gt = gt_flaws[g_i]
                    gt_t = gt.get("flaw_type", gt.get("type", "unknown"))
                    matched_det.add(d_i)
                    matched_gt.add(g_i)
                    eval_rows.append({
                        "status": "MATCHED",
                        "detected_id": det["region_id"],
                        "detected_type": det["flaw_type"],
                        "detected_span": [det["start_s"], det["end_s"]],
                        "detected_words": det.get("words", ""),
                        "gt_id": gt.get("flaw_id", f"gt_{g_i}"),
                        "gt_type": gt_t,
                        "gt_span": [gt["start_s"], gt["end_s"]],
                        "gt_words": gt.get("words", ""),
                        "iou": round(iou, 3),
                        "start_error_ms": round(abs(det["start_s"] - gt["start_s"]) * 1000.0, 1),
                        "end_error_ms": round(abs(det["end_s"] - gt["end_s"]) * 1000.0, 1),
                        "type_match": det["flaw_type"] == gt_t
                    })
        for d_i, det in enumerate(det_flaws):
            if d_i not in matched_det:
                eval_rows.append({
                    "status": "FALSE_POSITIVE",
                    "detected_id": det["region_id"],
                    "detected_type": det["flaw_type"],
                    "detected_span": [det["start_s"], det["end_s"]],
                    "detected_words": det.get("words", ""),
                    "gt_id": None,
                    "gt_type": None,
                    "gt_span": None,
                    "gt_words": None,
                    "iou": 0.0,
                    "start_error_ms": None,
                    "end_error_ms": None,
                    "type_match": False
                })
        for g_i, gt in enumerate(gt_flaws):
            if g_i not in matched_gt:
                gt_t = gt.get("flaw_type", gt.get("type", "unknown"))
                eval_rows.append({
                    "status": "MISSED_GT",
                    "detected_id": None,
                    "detected_type": None,
                    "detected_span": None,
                    "detected_words": None,
                    "gt_id": gt.get("flaw_id", f"gt_{g_i}"),
                    "gt_type": gt_t,
                    "gt_span": [gt["start_s"], gt["end_s"]],
                    "gt_words": gt.get("words", ""),
                    "iou": 0.0,
                    "start_error_ms": 2000.0,
                    "end_error_ms": 2000.0,
                    "type_match": False
                })
        result["ground_truth_eval"] = eval_rows
    except Exception:
        pass
    return result


@app.get("/results/{result_id}", response_model=AnalysisResult)
def get_analysis_result(result_id: str):
    """Fetches full structured analysis result by result_id or sample_id."""
    # 1. Check in-memory results
    if result_id in RESULTS_CACHE:
        return enrich_with_ground_truth(RESULTS_CACHE[result_id], result_id)

    # 2. Check cached samples
    sample_result = get_cached_result_by_id(result_id)
    if sample_result:
        sample_result = enrich_with_ground_truth(sample_result, result_id)
        RESULTS_CACHE[result_id] = sample_result
        return sample_result

    # 3. Check disk cache
    disk_path = os.path.join(CACHE_DIR, f"{result_id}.json")
    if os.path.exists(disk_path):
        with open(disk_path, encoding="utf-8") as f:
            data = json.load(f)
            data = enrich_with_ground_truth(data, result_id)
            RESULTS_CACHE[result_id] = data
            return data

    raise HTTPException(status_code=404, detail="Analysis result not found")


from fastapi.staticfiles import StaticFiles

FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
