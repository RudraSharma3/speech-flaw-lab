"""
FastAPI application for Contrastive Speech Analytics & Temporal Flaw Grounding.
Implements non-blocking async job queue, file SHA-256 caching, and pre-cached demo samples.
"""

import os
import io
import json
import uuid
import shutil
import hashlib
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from backend.schemas.api import (
    AnalysisResult,
    JobStatus,
    SampleRecording,
)
from backend.app.demo_samples import get_demo_samples, get_cached_result_by_id
from backend.pipeline.orchestrator import run_speech_pipeline

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
JOBS_STORE: Dict[str, Dict[str, Any]] = {}
RESULTS_CACHE: Dict[str, Dict[str, Any]] = {}

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cached_results")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "demo_audio")
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)


def process_audio_job_async(job_id: str, audio_bytes: bytes, filename: str, transcript: str, reference_id: Optional[str]):
    """Background task worker for audio pipeline processing."""
    try:
        JOBS_STORE[job_id]["status"] = "processing"
        JOBS_STORE[job_id]["progress"] = 0.15
        JOBS_STORE[job_id]["message"] = "Preprocessing audio and performing LUFS normalization..."

        # Check if already cached by SHA-256
        sha256 = hashlib.sha256(audio_bytes).hexdigest()
        cached_disk_path = os.path.join(CACHE_DIR, f"{sha256}.json")
        
        if os.path.exists(cached_disk_path):
            with open(cached_disk_path, "r", encoding="utf-8") as f:
                result_data = json.load(f)
            JOBS_STORE[job_id]["progress"] = 1.0
            JOBS_STORE[job_id]["status"] = "completed"
            JOBS_STORE[job_id]["message"] = "Analysis retrieved from SHA-256 cache."
            JOBS_STORE[job_id]["result_id"] = result_data["meta"]["analysis_id"]
            RESULTS_CACHE[result_data["meta"]["analysis_id"]] = result_data
            return

        JOBS_STORE[job_id]["progress"] = 0.35
        JOBS_STORE[job_id]["message"] = "Running forced alignment and phoneme segmentation..."

        # Load reference baseline words if reference_id provided
        ref_words = None
        if reference_id:
            cached_ref = get_cached_result_by_id(reference_id) or RESULTS_CACHE.get(reference_id)
            if cached_ref:
                ref_words = cached_ref.get("words")

        JOBS_STORE[job_id]["progress"] = 0.60
        JOBS_STORE[job_id]["message"] = "Extracting Parselmouth F0, intensity, and spectral features..."

        # Execute pipeline
        result_payload = run_speech_pipeline(
            audio_source=audio_bytes,
            transcript=transcript,
            filename=filename,
            reference_words=ref_words,
            reference_id=reference_id,
        )

        analysis_id = result_payload["meta"]["analysis_id"]

        # Cache in memory and on disk
        RESULTS_CACHE[analysis_id] = result_payload
        with open(cached_disk_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2)

        JOBS_STORE[job_id]["progress"] = 1.0
        JOBS_STORE[job_id]["status"] = "completed"
        JOBS_STORE[job_id]["message"] = "Analysis completed successfully."
        JOBS_STORE[job_id]["result_id"] = analysis_id

    except Exception as e:
        JOBS_STORE[job_id]["status"] = "failed"
        JOBS_STORE[job_id]["progress"] = 1.0
        JOBS_STORE[job_id]["message"] = "Processing failed."
        JOBS_STORE[job_id]["error"] = str(e)


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


@app.get("/samples", response_model=List[SampleRecording])
def list_demo_samples():
    """Returns catalog of pre-cached demo samples across all 5 quality levels."""
    return get_demo_samples()


@app.get("/api/audio/{filename}")
def stream_audio(filename: str):
    """Streams audio WAV files for browser waveform playback."""
    file_path = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")


@app.post("/analyze")
async def analyze_speech(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    transcript: str = Form(...),
    reference_id: Optional[str] = Form(None),
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


@app.get("/results/{result_id}", response_model=AnalysisResult)
def get_analysis_result(result_id: str):
    """Fetches full structured analysis result by result_id or sample_id."""
    # 1. Check in-memory results
    if result_id in RESULTS_CACHE:
        return RESULTS_CACHE[result_id]

    # 2. Check cached samples
    sample_result = get_cached_result_by_id(result_id)
    if sample_result:
        RESULTS_CACHE[result_id] = sample_result
        return sample_result

    # 3. Check disk cache
    disk_path = os.path.join(CACHE_DIR, f"{result_id}.json")
    if os.path.exists(disk_path):
        with open(disk_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            RESULTS_CACHE[result_id] = data
            return data

    raise HTTPException(status_code=404, detail="Analysis result not found")
