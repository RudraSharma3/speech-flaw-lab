import React from 'react';
import { useAudioStore } from './store/useAudioStore';
import { IS_STATIC_DEMO } from './lib/staticApi';
import { Segmented } from './components/ui';
import { RecordingPicker } from './components/RecordingPicker';
import { SummaryStrip } from './components/SummaryStrip';
import { WaveformViewer } from './components/WaveformViewer';
import { FlawInspector } from './components/FlawInspector';
import { GroundTruthTable } from './components/GroundTruthTable';
import { TranscriptHeatmap } from './components/TranscriptHeatmap';
import { AcousticPlots } from './components/AcousticPlots';
import { RubricBreakdown } from './components/RubricBreakdown';
import { ClarityPanel } from './components/ClarityPanel';
import { UploadPanel } from './components/UploadPanel';
import { BenchmarkView } from './components/BenchmarkView';

const Logo: React.FC = () => (
  <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden>
    <rect width="22" height="22" rx="5" fill="#0f4c5c" />
    {[4, 8, 12, 16].map((x, i) => {
      const h = [6, 12, 8, 4][i];
      return <rect key={x} x={x + 0.5} y={11 - h / 2} width="2" height={h} rx="1" fill="#ffffff" />;
    })}
  </svg>
);

const RecordingView: React.FC = () => {
  const { resultData } = useAudioStore();
  return (
    <div className="space-y-5">
      <div className="max-w-[78ch]">
        <h1 className="text-[22px] font-semibold tracking-tight text-ink">Where does the delivery go wrong?</h1>
        <p className="mt-1 text-[14px] leading-relaxed text-ink-2">
          Speech Flaw Lab lines a recording up word by word against a reference take of the same text and marks the spans that
          are rushed, too slow, monotone or badly paused. The recordings here are historical speeches with flaws injected at
          known places, so every detection can be checked against the truth.
          {IS_STATIC_DEMO && ' This shared copy shows stored pipeline results.'}
        </p>
      </div>

      <RecordingPicker />

      {resultData && (
        <>
          <SummaryStrip />
          <WaveformViewer />
          <FlawInspector />
          <GroundTruthTable />
          <TranscriptHeatmap />
          <AcousticPlots />
          <RubricBreakdown />
          <ClarityPanel />
        </>
      )}

      <UploadPanel />
    </div>
  );
};

export const App: React.FC = () => {
  const { view, setView } = useAudioStore();

  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <header className="sticky z-30 border-b border-line bg-surface/95 backdrop-blur" style={{ top: 'env(safe-area-inset-top, 0px)' }}>
        <div className="mx-auto flex max-w-[1180px] flex-wrap items-center justify-between gap-3 px-4 py-2.5 sm:px-6">
          <div className="flex items-center gap-2.5">
            <Logo />
            <span className="text-[15px] font-semibold tracking-tight text-ink">Speech Flaw Lab</span>
            {IS_STATIC_DEMO && (
              <span className="hidden rounded border border-line px-1.5 py-0.5 text-[11px] text-ink-3 sm:inline">Read-only demo</span>
            )}
          </div>
          <Segmented<"recording" | "benchmark">
            ariaLabel="View"
            value={view}
            onChange={(v) => {
              setView(v);
              window.scrollTo({ top: 0 });
            }}
            options={[
              { value: 'recording', label: 'Recording' },
              { value: 'benchmark', label: 'Benchmark' },
            ]}
          />
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1180px] flex-1 px-4 py-6 sm:px-6">
        {view === 'recording' ? <RecordingView /> : <BenchmarkView />}
      </main>

      <footer className="border-t border-line bg-surface">
        <div className="mx-auto flex max-w-[1180px] flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-5 text-[12px] text-ink-3 sm:px-6">
          <span>Multimodal AI Hackathon 2026 · Track C</span>
          <span>Alignment: torchaudio MMS_FA · Pitch and HNR: Praat (Parselmouth) · Scoring: deterministic, no LLM</span>
          <a className="font-medium text-accent hover:underline" href="https://github.com/RudraSharma3/speech-flaw-lab">
            Source on GitHub
          </a>
        </div>
      </footer>
    </div>
  );
};
