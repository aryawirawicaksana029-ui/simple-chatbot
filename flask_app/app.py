import os
import uuid

from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context

from chatbot_core import AriaChatbot

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


@app.route("/clear", methods=["POST"])
def clear():
    aria = get_chatbot()
    aria.clear_history()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True)