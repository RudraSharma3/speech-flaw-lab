import React, { useMemo } from 'react';
import { useAudioStore } from '../store/useAudioStore';
import { Metric, Notice, Panel } from './ui';

/**
 * Voice quality, real measurements only: per-word HNR from the stored result and jitter
 * when the pipeline raised a HIGH_JITTER flag. Shimmer is not measured by the pipeline,
 * so it is not shown.
 */
export const ClarityPanel: React.FC = () => {
  const { resultData, selectedWord, setSelectedWord, seekTo } = useAudioStore();

  const hnr = useMemo(() => {
    const vals = (resultData?.words ?? [])
      .map((w: any) => w.hnr_mean_db)
      .filter((v: any): v is number => typeof v === 'number' && Number.isFinite(v))
      .sort((a, b) => a - b);
    return vals.length ? vals[Math.floor(vals.length / 2)] : null;
  }, [resultData]);

  if (!resultData?.words?.length) return null;
  const jitter = resultData.quality_flags?.find((q) => q.code === 'HIGH_JITTER');

  return (
    <Panel
      title="Voice quality"
      subtitle="Harmonics-to-noise ratio per word, measured with Praat. Breathiness flags are switched off in reference mode because old recordings are noisy."
    >
      <div className="grid gap-4 sm:grid-cols-[minmax(0,240px)_minmax(0,1fr)]">
        <div className="space-y-4">
          <Metric label="Median HNR" value={hnr !== null ? hnr.toFixed(1) : '—'} unit="dB" hint="across aligned words" />
          <Metric
            label="Jitter"
            value={jitter?.metric_value != null ? (jitter.metric_value * 100).toFixed(1) : '—'}
            unit={jitter?.metric_value != null ? '%' : undefined}
            hint={jitter ? 'flagged as elevated by the pipeline' : 'not flagged for this recording'}
          />
          <Notice tone="neutral">
            1933–1986 broadcast and tape audio lowers HNR on its own, so compare takes of the same speech, not speakers.
          </Notice>
        </div>

        <div className="max-h-[300px] overflow-auto rounded-md border border-line">
          <table className="w-full text-left text-[13px]">
            <thead className="sticky top-0 bg-surface-2">
              <tr className="text-ink-3">
                <th className="eyebrow px-3 py-2 font-medium">#</th>
                <th className="eyebrow px-3 py-2 font-medium">Word</th>
                <th className="eyebrow px-3 py-2 text-right font-medium">Time</th>
                <th className="eyebrow px-3 py-2 text-right font-medium">HNR</th>
              </tr>
            </thead>
            <tbody>
              {resultData.words.map((w: any) => (
                <tr
                  key={w.index}
                  onClick={() => {
                    setSelectedWord(w);
                    seekTo(w.start);
                  }}
                  className={`cursor-pointer border-t border-line ${selectedWord?.index === w.index ? 'bg-accent-soft' : 'hover:bg-surface-2/60'}`}
                >
                  <td className="num px-3 py-1.5 text-ink-3">{w.index}</td>
                  <td className="px-3 py-1.5 text-ink">{w.text}</td>
                  <td className="num px-3 py-1.5 text-right font-mono text-[12px] text-ink-2">{w.start.toFixed(2)} s</td>
                  <td className="num px-3 py-1.5 text-right font-mono text-[12px] text-ink">
                    {typeof w.hnr_mean_db === 'number' ? `${w.hnr_mean_db.toFixed(1)} dB` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Panel>
  );
};
