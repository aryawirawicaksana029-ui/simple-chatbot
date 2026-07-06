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
        try:
            for chunk in aria.chat_stream(user_input):
                print(chunk, end="", flush=True)
        except Exception as e:
            print(f"\n⚠️  Failed to reach Groq API: {e}", end="")
        print()


if __name__ == "__main__":
    main()