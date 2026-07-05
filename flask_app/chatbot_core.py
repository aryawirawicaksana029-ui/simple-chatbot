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
        """Send a user message to Groq and return Aria's reply."""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + self.conversation_history
        )

        assistant_message = response.choices[0].message.content

        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def clear_history(self):
        self.conversation_history.clear()
