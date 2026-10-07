import React from 'react';
import { useAudioStore } from '../store/useAudioStore';
import { FileText, Clock } from 'lucide-react';
import { WordMetric } from '../types/api';

export const TranscriptHeatmap: React.FC = () => {
  const { resultData, currentTime, hoveredWord, selectedWord, seekTo, setHoveredWord, setSelectedWord } =
    useAudioStore();

  if (!resultData || !resultData.words) {
    return null;
  }

  const words = resultData.words;

  const getZScoreColor = (word: WordMetric) => {
    if (word.is_flawed) {
      return 'bg-red-500/20 text-red-300 border-red-500/50 hover:bg-red-500/30';
    }
    const maxZ = Math.max(
      ...Object.values(word.z_by_feature || {}).map((v) => Math.abs(v)),
      0
    );

    if (maxZ >= 2.5) {
      return 'bg-orange-500/20 text-orange-300 border-orange-500/50 hover:bg-orange-500/30';
    }
    if (maxZ >= 1.5) {
      return 'bg-yellow-500/15 text-yellow-300 border-yellow-500/40 hover:bg-yellow-500/25';
    }
    return 'bg-slate-800/60 text-slate-200 border-slate-700/60 hover:bg-slate-700/80';
  };

  return (
    <div className="glass-panel p-5 rounded-2xl mb-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-brand-accent" />
          Aligned Transcript & Word-Level Deviation Heat-Strip
        </h2>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-slate-700" /> Normal (|z|&lt;1.5)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-yellow-500/50" /> Moderate (1.5≤|z|&lt;2.5)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-red-500/60" /> Flawed (|z|≥2.5)
          </span>
        </div>
      </div>

      <p className="text-xs text-slate-400 mb-4">
        Every token is snapped to exact forced-alignment boundaries. Click any word to jump audio and inspect local acoustic metrics.
      </p>

      {/* Transcript Tokens Flow */}
      <div className="bg-slate-950/80 p-5 rounded-xl border border-slate-800 flex flex-wrap gap-x-1.5 gap-y-2.5 items-center leading-relaxed font-mono text-sm">
        {words.map((word) => {
          const isCurrent = currentTime >= word.start && currentTime <= word.end;
          const isSelected = selectedWord?.index === word.index;
          const colorClasses = getZScoreColor(word);

          return (
            <React.Fragment key={word.index}>
              <button
                onClick={() => {
                  setSelectedWord(word);
                  seekTo(word.start);
                }}
                onMouseEnter={() => setHoveredWord(word)}
                onMouseLeave={() => setHoveredWord(null)}
                className={`px-2 py-1 rounded-md border text-xs font-semibold transition-all relative group ${colorClasses} ${
                  isCurrent ? 'ring-2 ring-brand-primary shadow-lg scale-105 z-10' : ''
                } ${isSelected ? 'border-brand-accent font-bold' : ''}`}
              >
                <span>{word.text}</span>
                {word.punctuation && <span className="text-slate-400">{word.punctuation}</span>}

                {/* Floating Word Inspection Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:flex flex-col gap-1 p-2.5 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl text-[11px] text-slate-200 z-50 whitespace-nowrap pointer-events-none">
                  <div className="font-bold text-white border-b border-slate-800 pb-1 flex items-center justify-between gap-3">
                    <span>Word #{word.index}: "{word.text}"</span>
                    <span className="text-slate-400">{word.duration.toFixed(2)}s</span>
                  </div>
                  <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 mt-1 font-sans">
                    <span className="text-slate-400">Time:</span>
                    <span>{word.start.toFixed(2)}s - {word.end.toFixed(2)}s</span>
                    <span className="text-slate-400">Pitch Range:</span>
                    <span>{word.f0_range_st ?? '--'} st</span>
                    <span className="text-slate-400">Speech Rate:</span>
                    <span>{word.articulation_rate ?? '--'} syl/s</span>
                    <span className="text-slate-400">Max |z| Score:</span>
                    <span className={word.is_flawed ? 'text-red-400 font-bold' : 'text-slate-200'}>
                      {Math.max(...Object.values(word.z_by_feature || {}).map(Math.abs), 0).toFixed(1)}
                    </span>
                  </div>
                </div>
              </button>

              {/* Injected / Measured Pause Pill */}
              {word.pause_after_s > 0.15 && (
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-sans border ${
                    word.pause_after_s >= 0.35 && !word.has_punctuation
                      ? 'bg-red-950/60 text-red-400 border-red-700'
                      : 'bg-slate-900 text-slate-500 border-slate-800'
                  }`}
                  title={`Pause duration: ${word.pause_after_s}s`}
                >
                  <Clock className="w-2.5 h-2.5 inline mr-0.5" />
                  {word.pause_after_s.toFixed(2)}s
                </span>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
