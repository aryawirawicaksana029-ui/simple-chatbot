"""
aria_core
Shared core logic for ARIA, used by all three interfaces — the CLI
(chatbot.py), the GUI (chatbot_gui.py), and the Web App (flask_app/app.py).

Before this refactor, chatbot_core.py, rag_utils.py, and tools_utils.py each
existed as two nearly-identical copies (project root and flask_app/), since
the Web App runs as a separate Flask project one directory down. Keeping
those copies in sync by hand was a real, recurring source of bugs (see repo
history / README "Known Limitations" for the pain this caused). Now there's
exactly one copy of each, imported by both entry points as `aria_core.<module>`.

How the Flask app (one directory down, in flask_app/) reaches this package:
flask_app/app.py appends the project root to sys.path before importing
anything from aria_core — see the comment there for why it's an *append*
and not an *insert(0, ...)*, which matters for config.py resolution.
"""
