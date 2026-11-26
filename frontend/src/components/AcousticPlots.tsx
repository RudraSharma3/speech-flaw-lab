import React, { useState } from 'react';
import { Plot } from './PlotComponent';
import { useAudioStore } from '../store/useAudioStore';
import { flawMeta, withAlpha } from '../lib/catalog';
import { Panel, Segmented } from './ui';

const INK = '#14181e';
const INK_2 = '#464e5a';
const INK_3 = '#69717d';
const GRID = '#eceef1';
const REF = '#9aa2ad';
const FONT = '"IBM Plex Sans", system-ui, sans-serif';

type Mode = 'contours' | 'spectrogram' | 'mfcc';

/**
 * Step 7: pitch, loudness and speaking rate over time (three panels, one shared time axis),
 * this take against the reference take. Spectrogram / MFCC views appear only when the
 * stored result actually contains those matrices; nothing is synthesised here.
 */
export const AcousticPlots: React.FC = () => {
  const { resultData, currentTime, selectedRegion, seekTo } = useAudioStore();
  const [mode, setMode] = useState<Mode>('contours');
  if (!resultData?.series) return null;

  const { series, flaws } = resultData;
  const t = series.t;
  const hasSpec = !!series.spectrogram?.matrix?.length;
  const hasMfcc = !!series.mfcc?.matrix?.length;
  const activeMode: Mode = (mode === 'spectrogram' && !hasSpec) || (mode === 'mfcc' && !hasMfcc) ? 'contours' : mode;

  const shapes: any[] = flaws.map((f) => {
    const color = flawMeta(f.flaw_type).color;
    const selected = selectedRegion?.region_id === f.region_id;
    return {
      type: 'rect',
      xref: 'x',
      yref: 'paper',
      x0: f.start_s,
      x1: f.end_s,
      y0: 0,
      y1: 1,
      fillcolor: withAlpha(color, selected ? 0.2 : 0.09),
      line: { width: selected ? 1 : 0, color },
      layer: 'below',
    };
  });
  shapes.push({
    type: 'line',
    xref: 'x',
    yref: 'paper',
    x0: currentTime,
    x1: currentTime,
    y0: 0,
    y1: 1,
    line: { color: '#0f4c5c', width: 1.5 },
  });

  const axis = (title: string, domain: [number, number]) => ({
    domain,
    title: { text: title, font: { size: 11, color: INK_3 }, standoff: 6 },
    gridcolor: GRID,
    zeroline: false,
    linecolor: '#c4cad3',
    tickfont: { size: 10, color: INK_3 },
    automargin: true,
  });

  let data: any[] = [];
  let layout: any = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: '#ffffff',
    font: { family: FONT, color: INK_2 },
    margin: { l: 56, r: 16, t: 36, b: 40 },
    height: 470,
    hovermode: 'x unified',
    hoverlabel: { bgcolor: '#ffffff', bordercolor: '#c4cad3', font: { family: FONT, size: 12, color: INK } },
    shapes,
  };

  if (activeMode === 'contours') {
    const line = (y: any, name: string, yaxis: string, color: string, extra: any = {}) => {
      const { line: lineExtra, ...rest } = extra;
      return {
        x: t,
        y,
        name,
        yaxis,
        mode: 'lines',
        type: 'scatter',
        ...rest,
        line: { color, width: 2, ...(lineExtra ?? {}) },
      };
    };
    // The pitch tracker emits a few deep outlier frames (octave errors); fit the pitch axis to
    // the central range so the contour stays readable. Exact values remain in the hover.
    const finite = [...series.f0_st, ...series.f0_base_st]
      .filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
      .sort((a, b) => a - b);
    const q = (p: number) => finite[Math.min(finite.length - 1, Math.max(0, Math.floor(p * (finite.length - 1))))];
    const pitchRange = finite.length ? [Math.floor(q(0.05)) - 2, Math.ceil(q(0.995)) + 2] : undefined;
    data = [
      { x: t, y: series.f0_mad_upper_st ?? [], yaxis: 'y', mode: 'lines', type: 'scatter', line: { width: 0 }, hoverinfo: 'skip', showlegend: false },
      {
        x: t,
        y: series.f0_mad_lower_st ?? [],
        yaxis: 'y',
        mode: 'lines',
        type: 'scatter',
        fill: 'tonexty',
        fillcolor: 'rgba(20, 24, 30, 0.06)',
        line: { width: 0 },
        name: 'Reference ±1.5 MAD',
        hoverinfo: 'skip',
      },
      line(series.f0_base_st, 'Reference take', 'y', REF, { line: { width: 1.5, dash: 'dash' } }),
      line(series.f0_st, 'This take', 'y', INK, { connectgaps: false }),
      line(series.energy_base_db, 'Reference take', 'y2', REF, { line: { width: 1.5, dash: 'dash' }, showlegend: false }),
      line(series.energy_db, 'This take', 'y2', INK, { showlegend: false }),
      line(series.rate, 'This take', 'y3', INK, { line: { width: 1.5, shape: 'hv' }, showlegend: false }),
    ];
    layout = {
      ...layout,
      legend: { orientation: 'h', x: 0, y: 1.08, font: { size: 12, color: INK_2 }, bgcolor: 'rgba(0,0,0,0)' },
      xaxis: {
        anchor: 'y3',
        title: { text: 'Time (s)', font: { size: 11, color: INK_3 } },
        gridcolor: GRID,
        zeroline: false,
        linecolor: '#c4cad3',
        tickfont: { size: 10, color: INK_3 },
      },
      yaxis: { ...axis('Pitch (st re median)', [0.7, 1]), ...(pitchRange ? { range: pitchRange } : {}) },
      yaxis2: axis('Loudness (dB)', [0.36, 0.64]),
      yaxis3: axis('Rate (syl/s)', [0, 0.28]),
    };
  } else {
    const m = activeMode === 'spectrogram' ? series.spectrogram! : series.mfcc!;
    data = [
      {
        type: 'heatmap',
        z: m.matrix,
        x: m.times,
        y: activeMode === 'spectrogram' ? (series.spectrogram as any).freqs : (series.mfcc as any).coefficients,
        colorscale: 'Blues',
        reversescale: false,
        colorbar: { thickness: 10, tickfont: { size: 10, color: INK_3 } },
      },
    ];
    layout = {
      ...layout,
      xaxis: { title: { text: 'Time (s)', font: { size: 11, color: INK_3 } }, tickfont: { size: 10, color: INK_3 } },
      yaxis: { title: { text: activeMode === 'spectrogram' ? 'Frequency (Hz)' : 'Coefficient', font: { size: 11, color: INK_3 } }, tickfont: { size: 10, color: INK_3 } },
    };
  }

  const views = [
    { value: 'contours' as Mode, label: 'Contours' },
    ...(hasSpec ? [{ value: 'spectrogram' as Mode, label: 'Spectrogram' }] : []),
    ...(hasMfcc ? [{ value: 'mfcc' as Mode, label: 'MFCC' }] : []),
  ];

  return (
    <Panel
      title="Prosody over time"
      subtitle="Pitch, loudness and speaking rate for this take, with the reference take dashed. Shaded bands are detected flaws. The pitch axis shows the central 5–99.5% of frames; hover for exact values. Click the chart to jump there."
      actions={views.length > 1 ? <Segmented<Mode> ariaLabel="Chart view" value={activeMode} onChange={setMode} options={views} /> : undefined}
      bodyClassName="px-3 pb-2 pt-1"
    >
      <Plot
        data={data}
        layout={layout}
        config={{ responsive: true, displayModeBar: false }}
        onClick={(e: any) => e?.points?.[0] && seekTo(e.points[0].x)}
        style={{ width: '100%' }}
      />
    </Panel>
  );
};
