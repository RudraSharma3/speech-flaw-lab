import React from 'react';
import { useAudioStore } from '../store/useAudioStore';
import { AlertTriangle, HelpCircle, ArrowRight, ShieldAlert, ChevronLeft, ChevronRight } from 'lucide-react';
import { GroundedFlaw } from '../types/api';

export const CausalExplanationCard: React.FC = () => {
  const { resultData, selectedRegion, setSelectedRegion, seekTo } = useAudioStore();

  if (!resultData || !resultData.flaws || resultData.flaws.length === 0) {
    return (
      <div className="glass-panel p-5 rounded-2xl mb-6">
        <div className="flex items-center gap-2 text-emerald-400 font-bold mb-2">
          <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
          Zero Flaws Detected — Pristine Canonical Delivery
        </div>
        <p className="text-sm text-slate-400">
          All acoustic contours (F0 modulation, energy contrast, syntactic pauses, and articulation rate) align with the canonical master reference baseline.
        </p>
      </div>
    );
  }

  const flaws = resultData.flaws;
  const currentFlaw: GroundedFlaw = selectedRegion || flaws[0];
  const currentIndex = flaws.findIndex((f) => f.region_id === currentFlaw.region_id);

  const handleNext = () => {
    const nextIdx = (currentIndex + 1) % flaws.length;
    const nextFlaw = flaws[nextIdx];
    setSelectedRegion(nextFlaw);
    seekTo(nextFlaw.start_s);
  };

  const handlePrev = () => {
    const prevIdx = (currentIndex - 1 + flaws.length) % flaws.length;
    const prevFlaw = flaws[prevIdx];
    setSelectedRegion(prevFlaw);
    seekTo(prevFlaw.start_s);
  };

  return (
    <div className="glass-panel-glow p-6 rounded-2xl mb-6 border-indigo-500/40">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-red-500/20 text-red-400 border border-red-500/30">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white uppercase tracking-wider">
                {currentFlaw.flaw_type.replace('_', ' ')}
              </h3>
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/30">
                z = {currentFlaw.z_score > 0 ? `+${currentFlaw.z_score}` : currentFlaw.z_score}
              </span>
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Severity {currentFlaw.severity}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Region [{currentFlaw.start_s.toFixed(2)}s – {currentFlaw.end_s.toFixed(2)}s] • Words #{currentFlaw.start_word_idx}–{currentFlaw.end_word_idx}
            </p>
          </div>
        </div>

        {/* Flaw Carousel Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">
            Flaw {currentIndex + 1} of {flaws.length}
          </span>
          <button
            onClick={handlePrev}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Previous Flaw"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={handleNext}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Next Flaw"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Words in Region Quote */}
      <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80 mb-4 font-mono text-xs text-slate-300">
        <span className="text-slate-500 font-sans uppercase font-bold text-[10px] tracking-wider block mb-1">
          Affected Word Span
        </span>
        <span className="text-indigo-300 font-medium font-sans text-sm">"{currentFlaw.words}"</span>
      </div>

      {/* Secondary Deviations in Merged Regions */}
      {currentFlaw.secondary_types && currentFlaw.secondary_types.length > 0 && (
        <div className="bg-indigo-950/40 p-3.5 rounded-xl border border-indigo-500/30 mb-4 text-xs">
          <span className="text-indigo-400 font-bold uppercase text-[10px] tracking-wider block mb-1.5">
            Secondary Deviations (Co-Occurring Merged Flaws)
          </span>
          <div className="flex flex-wrap gap-2">
            {currentFlaw.secondary_types.map((sec, sidx) => (
              <span
                key={sidx}
                className="px-2.5 py-1 rounded-lg bg-indigo-900/60 border border-indigo-700/60 text-indigo-200 font-mono text-[11px] flex items-center gap-1.5"
              >
                <span className="font-sans font-semibold capitalize">{sec.flaw_type.replace('_', ' ')}</span>
                <span className="text-indigo-400">z = {sec.z_score > 0 ? `+${sec.z_score.toFixed(1)}` : sec.z_score.toFixed(1)}σ</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Exact Quantitative Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
          <span className="text-[11px] text-slate-400 block">Baseline Ideal</span>
          <span className="text-base font-mono font-bold text-slate-200">
            {currentFlaw.baseline_value} <span className="text-xs font-sans text-slate-400">{currentFlaw.unit}</span>
          </span>
        </div>

        <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
          <span className="text-[11px] text-slate-400 block">Observed Value</span>
          <span className="text-base font-mono font-bold text-red-400">
            {currentFlaw.observed_value} <span className="text-xs font-sans text-slate-400">{currentFlaw.unit}</span>
          </span>
        </div>

        <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
          <span className="text-[11px] text-slate-400 block">Statistical Delta (Δ)</span>
          <span className="text-base font-mono font-bold text-amber-300">
            {currentFlaw.delta > 0 ? `+${currentFlaw.delta}` : currentFlaw.delta} <span className="text-xs font-sans text-slate-400">{currentFlaw.unit}</span>
          </span>
        </div>

        <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
          <span className="text-[11px] text-slate-400 block">Robust Z-Score</span>
          <span className="text-base font-mono font-bold text-indigo-400">
            {currentFlaw.z_score > 0 ? `+${currentFlaw.z_score}` : currentFlaw.z_score} σ
          </span>
        </div>
      </div>

      {/* Structured Mathematical Rationale */}
      <div className="mb-3">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
          Mathematical Causal Diagnosis
        </h4>
        <p className="text-sm text-slate-200 leading-relaxed bg-slate-900/50 p-3 rounded-lg border border-slate-800">
          {currentFlaw.rationale_text}
        </p>
      </div>

      {/* Why It Hurts: Cognitive & Rhetorical Friction */}
      <div>
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <HelpCircle className="w-3.5 h-3.5 text-brand-accent" />
          Cognitive & Rhetorical Impact (Why It Hurts)
        </h4>
        <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/50 p-3 rounded-lg border border-slate-800">
          {currentFlaw.why_it_hurts}
        </p>
      </div>
    </div>
  );
};
