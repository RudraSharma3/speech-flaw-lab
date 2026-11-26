/**
 * Display metadata for the benchmark. Every value is copied from a committed file:
 *  - FLAW_META colours: validated categorical palette (light mode, white surface);
 *    colour never appears without its text label.
 *  - SPEECHES: data/manifests/real_speech_manifest.json and splits.json.
 *  - LEVELS: configs/injector_levels.yaml (name, description, flaw_count).
 */

export interface FlawMeta {
  label: string;
  color: string;
}

export const FLAW_META: Record<string, FlawMeta> = {
  monotone: { label: 'Monotone', color: '#257de0' },
  rushed: { label: 'Rushed', color: '#f47230' },
  drag_slow: { label: 'Too slow', color: '#00b894' },
  inappropriate_pause: { label: 'Misplaced pause', color: '#f2a600' },
  missing_pause: { label: 'Missing pause', color: '#ee7fac' },
  volume_drop: { label: 'Volume drop', color: '#008a17' },
  breathy_unclear: { label: 'Breathy / unclear', color: '#6a4ce2' },
};

export function flawMeta(type: string | null | undefined): FlawMeta {
  if (!type) return { label: 'Unknown', color: '#8a919c' };
  return FLAW_META[type] ?? { label: type.replace(/_/g, ' '), color: '#8a919c' };
}

export function withAlpha(hex: string, alpha: number): string {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export interface SpeechInfo {
  id: string;
  speaker: string;
  label: string;
  split: 'tuning' | 'held-out';
}

export const SPEECHES: SpeechInfo[] = [
  { id: 'jfk_moon_1962', speaker: 'John F. Kennedy', label: 'Rice University address, 1962 ("240,000 miles away")', split: 'tuning' },
  { id: 'jfk_we_choose_1962', speaker: 'John F. Kennedy', label: 'Rice University address, 1962 ("We choose to go to the Moon")', split: 'tuning' },
  { id: 'reagan_mourning_1986', speaker: 'Ronald Reagan', label: 'Challenger address, 1986 (opening)', split: 'tuning' },
  { id: 'reagan_challenger_1986', speaker: 'Ronald Reagan', label: 'Challenger address, 1986 (later passage)', split: 'tuning' },
  { id: 'fdr_fear_itself_1933', speaker: 'Franklin D. Roosevelt', label: 'First inaugural address, 1933', split: 'held-out' },
];

export interface LevelInfo {
  level: number;
  name: string;
  injected: number;
  description: string;
}

export const LEVELS: LevelInfo[] = [
  { level: 4, name: 'Ideal Reference', injected: 0, description: 'Original master recording, pristine prosody, optimal cadence and emphasis.' },
  { level: 3, name: 'Near Perfect', injected: 1, description: 'Very mild, subtle prosodic imperfections (e.g. slight pace acceleration or minor pitch dip).' },
  { level: 2, name: 'Slightly Flawed', injected: 2, description: 'Noticeable pacing, pause, or intonation errors across 2 distinct regions.' },
  { level: 1, name: 'Flawed', injected: 3, description: 'Multiple pronounced flaws (3 distinct regions) with severe prosodic disruption.' },
  { level: 0, name: 'Egregiously Wrong', injected: 4, description: 'Extreme, multi-tier failure across 4 distinct regions combining robotic pitch, erratic tempo, and jarring pauses.' },
];

export const SEEDS = [
  { id: '', label: 'Seed 0' },
  { id: '_s1', label: 'Seed 1' },
  { id: '_s2', label: 'Seed 2' },
];

export function recordingId(speechId: string, level: number, seed: string): string {
  return `${speechId}_level_${level}${seed}`;
}

export function parseRecordingId(id: string | null): { speechId: string; level: number; seed: string } | null {
  if (!id) return null;
  const m = id.match(/^(.+)_level_(\d)(_s\d)?$/);
  return m ? { speechId: m[1], level: Number(m[2]), seed: m[3] ?? '' } : null;
}

export const fmtSeconds = (s: number, digits = 2) => `${s.toFixed(digits)} s`;

export const fmtSigned = (v: number, digits = 2) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(digits)}`;
