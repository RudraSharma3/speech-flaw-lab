import React, { useEffect, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileAudio, Loader2, Upload } from 'lucide-react';
import { useAudioStore } from '../store/useAudioStore';
import { IS_STATIC_DEMO } from '../lib/staticApi';
import { parseRecordingId } from '../lib/catalog';
import { ReferenceSpeech, SampleRecording } from '../types/api';
import { Notice, Panel, Segmented } from './ui';

type Mode = 'contrastive' | 'reference_free';

/** Live analysis of a new recording through the FastAPI backend (/analyze then /jobs then /results). */
export const UploadPanel: React.FC = () => {
  const [references, setReferences] = useState<ReferenceSpeech[]>([]);
  const [otherSamples, setOtherSamples] = useState<SampleRecording[]>([]);
  const [referenceId, setReferenceId] = useState('jfk_moon_1962_level_4');
  const [mode, setMode] = useState<Mode>('contrastive');
  const [transcript, setTranscript] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const { setResultData, loadRecording } = useAudioStore();
  const report = (isBusy: boolean, p: number, msg: string) => {
    setBusy(isBusy);
    setProgress(p);
    setStatus(msg);
  };

  useEffect(() => {
    fetch('/api/references')
      .then((r) => (r.ok ? r.json() : []))
      .then((refs: ReferenceSpeech[]) => {
        setReferences(refs);
        const first = refs.find((r) => r.reference_id === referenceId) ?? refs[0];
        if (first) setTranscript(first.transcript);
      })
      .catch(() => {});
    // Recordings outside the 75-file benchmark (e.g. consented self-recordings on a live server).
    fetch('/samples')
      .then((r) => (r.ok ? r.json() : []))
      .then((s: SampleRecording[]) => setOtherSamples(s.filter((x) => !parseRecordingId(x.sample_id))))
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'audio/*': ['.wav', '.mp3', '.m4a', '.ogg', '.flac'] },
    maxFiles: 1,
    disabled: IS_STATIC_DEMO,
    onDrop: (files) => files[0] && setFile(files[0]),
  });

  const analyze = async () => {
    if (!file) return;
    report(true, 0.1, 'Uploading');
    const form = new FormData();
    form.append('audio', file);
    form.append('transcript', transcript);
    if (mode === 'contrastive' && referenceId) form.append('reference_id', referenceId);
    try {
      const up = await fetch('/analyze', { method: 'POST', body: form });
      if (!up.ok) {
        const err = await up.json().catch(() => ({}));
        throw new Error(err.detail || 'Upload failed.');
      }
      const { job_id } = await up.json();
      const poll = setInterval(async () => {
        try {
          const st = await fetch(`/jobs/${job_id}`);
          if (!st.ok) return;
          const job = await st.json();
          report(true, job.progress, job.message);
          if (job.status === 'completed' && job.result_id) {
            clearInterval(poll);
            const res = await fetch(`/results/${job.result_id}`);
            if (res.ok) setResultData(await res.json(), URL.createObjectURL(file), null);
            report(false, 1, 'Analysis complete.');
          } else if (job.status === 'failed') {
            clearInterval(poll);
            report(false, 0, `Analysis failed: ${job.error || 'unknown error'}`);
          }
        } catch {
          clearInterval(poll);
          report(false, 0, 'Lost contact with the analysis job.');
        }
      }, 500);
    } catch (e: any) {
      report(false, 0, e.message);
    }
  };

  return (
    <Panel
      title="Analyze your own recording"
      subtitle="Upload a reading of one of the reference passages. The backend aligns it word by word and compares it with the reference take."
    >
      {IS_STATIC_DEMO && (
        <div className="mb-4">
          <Notice tone="info" title="Not available in this shared demo.">
            Analysis runs a Python pipeline (forced alignment and Praat) on a server. Run the project locally to try your own
            audio.
          </Notice>
        </div>
      )}

      <fieldset disabled={IS_STATIC_DEMO} className="grid gap-5 disabled:opacity-60 lg:grid-cols-2">
        <div className="space-y-4">
          <div>
            <span className="eyebrow">Compare against</span>
            <div className="mt-1.5">
              <Segmented<Mode>
                ariaLabel="Analysis mode"
                value={mode}
                onChange={setMode}
                options={[
                  { value: 'contrastive', label: 'Reference take' },
                  { value: 'reference_free', label: 'Population norms' },
                ]}
              />
            </div>
          </div>
          {mode === 'contrastive' ? (
            <label className="block">
              <span className="eyebrow">Reference take</span>
              <select
                id="reference-select"
                className="field mt-1.5"
                value={referenceId}
                onChange={(e) => {
                  setReferenceId(e.target.value);
                  const ref = references.find((r) => r.reference_id === e.target.value);
                  if (ref) setTranscript(ref.transcript);
                }}
              >
                {references.map((r) => (
                  <option key={r.reference_id} value={r.reference_id}>
                    {r.name} ({r.speaker})
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <p className="text-[13px] text-ink-2">
              Without a reference take the recording is scored against broad population norms. Treat that as coarse screening.
            </p>
          )}
          <div
            {...getRootProps()}
            className={`flex cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed px-4 py-5 text-[13px] transition-colors ${
              isDragActive ? 'border-accent bg-accent-soft text-accent' : 'border-line-strong text-ink-2 hover:bg-surface-2'
            }`}
          >
            <input {...getInputProps()} />
            {file ? (
              <>
                <FileAudio className="h-4 w-4 text-accent" /> {file.name} ({(file.size / 1024).toFixed(0)} KB)
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" /> Drop a WAV, MP3, M4A, OGG or FLAC file, or click to choose one
              </>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <label className="block">
            <span className="eyebrow">Exact transcript of what was said</span>
            <textarea
              id="transcript-input"
              rows={6}
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              className="field mt-1.5 resize-y font-mono text-[12px] leading-relaxed"
            />
          </label>
          <div className="flex flex-wrap items-center gap-3">
            <button onClick={analyze} disabled={!file || busy} className="btn-primary">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Analyze recording
            </button>
            {status && (
              <span className="text-[12px] text-ink-2">
                {status}
                {busy && ` · ${(progress * 100).toFixed(0)}%`}
              </span>
            )}
          </div>
        </div>
      </fieldset>

      {otherSamples.length > 0 && (
        <div className="mt-5 border-t border-line pt-4">
          <div className="eyebrow mb-2">Other stored recordings</div>
          <div className="flex flex-wrap gap-2">
            {otherSamples.map((s) => (
              <button key={s.sample_id} className="btn" onClick={() => loadRecording(s.sample_id)}>
                {s.title}
              </button>
            ))}
          </div>
        </div>
      )}
    </Panel>
  );
};
