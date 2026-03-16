# JARVIS Implementation Plan (Goal-Based Architecture)

Last updated: March 16, 2026

This plan is aligned with the current architecture:

- Input -> Goal understanding -> Tool planning -> Tool execution -> Response synthesis
- Progress is driven by tool quality, safety, and orchestration (not hard-coded command rules)

---

## 1) Current Baseline

### Implemented
- Goal planner and ReAct loop in `features/agent.py`
- Unified tool registry in `features/tools.py`
- 43 registered tools across system, web, productivity, entertainment
- Voice and UI entry points route through the same agent (`jarvis.py`, `ui.py`)
- Session memory (rolling history)
- Fallback execution when Ollama is unavailable

### Gaps
- No confirmation gate for high-risk tools yet
- No long-term persistent memory yet
- No automated test suite yet
- Browser automation is still shallow (open/search only, no element-level actions)

---

## 2) Phase Plan

### Phase A - Reliability and Safety (Highest Priority)
Goal: make the existing agent safe and stable for daily use.

Tasks:
- [ ] Add confirmation flow for destructive actions:
  - `shutdown`, `restart`, `sleep`, `lock_screen`
- [ ] Add per-tool timeout and retry policy in agent execution
- [ ] Add clear user-facing tool error normalization
- [ ] Add optional allowlist/denylist policy file for tools

Deliverable:
- Agent will refuse risky actions unless user confirms
- Better failure recovery and predictable behavior

Estimated effort:
- 1-2 days

---

### Phase B - Memory and Personalization
Goal: enable persistence and context beyond one session.

Tasks:
- [ ] Add persistent memory store in `data/`:
  - user preferences
  - recent goals
  - successful tool patterns
- [ ] Build memory read/write utilities and integrate into `agent.run(...)`
- [ ] Add memory retention policy (size limits, pruning)
- [ ] Add opt-out toggle for memory

Deliverable:
- Agent remembers stable preferences across restarts

Estimated effort:
- 2-3 days

---

### Phase C - Testing and Quality Gates
Goal: prevent regressions while adding tools.

Tasks:
- [ ] Add `tests/` structure with `pytest`
- [ ] Unit tests for:
  - tool dispatch (`features/tools.py`)
  - fallback routing (`features/agent.py`)
  - high-use tools (weather/news/todo/system)
- [ ] Mock network calls for deterministic tests
- [ ] Add one smoke test for end-to-end planning loop

Deliverable:
- CI-ready basic test suite for core agent flows

Estimated effort:
- 2 days

---

### Phase D - Browser and Productivity Expansion
Goal: close major capability gaps requested in tracker.

Tasks:
- [ ] Browser action tools:
  - click element
  - fill form
  - extract content
  - navigation controls (back/forward/refresh/close)
- [ ] Productivity tools:
  - reminders/scheduler
  - email send
  - calendar event add/view

Deliverable:
- Multi-step web and productivity goals executable by planner

Estimated effort:
- 4-6 days

---

### Phase E - Intelligence Improvements
Goal: improve planning quality and user experience.

Tasks:
- [ ] Clarification behavior for ambiguous goals
- [ ] Tool confidence scoring and tool selection hints
- [ ] Better structured prompt templates and few-shot plans
- [ ] Optional command suggestion/prediction from history

Deliverable:
- More accurate planning, fewer wrong tool calls

Estimated effort:
- 3-5 days

---

## 3) Tracking Model (How Progress Is Measured)

Track by these metrics instead of command-count checklists:

- Tool coverage: number and quality of tools exposed in `features/tools.py`
- Safety coverage: risky tools protected by confirmation policies
- Reliability: error rate and fallback success rate
- Planning quality: percent of goals solved within max steps
- Test coverage: core modules covered by automated tests

---

## 4) Definition of Done (Per Tool)

A tool is considered complete when all are true:

- [ ] Registered in `features/tools.py` with clear description and params
- [ ] Handles invalid args gracefully
- [ ] Has timeout/failure-safe behavior
- [ ] Has at least one unit test
- [ ] Produces concise, speech-friendly output

---

## 5) Near-Term Execution Order

1. Phase A (Safety and reliability)
2. Phase C (Testing baseline)
3. Phase B (Persistent memory)
4. Phase D (Browser and productivity expansion)
5. Phase E (Advanced planning quality)

---

## 6) Required Runtime Stack

Core dependencies are already in `requirements.txt`.

For full goal-based planning:

```bash
ollama serve
ollama pull llama3.2
```

Run:

```bash
python ui.py
# or
python jarvis.py
```

---

## 7) Notes

- This plan intentionally avoids returning to rule-based command routers.
- New capabilities should be added as tools first, then exposed to the planner.
- Documentation (`FUNCTIONS.md`, `README.md`, this file) should stay tool-centric and architecture-centric.
