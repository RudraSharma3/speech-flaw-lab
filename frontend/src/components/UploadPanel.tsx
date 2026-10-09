import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileAudio, Check, Loader2, Sparkles, Database, Compass, SlidersHorizontal } from 'lucide-react';
import { useAudioStore } from '../store/useAudioStore';
import { SampleRecording, ReferenceSpeech } from '../types/api';

export const UploadPanel: React.FC = () => {
  const [samples, setSamples] = useState<SampleRecording[]>([]);
  const [references, setReferences] = useState<ReferenceSpeech[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string>('jfk_moon_1962_level_1');
  const [selectedReferenceId, setSelectedReferenceId] = useState<string>('jfk_moon_1962_level_4');
  const [analysisMode, setAnalysisMode] = useState<'contrastive' | 'reference_free'>('contrastive');
  const [transcript, setTranscript] = useState<string>(
    '140,000 miles away from the control station in Houston, a giant rocket, more than 300 feet tall, the length of this football field, made of new metal alloys, some of which have not yet been embedded, capable of standing heat and stresses, several times more than have ever been experienced, pitted together with a precision better than the finest watch, carrying all the equipment needed for propulsion, guidance, control, communication, food and survival, on an untried mission to an unknown celestial body and then return it safely to earth, re-entering the atmosphere at speeds of over 25,000 miles per hour, causing heat about half that on the temperature of the sun, almost as hot as it is here today and do all this and do all this and do it right and do it first, if all this thick heat is out, then we must be bald.'
  );
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const { isAnalyzing, analysisProgress, statusMessage, setIsAnalyzing, setResultData } =
    useAudioStore();

  // Load sample catalog and reference speeches
  useEffect(() => {
    fetch('/samples')
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (data && data.length > 0) {
          setSamples(data);
          // Initial auto-load first flawed sample
          const initialSample = data.find((s: SampleRecording) => s.sample_id === 'jfk_moon_1962_level_1') || data[0];
          if (initialSample) {
            handleLoadSample(initialSample.sample_id, initialSample);
          }
        }
      })
      .catch(() => {});

    fetch('/api/references')
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (data && data.length > 0) {
          setReferences(data);
        }
      })
      .catch(() => {});
  }, []);

  // Dropzone setup
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'audio/*': ['.wav', '.mp3', '.m4a', '.ogg', '.flac'] },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setUploadedFile(acceptedFiles[0]);
      }
    },
  });

  // Handle Loading a Sample
  const handleLoadSample = async (sampleId: string, preSample?: SampleRecording) => {
    setSelectedSampleId(sampleId);
    const sample = preSample || samples.find((s) => s.sample_id === sampleId);
    if (sample && sample.transcript) {
      setTranscript(sample.transcript);
    }

    setIsAnalyzing(true, 0.4, `Loading real analysis for ${sampleId}...`);

    try {
      const res = await fetch(`/results/${sampleId}`);
      if (res.ok) {
        const result = await res.json();
        const audioPath = sample?.audio_url || `/api/audio/${sampleId}.wav`;
        setResultData(result, audioPath);
        setIsAnalyzing(false, 1.0, `Loaded ${sample?.title || sampleId}`);
      } else {
        setIsAnalyzing(false, 0.0, 'Sample result not yet cached on disk.');
      }
    } catch {
      setIsAnalyzing(false, 0.0, 'Failed to fetch sample result.');
    }
  };

  // Handle Live Upload & Analysis
  const handleAnalyze = async () => {
    if (!uploadedFile) {
      // Re-analyze or reload selected sample
      handleLoadSample(selectedSampleId);
      return;
    }

    setIsAnalyzing(true, 0.1, 'Uploading audio file to non-blocking worker queue...');

    const formData = new FormData();
    formData.append('audio', uploadedFile);
    formData.append('transcript', transcript);
    if (analysisMode === 'contrastive' && selectedReferenceId) {
      formData.append('reference_id', selectedReferenceId);
    }

    try {
      const uploadRes = await fetch('/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!uploadRes.ok) {
        const errJson = await uploadRes.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Upload failed');
      }

      const { job_id } = await uploadRes.json();

      // Poll job status
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`/jobs/${job_id}`);
          if (!statusRes.ok) return;

          const job = await statusRes.json();
          setIsAnalyzing(true, job.progress, job.message);

          if (job.status === 'completed' && job.result_id) {
            clearInterval(pollInterval);
            const resultRes = await fetch(`/results/${job.result_id}`);
            if (resultRes.ok) {
              const fullResult = await resultRes.json();
              const objectUrl = URL.createObjectURL(uploadedFile);
              setResultData(fullResult, objectUrl);
            }
            setIsAnalyzing(false, 1.0, 'Analysis complete!');
          } else if (job.status === 'failed') {
            clearInterval(pollInterval);
            setIsAnalyzing(false, 0.0, `Analysis failed: ${job.error || 'Unknown error'}`);
          }
        } catch {
          clearInterval(pollInterval);
          setIsAnalyzing(false, 0.0, 'Polling failed.');
        }
      }, 500);
    } catch (err: any) {
      setIsAnalyzing(false, 0.0, `Error: ${err.message}`);
    }
  };

  return (
    <div className="glass-panel p-6 rounded-2xl mb-6">
      {/* Mode Toggle Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Compass className="w-5 h-5 text-brand-primary" />
            Evaluation Pipeline Configuration
          </h2>
          <p className="text-xs text-slate-400">
            Select contrastive ideal reference take (primary) or reference-free coarse screening.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setAnalysisMode('contrastive')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              analysisMode === 'contrastive'
                ? 'bg-brand-primary text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Contrastive (Ideal Take)
          </button>
          <button
            onClick={() => setAnalysisMode('reference_free')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              analysisMode === 'reference_free'
                ? 'bg-slate-800 text-amber-300 border border-amber-500/30 shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Reference-Free (Coarse Screening)
          </button>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Column: Sample Selector & Reference Choice */}
        <div className="w-full lg:w-1/2">
          {/* Reference Choice (if in Contrastive mode) */}
          {analysisMode === 'contrastive' ? (
            <div className="mb-4 bg-slate-900/60 p-3.5 rounded-xl border border-indigo-500/30">
              <label className="text-xs font-bold text-slate-200 uppercase tracking-wider block mb-1.5 flex items-center gap-1.5">
                <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-400" />
                Ideal Reference Baseline (Level 4 Take)
              </label>
              <select
                value={selectedReferenceId}
                onChange={(e) => {
                  setSelectedReferenceId(e.target.value);
                  const refMatch = references.find((r) => r.reference_id === e.target.value);
                  if (refMatch && refMatch.transcript) {
                    setTranscript(refMatch.transcript);
                  }
                }}
                className="w-full p-2.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 font-semibold focus:outline-none focus:border-brand-primary"
              >
                {references.map((ref) => (
                  <option key={ref.reference_id} value={ref.reference_id}>
                    {ref.name} ({ref.speaker})
                  </option>
                ))}
              </select>
              <p className="text-[10px] text-slate-400 mt-1">
                Acoustic contours and word boundaries will be scored contrastively against this pristine delivery.
              </p>
            </div>
          ) : (
            <div className="mb-4 bg-amber-950/20 p-3 rounded-xl border border-amber-600/30 text-xs text-amber-300">
              <span className="font-bold block mb-0.5">Reference-Free Coarse Screening Mode</span>
              Scored against broad population distribution norms without an ideal speaker reference take.
            </div>
          )}

          {/* Sample Selector */}
          <div className="flex items-center gap-2 mb-2">
            <Database className="w-4 h-4 text-brand-primary" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Dataset Participant Recordings
            </h3>
          </div>

          <div className="grid grid-cols-1 gap-2 mb-4 max-h-52 overflow-y-auto pr-1">
            {samples.map((sample) => {
              const isSelected = selectedSampleId === sample.sample_id && !uploadedFile;
              return (
                <button
                  key={sample.sample_id}
                  onClick={() => {
                    setUploadedFile(null);
                    handleLoadSample(sample.sample_id, sample);
                  }}
                  className={`p-2.5 rounded-xl border text-left transition-all flex items-start justify-between ${
                    isSelected
                      ? 'bg-indigo-950/60 border-indigo-500 shadow-md ring-1 ring-indigo-500'
                      : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/60'
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">{sample.title}</span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {sample.flaws_count} flaw{sample.flaws_count === 1 ? '' : 's'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">{sample.description}</p>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />}
                </button>
              );
            })}
          </div>

          {/* Audio Dropzone */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-3.5 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-brand-primary bg-indigo-500/10'
                : uploadedFile
                ? 'border-emerald-500/60 bg-emerald-500/10'
                : 'border-slate-700 bg-slate-900/40 hover:border-slate-600'
            }`}
          >
            <input {...getInputProps()} />
            {uploadedFile ? (
              <div className="flex items-center justify-center gap-2 text-emerald-300 text-xs font-medium">
                <FileAudio className="w-4 h-4" />
                <span>Uploaded: {uploadedFile.name} ({(uploadedFile.size / 1024).toFixed(0)} KB)</span>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center gap-1 text-slate-400 text-xs">
                <Upload className="w-4 h-4 text-slate-500" />
                <span>Upload custom WAV, MP3, M4A, OGG file</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Transcript & Action */}
        <div className="w-full lg:w-1/2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Canonical Alignment Transcript
              </label>
              <span className="text-[10px] text-slate-500 font-mono">Word-level forced alignment</span>
            </div>

            <textarea
              rows={6}
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs font-mono focus:outline-none focus:border-brand-primary leading-relaxed resize-none"
              placeholder="Paste exact spoken transcript..."
            />
          </div>

          {/* Run Analysis Button & Progress */}
          <div className="mt-4">
            {isAnalyzing && (
              <div className="mb-3">
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span className="flex items-center gap-1.5">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                    {statusMessage}
                  </span>
                  <span className="font-mono font-bold text-indigo-300">{(analysisProgress * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-brand-primary rounded-full transition-all duration-300"
                    style={{ width: `${analysisProgress * 100}%` }}
                  />
                </div>
              </div>
            )}

            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="w-full py-3 px-5 rounded-xl bg-gradient-to-r from-brand-primary to-brand-secondary hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm shadow-xl flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing Speech Contours...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  {analysisMode === 'contrastive' ? 'Run Contrastive Flaw Grounding' : 'Run Coarse Screening Analysis'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
