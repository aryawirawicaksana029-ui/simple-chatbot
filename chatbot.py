import os
from datetime import datetime

from chatbot_core import AriaChatbot

aria = AriaChatbot()

HISTORY_DIR = "chat_history"


def save_history_to_file(fmt: str = "txt") -> str:
    """Save the current conversation to chat_history/aria_chat_<timestamp>.<ext>"""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"aria_chat_{timestamp}.{fmt}"
    filepath = os.path.join(HISTORY_DIR, filename)
    return aria.save_to_file(filepath, fmt=fmt)


def main():
    print("=" * 45)
    print("  🤖 ARIA - AI Chatbot powered by Groq")
    print("=" * 45)
    print("  Type 'quit' or 'exit' to stop")
    print("  Type 'clear' to clear history")
    print("  Type 'save' to save conversation to a .txt file")
    print("  Type 'save json' to save conversation to a .json file")
    print("=" * 45)

    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit"]:
            print("\nAria: Goodbye! Have a great day! 👋")
            break

        if user_input.lower() == "clear":
            aria.clear_history()
            print("\n✅ Conversation history cleared!")
            continue

        if user_input.lower() in ["save", "save json"]:
            if not aria.has_messages():
                print("\n⚠️  Nothing to save yet — start chatting first!")
                continue

            fmt = "json" if user_input.lower() == "save json" else "txt"
            filepath = save_history_to_file(fmt)
            print(f"\n💾 Conversation saved to: {filepath}")
            continue

        print("\nAria: ", end="", flush=True)
        try:
            for chunk in aria.chat_stream(user_input):
                print(chunk, end="", flush=True)
        except Exception as e:
            print(f"\n⚠️  Failed to reach Groq API: {e}", end="")
        print()


if __name__ == "__main__":
    main()