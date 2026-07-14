"""
app.py
Flask Web App version of ARIA chatbot.

Run with:
    python app.py
Then open http://127.0.0.1:5000 in your browser.
"""

import os
import uuid
import tempfile
import json
from datetime import datetime

from flask import (
    Flask, render_template, request, jsonify, session,
    Response, stream_with_context, make_response
)

from chatbot_core import AriaChatbot, PERSONAS, RAG_AVAILABLE
import db_utils

app = Flask(__name__)
# Secret key for signing the session cookie (session only stores a session_id,
# never the API key or chat content itself).
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

# In-memory store: session_id -> AriaChatbot instance.
# This still resets whenever the Flask *process* restarts, but get_chatbot()
# below repopulates each AriaChatbot from SQLite (db_utils.py) the moment
# it's recreated, so conversation history and settings aren't actually lost —
# only the in-memory cache is empty right after a restart.
sessions: dict[str, AriaChatbot] = {}


def _persist_settings(aria: AriaChatbot, session_id: str):
    """Save this session's current persona, RAG toggle, and tools toggle to SQLite."""
    persona_key = aria.persona_name
    custom_prompt = aria.system_prompt if persona_key == "custom" else None
    db_utils.save_settings(session_id, persona_key, custom_prompt, aria.rag_enabled, aria.tools_enabled)


def get_chatbot() -> AriaChatbot:
    """Get (or create) the AriaChatbot tied to the current browser session.
    On first access after a process restart, this restores conversation
    history and settings (persona, RAG toggle, tools toggle) from SQLite
    instead of starting the person's session over from scratch."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    session_id = session["session_id"]

    if session_id not in sessions:
        aria = AriaChatbot()

        settings = db_utils.load_settings(session_id)
        if settings["persona_key"] == "custom" and settings["custom_prompt"]:
            aria.set_persona(settings["custom_prompt"])
        else:
            aria.set_persona(settings["persona_key"])

        if settings["rag_enabled"] and RAG_AVAILABLE:
            aria.enable_rag()

        if not settings["tools_enabled"]:
            aria.disable_tools()  # AriaChatbot defaults tools_enabled=True already

        aria.conversation_history = db_utils.load_messages(session_id)

        sessions[session_id] = aria

    return sessions[session_id]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/config")
def config_info():
    """Tells the frontend which features are available on this deployment,
    so it can hide UI elements for features that are disabled (e.g. RAG on
    a low-memory hosting tier) instead of showing broken buttons."""
    return jsonify({"rag_enabled": RAG_AVAILABLE})


STREAM_ERROR_PREFIX = "__ARIA_STREAM_ERROR__:"
STREAM_CITATIONS_PREFIX = "__ARIA_CITATIONS__:"
STREAM_TOOLS_PREFIX = "__ARIA_TOOLS__:"


@app.route("/chat", methods=["POST"])
def chat():
    """
    Streams Aria's reply back to the browser chunk by chunk (ChatGPT-style),
    using plain chunked HTTP responses instead of one big JSON blob.

    If something goes wrong *after* streaming has already started, we can't
    change the HTTP status anymore (headers are already sent), so the error
    is sent inline with a special prefix that the frontend knows to detect.
    RAG citations (if any) are sent the same way, as a trailing JSON blob
    after a special prefix, once the reply has fully streamed.
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Message can't be empty."}), 400

    aria = get_chatbot()
    session_id = session["session_id"]

    def generate():
        full_reply = ""
        try:
            for chunk in aria.chat_stream(user_message):
                full_reply += chunk
                yield chunk
            # Only persist once the full reply has arrived successfully —
            # avoids saving a half-finished exchange if the stream errors out.
            db_utils.append_message(session_id, "user", user_message)
            db_utils.append_message(session_id, "assistant", full_reply)

            citations = aria.get_rag_citations()
            if citations:
                yield f"{STREAM_CITATIONS_PREFIX}{json.dumps(citations)}"

            tool_calls = aria.get_tool_usage()
            if tool_calls:
                yield f"{STREAM_TOOLS_PREFIX}{json.dumps(tool_calls)}"
        except Exception as e:
            yield f"{STREAM_ERROR_PREFIX}Failed to reach Groq API: {e}"

    return Response(stream_with_context(generate()), mimetype="text/plain")


@app.route("/rag/upload", methods=["POST"])
def rag_upload():
    """Upload a .txt/.pdf/.docx file and add it to the shared knowledge base."""
    if not RAG_AVAILABLE:
        return jsonify({"error": "RAG is disabled on this deployment."}), 503

    if "document" not in request.files:
        return jsonify({"error": "No document received."}), 400

    doc_file = request.files["document"]
    filename = doc_file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".txt", ".pdf", ".docx"]:
        return jsonify({"error": "Only .txt, .pdf, and .docx files are supported."}), 400

    aria = get_chatbot()

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        doc_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = aria.add_document_to_kb(tmp_path)
    except Exception as e:
        return jsonify({"error": f"Failed to process document: {e}"}), 500
    finally:
        os.remove(tmp_path)

    return jsonify({"filename": filename, "chunks": result["chunks"], "flagged": result["flagged"]})


@app.route("/rag/toggle", methods=["POST"])
def rag_toggle():
    """Enable/disable RAG for the current session."""
    if not RAG_AVAILABLE:
        return jsonify({"error": "RAG is disabled on this deployment."}), 503

    data = request.get_json(silent=True) or {}
    enabled = bool(data.get("enabled"))

    aria = get_chatbot()
    session_id = session["session_id"]
    if enabled:
        aria.enable_rag()
    else:
        aria.disable_rag()

    _persist_settings(aria, session_id)

    return jsonify({"rag_enabled": aria.rag_enabled})


@app.route("/tools/toggle", methods=["POST"])
def tools_toggle():
    """Enable/disable tool calling (calculator + web search) for the current session."""
    data = request.get_json(silent=True) or {}
    enabled = bool(data.get("enabled"))

    aria = get_chatbot()
    session_id = session["session_id"]
    if enabled:
        aria.enable_tools()
    else:
        aria.disable_tools()

    _persist_settings(aria, session_id)

    return jsonify({"tools_enabled": aria.tools_enabled})


@app.route("/rag/documents", methods=["GET"])
def rag_documents():
    """List documents currently in the shared knowledge base."""
    aria = get_chatbot()
    return jsonify({"documents": aria.list_kb_documents()})


@app.route("/rag/clear", methods=["POST"])
def rag_clear():
    """Wipe the entire knowledge base (shared across all sessions)."""
    aria = get_chatbot()
    aria.clear_kb()
    return jsonify({"status": "cleared"})


@app.route("/clear", methods=["POST"])
def clear():
    aria = get_chatbot()
    session_id = session["session_id"]
    aria.clear_history()
    db_utils.clear_messages(session_id)
    return jsonify({"status": "cleared"})


@app.route("/transcribe", methods=["POST"])
def transcribe():
    """
    Accepts an audio recording captured in the browser (via the
    MediaRecorder API) and returns its transcription using Groq's
    hosted Whisper model.

    Note: text-to-speech (Aria talking back) is handled entirely on the
    client with the browser's speechSynthesis API — no endpoint needed
    for that direction, only for speech-to-text.
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file received."}), 400

    audio_file = request.files["audio"]
    aria = get_chatbot()

    # Groq's SDK expects a filesystem path / bytes, not a raw Flask
    # FileStorage object, so we save the upload to a temp file first.
    suffix = os.path.splitext(audio_file.filename or "audio.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        text = aria.transcribe_audio(tmp_path)
    except Exception as e:
        return jsonify({"error": f"Failed to transcribe audio: {e}"}), 500
    finally:
        os.remove(tmp_path)

    return jsonify({"text": text})


@app.route("/persona", methods=["GET", "POST"])
def persona():
    aria = get_chatbot()

    if request.method == "GET":
        return jsonify({"current": aria.persona_name, "available": list(PERSONAS.keys())})

    data = request.get_json(silent=True) or {}
    new_persona = (data.get("persona") or "").strip()

    if not new_persona:
        return jsonify({"error": "Persona can't be empty."}), 400

    aria.set_persona(new_persona)
    _persist_settings(aria, session["session_id"])
    return jsonify({"current": aria.persona_name})


@app.route("/download")
def download():
    """
    Lets the browser download the current session's conversation as a file.
    Usage: /download            -> plain text transcript
           /download?format=json -> structured JSON export
    """
    aria = get_chatbot()

    if not aria.has_messages():
        return jsonify({"error": "No conversation to save yet."}), 400

    fmt = request.args.get("format", "txt").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "json":
        content = aria.export_history_json()
        filename = f"aria_chat_{timestamp}.json"
        mimetype = "application/json"
    else:
        content = aria.export_history_text()
        filename = f"aria_chat_{timestamp}.txt"
        mimetype = "text/plain"

    response = make_response(content)
    response.headers["Content-Type"] = f"{mimetype}; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


if __name__ == "__main__":
    app.run(debug=True)