import { create } from 'zustand';
import { AnalysisResult, GroundedFlaw, WordMetric } from '../types/api';
import { resolveApiUrl } from '../lib/staticApi';

export type View = 'recording' | 'benchmark';

interface AudioStoreState {
  resultData: AnalysisResult | null;
  audioUrl: string | null;
  recordingId: string | null;
  currentTime: number;
  duration: number;
  isPlaying: boolean;
  selectedRegion: GroundedFlaw | null;
  hoveredWord: WordMetric | null;
  selectedWord: WordMetric | null;
  view: View;
  isAnalyzing: boolean;
  analysisProgress: number;
  statusMessage: string;
  loadError: string | null;

  // Actions
  setResultData: (data: AnalysisResult, audioUrl?: string, recordingId?: string | null) => void;
  loadRecording: (recordingId: string) => Promise<void>;
  setCurrentTime: (time: number) => void;
  setDuration: (duration: number) => void;
  setIsPlaying: (isPlaying: boolean) => void;
  setSelectedRegion: (region: GroundedFlaw | null) => void;
  setHoveredWord: (word: WordMetric | null) => void;
  setSelectedWord: (word: WordMetric | null) => void;
  setView: (view: View) => void;
  setIsAnalyzing: (isAnalyzing: boolean, progress?: number, message?: string) => void;
  seekTo: (timeSeconds: number) => void;
}

export const useAudioStore = create<AudioStoreState>((set, get) => ({
  resultData: null,
  audioUrl: null,
  recordingId: null,
  currentTime: 0.0,
  duration: 0.0,
  isPlaying: false,
  selectedRegion: null,
  hoveredWord: null,
  selectedWord: null,
  view: 'recording',
  isAnalyzing: false,
  analysisProgress: 0.0,
  statusMessage: 'Ready',
  loadError: null,

  setResultData: (data, audioUrl, recordingId = null) => {
    set({
      resultData: data,
      audioUrl: audioUrl ? resolveApiUrl(audioUrl) : get().audioUrl,
      recordingId,
      duration: data.meta.duration_s,
      currentTime: 0.0,
      selectedRegion: data.flaws.length > 0 ? data.flaws[0] : null,
      selectedWord: null,
      hoveredWord: null,
      loadError: null,
    });
  },

  loadRecording: async (recordingId) => {
    set({ isAnalyzing: true, analysisProgress: 0.4, statusMessage: `Loading ${recordingId}`, loadError: null });
    try {
      const res = await fetch(`/results/${recordingId}`);
      if (!res.ok) {
        throw new Error(`No stored result for ${recordingId}.`);
      }
      const data: AnalysisResult = await res.json();
      get().setResultData(data, `/api/audio/${recordingId}.wav`, recordingId);
      set({ isAnalyzing: false, analysisProgress: 1.0, statusMessage: 'Loaded' });
    } catch (err: any) {
      set({ isAnalyzing: false, analysisProgress: 0.0, loadError: err?.message ?? 'Could not load the result.' });
    }
  },

  setCurrentTime: (time) => set({ currentTime: Math.max(0, time) }),
  setDuration: (duration) => set({ duration: Math.max(0, duration) }),
  setIsPlaying: (isPlaying) => set({ isPlaying }),
  setSelectedRegion: (region) => set({ selectedRegion: region }),
  setHoveredWord: (word) => set({ hoveredWord: word }),
  setSelectedWord: (word) => set({ selectedWord: word }),
  setView: (view) => set({ view }),
  setIsAnalyzing: (isAnalyzing, progress = 0.0, message = '') =>
    set({ isAnalyzing, analysisProgress: progress, statusMessage: message }),

  seekTo: (timeSeconds) => {
    set({ currentTime: timeSeconds });
    // Custom event dispatched so wavesurfer instances sync instantly
    window.dispatchEvent(new CustomEvent('speech_seek', { detail: { time: timeSeconds } }));
  },
}));
