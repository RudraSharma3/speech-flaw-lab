import React from 'react';
import { useAudioStore } from '../store/useAudioStore';
import { Award, CheckCircle2, AlertCircle, Info } from 'lucide-react';

export const ScoreCard: React.FC = () => {
  const { resultData } = useAudioStore();

  if (!resultData || !resultData.scores) {
    return null;
  }

  const { scores, quality_flags, meta } = resultData;

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-emerald-400 bg-emerald-500/20 border-emerald-500/40';
    if (score >= 70) return 'text-blue-400 bg-blue-500/20 border-blue-500/40';
    if (score >= 50) return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/40';
    return 'text-red-400 bg-red-500/20 border-red-500/40';
  };

  const getProgressBarColor = (score: number) => {
    if (score >= 85) return 'bg-emerald-500';
    if (score >= 70) return 'bg-blue-500';
    if (score >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="glass-panel p-6 rounded-2xl mb-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-6 border-b border-slate-800">
        <div className="flex items-center gap-4">
          {/* Circular / Badge Grade Display */}
          <div
            className={`w-20 h-20 rounded-2xl flex flex-col items-center justify-center border ${getScoreColor(scores.overall)} cursor-help transition-all hover:scale-105`}
            title={`Raw Rubric Score: ${scores.raw_overall !== undefined ? scores.raw_overall.toFixed(1) : scores.overall.toFixed(1)} / 100 (Uncalibrated)`}
          >
            <span className="text-2xl font-black tracking-tight">{scores.grade}</span>
            <span className="text-xs font-mono font-bold">{scores.overall.toFixed(1)}/100</span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Award className="w-6 h-6 text-brand-primary" />
                Deterministic Rubric Evaluation
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 border border-slate-700 text-slate-300">
                Tier Level {scores.quality_level_est} / 4
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1.5">
              <span
                className="px-2.5 py-0.5 rounded text-[11px] font-medium bg-indigo-950/70 border border-indigo-700/60 text-indigo-300 cursor-help"
                title={`Raw Uncalibrated Score: ${scores.raw_overall !== undefined ? scores.raw_overall.toFixed(1) : scores.overall.toFixed(1)} / 100`}
              >
                calibrated on the injected gradient (tuning speeches)
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Reference: <span className="text-slate-300 font-medium">{meta.reference_id || 'LibriSpeech Population Priors'}</span> • Alignment: <span className="text-indigo-300 font-mono">{meta.alignment_engine}</span>
            </p>
          </div>
        </div>

        {/* Quality Flags */}
        {quality_flags && quality_flags.length > 0 && (
          <div className="flex flex-col gap-1.5 text-xs">
            {quality_flags.map((flag, idx) => (
              <div
                key={idx}
                className={`px-3 py-1.5 rounded-lg border flex items-center gap-2 ${
                  flag.severity === 'WARNING'
                    ? 'bg-amber-950/40 border-amber-800 text-amber-300'
                    : flag.severity === 'ERROR'
                    ? 'bg-red-950/40 border-red-800 text-red-300'
                    : 'bg-slate-900 border-slate-800 text-slate-300'
                }`}
              >
                {flag.severity === 'WARNING' ? (
                  <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                ) : (
                  <Info className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                )}
                <span>{flag.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Dimension Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
        {scores.dimensions.map((dim) => (
          <div key={dim.id} className="bg-slate-900/70 p-4 rounded-xl border border-slate-800/80 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-white">{dim.name}</span>
                <span className="text-xs font-mono font-bold text-slate-200">
                  {dim.score.toFixed(1)} <span className="text-[10px] text-slate-400">({(dim.weight * 100).toFixed(0)}% wt)</span>
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden mb-2">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${getProgressBarColor(dim.score)}`}
                  style={{ width: `${dim.score}%` }}
                />
              </div>
            </div>

            <div className="mt-2 pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
              <span className="block text-slate-300 font-medium mb-0.5">{dim.summary}</span>
              <span className="font-mono text-[10px] text-slate-500">Metric z = {dim.metric_z > 0 ? `+${dim.metric_z}` : dim.metric_z}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
