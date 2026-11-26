import React, { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js';
import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.esm.js';
import { Pause, Play, RotateCcw, ZoomIn, ZoomOut } from 'lucide-react';
import { useAudioStore } from '../store/useAudioStore';
import { flawMeta, withAlpha } from '../lib/catalog';
import { FlawLabel, Panel } from './ui';

const GT_HATCH = 'repeating-linear-gradient(135deg, #464e5a 0 2px, transparent 2px 5px)';

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = (seconds % 60).toFixed(1).padStart(4, '0');
  return `${mins}:${secs}`;
};

/** Step 3: waveform with detected flaw spans and the injected ground truth underneath. */
export const WaveformViewer: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const regionsRef = useRef<any>(null);
  const readyRef = useRef(false);

  const [zoom, setZoom] = useState<number>(0);
  const [audioError, setAudioError] = useState<boolean>(false);
  const {
    resultData,
    audioUrl,
    isPlaying,
    currentTime,
    duration,
    selectedRegion,
    setIsPlaying,
    setCurrentTime,
    setDuration,
    setSelectedRegion,
  } = useAudioStore();

  const drawRegions = () => {
    const regions = regionsRef.current;
    if (!regions || !resultData || !readyRef.current) return;
    regions.clearRegions();

    (resultData.ground_truth_flaws ?? []).forEach((gt: any, idx: number) => {
      const r = regions.addRegion({
        id: `gt_${idx}`,
        start: gt.start_s,
        end: gt.end_s,
        color: 'transparent',
        drag: false,
        resize: false,
      });
      if (r?.element) {
        Object.assign(r.element.style, {
          top: 'auto',
          bottom: '0',
          height: '7px',
          background: GT_HATCH,
          borderRadius: '1px',
          pointerEvents: 'none',
        });
        r.element.title = `Injected: ${flawMeta(gt.flaw_type).label} (${gt.start_s.toFixed(2)}–${gt.end_s.toFixed(2)} s)`;
      }
    });

    resultData.flaws.forEach((flaw) => {
      const color = flawMeta(flaw.flaw_type).color;
      const isSelected = selectedRegion?.region_id === flaw.region_id;
      const r = regions.addRegion({
        id: flaw.region_id,
        start: flaw.start_s,
        end: flaw.end_s,
        color: withAlpha(color, isSelected ? 0.3 : 0.14),
        drag: false,
        resize: false,
      });
      if (r?.element) {
        Object.assign(r.element.style, {
          height: 'calc(100% - 10px)',
          borderTop: `3px solid ${color}`,
          boxShadow: isSelected ? `inset 0 0 0 1px ${color}` : 'none',
          cursor: 'pointer',
        });
        r.element.title = `Detected: ${flawMeta(flaw.flaw_type).label} (${flaw.start_s.toFixed(2)}–${flaw.end_s.toFixed(2)} s)`;
      }
    });
  };

  useEffect(() => {
    if (!containerRef.current) return;
    wsRef.current?.destroy();
    readyRef.current = false;

    const regions = RegionsPlugin.create();
    regionsRef.current = regions;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: '#b3bac4',
      progressColor: '#464e5a',
      cursorColor: '#0f4c5c',
      cursorWidth: 2,
      height: 120,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      normalize: true,
      minPxPerSec: zoom,
      plugins: [
        regions,
        ...(timelineRef.current
          ? [
              TimelinePlugin.create({
                container: timelineRef.current,
                height: 18,
                timeInterval: 1,
                primaryLabelInterval: 5,
                secondaryLabelInterval: 0,
                style: { fontSize: '11px', color: '#69717d' },
              }),
            ]
          : []),
      ],
    });
    wsRef.current = ws;

    setAudioError(false);
    if (audioUrl) {
      ws.load(audioUrl).catch(() => setAudioError(true));
    }

    ws.on('ready', () => {
      readyRef.current = true;
      setDuration(ws.getDuration());
      drawRegions();
    });
    ws.on('timeupdate', (time) => setCurrentTime(time));
    ws.on('play', () => setIsPlaying(true));
    ws.on('pause', () => setIsPlaying(false));
    ws.on('finish', () => setIsPlaying(false));

    regions.on('region-clicked', (region: any, e: MouseEvent) => {
      e.stopPropagation();
      const flaw = useAudioStore.getState().resultData?.flaws.find((f) => f.region_id === region.id);
      if (flaw) {
        setSelectedRegion(flaw);
        region.play();
      }
    });

    const handleSeek = (e: any) => {
      if (wsRef.current && typeof e.detail?.time === 'number') {
        const dur = wsRef.current.getDuration() || 1;
        wsRef.current.seekTo(Math.min(1, Math.max(0, e.detail.time / dur)));
      }
    };
    window.addEventListener('speech_seek', handleSeek);

    return () => {
      window.removeEventListener('speech_seek', handleSeek);
      ws.destroy();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audioUrl, resultData]);

  // Restyle when the selected flaw changes.
  useEffect(() => {
    drawRegions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRegion]);

  useEffect(() => {
    if (wsRef.current && readyRef.current) {
      try {
        wsRef.current.zoom(zoom);
      } catch {
        // audio not decoded yet
      }
    }
  }, [zoom]);

  if (!resultData) return null;

  const typesPresent = Array.from(
    new Set([...resultData.flaws.map((f) => f.flaw_type as string), ...(resultData.ground_truth_flaws ?? []).map((g: any) => g.flaw_type)]),
  );

  return (
    <Panel
      title="Timeline"
      subtitle="Coloured spans are detected flaws; click one to hear it. The hatched bars along the bottom mark where flaws were injected."
    >
      <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[12px] text-ink-2">
        {typesPresent.map((t) => (
          <FlawLabel key={t} type={t} />
        ))}
        {(resultData.ground_truth_flaws?.length ?? 0) > 0 && (
          <span className="inline-flex items-center gap-1.5">
            <span aria-hidden className="inline-block h-2 w-4 rounded-[1px]" style={{ background: GT_HATCH }} />
            Injected (ground truth)
          </span>
        )}
      </div>

      <div className="overflow-hidden rounded-md border border-line bg-[#fbfbfc] px-3 pt-3">
        <div ref={containerRef} className="w-full" />
        <div ref={timelineRef} className="w-full pb-1" />
      </div>

      {audioError && (
        <p className="mt-2 text-[12px] text-warn">
          The audio for this recording isn't included in this demo yet, so the waveform is empty. Every analysis below still
          comes from the stored result.
        </p>
      )}

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => wsRef.current?.playPause()}
            className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-accent text-white transition-colors hover:bg-accent-hover"
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="ml-0.5 h-4 w-4" />}
          </button>
          <button
            onClick={() => {
              wsRef.current?.seekTo(0);
              setCurrentTime(0);
            }}
            className="btn h-9 w-9 px-0"
            aria-label="Back to start"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
          <span className="num ml-1 font-mono text-[13px] text-ink-2">
            {formatTime(currentTime)} <span className="text-ink-3">/ {formatTime(duration)}</span>
          </span>
        </div>

        <label className="flex items-center gap-2 text-ink-3">
          <ZoomOut className="h-4 w-4" />
          <input
            id="zoom-range"
            type="range"
            min="0"
            max="150"
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
            className="w-28 cursor-pointer accent-[#0f4c5c]"
            aria-label="Zoom"
          />
          <ZoomIn className="h-4 w-4" />
        </label>
      </div>
    </Panel>
  );
};
