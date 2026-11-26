import React from 'react';
import { useAudioStore } from '../store/useAudioStore';
import { GroundTruthEvalRow } from '../types/api';
import { FlawLabel, Panel, StatusBadge } from './ui';

const span = (s?: [number, number] | null) => (s ? `${s[0].toFixed(2)}–${s[1].toFixed(2)} s` : null);

/** Step 5: one-to-one match of detections against the injected ground truth. */
export const GroundTruthTable: React.FC = () => {
  const { resultData, seekTo, setSelectedRegion } = useAudioStore();
  const rows = resultData?.ground_truth_eval ?? [];
  if (!resultData || rows.length === 0) return null;

  const onRow = (row: GroundTruthEvalRow) => {
    const match = row.detected_id ? resultData.flaws.find((f) => f.region_id === row.detected_id) : undefined;
    if (match) {
      setSelectedRegion(match);
      seekTo(match.start_s);
    } else if (row.gt_span) {
      seekTo(row.gt_span[0]);
    }
  };

  return (
    <Panel
      title="Check against injected ground truth"
      subtitle="Each detection is paired with at most one injected flaw (Hungarian matching on time overlap, IoU ≥ 0.3). Click a row to jump to it."
      bodyClassName="overflow-x-auto"
    >
      <table className="w-full min-w-[720px] text-left text-[13px]">
        <thead>
          <tr className="border-b border-line bg-surface-2/70 text-ink-3">
            <th className="eyebrow px-4 py-2 font-medium">Result</th>
            <th className="eyebrow px-4 py-2 font-medium">Detected</th>
            <th className="eyebrow px-4 py-2 font-medium">Injected</th>
            <th className="eyebrow px-4 py-2 text-right font-medium">IoU</th>
            <th className="eyebrow px-4 py-2 text-right font-medium">Start error</th>
            <th className="eyebrow px-4 py-2 text-right font-medium">End error</th>
            <th className="eyebrow px-4 py-2 font-medium">Words</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const matched = row.status === 'MATCHED';
            return (
              <tr key={i} onClick={() => onRow(row)} className="cursor-pointer border-b border-line last:border-b-0 hover:bg-surface-2/60">
                <td className="px-4 py-2.5 align-top">
                  {matched && <StatusBadge tone="good">Found</StatusBadge>}
                  {row.status === 'FALSE_POSITIVE' && <StatusBadge tone="crit">False alarm</StatusBadge>}
                  {row.status === 'MISSED_GT' && <StatusBadge tone="warn">Missed</StatusBadge>}
                  {matched && !row.type_match && <div className="mt-1 text-[11px] text-ink-3">type differs</div>}
                </td>
                <td className="px-4 py-2.5 align-top">
                  {row.detected_type ? (
                    <>
                      <FlawLabel type={row.detected_type} className="text-ink" />
                      <div className="num font-mono text-[11px] text-ink-3">{span(row.detected_span)}</div>
                    </>
                  ) : (
                    <span className="text-ink-3">—</span>
                  )}
                </td>
                <td className="px-4 py-2.5 align-top">
                  {row.gt_type ? (
                    <>
                      <FlawLabel type={row.gt_type} className="text-ink" />
                      <div className="num font-mono text-[11px] text-ink-3">{span(row.gt_span)}</div>
                    </>
                  ) : (
                    <span className="text-ink-3">—</span>
                  )}
                </td>
                <td className="num px-4 py-2.5 text-right align-top font-mono">{matched ? row.iou.toFixed(2) : '—'}</td>
                <td className="num px-4 py-2.5 text-right align-top font-mono">
                  {matched && row.start_error_ms != null ? `${row.start_error_ms.toFixed(0)} ms` : '—'}
                </td>
                <td className="num px-4 py-2.5 text-right align-top font-mono">
                  {matched && row.end_error_ms != null ? `${row.end_error_ms.toFixed(0)} ms` : '—'}
                </td>
                <td className="max-w-[260px] truncate px-4 py-2.5 align-top text-ink-2" title={row.detected_words || row.gt_words || ''}>
                  “{row.detected_words || row.gt_words || ''}”
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Panel>
  );
};
