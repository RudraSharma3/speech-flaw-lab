# Project Instructions

Read this entire file before starting any task on this project.

---

## 1. Project Purpose

Speech is a high-performance voice and conversational AI platform featuring real-time audio capture, speech-to-text (STT) transcription, agentic LLM reasoning with MCP multi-agent worker orchestration, and text-to-speech (TTS) voice synthesis.

## 2. Required Reading

Before taking action, review:
- `docs/architecture.md` (System context, components, data flows)
- `docs/graph.md` (Component hierarchy, route call paths, blast radius matrix)
- `docs/conventions.md` (Code style, git workflows, test patterns)
- `docs/task-state.md` (Active task progress, goals, blockers)
- Relevant records in `docs/decisions/` (Accepted architectural choices)
- `docs/lessons.md` (Verified project lessons)

---

## 3. Environment & Commands

<!-- List exact development commands for this repository -->
- **Install**: `npm install` <!-- update with actual package manager -->
- **Dev**: `npm run dev`
- **Test**: `npm test`
- **Lint / Typecheck**: `npm run lint`
- **Build**: `npm run build`

---

## 4. Engineering Rules

1. Make the smallest surgical change that satisfies the acceptance criteria.
2. Follow established patterns in `docs/conventions.md` and `docs/architecture.md`.
3. Never modify unrelated files or alter working behavior without justification.
4. Always add or update tests for functional changes.
5. Record material architectural trade-offs as ADRs in `docs/decisions/`.
6. Never commit secrets, credentials, API keys, or private tokens to version control.
7. Automatically apply Reverse Prompting (clarifying questions) and generate a 4-part Prompt Contract (GOAL, CONSTRAINTS, FORMAT, FAILURE) in `docs/task-state.md` for messy or ambiguous requests before executing.
8. Practice Proportional Effort: Use Solo Model execution for routine tasks; reserve Multi-Agent MCP orchestration and Consensus sampling strictly for high-complexity architectural decisions.

---

## 5. Self-Modifying Learning Loop

When the user gives a direct correction or states a recurring preference:
1. **Append Rule**: Immediately assign the next sequential number and append it to `## 6. Learned Rules` below.
   - Format: `N. [CATEGORY] Rule description — rationale.`
   - Allowed Categories: `[STYLE]`, `[CODE]`, `[ARCH]`, `[TOOL]`, `[PROCESS]`, `[DATA]`, `[UX]`, `[SECURITY]`, `[TEST]`, `[OTHER]`.
2. **Supersede Obsolete Rules**: If a new preference replaces an older rule, mark the older rule with `- SUPERSEDED BY RULE N.` (never silently delete).
3. **Generalize Secrets**: Never store raw credentials or API keys; generalize into security practices.
4. **Notify User**: Explicitly state in the response: `🧠 Learned Rule Added to AGENTS.md: N. [CATEGORY] Rule — rationale.`

For unverified internal errors or complex edge cases, log a candidate first in `.ai/mistakes-candidates.md`.

---

## 6. Learned Rules

<!--
Validated project-specific rules are appended below sequentially.
Format: N. [CATEGORY] Rule description — rationale.
-->

1. [PROCESS] Read `docs/task-state.md` and `docs/architecture.md` before writing code — ensures alignment with current project context and architecture.
2. [SECURITY] Never hardcode secrets or private keys — load credentials through environment variables or configuration managers.
3. [TEST] Run project test suite and verify changes before declaring task completion — ensures code quality and prevents regressions.
4. [DATA] Never substitute stand-ins or synthetically generated files for user-recorded data in benchmarks, docs, catalogs, or scripts; mark uncollected inputs as NOT YET INGESTED — prevents fabricating evaluation evidence.
