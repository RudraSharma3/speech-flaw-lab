import { create } from 'zustand';
import { AnalysisResult, GroundedFlaw, WordMetric } from '../types/api';
import { resolveApiUrl } from '../lib/staticApi';

interface AudioStoreState {
  resultData: AnalysisResult | null;
  audioUrl: string | null;
  currentTime: number;
  duration: number;
  isPlaying: boolean;
  selectedRegion: GroundedFlaw | null;
  hoveredWord: WordMetric | null;
  selectedWord: WordMetric | null;
  activeTab: 'overview' | 'acoustic_plots' | 'compare_gradient';
  isAnalyzing: boolean;
  analysisProgress: number;
  statusMessage: string;

  // Actions
  setResultData: (data: AnalysisResult, audioUrl?: string) => void;
  setCurrentTime: (time: number) => void;
  setDuration: (duration: number) => void;
  setIsPlaying: (isPlaying: boolean) => void;
  setSelectedRegion: (region: GroundedFlaw | null) => void;
  setHoveredWord: (word: WordMetric | null) => void;
  setSelectedWord: (word: WordMetric | null) => void;
  setActiveTab: (tab: 'overview' | 'acoustic_plots' | 'compare_gradient') => void;
  setIsAnalyzing: (isAnalyzing: boolean, progress?: number, message?: string) => void;
  seekTo: (timeSeconds: number) => void;
}

export const useAudioStore = create<AudioStoreState>((set, get) => ({
  resultData: null,
  audioUrl: null,
  currentTime: 0.0,
  duration: 0.0,
  isPlaying: false,
  selectedRegion: null,
  hoveredWord: null,
  selectedWord: null,
  activeTab: 'overview',
  isAnalyzing: false,
  analysisProgress: 0.0,
  statusMessage: 'Ready',

  setResultData: (data, audioUrl) => {
    set({
      resultData: data,
      audioUrl: audioUrl ? resolveApiUrl(audioUrl) : get().audioUrl,
      duration: data.meta.duration_s,
      currentTime: 0.0,
      selectedRegion: data.flaws.length > 0 ? data.flaws[0] : null,
      selectedWord: null,
      hoveredWord: null,
    });
  },

  setCurrentTime: (time) => set({ currentTime: Math.max(0, time) }),
  setDuration: (duration) => set({ duration: Math.max(0, duration) }),
  setIsPlaying: (isPlaying) => set({ isPlaying }),
  setSelectedRegion: (region) => set({ selectedRegion: region }),
  setHoveredWord: (word) => set({ hoveredWord: word }),
  setSelectedWord: (word) => set({ selectedWord: word }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setIsAnalyzing: (isAnalyzing, progress = 0.0, message = '') =>
    set({ isAnalyzing, analysisProgress: progress, statusMessage: message }),

  seekTo: (timeSeconds) => {
    set({ currentTime: timeSeconds });
    // Custom event dispatched so wavesurfer instances sync instantly
    window.dispatchEvent(new CustomEvent('speech_seek', { detail: { time: timeSeconds } }));
  },
}));
