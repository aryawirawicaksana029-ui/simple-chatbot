import os
import uuid

from flask import Flask, render_template, request, jsonify, session

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


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Message can't be empty."}), 400

    aria = get_chatbot()

    try:
        reply = aria.chat(user_message)
    except Exception as e:
        return jsonify({"error": f"Failed to reach Groq API: {e}"}), 500

    return jsonify({"reply": reply})


@app.route("/clear", methods=["POST"])
def clear():
    aria = get_chatbot()
    aria.clear_history()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True)
