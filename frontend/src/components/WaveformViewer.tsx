import React, { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js';
import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.esm.js';
import { Play, Pause, RotateCcw, Volume2, ZoomIn, ZoomOut } from 'lucide-react';
import { useAudioStore } from '../store/useAudioStore';
import { GroundedFlaw, FlawType } from '../types/api';

const FLAW_COLORS: Record<FlawType, string> = {
  monotone: 'rgba(236, 72, 153, 0.35)',
  rushed: 'rgba(249, 115, 22, 0.35)',
  drag_slow: 'rgba(168, 85, 247, 0.35)',
  inappropriate_pause: 'rgba(239, 68, 68, 0.45)',
  missing_pause: 'rgba(234, 179, 8, 0.40)',
  volume_drop: 'rgba(59, 130, 246, 0.35)',
  breathy_unclear: 'rgba(20, 184, 166, 0.35)',
};

const FLAW_BORDER_COLORS: Record<FlawType, string> = {
  monotone: '#ec4899',
  rushed: '#f97316',
  drag_slow: '#a855f7',
  inappropriate_pause: '#ef4444',
  missing_pause: '#eab308',
  volume_drop: '#3b82f6',
  breathy_unclear: '#14b8a6',
};

export const WaveformViewer: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const regionsPluginRef = useRef<any>(null);

  const [zoom, setZoom] = useState<number>(50);
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

  // Initialize WaveSurfer
  useEffect(() => {
    if (!containerRef.current) return;

    if (wsRef.current) {
      wsRef.current.destroy();
    }

    const regions = RegionsPlugin.create();
    regionsPluginRef.current = regions;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: '#4b5563',
      progressColor: '#6366f1',
      cursorColor: '#f43f5e',
      cursorWidth: 2,
      height: 100,
      normalize: true,
      minPxPerSec: zoom,
      plugins: [
        regions,
        ...(timelineRef.current
          ? [
              TimelinePlugin.create({
                container: timelineRef.current,
                height: 20,
                timeInterval: 1,
                primaryLabelInterval: 5,
                secondaryLabelInterval: 1,
                style: {
                  fontSize: '10px',
                  color: '#9ca3af',
                },
              }),
            ]
          : []),
      ],
    });

    wsRef.current = ws;

    // Load audio or synthetic buffer
    if (audioUrl) {
      ws.load(audioUrl);
    }

    ws.on('ready', () => {
      setDuration(ws.getDuration());
      renderRegions(regions);
    });

    ws.on('timeupdate', (time) => {
      setCurrentTime(time);
    });

    ws.on('play', () => setIsPlaying(true));
    ws.on('pause', () => setIsPlaying(false));
    ws.on('finish', () => setIsPlaying(false));

    // Handle region click
    regions.on('region-clicked', (region: any, e: MouseEvent) => {
      e.stopPropagation();
      const flawMatch = resultData?.flaws.find((f) => f.region_id === region.id);
      if (flawMatch) {
        setSelectedRegion(flawMatch);
        region.play();
      }
    });

    // Custom seek listener
    const handleCustomSeek = (e: any) => {
      if (wsRef.current && typeof e.detail?.time === 'number') {
        const targetTime = e.detail.time;
        const dur = wsRef.current.getDuration() || 1;
        wsRef.current.seekTo(targetTime / dur);
      }
    };
    window.addEventListener('speech_seek', handleCustomSeek);

    return () => {
      window.removeEventListener('speech_seek', handleCustomSeek);
      ws.destroy();
    };
  }, [audioUrl, resultData]);

  // Re-render regions whenever resultData changes
  const renderRegions = (regionsPlugin: any) => {
    if (!regionsPlugin || !resultData) return;
    regionsPlugin.clearRegions();

    // 1. Draw Injected Ground-Truth Flaw Regions (Hatched Bars Under Detected Regions)
    if (resultData.ground_truth_flaws && resultData.ground_truth_flaws.length > 0) {
      resultData.ground_truth_flaws.forEach((gt: any, idx: number) => {
        const gtType = gt.flaw_type || gt.type || 'ground_truth';
        regionsPlugin.addRegion({
          id: gt.flaw_id || `gt_region_${idx}`,
          start: gt.start_s,
          end: gt.end_s,
          color: 'rgba(234, 179, 8, 0.20)',
          drag: false,
          resize: false,
          attributes: {
            style: 'border-bottom: 3px dashed #eab308; background: repeating-linear-gradient(45deg, rgba(234, 179, 8, 0.22), rgba(234, 179, 8, 0.22) 6px, rgba(0, 0, 0, 0.25) 6px, rgba(0, 0, 0, 0.25) 12px); border-radius: 4px; pointer-events: none;',
            title: `Ground Truth Flaw: ${gtType} [${gt.start_s}s - ${gt.end_s}s]`,
          },
        });
      });
    }

    // 2. Draw Detected Flaw Regions (Solid Bordered Overlays)
    resultData.flaws.forEach((flaw: GroundedFlaw) => {
      const color = FLAW_COLORS[flaw.flaw_type] || 'rgba(99, 102, 241, 0.3)';
      const borderColor = FLAW_BORDER_COLORS[flaw.flaw_type] || '#6366f1';
      const isSelected = selectedRegion?.region_id === flaw.region_id;

      regionsPlugin.addRegion({
        id: flaw.region_id,
        start: flaw.start_s,
        end: flaw.end_s,
        color: isSelected ? color.replace('0.35', '0.6') : color,
        drag: false,
        resize: false,
        attributes: {
          style: `border: ${isSelected ? '2px solid' : '1px solid'} ${borderColor}; border-radius: 4px;`,
        },
      });
    });
  };

  // Zoom control update
  useEffect(() => {
    if (wsRef.current && audioUrl) {
      try {
        wsRef.current.zoom(zoom);
      } catch {
        // Audio not decoded yet
      }
    }
  }, [zoom, audioUrl]);

  // Toggle Playback
  const handlePlayPause = () => {
    if (wsRef.current) {
      wsRef.current.playPause();
    }
  };

  const handleReset = () => {
    if (wsRef.current) {
      wsRef.current.seekTo(0);
      setCurrentTime(0);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(2);
    return `${mins}:${secs.padStart(5, '0')}`;
  };

  return (
    <div className="glass-panel p-5 rounded-2xl mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Volume2 className="w-5 h-5 text-brand-primary" />
            Interactive Audio Waveform & Grounded Flaws
          </h2>
          <p className="text-xs text-slate-400">
            Click on any highlighted flaw region to inspect acoustic delta, zoom timeline, and play localized audio.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-950/40 border border-amber-600/60 text-amber-300 font-semibold">
            <span className="w-3.5 h-2.5 rounded border border-amber-400 bg-[repeating-linear-gradient(45deg,#eab308,#eab308_2px,transparent_2px,transparent_4px)]" />
            GT Flaw (Hatched Bar)
          </span>
          {Object.entries(FLAW_BORDER_COLORS).map(([type, color]) => (
            <span
              key={type}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300"
            >
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
              {type.replace('_', ' ')}
            </span>
          ))}
        </div>
      </div>

      {/* WaveSurfer Container */}
      <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800 relative">
        <div ref={containerRef} className="w-full" />
        <div ref={timelineRef} className="w-full mt-1" />
      </div>

      {/* Player Controls Bar */}
      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center gap-3">
          <button
            onClick={handlePlayPause}
            className="flex items-center justify-center w-10 h-10 rounded-xl bg-brand-primary hover:bg-brand-secondary text-white shadow-lg transition-all"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </button>

          <button
            onClick={handleReset}
            className="flex items-center justify-center w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Restart Audio"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <div className="text-sm font-mono text-slate-300 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-2">
          <ZoomOut className="w-4 h-4 text-slate-400" />
          <input
            type="range"
            min="20"
            max="150"
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
            className="w-28 accent-brand-primary cursor-pointer"
          />
          <ZoomIn className="w-4 h-4 text-slate-400" />
        </div>
      </div>
    </div>
  );
};
