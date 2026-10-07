import React from 'react';
import Plot from 'react-plotly.js';
import { useAudioStore } from '../store/useAudioStore';
import { Activity, BarChart2 } from 'lucide-react';

export const AcousticPlots: React.FC = () => {
  const { resultData, currentTime, selectedRegion, seekTo } = useAudioStore();

  if (!resultData || !resultData.series) {
    return (
      <div className="glass-panel p-6 rounded-2xl text-center text-slate-400">
        No acoustic time-series data available.
      </div>
    );
  }

  const { series, flaws } = resultData;
  const t = series.t;

  // Shapes for vertical playback cursor and flaw regions
  const shapes: any[] = [
    // Current Playback Cursor
    {
      type: 'line',
      x0: currentTime,
      x1: currentTime,
      y0: 0,
      y1: 1,
      yref: 'paper',
      line: {
        color: '#f43f5e',
        width: 2,
        dash: 'solid',
      },
    },
  ];

  // Add Flaw region background spans
  flaws.forEach((flaw) => {
    const isSelected = selectedRegion?.region_id === flaw.region_id;
    shapes.push({
      type: 'rect',
      x0: flaw.start_s,
      x1: flaw.end_s,
      y0: 0,
      y1: 1,
      yref: 'paper',
      fillcolor: isSelected ? 'rgba(99, 102, 241, 0.22)' : 'rgba(239, 68, 68, 0.10)',
      line: {
        color: isSelected ? '#6366f1' : 'rgba(239, 68, 68, 0.4)',
        width: isSelected ? 2 : 1,
        dash: isSelected ? 'solid' : 'dot',
      },
    });
  });

  // Plotly Traces:
  // Subplot 1: Pitch F0 in Semitones re Median
  const f0Upper = {
    x: t,
    y: series.f0_mad_upper_st || [],
    mode: 'lines',
    line: { width: 0, color: 'transparent' },
    name: '+1.5 MAD Baseline',
    showlegend: false,
    hoverinfo: 'skip',
    xaxis: 'x',
    yaxis: 'y1',
  };

  const f0Lower = {
    x: t,
    y: series.f0_mad_lower_st || [],
    mode: 'lines',
    fill: 'tonexty',
    fillcolor: 'rgba(99, 102, 241, 0.12)',
    line: { width: 0, color: 'transparent' },
    name: '±1.5 MAD Confidence Band',
    hoverinfo: 'skip',
    xaxis: 'x',
    yaxis: 'y1',
  };

  const f0Baseline = {
    x: t,
    y: series.f0_base_st,
    mode: 'lines',
    line: { color: '#9ca3af', width: 1.5, dash: 'dash' },
    name: 'Baseline Ideal F0 (st)',
    xaxis: 'x',
    yaxis: 'y1',
  };

  const f0Observed = {
    x: t,
    y: series.f0_st,
    mode: 'lines',
    line: { color: '#ec4899', width: 2.2 },
    name: 'Observed F0 (st)',
    xaxis: 'x',
    yaxis: 'y1',
  };

  // Subplot 2: Energy in dB re Median
  const energyBaseline = {
    x: t,
    y: series.energy_base_db,
    mode: 'lines',
    line: { color: '#9ca3af', width: 1.5, dash: 'dash' },
    name: 'Baseline Energy (dB)',
    xaxis: 'x',
    yaxis: 'y2',
  };

  const energyObserved = {
    x: t,
    y: series.energy_db,
    mode: 'lines',
    line: { color: '#38bdf8', width: 2.0 },
    name: 'Observed Energy (dB)',
    xaxis: 'x',
    yaxis: 'y2',
  };

  // Subplot 3: Articulation Rate (Syllables/sec)
  const rateTrace = {
    x: t,
    y: series.rate,
    mode: 'lines',
    line: { color: '#fbbf24', width: 2.0, shape: 'hv' },
    name: 'Speech Rate (syl/s)',
    xaxis: 'x',
    yaxis: 'y3',
  };

  const layout: any = {
    grid: { rows: 3, columns: 1, pattern: 'independent', roworder: 'top to bottom' },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'rgba(15, 23, 42, 0.65)',
    margin: { l: 55, r: 25, t: 25, b: 40 },
    height: 480,
    showlegend: true,
    legend: {
      orientation: 'h',
      x: 0.0,
      y: 1.14,
      font: { color: '#cbd5e1', size: 10 },
      bgcolor: 'transparent',
    },
    hovermode: 'x unified',
    shapes: shapes,
    xaxis: {
      anchor: 'y3',
      showgrid: true,
      gridcolor: '#1e293b',
      zerolinecolor: '#334155',
      tickfont: { color: '#94a3b8', size: 10 },
      title: { text: 'Time (seconds)', font: { color: '#94a3b8', size: 11 } },
    },
    yaxis: {
      domain: [0.70, 1.0],
      title: { text: 'F0 (st re med)', font: { color: '#ec4899', size: 10 } },
      gridcolor: '#1e293b',
      tickfont: { color: '#94a3b8', size: 9 },
      range: [-8, 8],
    },
    yaxis2: {
      domain: [0.36, 0.64],
      title: { text: 'Energy (dB)', font: { color: '#38bdf8', size: 10 } },
      gridcolor: '#1e293b',
      tickfont: { color: '#94a3b8', size: 9 },
      range: [-20, 10],
    },
    yaxis3: {
      domain: [0.0, 0.28],
      title: { text: 'Rate (syl/s)', font: { color: '#fbbf24', size: 10 } },
      gridcolor: '#1e293b',
      tickfont: { color: '#94a3b8', size: 9 },
      range: [0, 10],
    },
  };

  const handlePlotClick = (event: any) => {
    if (event.points && event.points[0]) {
      const clickedX = event.points[0].x;
      seekTo(clickedX);
    }
  };

  return (
    <div className="glass-panel p-5 rounded-2xl mb-6">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-brand-secondary" />
          Synchronized Acoustic Contours vs Canonical Baseline
        </h2>
        <span className="text-xs text-slate-400">Click anywhere on plot to seek audio</span>
      </div>

      <div className="rounded-xl overflow-hidden border border-slate-800">
        <Plot
          data={[f0Upper, f0Lower, f0Baseline, f0Observed, energyBaseline, energyObserved, rateTrace]}
          layout={layout}
          config={{ responsive: true, displayModeBar: false }}
          onClick={handlePlotClick}
          style={{ width: '100%' }}
        />
      </div>
    </div>
  );
};
