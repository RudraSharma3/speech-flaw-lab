import React, { useEffect, useState } from 'react';
import { AlertTriangle, Users, Sliders, ShieldX, Info } from 'lucide-react';

interface BenchmarkData {
  gates?: {
    l01_recall_target_80?: {
      achieved_recall_03: number;
      achieved_recall_05: number;
      status: string;
    };
    null_injection_control?: {
      fp_rate_flags_per_min: number;
      status: string;
    };
  };
  boundary_accuracy?: {
    single_regions?: {
      median_start_ms: number;
      p90_start_ms: number;
    };
    merged_regions?: {
      median_start_ms: number;
      p90_start_ms: number;
    };
  };
  by_quality_level?: {
    level_3?: {
      recall_03: number;
      det_count: number;
      gt_count: number;
    };
  };
  by_flaw_type?: {
    monotone?: {
      strict_recall_03: number;
      strict_precision_03: number;
    };
  };
}

export const LimitationsPanel: React.FC = () => {
  const [benchmark, setBenchmark] = useState<BenchmarkData | null>(null);

  useEffect(() => {
    fetch('/api/benchmark')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setBenchmark(data);
      })
      .catch(() => {});
  }, []);

  const l3Recall = benchmark?.by_quality_level?.level_3?.recall_03 ?? 0.0;
  const monotoneRecall = benchmark?.by_flaw_type?.monotone?.strict_recall_03 ?? 28.3;
  const singleMedian = benchmark?.boundary_accuracy?.single_regions?.median_start_ms ?? 200.0;
  const mergedMedian = benchmark?.boundary_accuracy?.merged_regions?.median_start_ms ?? 223.0;

  return (
    <div className="glass-panel p-5 rounded-2xl mb-6 border-amber-500/30">
      <div className="flex items-center gap-2 mb-3">
        <AlertTriangle className="w-5 h-5 text-amber-400" />
        <h3 className="text-base font-bold text-white">System Limitations & Scope Boundaries</h3>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/30">
          Evaluated from results/benchmark.json
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        {/* Limitation 1: Historical Demographic Bias */}
        <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 font-bold text-slate-200 mb-1">
              <Users className="w-4 h-4 text-indigo-400" />
              <span>3 Historical Male Speakers</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              Corpus spans JFK (1962), Reagan (1986), and FDR (1933). Does not include female voices, modern casual speech, or accented non-native delivery.
            </p>
          </div>
          <div className="mt-2.5 pt-2 border-t border-slate-800 text-[10px] text-indigo-300 font-mono">
            Demographic Scope: Historical American Political Oratory
          </div>
        </div>

        {/* Limitation 2: Level 3 Detection Threshold */}
        <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 font-bold text-slate-200 mb-1">
              <Sliders className="w-4 h-4 text-amber-400" />
              <span>Level 3 (Near-Perfect) Undetectable</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              Subtle -35% pitch compression falls below the 2.0σ detection threshold to prevent false alarms on natural oratorical variations.
            </p>
          </div>
          <div className="mt-2.5 pt-2 border-t border-slate-800 text-[10px] text-amber-400 font-mono">
            Level 3 Recall: {l3Recall.toFixed(1)}% (Targeted design trade-off)
          </div>
        </div>

        {/* Limitation 3: Monotone Recall & Boundary Accuracy */}
        <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 font-bold text-slate-200 mb-1">
              <ShieldX className="w-4 h-4 text-rose-400" />
              <span>Monotone Sensitivity & Boundary Shift</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              Pitch flattening without tempo alteration is difficult to isolate from solemn pacing. Region boundary median start error: {singleMedian.toFixed(0)} ms (single) vs {mergedMedian.toFixed(0)} ms (merged).
            </p>
          </div>
          <div className="mt-2.5 pt-2 border-t border-slate-800 text-[10px] text-rose-300 font-mono">
            Monotone Strict Recall: {monotoneRecall.toFixed(1)}%
          </div>
        </div>
      </div>
    </div>
  );
};
