import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, PlayCircle, FileAudio, Check, Loader2, Sparkles, Database } from 'lucide-react';
import { useAudioStore } from '../store/useAudioStore';
import { SampleRecording } from '../types/api';

export const UploadPanel: React.FC = () => {
  const [samples, setSamples] = useState<SampleRecording[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string>('demo_jfk_moon_level1_flawed');
  const [transcript, setTranscript] = useState<string>(
    'We choose to go to the moon . We choose to go to the moon in this decade and do the other things , not because they are easy , but because they are hard , because that goal will serve to organize and measure the best of our energies and skills .'
  );
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const { isAnalyzing, analysisProgress, statusMessage, setIsAnalyzing, setResultData, loadMockData } =
    useAudioStore();

  // Fetch sample catalog from backend or fallback
  useEffect(() => {
    fetch('/samples')
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (data && data.length > 0) {
          setSamples(data);
        }
      })
      .catch(() => {
        // Fallback local samples
        setSamples([
          {
            sample_id: 'demo_jfk_moon_level4_ideal',
            title: 'JFK Moon Speech — Level 4 (Ideal Reference)',
            speech_name: 'John F. Kennedy (1962)',
            quality_level: 4,
            quality_label: 'Level 4: Pristine Master',
            speaker_name: 'John F. Kennedy',
            duration_s: 17.5,
            description: 'Flawless canonical delivery, optimal rhythmic cadence and resonance.',
            flaws_count: 0,
            audio_url: '/api/audio/jfk_moon_level4_ideal.wav',
            transcript:
              'We choose to go to the moon . We choose to go to the moon in this decade and do the other things , not because they are easy , but because they are hard , because that goal will serve to organize and measure the best of our energies and skills .',
          },
          {
            sample_id: 'demo_jfk_moon_level3_near_perfect',
            title: 'JFK Moon Speech — Level 3 (Near Perfect)',
            speech_name: 'John F. Kennedy (1962)',
            quality_level: 3,
            quality_label: 'Level 3: Near Perfect',
            speaker_name: 'John F. Kennedy',
            duration_s: 17.5,
            description: 'Very mild localized pitch compression.',
            flaws_count: 1,
            audio_url: '/api/audio/jfk_moon_level3_near_perfect.wav',
            transcript:
              'We choose to go to the moon . We choose to go to the moon in this decade and do the other things , not because they are easy , but because they are hard , because that goal will serve to organize and measure the best of our energies and skills .',
          },
          {
            sample_id: 'demo_jfk_moon_level2_slightly_flawed',
            title: 'JFK Moon Speech — Level 2 (Slightly Flawed)',
            speech_name: 'John F. Kennedy (1962)',
            quality_level: 2,
            quality_label: 'Level 2: Slightly Flawed',
            speaker_name: 'John F. Kennedy',
            duration_s: 17.5,
            description: 'Noticeable pacing surge combined with pitch flatness.',
            flaws_count: 2,
            audio_url: '/api/audio/jfk_moon_level2_slightly_flawed.wav',
            transcript:
              'We choose to go to the moon . We choose to go to the moon in this decade and do the other things , not because they are easy , but because they are hard , because that goal will serve to organize and measure the best of our energies and skills .',
          },
          {
            sample_id: 'demo_jfk_moon_level1_flawed',
            title: 'JFK Moon Speech — Level 1 (Flawed)',
            speech_name: 'John F. Kennedy (1962)',
            quality_level: 1,
            quality_label: 'Level 1: Flawed',
            speaker_name: 'John F. Kennedy',
            duration_s: 17.5,
            description: 'Severe monotone pitch collapse, rushed tempo, and disruptive hesitation.',
            flaws_count: 3,
            audio_url: '/api/audio/jfk_moon_level1_flawed.wav',
            transcript:
              'We choose to go to the moon . We choose to go to the moon in this decade and do the other things , not because they are easy , but because they are hard , because that goal will serve to organize and measure the best of our energies and skills .',
          },
          {
            sample_id: 'demo_jfk_moon_level0_egregious',
            title: 'JFK Moon Speech — Level 0 (Egregiously Wrong)',
            speech_name: 'John F. Kennedy (1962)',
            quality_level: 0,
            quality_label: 'Level 0: Egregious',
            speaker_name: 'John F. Kennedy',
            duration_s: 17.5,
            description: 'Multi-tier failure: flatline pitch, erratic tempo shifts, and awkward pauses.',
            flaws_count: 4,
            audio_url: '/api/audio/jfk_moon_level0_egregious.wav',
            transcript:
              'We choose to go to the moon . We choose to go to the moon in this decade and do the other things , not because they are easy , but because they are hard , because that goal will serve to organize and measure the best of our energies and skills .',
          },
        ]);
      });
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
  const handleLoadSample = async (sampleId: string) => {
    setSelectedSampleId(sampleId);
    const sample = samples.find((s) => s.sample_id === sampleId);
    if (sample) {
      setTranscript(sample.transcript);
    }

    setIsAnalyzing(true, 0.4, `Loading pre-cached analysis for ${sampleId}...`);

    try {
      const res = await fetch(`/results/${sampleId}`);
      if (res.ok) {
        const result = await res.json();
        const audioPath = sample?.audio_url || `/api/audio/${sampleId.replace('demo_', '')}.wav`;
        setResultData(result, audioPath);
        setIsAnalyzing(false, 1.0, 'Loaded pre-cached sample result.');
      } else {
        // Fallback to local mock data
        loadMockData();
        setIsAnalyzing(false, 1.0, 'Loaded local mock data.');
      }
    } catch {
      loadMockData();
      setIsAnalyzing(false, 1.0, 'Loaded local mock data.');
    }
  };

  // Handle Live Upload & Analysis
  const handleAnalyze = async () => {
    if (!uploadedFile) {
      // Analyze current sample
      handleLoadSample(selectedSampleId);
      return;
    }

    setIsAnalyzing(true, 0.1, 'Uploading audio file and starting job...');

    const formData = new FormData();
    formData.append('audio', uploadedFile);
    formData.append('transcript', transcript);
    if (selectedSampleId) {
      formData.append('reference_id', 'demo_jfk_moon_level4_ideal');
    }

    try {
      const uploadRes = await fetch('/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!uploadRes.ok) {
        throw new Error('Upload failed');
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
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Column: Sample Selector */}
        <div className="w-full lg:w-1/2">
          <div className="flex items-center gap-2 mb-3">
            <Database className="w-5 h-5 text-brand-primary" />
            <h3 className="text-base font-bold text-white">Pre-Cached Gradient Samples</h3>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30">
              Demo-Safe Guarantee
            </span>
          </div>

          <div className="grid grid-cols-1 gap-2 mb-4 max-h-56 overflow-y-auto pr-1">
            {samples.map((sample) => {
              const isSelected = selectedSampleId === sample.sample_id && !uploadedFile;
              return (
                <button
                  key={sample.sample_id}
                  onClick={() => {
                    setUploadedFile(null);
                    handleLoadSample(sample.sample_id);
                  }}
                  className={`p-3 rounded-xl border text-left transition-all flex items-start justify-between ${
                    isSelected
                      ? 'bg-indigo-950/60 border-indigo-500 shadow-md ring-1 ring-indigo-500'
                      : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/60'
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">{sample.quality_label}</span>
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
            className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
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
                <span>Drag & drop custom WAV/MP3, or click to browse</span>
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
              <span className="text-[10px] text-slate-500">MFA Word & Phoneme Target</span>
            </div>

            <textarea
              rows={5}
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs font-mono focus:outline-none focus:border-brand-primary leading-relaxed resize-none"
              placeholder="Paste exact spoken transcript with punctuation..."
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
                  Run Contrastive Flaw Grounding
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
