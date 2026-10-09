import React from 'react';
import { useAudioStore } from '../store/useAudioStore';
import { Target, CheckCircle2, AlertOctagon, AlertTriangle } from 'lucide-react';
import { GroundTruthEvalRow } from '../types/api';

export const GroundTruthTable: React.FC = () => {
  const { resultData, seekTo, setSelectedRegion } = useAudioStore();

  const evalRows = resultData?.ground_truth_eval || [];
  const gtFlaws = resultData?.ground_truth_flaws || [];

  if (evalRows.length === 0 && gtFlaws.length === 0) {
    return null;
  }

  const handleRowClick = (row: GroundTruthEvalRow) => {
    if (row.detected_id && resultData?.flaws) {
      const match = resultData.flaws.find((f) => f.region_id === row.detected_id);
      if (match) {
        setSelectedRegion(match);
        seekTo(match.start_s);
        return;
      }
    }
    if (row.gt_span) {
      seekTo(row.gt_span[0]);
    } else if (row.detected_span) {
      seekTo(row.detected_span[0]);
    }
  };

  const matchedCount = evalRows.filter((r) => r.status === 'MATCHED').length;
  const fpCount = evalRows.filter((r) => r.status === 'FALSE_POSITIVE').length;
  const missedCount = evalRows.filter((r) => r.status === 'MISSED_GT').length;

  return (
    <div className="glass-panel p-5 rounded-2xl mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Target className="w-5 h-5 text-amber-400" />
            Ground-Truth Flaw Alignment & Boundary Verification
          </h3>
          <p className="text-xs text-slate-400">
            One-to-one bipartite Hungarian IoU matching against known injected flaw parameters (IoU threshold ≥ 0.3).
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {matchedCount} Matched
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-500/30 font-semibold flex items-center gap-1">
            <AlertOctagon className="w-3.5 h-3.5" />
            {fpCount} False Positives
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" />
            {missedCount} Missed GT
          </span>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/70">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-900/90 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3">Detected Flaw</th>
              <th className="py-2.5 px-3">Ground Truth Flaw</th>
              <th className="py-2.5 px-3">IoU</th>
              <th className="py-2.5 px-3">Start Error</th>
              <th className="py-2.5 px-3">End Error</th>
              <th className="py-2.5 px-3">Affected Words</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
            {evalRows.map((row, idx) => {
              const isMatched = row.status === 'MATCHED';
              const isFp = row.status === 'FALSE_POSITIVE';
              const isMiss = row.status === 'MISSED_GT';

              return (
                <tr
                  key={idx}
                  onClick={() => handleRowClick(row)}
                  className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                >
                  <td className="py-2 px-3">
                    {isMatched && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        MATCHED
                      </span>
                    )}
                    {isFp && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                        FALSE POS
                      </span>
                    )}
                    {isMiss && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        MISSED
                      </span>
                    )}
                  </td>

                  <td className="py-2 px-3">
                    {row.detected_type ? (
                      <div>
                        <span className="font-sans font-bold text-slate-200">
                          {row.detected_type.replace('_', ' ')}
                        </span>
                        {row.detected_span && (
                          <div className="text-[10px] text-slate-500">
                            [{row.detected_span[0].toFixed(2)}s – {row.detected_span[1].toFixed(2)}s]
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>

                  <td className="py-2 px-3">
                    {row.gt_type ? (
                      <div>
                        <span className="font-sans font-bold text-amber-300">
                          {row.gt_type.replace('_', ' ')}
                        </span>
                        {row.gt_span && (
                          <div className="text-[10px] text-slate-500">
                            [{row.gt_span[0].toFixed(2)}s – {row.gt_span[1].toFixed(2)}s]
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>

                  <td className="py-2 px-3">
                    {isMatched ? (
                      <span className="font-bold text-emerald-400">{(row.iou * 100).toFixed(1)}%</span>
                    ) : (
                      <span className="text-slate-600">0.0%</span>
                    )}
                  </td>

                  <td className="py-2 px-3">
                    {row.start_error_ms !== null && row.start_error_ms !== undefined ? (
                      <span className={row.start_error_ms > 500 ? 'text-amber-400' : 'text-slate-300'}>
                        {row.start_error_ms.toFixed(0)} ms
                      </span>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>

                  <td className="py-2 px-3">
                    {row.end_error_ms !== null && row.end_error_ms !== undefined ? (
                      <span className={row.end_error_ms > 500 ? 'text-amber-400' : 'text-slate-300'}>
                        {row.end_error_ms.toFixed(0)} ms
                      </span>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>

                  <td className="py-2 px-3 max-w-xs truncate font-sans text-slate-300">
                    "{row.detected_words || row.gt_words || '—'}"
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
