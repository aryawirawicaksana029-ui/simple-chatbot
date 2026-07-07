import json
from datetime import datetime

from groq import Groq
from config import GROQ_API_KEY

SYSTEM_PROMPT = (
    "You are a helpful assistant named Aria. "
    "You are friendly, smart, and concise."
)

MODEL_NAME = "llama-3.3-70b-versatile"


class AriaChatbot:
    """Wraps the Groq client and keeps conversation history."""

    def __init__(self, api_key: str = GROQ_API_KEY, model: str = MODEL_NAME):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.conversation_history = []

    def chat(self, user_message: str) -> str:
        """Send a user message to Groq and return Aria's full reply (no streaming)."""
        return "".join(self.chat_stream(user_message))

    def chat_stream(self, user_message: str):
        """
        Send a user message to Groq and yield Aria's reply piece by piece
        (word/token chunks) as they arrive, ChatGPT-style.

        The full reply is still saved to conversation_history once the
        stream finishes, so streaming and non-streaming stay consistent.
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + self.conversation_history,
            stream=True,
        )

        full_reply = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_reply += delta
                yield delta

        self.conversation_history.append({
            "role": "assistant",
            "content": full_reply
        })

    def clear_history(self):
        self.conversation_history.clear()

    # ---------- Save / export conversation history ----------

    def has_messages(self) -> bool:
        return len(self.conversation_history) > 0

    def export_history_text(self) -> str:
        """Return a human-readable transcript of the conversation."""
        lines = [
            "ARIA Chat Export",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 45,
            "",
        ]

        if not self.conversation_history:
            lines.append("(no messages yet)")
        else:
            for msg in self.conversation_history:
                speaker = "You" if msg["role"] == "user" else "Aria"
                lines.append(f"{speaker}: {msg['content']}")
                lines.append("")

        return "\n".join(lines)

    def export_history_json(self) -> str:
        """Return the conversation as a JSON string (structured, machine-readable)."""
        payload = {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "model": self.model,
            "messages": self.conversation_history,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def save_to_file(self, filepath: str, fmt: str = "txt") -> str:
        """
        Write the conversation history to disk.
        fmt: "txt" for a readable transcript, "json" for structured data.
        Returns the filepath that was written.
        """
        content = self.export_history_json() if fmt == "json" else self.export_history_text()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath