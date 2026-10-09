const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function renderArchitecture() {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1200, height: 680 } });

  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    padding: 24px;
    background: #0f172a;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .canvas {
    width: 1150px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 24px 28px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
  }
  .title {
    color: #f8fafc;
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid #334155;
    padding-bottom: 12px;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }
  .card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 14px 16px;
    position: relative;
  }
  .card.active {
    border-color: #3b82f6;
  }
  .card-num {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: #60a5fa;
    margin-bottom: 4px;
  }
  .card-title {
    font-size: 14px;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 8px;
  }
  .card-items {
    font-size: 12px;
    color: #94a3b8;
    line-height: 1.5;
  }
  .tag {
    display: inline-block;
    background: #1e293b;
    color: #38bdf8;
    border: 1px solid #0284c7;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 11px;
    margin: 2px 2px 2px 0;
    font-family: monospace;
  }
  .flow-arrow {
    text-align: center;
    color: #64748b;
    font-size: 16px;
    margin: 4px 0;
  }
  .footer-banner {
    margin-top: 18px;
    padding: 10px 16px;
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: #93c5fd;
  }
</style>
</head>
<body>
<div class="canvas">
  <div class="title">
    <span>🎙️ Track C: Contrastive Speech Analytics Architecture</span>
    <span style="font-size: 12px; color: #94a3b8; font-weight: 400; margin-left: auto;">Zero-LLM &bull; Sub-Millisecond Grounding &bull; MMS_FA Aligned</span>
  </div>
  <div class="grid">
    <div class="card">
      <div class="card-num">Stage 1</div>
      <div class="card-title">Audio Ingestion & Normalization</div>
      <div class="card-items">
        <div>&bull; Multi-format audio parsing (WAV/MP3/M4A)</div>
        <div>&bull; Resampled to 16 kHz Mono Float32</div>
        <div>&bull; BS.1770 -20 LUFS Loudness Target</div>
        <div style="margin-top: 6px;"><span class="tag">soundfile</span> <span class="tag">pyloudnorm</span></div>
      </div>
    </div>

    <div class="card active">
      <div class="card-num">Stage 2</div>
      <div class="card-title">Forced Alignment Engine</div>
      <div class="card-items">
        <div>&bull; <strong>torchaudio MMS_FA</strong> Wav2Vec2 CTC</div>
        <div>&bull; Single model preload + warm-up</div>
        <div>&bull; Sub-millisecond word & phoneme spans</div>
        <div style="margin-top: 6px;"><span class="tag">torchaudio</span> <span class="tag">MMS_FA</span> <span class="tag">PyTorch</span></div>
      </div>
    </div>

    <div class="card">
      <div class="card-num">Stage 3</div>
      <div class="card-title">Deterministic DSP Extraction</div>
      <div class="card-items">
        <div>&bull; Adaptive pitch contour $F_0$ (Praat)</div>
        <div>&bull; Harmonicity (HNR) & Intensity</div>
        <div>&bull; 13 MFCCs, Spectral Flux & Centroid</div>
        <div style="margin-top: 6px;"><span class="tag">praat-parselmouth</span> <span class="tag">librosa</span></div>
      </div>
    </div>

    <div class="card">
      <div class="card-num">Stage 4</div>
      <div class="card-title">Temporal Flaw Grounding</div>
      <div class="card-items">
        <div>&bull; Word-by-word contrastive $\Delta$ vs L4 reference</div>
        <div>&bull; Reference-free MAD $z$-scores vs LibriSpeech</div>
        <div>&bull; Hysteresis triggers ($z_{\\text{act}}=2.2, z_{\\text{deact}}=1.5$)</div>
        <div style="margin-top: 6px;"><span class="tag">numpy</span> <span class="tag">scipy</span> <span class="tag">grounding.py</span></div>
      </div>
    </div>

    <div class="card">
      <div class="card-num">Stage 5</div>
      <div class="card-title">Scoring & Causal Explanation</div>
      <div class="card-items">
        <div>&bull; 5 Rubric dimensions (Pacing, Pitch, Vol, ...)</div>
        <div>&bull; Isotonic score calibration (fit on tuning set)</div>
        <div>&bull; Deterministic causal rationale cards</div>
        <div style="margin-top: 6px;"><span class="tag">scikit-learn</span> <span class="tag">explain.py</span></div>
      </div>
    </div>

    <div class="card">
      <div class="card-num">Stage 6</div>
      <div class="card-title">Interactive Web Dashboard</div>
      <div class="card-items">
        <div>&bull; WaveSurfer synced word/flaw overlays</div>
        <div>&bull; Plotly $F_0$, Mel spectrogram, MFCC toggles</div>
        <div>&bull; Gradient comparisons & Clarity metrics</div>
        <div style="margin-top: 6px;"><span class="tag">React</span> <span class="tag">Vite</span> <span class="tag">Plotly.js</span> <span class="tag">WaveSurfer</span></div>
      </div>
    </div>
  </div>

  <div class="footer-banner">
    <span><strong>Aligner:</strong> torchaudio MMS_FA (MFA is not used in production pipeline)</span>
    <span><strong>Calibration:</strong> Fit strictly on Injected Gradient tuning speeches</span>
    <span><strong>F1 (IoU &ge; 0.3):</strong> L0: 73.5% &bull; L1: 79.5%</span>
  </div>
</div>
</body>
</html>`;

  await page.setContent(html);
  const outPath = path.resolve(__dirname, '../docs/screenshots/architecture_diagram.png');
  await page.screenshot({ path: outPath });
  console.log('Saved architecture diagram to:', outPath);
  await browser.close();
}

renderArchitecture().catch(err => {
  console.error(err);
  process.exit(1);
});
