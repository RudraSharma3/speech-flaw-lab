# Project Dependency & Relationship Graph

This document is the structural wiring diagram for the codebase. It maps component hierarchies, speech processing call paths, and data relationships to enable safe refactoring and instant blast-radius analysis.

---

## 1. System Context & Component Graph

```mermaid
graph TD
    User([User Voice & Controls]) --> Client[Speech UI / Web Audio Client]
    
    subgraph PresentationLayer [Presentation & Input Layer]
        Client --> AudioRecorder[Audio Capture Controller]
        Client --> Visualizer[Audio Frequency Visualizer]
        Client --> TranscriptView[Transcript & Response UI]
    end

    subgraph SpeechPipeline [Speech & Audio Engine]
        AudioRecorder --> StreamBuffer[PCM / WAV Audio Buffer]
        StreamBuffer --> STTEngine[Speech-to-Text Transcriber]
        STTEngine --> TranscriptStore[Transcript History]
    end

    subgraph AgentOrchestration [AI Agent & Reasoning Layer]
        TranscriptStore --> AgentRouter[Agent Orchestrator]
        AgentRouter --> GeminiWorker["Gemini Worker (MCP / Vision & Context)"]
        AgentRouter --> CodexWorker["Codex Worker (MCP / Code & Filesystem)"]
        AgentRouter --> OllamaWorker["Ollama Worker (MCP / Local Offline LLM)"]
    end

    subgraph SynthesisAndOutput [Voice Synthesis & Output Layer]
        AgentRouter --> TTSEngine[Text-to-Speech Synthesizer]
        TTSEngine --> AudioPlayer[Web Audio Playback]
        AudioPlayer --> SpeakerOutput([Audio Output / Speaker])
    end

    subgraph StateAndStorage [Governance & Task State]
        AgentRouter --> TaskStateDocs["docs/task-state.md"]
        AgentRouter --> SessionDB[(Session & Interaction Store)]
    end
```

---

## 2. Audio Processing & Agent Interaction Flow Graph

```mermaid
sequenceDiagram
    autonumber
    actor User as User Voice
    participant Client as Web Audio UI
    participant Buffer as Audio Buffer
    participant STT as STT Service
    participant Agent as Agent Orchestrator
    participant Worker as MCP Worker (Gemini/Codex/Ollama)
    participant TTS as TTS Service
    participant Speaker as Audio Playback
    participant State as docs/task-state.md

    User->>Client: Speak into microphone
    Client->>Buffer: Capture raw PCM audio stream
    Buffer->>STT: Stream audio chunks
    STT-->>Client: Real-time interim transcript
    STT->>Agent: Final transcript text payload
    Agent->>State: Record user query & update task state
    Agent->>Worker: Dispatch context & tool execution
    Worker-->>Agent: Structured reasoning response
    Agent->>TTS: Request audio synthesis for response
    TTS-->>Speaker: Stream synthesized audio
    Speaker-->>User: Playback spoken response
    Agent->>Client: Render markdown response & update transcript UI
```

---

## 3. Database & Session Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    SPEECH_SESSION ||--o{ TRANSCRIPT_CHUNK : contains
    SPEECH_SESSION ||--o{ AGENT_TURN : executes
    AGENT_TURN ||--o{ TOOL_CALL : invokes
    AGENT_TURN ||--o| SYNTHESIS_AUDIO : produces
    SPEECH_SESSION ||--o{ TASK_STATE_LOG : tracks

    SPEECH_SESSION {
        string session_id PK
        datetime started_at
        datetime ended_at
        string status
        string audio_sample_rate
    }
    TRANSCRIPT_CHUNK {
        string chunk_id PK
        string session_id FK
        float timestamp_start
        float timestamp_end
        string speaker_role
        string text_content
        float confidence_score
    }
    AGENT_TURN {
        string turn_id PK
        string session_id FK
        string model_used
        string prompt_text
        string response_text
        datetime timestamp
    }
    TOOL_CALL {
        string call_id PK
        string turn_id FK
        string worker_name
        string tool_name
        json arguments
        json result
    }
    SYNTHESIS_AUDIO {
        string audio_id PK
        string turn_id FK
        string voice_id
        string audio_format
        int byte_length
        float duration_seconds
    }
    TASK_STATE_LOG {
        string log_id PK
        string session_id FK
        string goal
        json acceptance_criteria
        string status
    }
```

---

## 4. Blast Radius & Dependency Matrix

Use this table to assess downstream impacts before modifying core system modules or governance configurations:

| Core Module / File | Direct Dependents (Imported By / Regulates) | Risk Level | Blast Radius Mitigation |
| :--- | :--- | :---: | :--- |
| [`AGENTS.md`](file:///c:/Users/HP/OneDrive/Desktop/Speech/AGENTS.md) | All AI Agents, Adapters ([`CLAUDE.md`](file:///c:/Users/HP/OneDrive/Desktop/Speech/CLAUDE.md), [`CODEX.md`](file:///c:/Users/HP/OneDrive/Desktop/Speech/CODEX.md), [`GEMINI.md`](file:///c:/Users/HP/OneDrive/Desktop/Speech/GEMINI.md)) | **CRITICAL** | Ensure self-modifying learning loop rules and prompt contract requirements remain intact. |
| [`mcp.json`](file:///c:/Users/HP/OneDrive/Desktop/Speech/mcp.json) | MCP Server Runners, Orchestrator, Subagent workers | **HIGH** | Validate environment variable substitution (`${GEMINI_API_KEY}`, `${OPENAI_API_KEY}`) and CLI package availability. |
| [`.githooks/pre-commit`](file:///c:/Users/HP/OneDrive/Desktop/Speech/.githooks/pre-commit) | Git commit pipeline & developer workflow | **HIGH** | Test hook execution with mock `.env` and clean commits before modifying. |
| [`docs/task-state.md`](file:///c:/Users/HP/OneDrive/Desktop/Speech/docs/task-state.md) | Agent task handoff, developer session state | **MEDIUM** | Keep format synchronized with `/sync-state` command conventions. |
| `src/audio/` (Audio Pipeline) | STT Transcribers, Visualizer, Audio Playback | **HIGH** | Verify sample rate conversions (16kHz / 44.1kHz / 48kHz) and cross-browser Web Audio API support. |
| `src/agent/` (Agent Router) | TTS Engine, UI State, MCP Worker Clients | **HIGH** | Run integration test suite mocking worker response timeouts and stream failures. |
| `src/ui/` (Frontend Views) | User presentation & visual feedback | **LOW** | Verify responsive CSS, audio visualizer canvas sizing, and accessibility standards. |

