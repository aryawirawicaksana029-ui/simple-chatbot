"""
chatbot_core.py
Core logic for ARIA chatbot (Groq + LLaMA 3.3 70B).
Shared by both the CLI (chatbot.py) and GUI (chatbot_gui.py) versions.
"""

import json
from datetime import datetime

from groq import Groq
from config import GROQ_API_KEY

SYSTEM_PROMPT = (
    "You are a helpful assistant named Aria. "
    "You are friendly, smart, and concise."
)

MODEL_NAME = "llama-3.3-70b-versatile"
WHISPER_MODEL = "whisper-large-v3"  # Groq's hosted speech-to-text model

# Preset personas. Each value is the system prompt used to steer Aria's style.
PERSONAS = {
    "default": SYSTEM_PROMPT,
    "formal": (
        "You are Aria, a professional and formal AI assistant. "
        "Always respond with precise, well-structured, businesslike language. Avoid slang and emoji."
    ),
    "santai": (
        "Kamu adalah Aria, asisten AI yang santai, gaul, dan ramah. "
        "Boleh pakai bahasa sehari-hari, singkatan, dan emoji secukupnya, tapi tetap membantu dan jelas."
    ),
    "sarcastic": (
        "You are Aria, a witty assistant with a sharp, sarcastic sense of humor. "
        "Tease the user a little, but always give a genuinely correct and helpful answer underneath the snark."
    ),
    "mentor": (
        "You are Aria, a patient and encouraging mentor. "
        "Explain things step by step, check understanding, and motivate the user like a supportive teacher."
    ),
}


class AriaChatbot:
    """Wraps the Groq client and keeps conversation history."""

    def __init__(self, api_key: str = GROQ_API_KEY, model: str = MODEL_NAME, persona: str = "default"):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.conversation_history = []
        self.persona_name = "custom"
        self.system_prompt = SYSTEM_PROMPT
        self.set_persona(persona)

    def set_persona(self, persona) -> str:
        """
        Switch Aria's personality.
        `persona` can be a preset key from PERSONAS (e.g. "formal", "santai")
        or any custom system-prompt text. Returns the resulting system prompt.
        """
        if persona in PERSONAS:
            self.persona_name = persona
            self.system_prompt = PERSONAS[persona]
        else:
            self.persona_name = "custom"
            self.system_prompt = persona
        return self.system_prompt

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
                {"role": "system", "content": self.system_prompt}
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

    def transcribe_audio(self, filepath: str, language: str = None) -> str:
        """
        Transcribe an audio file (wav, mp3, m4a, webm, etc.) to text using
        Groq's hosted Whisper model.

        `language` is an optional ISO-639-1 code (e.g. "id" for Indonesian,
        "en" for English). Leaving it as None lets Whisper auto-detect the
        language, which works well enough for mixed Indonesian/English speech.

        Returns the transcribed text (empty string if nothing was recognized).
        """
        with open(filepath, "rb") as audio_file:
            transcription = self.client.audio.transcriptions.create(
                file=(filepath, audio_file.read()),
                model=WHISPER_MODEL,
                language=language,
                response_format="text",
            )
        # The SDK sometimes returns a plain string, sometimes an object with
        # a .text attribute depending on response_format — handle both.
        return transcription if isinstance(transcription, str) else transcription.text

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