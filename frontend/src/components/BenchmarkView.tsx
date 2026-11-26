import React, { useEffect, useState } from 'react';
import { ArrowRight, Loader2 } from 'lucide-react';
import { Plot } from './PlotComponent';
import { useAudioStore } from '../store/useAudioStore';
import { FLAW_META, LEVELS, SPEECHES, recordingId } from '../lib/catalog';
import { FlawLabel, Metric, Notice, Panel, StatusBadge } from './ui';

const pct = (v: number | undefined | null, d = 1) => (v == null ? '—' : `${v.toFixed(d)}%`);
const FONT = '"IBM Plex Sans", system-ui, sans-serif';

const GateRow: React.FC<{ name: string; detail: React.ReactNode; value: React.ReactNode; target: string; status?: string }> = ({
  name,
  detail,
  value,
  target,
  status,
}) => (
  <div className="grid gap-x-6 gap-y-1 px-5 py-4 md:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)_auto] md:items-center">
    <div className="min-w-0">
      <div className="text-[14px] font-medium text-ink">{name}</div>
      <div className="text-[13px] text-ink-2">{detail}</div>
    </div>
    <div className="num">
      <span className="text-[20px] font-semibold text-ink">{value}</span>
      <span className="ml-2 text-[12px] text-ink-3">target {target}</span>
    </div>
    <div>
      {status === 'PASS' && <StatusBadge tone="good">Passes</StatusBadge>}
      {status === 'FAIL' && <StatusBadge tone="crit">Fails</StatusBadge>}
    </div>
  </div>
);

/** Dataset-level results, read from results/benchmark.json. */
export const BenchmarkView: React.FC = () => {
  const { setView, loadRecording } = useAudioStore();
  const [bm, setBm] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [speechId, setSpeechId] = useState('fdr_fear_itself_1933');

  useEffect(() => {
    fetch('/api/benchmark')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('results/benchmark.json is not available.'))))
      .then(setBm)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <Notice tone="crit">{error}</Notice>;
  if (!bm) {
    return (
      <div className="flex items-center gap-2 text-[13px] text-ink-3">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading benchmark results
      </div>
    );
  }

  const gates = bm.gates ?? {};
  const recall = gates.l01_recall_target_80 ?? {};
  const nullCtl = gates.null_injection_control ?? {};
  const l4 = gates.level4_false_positives ?? {};
  const levels = [0, 1, 2, 3].map((l) => ({ level: l, ...(bm.by_quality_level?.[`level_${l}`] ?? {}) }));
  const totalInjected = levels.reduce((a, l) => a + (l.gt_count ?? 0), 0);
  const types = Object.keys(bm.by_flaw_type ?? {}).sort((a, b) => Object.keys(FLAW_META).indexOf(a) - Object.keys(FLAW_META).indexOf(b));
  const ta = bm.type_accuracy_among_matches?.at_iou_03;
  const pr = bm.pairwise_ranking_l0_l3;
  const ba = bm.boundary_accuracy ?? {};

  const raw: number[] = bm.score_tables?.contrastive_uncalibrated?.[speechId] ?? [];
  const cal: number[] = bm.score_tables?.contrastive_isotonic_calibrated?.[speechId] ?? [];
  const refFree: number[] = bm.score_tables?.reference_free_uncalibrated?.[speechId] ?? [];
  const levelLabels = LEVELS.map((l) => `L${l.level}`);
  const speech = SPEECHES.find((s) => s.id === speechId)!;

  const open = (level: number) => {
    loadRecording(recordingId(speechId, level, ''));
    setView('recording');
    window.scrollTo({ top: 0 });
  };

  return (
    <div className="space-y-6">
      <div className="max-w-[75ch]">
        <h1 className="text-[22px] font-semibold tracking-tight text-ink">Benchmark</h1>
        <p className="mt-1 text-[14px] text-ink-2">
          75 recordings: 5 speech excerpts × 5 quality levels × 3 injection seeds, with{' '}
          <span className="num font-medium text-ink">{totalInjected}</span> injected flaws in L0–L3. Every figure on this page is
          read from <code className="font-mono text-[12px]">results/benchmark.json</code>, written by{' '}
          <code className="font-mono text-[12px]">python -m dataset_tools.run_benchmark</code>.
        </p>
      </div>

      <Panel title="Targets" bodyClassName="divide-y divide-line">
        <GateRow
          name="Recall on L0 and L1 flaws"
          detail={`A flaw counts as found when a detection overlaps it by IoU ≥ 0.3. At IoU ≥ 0.5 recall is ${pct(recall.achieved_recall_05)}.`}
          value={pct(recall.achieved_recall_03)}
          target={`≥ ${recall.target ?? 80}%`}
          status={recall.status}
        />
        <GateRow
          name="False alarms with nothing injected"
          detail={`Null control: each reference run through the injector with every effect at identity (${nullCtl.total_duration_s ?? '—'} s of audio).`}
          value={`${nullCtl.fp_rate_flags_per_min?.toFixed(2) ?? '—'} / min`}
          target="≤ 2.0 / min"
          status={nullCtl.status}
        />
        <GateRow
          name="False alarms on L4 reference takes"
          detail={`Tuning speeches ${l4.tuning_rate_flags_per_min?.toFixed(2) ?? '—'} / min, held-out speech ${l4.heldout_rate_flags_per_min?.toFixed(2) ?? '—'} / min.`}
          value={`${Math.max(l4.tuning_rate_flags_per_min ?? 0, l4.heldout_rate_flags_per_min ?? 0).toFixed(2)} / min`}
          target={`≤ ${l4.target ?? 2.0} / min`}
          status={l4.status}
        />
      </Panel>

      <Panel title="Detection by quality level" subtitle="All 5 speeches and 3 seeds pooled. Matching is one-to-one." bodyClassName="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-[13px]">
            <thead>
              <tr className="border-b border-line bg-surface-2/70">
                {['Level', 'Injected', 'Detected', 'Found', 'Precision', 'Recall', 'F1', 'Recall @0.5'].map((h, i) => (
                  <th key={h} className={`eyebrow px-4 py-2 font-medium ${i ? 'text-right' : ''}`}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {levels.map((l) => (
                <tr key={l.level} className="border-b border-line last:border-b-0">
                  <td className="whitespace-nowrap px-4 py-2.5 text-ink">
                    L{l.level} <span className="text-ink-3">{LEVELS.find((x) => x.level === l.level)?.name}</span>
                  </td>
                  <td className="num px-4 py-2.5 text-right font-mono">{l.gt_count}</td>
                  <td className="num px-4 py-2.5 text-right font-mono">{l.det_count}</td>
                  <td className="num px-4 py-2.5 text-right font-mono">{l.matched_03}</td>
                  <td className="num px-4 py-2.5 text-right font-mono">{pct(l.precision_03)}</td>
                  <td className="num px-4 py-2.5 text-right font-mono font-medium text-ink">{pct(l.recall_03)}</td>
                  <td className="num px-4 py-2.5 text-right font-mono">{pct(l.f1_03)}</td>
                  <td className="num px-4 py-2.5 text-right font-mono text-ink-2">{pct(l.recall_05)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Recall by flaw type" subtitle="The detected type must match the injected type (IoU ≥ 0.3).">
          <div className="space-y-3">
            {types.map((t) => {
              const row = bm.by_flaw_type[t];
              return (
                <div key={t}>
                  <div className="flex items-baseline justify-between gap-3 text-[13px]">
                    <FlawLabel type={t} className="text-ink" />
                    <span className="num font-mono text-ink">
                      {pct(row.strict_recall_03)}{' '}
                      <span className="text-ink-3">
                        ({row.strict_matched_03} of {row.gt_count})
                      </span>
                    </span>
                  </div>
                  <div className="mt-1 h-2 overflow-hidden rounded-full bg-surface-2">
                    <div className="h-full rounded-full bg-accent" style={{ width: `${Math.min(100, row.strict_recall_03)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>

        <Panel title="Other measurements" bodyClassName="grid gap-5 p-5 sm:grid-cols-2">
        <Metric
          label="Type correct, when found"
          value={pct(ta?.accuracy_percent)}
          hint={ta ? `${ta.correct_type} of ${ta.total_matched} matches` : undefined}
        />
        <Metric
          label="Boundary error, single spans"
          value={ba.single_regions?.median_start_ms?.toFixed(0) ?? '—'}
          unit="ms"
          hint={`median start; end ${ba.single_regions?.median_end_ms?.toFixed(0) ?? '—'} ms (n=${ba.single_regions?.count ?? '—'})`}
        />
        <Metric
          label="Boundary error, merged spans"
          value={ba.merged_regions?.median_start_ms?.toFixed(0) ?? '—'}
          unit="ms"
          hint={`median start; end ${ba.merged_regions?.median_end_ms?.toFixed(0) ?? '—'} ms (n=${ba.merged_regions?.count ?? '—'})`}
        />
        <Metric
          label="Levels ranked correctly"
          value={pct(pr?.accuracy_percent, 2)}
          hint={pr ? `${pr.total_pairs - pr.violations} of ${pr.total_pairs} L0–L3 pairs; 95% CI ${pr.cluster_bootstrap_95_ci?.[0]}–${pr.cluster_bootstrap_95_ci?.[1]}%` : undefined}
        />
        </Panel>
      </div>

      <Panel
        title="Score by quality level"
        subtitle="Mean over the three seeds. The calibration curve is fitted on the four tuning speeches, so only the held-out speech's calibrated scores are out-of-sample."
        actions={
          <select id="benchmark-speech" className="field w-auto min-w-[260px]" value={speechId} onChange={(e) => setSpeechId(e.target.value)}>
            {SPEECHES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.speaker}: {s.label}
                {s.split === 'held-out' ? ' (held-out)' : ''}
              </option>
            ))}
          </select>
        }
        bodyClassName="grid gap-4 p-5 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]"
      >
        <Plot
          data={[
            {
              type: 'bar',
              x: levelLabels,
              y: raw,
              name: 'Contrastive score',
              marker: { color: '#0f4c5c' },
              width: 0.45,
              text: raw.map((v) => v.toFixed(1)),
              textposition: 'outside',
              textfont: { size: 11, color: '#464e5a' },
              cliponaxis: false,
              hovertemplate: '%{x}: %{y:.1f}<extra>Contrastive</extra>',
            },
            {
              type: 'scatter',
              mode: 'lines+markers',
              x: levelLabels,
              y: cal,
              name: 'Calibrated',
              line: { color: '#14181e', width: 2 },
              marker: { size: 8, color: '#14181e', line: { color: '#ffffff', width: 2 } },
              hovertemplate: '%{x}: %{y:.1f}<extra>Calibrated</extra>',
            },
          ]}
          layout={{
            height: 280,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: '#ffffff',
            font: { family: FONT, color: '#464e5a' },
            margin: { l: 40, r: 10, t: 30, b: 30 },
            legend: { orientation: 'h', x: 0, y: 1.16, font: { size: 12 } },
            yaxis: { range: [0, 108], gridcolor: '#eceef1', zeroline: false, tickfont: { size: 10, color: '#69717d' } },
            xaxis: { tickfont: { size: 12, color: '#14181e' }, linecolor: '#c4cad3' },
            hoverlabel: { bgcolor: '#ffffff', bordercolor: '#c4cad3', font: { family: FONT, size: 12, color: '#14181e' } },
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: '100%' }}
        />
        <div className="min-w-0 overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-line">
                {['Level', 'Contrastive', 'Calibrated', 'No reference', ''].map((h, i) => (
                  <th key={i} className={`eyebrow px-2 py-2 font-medium ${i && i < 4 ? 'text-right' : ''}`}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {LEVELS.map((l, i) => (
                <tr key={l.level} className="border-b border-line last:border-b-0">
                  <td className="px-2 py-2 text-ink">L{l.level}</td>
                  <td className="num px-2 py-2 text-right font-mono">{raw[i]?.toFixed(1) ?? '—'}</td>
                  <td className="num px-2 py-2 text-right font-mono">{cal[i]?.toFixed(1) ?? '—'}</td>
                  <td className="num px-2 py-2 text-right font-mono text-ink-2">{refFree[i]?.toFixed(1) ?? '—'}</td>
                  <td className="px-2 py-2 text-right">
                    <button className="inline-flex items-center gap-1 text-[12px] font-medium text-accent hover:underline" onClick={() => open(l.level)}>
                      Open <ArrowRight className="h-3 w-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-[12px] text-ink-3">
            {speech.speaker}, {speech.label}. “Open” loads seed 0 of that level.
          </p>
        </div>
      </Panel>

      <Panel title="Limitations">
        <ul className="max-w-[80ch] list-disc space-y-1.5 pl-5 text-[14px] text-ink-2">
          <li>
            Every flaw was created by this project's own injector (time-stretch, pitch flattening, inserted silence), not by real
            speakers. Results on natural speech are not measured yet.
          </li>
          <li>Three speakers, all American men, recorded between 1933 and 1986. Tuning used Kennedy and Reagan; Roosevelt is held out.</li>
          <li>
            L3 flaws are too mild to detect: recall {pct(bm.by_quality_level?.level_3?.recall_03)}. Monotone is the hardest type:
            recall {pct(bm.by_flaw_type?.monotone?.strict_recall_03)}.
          </li>
          <li>
            Small sample: {totalInjected} injected flaws in total, {bm.by_flaw_type?.inappropriate_pause?.gt_count ?? '—'} of them
            misplaced pauses.
          </li>
        </ul>
      </Panel>
    </div>
  );
};
