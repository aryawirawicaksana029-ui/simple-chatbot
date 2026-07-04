import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chatbot_core import AriaChatbot

aria = AriaChatbot()


def main():
    print("=" * 45)
    print("  🤖 ARIA - AI Chatbot powered by Groq")
    print("=" * 45)
    print("  Type 'quit' or 'exit' to stop")
    print("  Type 'clear' to clear history")
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

        print("\nAria: ", end="", flush=True)
        response = aria.chat(user_input)
        print(response)


if __name__ == "__main__":
    main()