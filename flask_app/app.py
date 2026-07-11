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
from datetime import datetime

from flask import (
    Flask, render_template, request, jsonify, session,
    Response, stream_with_context, make_response
)

from chatbot_core import AriaChatbot, PERSONAS

app = Flask(__name__)
# Secret key for signing the session cookie (session only stores a session_id,
# never the API key or chat content itself).
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

# In-memory store: session_id -> AriaChatbot instance.
# NOTE: This resets whenever the server restarts, and only works with a
# single process (fine for local/dev use). For production with multiple
# workers, back this with Redis or a database instead.
sessions: dict[str, AriaChatbot] = {}


def get_chatbot() -> AriaChatbot:
    """Get (or create) the AriaChatbot tied to the current browser session."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    session_id = session["session_id"]

    if session_id not in sessions:
        sessions[session_id] = AriaChatbot()

    return sessions[session_id]


@app.route("/")
def index():
    return render_template("index.html")


STREAM_ERROR_PREFIX = "__ARIA_STREAM_ERROR__:"


@app.route("/chat", methods=["POST"])
def chat():
    """
    Streams Aria's reply back to the browser chunk by chunk (ChatGPT-style),
    using plain chunked HTTP responses instead of one big JSON blob.

    If something goes wrong *after* streaming has already started, we can't
    change the HTTP status anymore (headers are already sent), so the error
    is sent inline with a special prefix that the frontend knows to detect.
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Message can't be empty."}), 400

    aria = get_chatbot()

    def generate():
        try:
            for chunk in aria.chat_stream(user_message):
                yield chunk
        except Exception as e:
            yield f"{STREAM_ERROR_PREFIX}Failed to reach Groq API: {e}"

    return Response(stream_with_context(generate()), mimetype="text/plain")


@app.route("/rag/upload", methods=["POST"])
def rag_upload():
    """Upload a .txt/.pdf/.docx file and add it to the shared knowledge base."""
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
        chunk_count = aria.add_document_to_kb(tmp_path)
    except Exception as e:
        return jsonify({"error": f"Failed to process document: {e}"}), 500
    finally:
        os.remove(tmp_path)

    return jsonify({"filename": filename, "chunks": chunk_count})


@app.route("/rag/toggle", methods=["POST"])
def rag_toggle():
    """Enable/disable RAG for the current session."""
    data = request.get_json(silent=True) or {}
    enabled = bool(data.get("enabled"))

    aria = get_chatbot()
    if enabled:
        aria.enable_rag()
    else:
        aria.disable_rag()

    return jsonify({"rag_enabled": aria.rag_enabled})


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
    aria.clear_history()
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