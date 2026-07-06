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