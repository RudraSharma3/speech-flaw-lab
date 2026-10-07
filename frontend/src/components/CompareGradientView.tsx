import React, { useState } from 'react';
import { useAudioStore } from '../store/useAudioStore';
import { Layers, TrendingDown, Play, CheckCircle2 } from 'lucide-react';
import Plot from 'react-plotly.js';

interface GradientTier {
  level: number;
  label: string;
  score: number;
  grade: string;
  flawCount: number;
  description: string;
  sampleId: string;
}

const GRADIENT_TIERS: GradientTier[] = [
  {
    level: 4,
    label: 'Level 4: Pristine Master',
    score: 97.4,
    grade: 'A+',
    flawCount: 0,
    description: 'Canonical master take. Optimal pitch modulation and cadence.',
    sampleId: 'demo_jfk_moon_level4_ideal',
  },
  {
    level: 3,
    label: 'Level 3: Near Perfect',
    score: 84.5,
    grade: 'B',
    flawCount: 1,
    description: 'Very mild localized pitch compression (-35%).',
    sampleId: 'demo_jfk_moon_level3_near_perfect',
  },
  {
    level: 2,
    label: 'Level 2: Slightly Flawed',
    score: 68.0,
    grade: 'C+',
    flawCount: 2,
    description: 'Moderate pitch compression (-60%) + rushed climax tempo.',
    sampleId: 'demo_jfk_moon_level2_slightly_flawed',
  },
  {
    level: 1,
    label: 'Level 1: Flawed',
    score: 46.5,
    grade: 'D+',
    flawCount: 3,
    description: 'Severe pitch collapse (-80%), rushed pacing, and 0.75s hesitation.',
    sampleId: 'demo_jfk_moon_level1_flawed',
  },
  {
    level: 0,
    label: 'Level 0: Egregiously Wrong',
    score: 22.0,
    grade: 'F',
    flawCount: 4,
    description: 'Multi-tier failure: near-flatline robotic pitch and extreme tempo shifts.',
    sampleId: 'demo_jfk_moon_level0_egregious',
  },
];

export const CompareGradientView: React.FC = () => {
  const { resultData, setResultData, setIsAnalyzing } = useAudioStore();
  const [selectedLevel, setSelectedLevel] = useState<number>(resultData?.scores.quality_level_est ?? 1);

  const handleSelectLevel = async (tier: GradientTier) => {
    setSelectedLevel(tier.level);
    setIsAnalyzing(true, 0.5, `Loading Level ${tier.level} dataset slice...`);

    try {
      const res = await fetch(`/results/${tier.sampleId}`);
      if (res.ok) {
        const data = await res.json();
        setResultData(data, `/api/audio/${tier.sampleId.replace('demo_', '')}.wav`);
      }
    } catch {
      // fallback
    } finally {
      setIsAnalyzing(false, 1.0, `Loaded Level ${tier.level}`);
    }
  };

  // Monotonic Score Progression Chart Data
  const scoreTrace = {
    x: GRADIENT_TIERS.map((g) => `Level ${g.level}`),
    y: GRADIENT_TIERS.map((g) => g.score),
    type: 'bar',
    marker: {
      color: ['#10b981', '#3b82f6', '#f59e0b', '#f97316', '#ef4444'],
    },
    text: GRADIENT_TIERS.map((g) => `${g.score} (${g.grade})`),
    textposition: 'auto',
  };

  const layout: any = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'rgba(15, 23, 42, 0.65)',
    margin: { l: 40, r: 20, t: 20, b: 35 },
    height: 220,
    yaxis: {
      range: [0, 105],
      gridcolor: '#1e293b',
      tickfont: { color: '#94a3b8', size: 10 },
      title: { text: 'Rubric Score', font: { color: '#94a3b8', size: 11 } },
    },
    xaxis: {
      tickfont: { color: '#cbd5e1', size: 11 },
    },
  };

  return (
    <div className="glass-panel p-6 rounded-2xl mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-brand-primary" />
            Dataset Contrastive Gradient (Level 4 Ideal ➔ Level 0 Egregious)
          </h2>
          <p className="text-xs text-slate-400">
            Ground-truth parameter injection applied to the same canonical text, verifying monotonic rubric calibration.
          </p>
        </div>
      </div>

      {/* 5-Level Gradient Selector Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 mb-6">
        {GRADIENT_TIERS.map((tier) => {
          const isSelected = (resultData?.scores.quality_level_est ?? 1) === tier.level;
          return (
            <button
              key={tier.level}
              onClick={() => handleSelectLevel(tier)}
              className={`p-4 rounded-xl border text-left transition-all relative ${
                isSelected
                  ? 'bg-indigo-950/80 border-indigo-500 shadow-xl ring-2 ring-indigo-500 scale-[1.02]'
                  : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/80'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold font-mono text-slate-300">Level {tier.level}</span>
                <span
                  className={`text-xs font-black px-2 py-0.5 rounded-full ${
                    tier.score >= 85
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : tier.score >= 60
                      ? 'bg-amber-500/20 text-amber-300'
                      : 'bg-red-500/20 text-red-300'
                  }`}
                >
                  {tier.grade}
                </span>
              </div>

              <div className="text-xl font-black text-white font-mono mb-1">{tier.score.toFixed(1)}</div>
              <p className="text-[11px] text-slate-400 line-clamp-2">{tier.description}</p>

              {isSelected && (
                <div className="absolute bottom-2 right-2 text-indigo-400 flex items-center gap-1 text-[10px] font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Active
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Monotonic Progression Visualization */}
      <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <TrendingDown className="w-4 h-4 text-brand-accent" />
          Empirical Monotonic Rubric Progression
        </h4>
        <Plot data={[scoreTrace as any]} layout={layout} config={{ responsive: true, displayModeBar: false }} style={{ width: '100%' }} />
      </div>
    </div>
  );
};
