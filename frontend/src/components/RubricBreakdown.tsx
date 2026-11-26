import React from 'react';
import { useAudioStore } from '../store/useAudioStore';
import { fmtSigned } from '../lib/catalog';
import { Panel } from './ui';

/** Step 8: how the overall score is built from the five rubric dimensions (configs/rubric.yaml). */
export const RubricBreakdown: React.FC = () => {
  const { resultData } = useAudioStore();
  if (!resultData?.scores?.dimensions?.length) return null;

  return (
    <Panel
      title="Score breakdown"
      subtitle="The overall score is a weighted sum of five rubric dimensions, each scored 0–100."
      bodyClassName="divide-y divide-line"
    >
      {resultData.scores.dimensions.map((d) => (
        <div key={d.id} className="grid gap-x-6 gap-y-1.5 px-5 py-3.5 md:grid-cols-[minmax(0,240px)_minmax(0,1fr)_minmax(0,1.2fr)] md:items-center">
          <div className="min-w-0">
            <div className="text-[13px] font-medium text-ink">{d.name}</div>
            <div className="num text-[12px] text-ink-3">weight {(d.weight * 100).toFixed(0)}%</div>
          </div>
          <div className="flex items-center gap-3">
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-2">
              <div className="h-full rounded-full bg-accent" style={{ width: `${Math.max(0, Math.min(100, d.score))}%` }} />
            </div>
            <span className="num w-10 text-right font-mono text-[13px] text-ink">{d.score.toFixed(1)}</span>
          </div>
          <div className="min-w-0 text-[12px] text-ink-2">
            {d.summary} <span className="num font-mono text-ink-3">z {fmtSigned(d.metric_z, 2)}</span>
          </div>
        </div>
      ))}
    </Panel>
  );
};
