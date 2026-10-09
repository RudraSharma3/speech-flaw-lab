import React from 'react';
import { useAudioStore } from './store/useAudioStore';
import { WaveformViewer } from './components/WaveformViewer';
import { AcousticPlots } from './components/AcousticPlots';
import { TranscriptHeatmap } from './components/TranscriptHeatmap';
import { CausalExplanationCard } from './components/CausalExplanationCard';
import { ScoreCard } from './components/ScoreCard';
import { UploadPanel } from './components/UploadPanel';
import { CompareGradientView } from './components/CompareGradientView';
import { GroundTruthTable } from './components/GroundTruthTable';
import { LimitationsPanel } from './components/LimitationsPanel';
import { ClarityPanel } from './components/ClarityPanel';
import { Mic2, Activity, Layers, Cpu } from 'lucide-react';

export const App: React.FC = () => {
  const { activeTab, setActiveTab } = useAudioStore();

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-primary to-brand-secondary flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Mic2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-black tracking-tight text-white">
                SPEECH CONTRASTIVE ANALYTICS
              </h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                TRACK C
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Deterministic Temporal Flaw Grounding & Acoustic Deviation Engine
            </p>
          </div>
        </div>

        {/* Status Indicators & Hackathon Badge */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-400">Pipeline:</span>
            <span className="text-slate-200 font-mono font-semibold">Deterministic / Zero-LLM</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-xs text-emerald-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>MFA + Praat Active</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 mb-6 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'overview'
                ? 'bg-brand-primary text-white shadow-lg shadow-indigo-500/25'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Mic2 className="w-4 h-4" />
            Dashboard & Grounding
          </button>

          <button
            onClick={() => setActiveTab('acoustic_plots')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'acoustic_plots'
                ? 'bg-brand-primary text-white shadow-lg shadow-indigo-500/25'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Activity className="w-4 h-4" />
            Acoustic Contours (Plotly)
          </button>

          <button
            onClick={() => setActiveTab('compare_gradient')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'compare_gradient'
                ? 'bg-brand-primary text-white shadow-lg shadow-indigo-500/25'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Layers className="w-4 h-4" />
            Compare Gradient (Levels 4 ➔ 0)
          </button>
        </div>

        {/* Upload & Sample Selector Panel */}
        <UploadPanel />

        {/* Tab 1: Overview */}
        {activeTab === 'overview' && (
          <>
            <ScoreCard />
            <WaveformViewer />
            <GroundTruthTable />
            <CausalExplanationCard />
            <TranscriptHeatmap />
            <ClarityPanel />
            <LimitationsPanel />
          </>
        )}

        {/* Tab 2: Acoustic Plots */}
        {activeTab === 'acoustic_plots' && (
          <>
            <WaveformViewer />
            <AcousticPlots />
            <GroundTruthTable />
            <CausalExplanationCard />
            <TranscriptHeatmap />
            <ClarityPanel />
            <LimitationsPanel />
          </>
        )}

        {/* Tab 3: Compare Gradient */}
        {activeTab === 'compare_gradient' && (
          <>
            <CompareGradientView />
            <ScoreCard />
            <WaveformViewer />
            <GroundTruthTable />
            <CausalExplanationCard />
            <ClarityPanel />
            <LimitationsPanel />
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 glass-panel py-5 px-6 mt-12 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            <span className="font-bold text-slate-300">Track C: Contrastive Speech Analytics</span> • Multimodal AI Hackathon 2026
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span>MFA 3.x Forced Alignment</span>
            <span>•</span>
            <span>Praat Parselmouth F0 / HNR</span>
            <span>•</span>
            <span>LUFS Normalization</span>
            <span>•</span>
            <span>Pydantic v2</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
