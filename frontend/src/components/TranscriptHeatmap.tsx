import React, { useMemo } from 'react';
import { useAudioStore } from '../store/useAudioStore';
import { flawMeta, withAlpha } from '../lib/catalog';
import { WordMetric } from '../types/api';
import { Panel } from './ui';

const maxAbsZ = (w: WordMetric) => Math.max(0, ...Object.values(w.z_by_feature ?? {}).map((v) => Math.abs(v)));

/** Step 6: the aligned transcript, with detected flaw spans underlined in their type colour. */
export const TranscriptHeatmap: React.FC = () => {
  const { resultData, currentTime, selectedWord, seekTo, setSelectedWord } = useAudioStore();

  // Map each word index to the flaw type that covers it (from the detected spans).
  const flawByWord = useMemo(() => {
    const m = new Map<number, string>();
    resultData?.flaws.forEach((f) => {
      for (let i = f.start_word_idx; i <= f.end_word_idx; i++) if (!m.has(i)) m.set(i, f.flaw_type);
    });
    return m;
  }, [resultData]);

  if (!resultData?.words?.length) return null;

  return (
    <Panel
      title="Transcript"
      subtitle="Words are placed by forced alignment. Underlined words fall inside a detected flaw; dotted words deviate strongly (|z| ≥ 2.5) without being flagged. Click a word to jump to it."
    >
      <p className="max-w-[90ch] text-[15px] leading-[2.1] text-ink">
        {resultData.words.map((w) => {
          const flawType = flawByWord.get(w.index);
          const z = maxAbsZ(w);
          const isCurrent = currentTime >= w.start && currentTime <= w.end;
          const isSelected = selectedWord?.index === w.index;
          const style: React.CSSProperties = flawType
            ? {
                background: withAlpha(flawMeta(flawType).color, 0.12),
                boxShadow: `inset 0 -2px 0 ${flawMeta(flawType).color}`,
              }
            : {};
          const longPause = w.pause_after_s >= 0.35 && !w.has_punctuation;
          return (
            <React.Fragment key={w.index}>
              <span className="group relative inline-block">
                <button
                  onClick={() => {
                    setSelectedWord(w);
                    seekTo(w.start);
                  }}
                  style={style}
                  className={`rounded-[3px] px-[3px] transition-colors ${
                    isCurrent ? 'bg-accent text-white' : isSelected ? 'outline outline-1 outline-accent' : 'hover:bg-surface-2'
                  } ${!flawType && z >= 2.5 ? 'underline decoration-ink-3 decoration-dotted underline-offset-4' : ''}`}
                >
                  {w.text}
                  {w.punctuation}
                </button>
                <span
                  role="tooltip"
                  className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-1.5 hidden w-max -translate-x-1/2 rounded-md border border-line bg-surface px-3 py-2 text-[12px] leading-snug text-ink-2 shadow-[0_4px_16px_rgba(20,24,30,0.12)] group-hover:block"
                >
                  <span className="block font-medium text-ink">
                    “{w.text}” · word {w.index}
                  </span>
                  <span className="num block font-mono">
                    {w.start.toFixed(2)}–{w.end.toFixed(2)} s
                  </span>
                  <span className="num block">pitch range {w.f0_range_st ?? '—'} st · rate {w.articulation_rate ?? '—'} syl/s</span>
                  <span className="num block">max |z| {z.toFixed(1)}</span>
                  {flawType && <span className="block">in a {flawMeta(flawType).label.toLowerCase()} span</span>}
                </span>
              </span>
              {w.pause_after_s > 0.15 && (
                <span
                  title={`Pause of ${w.pause_after_s.toFixed(2)} s${longPause ? ' with no punctuation' : ''}`}
                  className={`num mx-0.5 align-middle font-mono text-[11px] ${longPause ? 'text-warn' : 'text-ink-3'}`}
                >
                  ‹{w.pause_after_s.toFixed(2)}s›
                </span>
              )}{' '}
            </React.Fragment>
          );
        })}
      </p>
    </Panel>
  );
};
