import React from 'react';
import { useAudioStore } from '../store/useAudioStore';
import { Notice, StatusBadge } from './ui';

/** Step 2: the headline numbers for the loaded recording. */
export const SummaryStrip: React.FC = () => {
  const { resultData } = useAudioStore();
  if (!resultData) return null;

  const { scores, meta, quality_flags, flaws } = resultData;
  const extra = scores as any;
  const evalRows = resultData.ground_truth_eval ?? [];
  const hasGt = (resultData.ground_truth_flaws?.length ?? 0) > 0 || evalRows.length > 0;
  const matched = evalRows.filter((r) => r.status === 'MATCHED').length;
  const falseAlarms = evalRows.filter((r) => r.status === 'FALSE_POSITIVE').length;
  const missed = evalRows.filter((r) => r.status === 'MISSED_GT').length;
  const injected = resultData.ground_truth_flaws?.length ?? matched + missed;

  return (
    <div className="space-y-3">
      <div className="grid gap-px overflow-hidden rounded-card border border-line bg-line sm:grid-cols-2 lg:grid-cols-[1.1fr_1.3fr_1fr]">
        {/* Overall score */}
        <div className="bg-surface px-5 py-4">
          <div className="eyebrow">Overall delivery score</div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="num text-[40px] font-semibold leading-none tracking-tight text-ink">{scores.overall.toFixed(1)}</span>
            <span className="text-[15px] text-ink-3">/ 100</span>
            <span className="ml-1 rounded border border-line-strong px-1.5 py-0.5 text-[13px] font-semibold text-ink">
              {scores.grade}
            </span>
          </div>
          <p className="mt-2 text-[13px] text-ink-2">
            Estimated level <span className="num font-medium text-ink">L{scores.quality_level_est}</span> of 4
            {scores.raw_overall !== undefined && (
              <span className="text-ink-3"> · uncalibrated {scores.raw_overall.toFixed(1)}</span>
            )}
          </p>
          {(extra.mode_label || extra.calibration_label) && (
            <p className="mt-0.5 text-[12px] text-ink-3">
              {[extra.mode_label, extra.calibration_label].filter(Boolean).join(' · ')}
            </p>
          )}
        </div>

        {/* Ground-truth check */}
        <div className="bg-surface px-5 py-4">
          <div className="eyebrow">Detected vs injected flaws</div>
          {hasGt ? (
            <>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <StatusBadge tone={matched > 0 ? 'good' : 'neutral'}>{matched} found</StatusBadge>
                <StatusBadge tone={missed > 0 ? 'warn' : 'neutral'}>{missed} missed</StatusBadge>
                <StatusBadge tone={falseAlarms > 0 ? 'crit' : 'neutral'}>
                  {falseAlarms} false alarm{falseAlarms === 1 ? '' : 's'}
                </StatusBadge>
              </div>
              <p className="mt-2 text-[13px] text-ink-2">
                <span className="num font-medium text-ink">{flaws.length}</span> detected,{' '}
                <span className="num font-medium text-ink">{injected}</span> injected. A detection counts as found when it
                overlaps an injected flaw by IoU ≥ 0.3.
              </p>
            </>
          ) : (
            <p className="mt-2 text-[13px] text-ink-2">
              <span className="num font-medium text-ink">{flaws.length}</span> flaw{flaws.length === 1 ? '' : 's'} detected.
              No ground truth exists for this recording.
            </p>
          )}
        </div>

        {/* Recording facts */}
        <div className="bg-surface px-5 py-4 sm:col-span-2 lg:col-span-1">
          <div className="eyebrow">Recording</div>
          <dl className="mt-2 grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1 text-[13px]">
            <dt className="text-ink-3">Length</dt>
            <dd className="num text-ink">{meta.duration_s.toFixed(1)} s</dd>
            <dt className="text-ink-3">Reference</dt>
            <dd className="truncate text-ink" title={meta.reference_id ?? undefined}>
              {meta.reference_id ?? 'Population priors (no reference take)'}
            </dd>
            <dt className="text-ink-3">Aligner</dt>
            <dd className="font-mono text-[12px] text-ink">{meta.alignment_engine}</dd>
            <dt className="text-ink-3">Median pitch</dt>
            <dd className="num text-ink">{meta.speaker_f0_median_hz.toFixed(1)} Hz</dd>
          </dl>
        </div>
      </div>

      {extra.transcript_coverage_warning && (
        <Notice tone="warn" title="Transcript coverage.">
          {extra.transcript_coverage_warning}
        </Notice>
      )}
      {extra.self_comparison_warning && (
        <Notice tone="crit" title="Self-comparison.">
          {extra.self_comparison_warning}
        </Notice>
      )}
      {quality_flags
        ?.filter(
          (f) =>
            f.code !== 'HIGH_JITTER' &&
            !(f.code === 'LOW_TRANSCRIPT_COVERAGE' && extra.transcript_coverage_warning) &&
            !(f.code === 'SELF_COMPARISON_WARNING' && extra.self_comparison_warning),
        )
        .map((flag, i) => (
          <Notice key={i} tone={flag.severity === 'ERROR' ? 'crit' : flag.severity === 'WARNING' ? 'warn' : 'info'}>
            {flag.message}
          </Notice>
        ))}
    </div>
  );
};
