import React, { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useAudioStore } from '../store/useAudioStore';
import { LEVELS, SEEDS, SPEECHES, parseRecordingId, recordingId } from '../lib/catalog';
import { Notice, Segmented } from './ui';

/** Step 1 of the flow: choose one of the 75 benchmark recordings (speech x level x seed). */
export const RecordingPicker: React.FC = () => {
  const { loadRecording, recordingId: loadedId, isAnalyzing, loadError } = useAudioStore();
  const [speechId, setSpeechId] = useState('jfk_moon_1962');
  const [level, setLevel] = useState(1);
  const [seed, setSeed] = useState('');

  // Follow recordings loaded from elsewhere (e.g. the Benchmark view).
  useEffect(() => {
    const parsed = parseRecordingId(loadedId);
    if (parsed) {
      setSpeechId(parsed.speechId);
      setLevel(parsed.level);
      setSeed(parsed.seed);
    }
  }, [loadedId]);

  useEffect(() => {
    const id = recordingId(speechId, level, seed);
    if (id !== useAudioStore.getState().recordingId) {
      loadRecording(id);
    }
  }, [speechId, level, seed, loadRecording]);

  const speech = SPEECHES.find((s) => s.id === speechId)!;
  const levelInfo = LEVELS.find((l) => l.level === level)!;

  return (
    <section className="rounded-card border border-line bg-surface">
      <div className="grid gap-4 px-5 py-4 md:grid-cols-[minmax(0,1.4fr)_auto_auto] md:items-end">
        <label className="block min-w-0">
          <span className="eyebrow">Speech</span>
          <select id="speech-select" className="field mt-1.5" value={speechId} onChange={(e) => setSpeechId(e.target.value)}>
            {SPEECHES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.speaker}: {s.label}
                {s.split === 'held-out' ? ' (held-out)' : ''}
              </option>
            ))}
          </select>
        </label>

        <div className="min-w-0">
          <span className="eyebrow">Quality level</span>
          <div className="mt-1.5">
            <Segmented<number>
              ariaLabel="Quality level"
              value={level}
              onChange={setLevel}
              options={LEVELS.map((l) => ({ value: l.level, label: `L${l.level}`, title: l.name }))}
            />
          </div>
        </div>

        <label className="block">
          <span className="eyebrow">Injection seed</span>
          <select id="seed-select" className="field mt-1.5" value={seed} onChange={(e) => setSeed(e.target.value)}>
            {SEEDS.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-t border-line bg-surface-2/60 px-5 py-3 text-[13px]">
        <p className="min-w-0 text-ink-2">
          <span className="font-medium text-ink">
            L{levelInfo.level} · {levelInfo.name}.
          </span>{' '}
          {levelInfo.description}{' '}
          <span className="text-ink-3">
            {levelInfo.injected} injected flaw{levelInfo.injected === 1 ? '' : 's'}. Compared against the L4 take of the same
            speech{speech.split === 'held-out' ? '; this speaker was never used for tuning.' : '.'}
          </span>
        </p>
        {isAnalyzing && (
          <span className="inline-flex items-center gap-1.5 text-ink-3">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> Loading
          </span>
        )}
      </div>
      {loadError && (
        <div className="border-t border-line px-5 py-3">
          <Notice tone="crit">{loadError}</Notice>
        </div>
      )}
    </section>
  );
};
