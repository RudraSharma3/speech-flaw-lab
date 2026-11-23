# Stage 1: Build React/Vite Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Runtime with Baked Weights (Zero-MFA)
FROM python:3.11-slim AS runner

USER root
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    KMP_DUPLICATE_LIB_OK=TRUE \
    TORCH_HOME=/app/.cache/torch \
    HF_HOME=/app/.cache/huggingface \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements with CPU-only PyTorch wheels (reduces image size from ~5GB to ~1.4GB)
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Bake Torchaudio MMS_FA aligner weights into the Docker image
RUN python -c "import torchaudio, torch; bundle = torchaudio.pipelines.MMS_FA; model = bundle.get_model(); model.eval(); dummy = torch.randn(1, 16000); _ = model(dummy); print('Baked MMS_FA weights into image.')"

# Bake faster-whisper base model weights into the Docker image
RUN python -c "from faster_whisper import WhisperModel; _ = WhisperModel('base', device='cpu', compute_type='int8'); print('Baked faster-whisper weights into image.')"

# Copy pre-built frontend bundle to be served on the unified port
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Copy application source code and configurations
COPY backend /app/backend
COPY configs /app/configs
COPY data /app/data
COPY results /app/results
COPY pytest.ini /app/pytest.ini

EXPOSE 8000

# Single-port unified serving: FastAPI serves static frontend + async API endpoints
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
