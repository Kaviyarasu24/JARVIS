# J.A.R.V.I.S

J.A.R.V.I.S (AI )is a Windows-first voice assistant built in Python and upgraded to a goal-based agent architecture.

Instead of matching commands with a long rule list, it now:

1. Understands user intent.
2. Plans tool actions.
3. Executes tools one-by-one.
4. Synthesizes a final response.

This enables more natural voice requests and multi-step behavior.

The repository includes both a terminal voice mode and a cinematic desktop UI. The UI adds a transcript panel, task and calendar widgets, face authentication, and speech controls on top of the same tool-based agent.

---

## Project Overview

- Platform: Windows
- Language: Python 3.13+
- Interaction modes:
  - Terminal voice mode
  - Desktop UI mode
- Agent model backend: Ollama (recommended model: `llama3.2`)
- Current tool count: 46

Core capabilities include weather, news, Wikipedia, system status, todo management, notes, finance data, network status, app control, screenshots, audio/display controls, and entertainment tools.

---

## Architecture

### High-Level Flow

User Voice/Text -> Agent Planner -> Tool Call(s) -> Observation(s) -> Final Response -> TTS/UI

### Main Components

1. Agent Orchestrator
- File: `features/agent.py`
- Responsibilities:
  - ReAct-style planning loop
  - JSON step parsing
  - conversation memory (rolling session window)
  - fallback routing when model is unavailable

2. Tool Registry
- File: `features/tools.py`
- Responsibilities:
  - single source of truth for tools
  - metadata for tool name/description/parameters
  - tool execution wrapper and error shaping

3. Feature Modules
- Folder: `features/`
- Responsibilities:
  - actual tool implementations
  - isolated logic by domain (weather, system, notes, etc.)

4. Entry Points
- `jarvis.py`: terminal mode + voice + face authentication + notifications
- `ui.py`: desktop interface + transcript + voice controls + agent routing
- `ui_components/`: shared UI helpers for auth, speech, and theme handling

5. Data Layer
- Folder: `data/`
- Stores local JSON for persistent user data (tasks, notes, config-style content)

---

## Repository Structure

```text
J.A.R.V.I.S/
  data/
  Face-Recognition/
  features/
    agent.py
    tools.py
    weather.py
    news_headlines.py
    stock_market.py
    system_control.py
    system_info.py
    network_status.py
    todo_list.py
    notes.py
    entertainment.py
    browser_control.py
    wikipedia_search.py
    calculator.py
    tell_time.py
  jarvis.py
  ui.py
  requirements.txt
  FUNCTIONS.md
  IMPLEMENTATION_PLAN.md
  README.md
```

---

## Setup Guide (Windows)

### 1) Clone and Enter Project

```powershell
git clone <your-repo-url>
cd J.A.R.V.I.S
```

### 2) Create and Activate Virtual Environment

```powershell
python -m venv .jarvis
.\.jarvis\Scripts\Activate.ps1
```

### 3) Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 4) Install and Start Ollama

Install Ollama from official installer, then:

```powershell
ollama serve
ollama pull llama3.2
```

If `llama3.2` is unavailable, the agent can auto-detect another installed model.

### 5) Face Recognition Prerequisite (Terminal and UI Auth)

Ensure trainer file exists:

- `Face-Recognition/trainer/trainer.yml`

If missing, run training scripts under `Face-Recognition/` first.

---

## How to Run

### UI Mode (Recommended)

```powershell
python ui.py
```

The UI starts with face authentication, then shows the main Jarvis dashboard and routes requests through the same agent used by terminal mode.

### Terminal Mode

```powershell
python jarvis.py
```

Terminal mode uses microphone input, text-to-speech, face authentication, and the same goal-based tool planner.

---

## Workflow (End-to-End)

1. User speaks or types request.
2. Input is sent to `agent.run(...)`.
3. Agent asks model for next JSON action.
4. Agent executes one tool from registry.
5. Tool result is returned as observation.
6. Agent repeats until it emits `respond`.
7. Final response is spoken and/or shown in UI transcript.

Fallback behavior:

- If Ollama is unavailable, fallback intent routing handles common requests.
- If tool args are malformed, tool executor returns safe error text.
- Public IP lookup is intentionally disabled.

---

## Implemented Capability Categories

- Time
- Weather
- News
- Wikipedia search
- System info and battery
- Calculator
- Todo manager
- Network status and ping
- Stock and crypto updates
- Browser open/search
- App launch
- Power controls
- Audio and brightness controls
- Screenshots
- Jokes and trivia
- Notes

Public IP lookup is currently disabled by design.

---

## Natural Voice Examples

- "What is the weather in Chennai?"
- "Add task submit project tomorrow"
- "Show my tasks"
- "Tell me a joke"
- "Open Notepad"
- "Set volume to 40 percent"
- "Take a screenshot"
- "Search Wikipedia for machine learning"

You do not need strict command format; natural speech is supported.

---

## Testing and Validation

### Syntax/Compile Check

```powershell
python -m py_compile jarvis.py ui.py features\agent.py features\tools.py
```

### Manual Smoke Test Suggestions

1. Weather request with city.
2. Add/view/complete/remove todo task.
3. Open app (safe app like Notepad).
4. Tell joke.
5. Screenshot capture.

Note: avoid running destructive power tools during routine smoke tests.

---

## How to Add a New Function

1. Implement function in an appropriate module inside `features/`.
2. Register it in `features/tools.py`:
   - name
   - description
   - parameters
   - callable
3. Keep output concise and speech-friendly.
4. Run compile test and a manual invocation.
5. Update docs:
   - `FUNCTIONS.md` (tool tracker)
   - `IMPLEMENTATION_PLAN.md` (if roadmap changed)

No rule-router edits are needed.

## UI Notes

- `ui.py` provides the primary desktop experience with a cinematic blue theme.
- Face recognition depends on `Face-Recognition/trainer/trainer.yml` and OpenCV's Haar cascade.
- Speech output is serialized so multiple responses do not overlap.
- The UI shares the same agent and tool registry as the terminal app, so new tools appear everywhere automatically.

---

## Configuration and Data

- `data/news.json`: source config for weather/news/finance selections
- `data/todo_tasks.json`: tasks storage
- `data/notes.json`: notes storage

Keep these files writable for normal operation.

---

## Troubleshooting

1. Agent replies with model unavailable
- Ensure Ollama daemon is running: `ollama serve`
- Ensure a model is installed: `ollama pull llama3.2`

2. Voice recognition is unreliable
- Check microphone permissions in Windows settings
- Reduce ambient noise
- Retry with shorter utterances

3. Face authentication fails
- Confirm webcam access
- Confirm trainer model exists at `Face-Recognition/trainer/trainer.yml`

4. Some tools return network errors
- Verify internet connectivity
- Retry after short delay

5. UI launches but action is inconsistent
- Restart app after dependency updates
- Re-activate virtual environment before running

---

## Security and Safety Notes

- Some tools can change system state (power, volume, app launch).
- Use responsibly, especially in shared systems.
- For production hardening, add confirmation gates for destructive actions.

---

## Documentation Map

- `README.md`: full project guide (this file)
- `FUNCTIONS.md`: tool coverage tracker
- `IMPLEMENTATION_PLAN.md`: phased architecture roadmap

---

## License and Usage

Add your project license details here.

