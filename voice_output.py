"""
voice_output.py
Text-to-speech helper using pyttsx3 (fully offline, no API calls, no cost).

Used by the CLI and GUI versions of ARIA. The Web App version instead
uses the browser's built-in speechSynthesis API (see flask_app/static/script.js),
since that's already free and doesn't need a Python TTS engine at all.
"""

import pyttsx3

_engine = None


def _get_engine():
    """Lazily create a single shared pyttsx3 engine instance (creating a new
    one per call can crash on some platforms if the previous one wasn't
    fully released)."""
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 175)  # a bit faster than the pyttsx3 default
    return _engine


def speak(text: str):
    """Speak `text` out loud. Blocks the calling thread until speech finishes,
    so callers running this on the GUI's main thread should use a background
    thread instead (see chatbot_gui.py)."""
    if not text or not text.strip():
        return
    engine = _get_engine()
    engine.say(text)
    engine.runAndWait()
