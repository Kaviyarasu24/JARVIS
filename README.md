# J.A.R.V.I.S (Goal-Based Agent Architecture)

This project has been migrated from a rule-based command router to a goal-based agent that plans actions and executes tools.

## What Changed

Old approach:
- User input -> normalize command -> long if/elif command map -> single action

New approach:
- User input -> LLM planner -> tool execution loop -> final response
- Supports multi-step tasks and more natural requests

## Core Design

### 1) Tool Registry
- File: `features/tools.py`
- All capabilities are exposed as named tools with:
  - `description`
  - `parameters`
  - `fn` (callable implementation)

### 2) Goal-Based Agent
- File: `features/agent.py`
- Uses a ReAct-style loop:
  1. Ask model for next step in JSON
  2. Execute one tool
  3. Feed observation back to model
  4. Repeat until model returns `respond`
- Includes rolling session memory for context
- Includes keyword fallback if Ollama is unavailable

### 3) App Entry Points
- `jarvis.py`: terminal/voice flow + authentication + notification loop
- `ui.py`: desktop UI flow; routes user input through `agent.run(...)`

### 4) Feature Modules
All feature modules remain in `features/` and are now consumed through the tool registry.
Examples:
- `features/weather.py`
- `features/news_headlines.py`
- `features/system_control.py`
- `features/browser_control.py`
- `features/entertainment.py`
- `features/notes.py`

## Requirements

Install dependencies:

```powershell
pip install -r requirements.txt
```

Ollama setup (required for full goal-based planning):

```powershell
ollama serve
ollama pull llama3.2
```

## Run

Terminal mode:

```powershell
python jarvis.py
```

UI mode:

```powershell
python ui.py
```

## How To Add New Capability

1. Implement function in a feature module under `features/`
2. Register it in `features/tools.py` with clear description/params
3. No router `if/elif` edits needed

## Notes

- If Ollama is offline, the agent uses safe keyword fallback for common commands.
- Keep tool parameter names simple and model-friendly.
- Keep tool outputs short and speech-friendly.
