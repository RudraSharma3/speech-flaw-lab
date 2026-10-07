# Project Conventions

This document establishes coding standards, style preferences, git workflows, and testing patterns for this repository.

---

## 1. Code Style & Formatting

- **Languages & Frameworks**: TypeScript / modern JavaScript (ES2022+), HTML5 Web Audio, CSS3.
- **Modularity**: Functions must adhere to Single Responsibility Principle (SRP). Keep modules modular, clean, and well-typed.
- **Type Safety**: Explicit type annotations required for all public functions, audio buffer contracts, transcript models, and API interfaces.
- **Naming Conventions**:
  - Files & Directories: `kebab-case` or `camelCase` (e.g. `audio-stream.ts`, `speechRecognition.ts`).
  - Classes & Interfaces: `PascalCase` (e.g. `AudioController`, `SpeechSession`).
  - Functions & Variables: `camelCase` (e.g. `startRecording`, `activeTranscript`).
  - Constants & Enums: `UPPER_SNAKE_CASE` (e.g. `MAX_SAMPLE_RATE`, `DEFAULT_BUFFER_SIZE`).
- **Formatting**: 2 spaces indentation, UTF-8 encoding, LF line endings, trailing commas in multi-line structures.

---

## 2. Git & Version Control

- **Commit Format**: `<type>(<scope>): <short imperative summary>`
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`.
  - Examples: `feat(stt): add real-time streaming transcription buffer`, `docs(arch): update component wiring diagram`.
- **Clean Diff Rule**: Make surgical, minimal changes. No emojis in commit messages unless explicitly requested.
- **Pre-Commit Enforcement**: Always ensure [`.githooks/pre-commit`](file:///c:/Users/HP/OneDrive/Desktop/Speech/.githooks/pre-commit) passes. Never bypass hooks. No staged `.env` files or hardcoded API keys.

---

## 3. Error Handling & Logging

- **Explicit Failures**: Always handle stream interrupts, audio device access denials (`NotAllowedError`, `NotFoundError`), and network failures explicitly.
- **No Empty Catches**: Never swallow exceptions or leave empty catch blocks.
- **Diagnostic Logging**:
  - Log structured diagnostic events (e.g., `[AudioController] Audio context initialized with sampleRate=48000`).
  - Never log sensitive user speech content, raw private keys, or credentials in log outputs.

---

## 4. Testing Conventions

- **Structure**: Place tests in `tests/` or co-located adjacent to implementation as `<module>.test.ts`.
- **Pattern**: Arrange-Act-Assert (AAA) pattern strictly applied.
- **Coverage**:
  - Unit test audio mathematical transforms, state transitions, and prompt formatters.
  - Mock external hardware (mic/speaker) and cloud APIs (Gemini, OpenAI) during CI testing.
  - Include edge case falsification: zero-byte buffers, invalid audio sample rates, rapid connect/disconnect cycles.

---

## 5. AI-OS Self-Modifying Learning Loop

- **User Preferences & Corrections**: When the user provides a direct preference or correction:
  1. Assign the next sequential rule number in [`AGENTS.md`](file:///c:/Users/HP/OneDrive/Desktop/Speech/AGENTS.md) under `## 6. Learned Rules`.
  2. Categorize appropriately (`[STYLE]`, `[CODE]`, `[ARCH]`, `[TOOL]`, `[PROCESS]`, `[SECURITY]`, `[TEST]`).
  3. Announce the addition to the user: `🧠 Learned Rule Added to AGENTS.md: N. [CATEGORY] Rule — rationale.`
- **Candidate Mistake Logging**: Log unverified edge cases or internal friction in [`.ai/mistakes-candidates.md`](file:///c:/Users/HP/OneDrive/Desktop/Speech/.ai/mistakes-candidates.md).
- **Architectural Records**: Record all major architectural tradeoffs in [`docs/decisions/`](file:///c:/Users/HP/OneDrive/Desktop/Speech/docs/decisions) following [`docs/decisions/000-template.md`](file:///c:/Users/HP/OneDrive/Desktop/Speech/docs/decisions/000-template.md).
