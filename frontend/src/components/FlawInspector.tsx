import React from 'react';
import { CornerDownRight } from 'lucide-react';
import { useAudioStore } from '../store/useAudioStore';
import { flawMeta, fmtSigned } from '../lib/catalog';
import { GroundedFlaw } from '../types/api';
import { FlawLabel, FlawSwatch, Metric, Panel } from './ui';

/** Step 4: every detected flaw in a list, with the selected one explained in full. */
export const FlawInspector: React.FC = () => {
  const { resultData, selectedRegion, setSelectedRegion, seekTo } = useAudioStore();
  if (!resultData) return null;

  const flaws = resultData.flaws;
  const injected = resultData.ground_truth_flaws?.length ?? 0;

  if (flaws.length === 0) {
    return (
      <Panel title="Detected flaws">
        <p className="text-[13px] text-ink-2">
          No flaws were detected in this recording.
          {injected > 0 && ` ${injected} flaw${injected === 1 ? ' was' : 's were'} injected; the ground-truth check below lists what was missed.`}
        </p>
      </Panel>
    );
  }

  const current: GroundedFlaw = flaws.find((f) => f.region_id === selectedRegion?.region_id) ?? flaws[0];
  const select = (f: GroundedFlaw) => {
    setSelectedRegion(f);
    seekTo(f.start_s);
  };

  return (
    <Panel
      title="Detected flaws"
      subtitle="Select a flaw to see the measurement behind it."
      bodyClassName="grid md:grid-cols-[minmax(0,300px)_minmax(0,1fr)]"
    >
      <ol className="max-h-[420px] overflow-y-auto border-b border-line md:border-b-0 md:border-r">
        {flaws.map((f, i) => {
          const active = f.region_id === current.region_id;
          return (
            <li key={f.region_id}>
              <button
                onClick={() => select(f)}
                aria-current={active}
                className={`flex w-full items-start gap-3 border-b border-line px-4 py-3 text-left transition-colors last:border-b-0 ${
                  active ? 'bg-accent-soft' : 'hover:bg-surface-2'
                }`}
              >
                <span className="num mt-0.5 w-4 shrink-0 text-[12px] text-ink-3">{i + 1}</span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-center justify-between gap-2">
                    <FlawLabel type={f.flaw_type} className="text-[13px] font-medium text-ink" />
                    <span className="num font-mono text-[12px] text-ink-3">
                      {f.start_s.toFixed(2)}–{f.end_s.toFixed(2)} s
                    </span>
                  </span>
                  <span className="mt-0.5 block truncate text-[12px] text-ink-2">“{f.words}”</span>
                </span>
              </button>
            </li>
          );
        })}
      </ol>

      <div className="min-w-0 p-5">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <FlawSwatch type={current.flaw_type} size={12} />
          <h3 className="text-[17px] font-semibold text-ink">{flawMeta(current.flaw_type).label}</h3>
          <span className="num font-mono text-[12px] text-ink-3">
            {current.start_s.toFixed(2)}–{current.end_s.toFixed(2)} s · words {current.start_word_idx}–{current.end_word_idx}
          </span>
        </div>
        <blockquote className="mt-3 border-l-2 border-line-strong pl-3 text-[15px] leading-relaxed text-ink">
          “{current.words}”
        </blockquote>

        <div className="mt-4 grid grid-cols-2 gap-4 rounded-md border border-line px-4 py-3 sm:grid-cols-4">
          <Metric label="Reference" value={current.baseline_value} unit={current.unit} />
          <Metric label="This take" value={current.observed_value} unit={current.unit} />
          <Metric label="Change" value={fmtSigned(current.delta)} unit={current.unit} />
          <Metric label="Robust z" value={fmtSigned(current.z_score, 1)} hint={`severity ${current.severity}`} />
        </div>
        <p className="mt-1.5 font-mono text-[11px] text-ink-3">feature: {current.feature}</p>

        <div className="mt-4 space-y-3 text-[14px] leading-relaxed">
          <div>
            <div className="eyebrow mb-1">Why it was flagged</div>
            <p className="max-w-[70ch] text-ink">{current.rationale_text}</p>
          </div>
          <div>
            <div className="eyebrow mb-1">Why it matters to a listener</div>
            <p className="max-w-[70ch] text-ink-2">{current.why_it_hurts}</p>
          </div>
        </div>

        {current.secondary_types && current.secondary_types.length > 0 && (
          <div className="mt-4">
            <div className="eyebrow mb-1.5">Also present in this span</div>
            <div className="flex flex-wrap gap-2">
              {current.secondary_types.map((s, i) => (
                <span key={i} className="inline-flex items-center gap-1.5 rounded border border-line px-2 py-1 text-[12px] text-ink-2">
                  <CornerDownRight className="h-3 w-3 text-ink-3" />
                  <FlawLabel type={s.flaw_type} />
                  <span className="num font-mono text-ink-3">z {fmtSigned(s.z_score, 1)}</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
};
