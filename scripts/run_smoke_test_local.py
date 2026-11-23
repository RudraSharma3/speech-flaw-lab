"""
Local Smoke Test: Replicates the CI Docker smoke test against the running Uvicorn server.
Performs exact steps from .github/workflows/docker.yml:
1. GET /health
2. GET / (Frontend serving)
3. Extract canonical transcript from data/manifests/real_speech_manifest.json
4. POST /analyze (audio=@data/demo_audio/jfk_moon_1962_level_1.wav, reference_id=jfk_moon_1962_level_4)
5. Poll /jobs/{job_id} until completed
6. GET /results/{result_id}
7. Assert flaw regions >= 1 and overall score < 90.0
"""

import json
import time
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_smoke_test():
    print("=" * 80)
    print("LOCAL CONTAINER SMOKE-TEST REPLICATION (AGAINST UVICORN SERVER)")
    print(f"Target: {BASE_URL}")
    print("=" * 80)

    # 1. Health check
    print("\n[STEP 1] Testing /health...")
    res = requests.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code} {res.text}"
    health_data = res.json()
    print(f"  Response (HTTP {res.status_code}): {json.dumps(health_data)}")
    assert health_data["status"] == "healthy", "Server not healthy"

    # 2. Static root check
    print("\n[STEP 2] Testing / (frontend serve)...")
    res = requests.get(f"{BASE_URL}/")
    print(f"  Response (HTTP {res.status_code}): content-length={len(res.content)} bytes")
    assert res.status_code == 200, f"Root endpoint failed: {res.status_code}"

    # 3. Read canonical transcript from single source of truth manifest
    print("\n[STEP 3] Reading canonical transcript from data/manifests/real_speech_manifest.json...")
    with open("data/manifests/real_speech_manifest.json", "r", encoding="utf-8") as f:
        speeches = json.load(f)
    jfk_transcript = next(s["transcript"] for s in speeches if s["speech_id"] == "jfk_moon_1962")
    print(f"  Transcript excerpt: {jfk_transcript[:80]}...")
    print(f"  Transcript total length: {len(jfk_transcript)} chars, {len(jfk_transcript.split())} words")

    # 4. POST flawed audio sample against canonical reference
    audio_file = "data/demo_audio/jfk_moon_1962_level_1.wav"
    ref_id = "jfk_moon_1962_level_4"
    print(f"\n[STEP 4] POST /analyze with flawed clip ({audio_file}) vs reference ({ref_id})...")
    with open(audio_file, "rb") as f:
        files = {"audio": (audio_file, f, "audio/wav")}
        data = {
            "transcript": jfk_transcript,
            "reference_id": ref_id,
        }
        res = requests.post(f"{BASE_URL}/analyze", files=files, data=data)

    assert res.status_code == 200, f"POST /analyze failed: {res.status_code} {res.text}"
    post_res = res.json()
    job_id = post_res["job_id"]
    print(f"  POST Response: {json.dumps(post_res)}")
    print(f"  Dispatched Job ID: {job_id}")

    # 5. Poll job status
    print(f"\n[STEP 5] Polling /jobs/{job_id}...")
    result_id = None
    for attempt in range(1, 45):
        res = requests.get(f"{BASE_URL}/jobs/{job_id}")
        assert res.status_code == 200, f"Job poll failed: {res.status_code}"
        job_data = res.json()
        status = job_data.get("status")
        progress = job_data.get("progress", 0.0)
        print(f"  Poll attempt {attempt}: status={status}, progress={progress:.1%}, message={job_data.get('message')}")
        if status == "completed":
            result_id = job_data["result_id"]
            print(f"  Job completed successfully! Result ID: {result_id}")
            break
        elif status == "failed":
            raise RuntimeError(f"Job failed: {job_data.get('error')}")
        time.sleep(2.0)

    assert result_id is not None, "Job timed out without completing"

    # 6. GET final result
    print(f"\n[STEP 6] Fetching /results/{result_id}...")
    res = requests.get(f"{BASE_URL}/results/{result_id}")
    assert res.status_code == 200, f"Result fetch failed: {res.status_code}"
    result = res.json()

    # 7. Assertions
    print("\n[STEP 7] Verifying Result Payload Assertions...")
    assert "scores" in result and "overall" in result["scores"], "Missing overall score"
    assert "words" in result and len(result["words"]) > 0, "Missing aligned words"

    overall_score = result["scores"]["overall"]
    flaws = result.get("flaws", [])
    flaw_count = len(flaws)

    print(f"  Overall Score: {overall_score:.2f}")
    print(f"  Detected Flaw Regions Count: {flaw_count}")
    for idx, fl in enumerate(flaws, 1):
        print(f"    Flaw #{idx}: {fl.get('flaw_type')} [{fl.get('start_s'):.2f}s - {fl.get('end_s'):.2f}s] words: '{fl.get('words')}'")

    quality_flags = result.get("quality_flags", [])
    print(f"  Quality Flags: {quality_flags}")

    # Verification checks
    assert flaw_count >= 1, f"Expected at least 1 flaw region on Level 1, found {flaw_count}"
    assert overall_score < 90.0, f"Expected score < 90.0 for Level 1 flawed clip, got {overall_score}"
    assert not any(qf.get("code") == "SELF_COMPARISON_WARNING" for qf in quality_flags), "Unexpected self-comparison warning"
    assert not any(qf.get("code") == "LOW_TRANSCRIPT_COVERAGE" for qf in quality_flags), "Unexpected low coverage warning"

    print("\n" + "=" * 80)
    print(">>> LOCAL SMOKE TEST PASSED WITH PROOF <<<")
    print(f"Flaws Detected: {flaw_count} (>= 1 required)")
    print(f"Score Achieved: {overall_score:.2f} (< 90.0 required)")
    print("=" * 80)

if __name__ == "__main__":
    run_smoke_test()
