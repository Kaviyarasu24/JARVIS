"""Wikipedia search feature for JARVIS."""
from __future__ import annotations

import wikipedia

# Max sentences spoken aloud — keeps TTS response short
_SUMMARY_SENTENCES = 3


def search_wikipedia(query: str) -> str:
    """Search Wikipedia and return a brief spoken summary."""
    query = query.strip()
    if not query:
        return "Please tell me what to search for on Wikipedia."

    try:
        wikipedia.set_lang("en")
        # Auto-suggest the closest matching title
        results = wikipedia.search(query, results=5)
        if not results:
            return f"No Wikipedia results found for '{query}'."

        # Try the top result; fall back to next if disambiguation occurs
        for title in results:
            try:
                summary = wikipedia.summary(
                    title,
                    sentences=_SUMMARY_SENTENCES,
                    auto_suggest=False,
                )
                return f"{title}. {summary}"
            except wikipedia.DisambiguationError as e:
                # Pick the first specific option from the disambiguation list
                option = e.options[0] if e.options else None
                if option:
                    try:
                        summary = wikipedia.summary(
                            option,
                            sentences=_SUMMARY_SENTENCES,
                            auto_suggest=False,
                        )
                        return f"{option}. {summary}"
                    except Exception:
                        continue
            except wikipedia.PageError:
                continue
            except Exception:
                continue

        return f"Could not retrieve a Wikipedia article for '{query}'."
    except Exception as exc:
        return f"Wikipedia search failed: {exc}"
