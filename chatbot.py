"""
chatbot.py
Terminal (CLI) version of ARIA chatbot.
"""

import os
from datetime import datetime

from chatbot_core import AriaChatbot, PERSONAS
from voice_input import record_audio
import voice_output

aria = AriaChatbot()
speak_enabled = False  # toggled with 'speak on' / 'speak off'

HISTORY_DIR = "chat_history"


def save_history_to_file(fmt: str = "txt") -> str:
    """Save the current conversation to chat_history/aria_chat_<timestamp>.<ext>"""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"aria_chat_{timestamp}.{fmt}"
    filepath = os.path.join(HISTORY_DIR, filename)
    return aria.save_to_file(filepath, fmt=fmt)


def handle_message(user_text: str):
    """
    Send `user_text` to Aria, stream the reply to the terminal as it
    arrives, and optionally read it out loud afterwards if voice output
    is enabled. Shared by both typed input and voice-transcribed input.
    """
    print("\nAria: ", end="", flush=True)
    full_reply = ""
    try:
        for chunk in aria.chat_stream(user_text):
            print(chunk, end="", flush=True)
            full_reply += chunk
    except Exception as e:
        print(f"\n⚠️  Failed to reach Groq API: {e}", end="")
    print()

    citations = aria.get_rag_citations()
    if citations:
        parts = [f"{c['source']} ({c['chunks_used']} bagian)" for c in citations]
        print(f"📚 Sumber: {', '.join(parts)}")

    tool_calls = aria.get_tool_usage()
    if tool_calls:
        for tc in tool_calls:
            args_str = ", ".join(f"{k}={v!r}" for k, v in tc["arguments"].items())
            result_preview = tc["result"] if len(tc["result"]) <= 100 else tc["result"][:100] + "..."
            print(f"🛠️  {tc['name']}({args_str}) → {result_preview}")

    if speak_enabled and full_reply.strip():
        voice_output.speak(full_reply)


def main():
    global speak_enabled

    print("=" * 45)
    print("  🤖 ARIA - AI Chatbot powered by Groq")
    print("=" * 45)
    print("  Type 'quit' or 'exit' to stop")
    print("  Type 'clear' to clear history")
    print("  Type 'save' to save conversation to a .txt file")
    print("  Type 'save json' to save conversation to a .json file")
    print(f"  Type 'persona' to list personas, 'persona <name>' to switch (current: {aria.persona_name})")
    print("  Type 'voice' to record a spoken message instead of typing")
    print("  Type 'speak on' / 'speak off' to toggle Aria reading replies aloud")
    print("  Type 'rag add <filepath>' to add a .txt/.pdf/.docx file to Aria's knowledge base")
    print("  Type 'rag on' / 'rag off' to toggle whether Aria uses the knowledge base")
    print("  Type 'rag list' to see loaded documents, 'rag clear' to wipe the knowledge base")
    print("  Type 'tools on' / 'tools off' to toggle calculator + web search tools (on by default)")
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

        if user_input.lower() == "persona":
            print(f"\n🎭 Persona aktif: {aria.persona_name}")
            print("Pilihan tersedia:", ", ".join(PERSONAS.keys()))
            continue

        if user_input.lower().startswith("persona "):
            new_persona = user_input[len("persona "):].strip()
            aria.set_persona(new_persona)
            print(f"\n🎭 Persona diganti ke: {aria.persona_name}")
            continue

        if user_input.lower() in ["speak on", "speak off"]:
            speak_enabled = user_input.lower() == "speak on"
            status = "🔊 ON" if speak_enabled else "🔇 OFF"
            print(f"\n🗣️  Text-to-speech: {status}")
            continue

        if user_input.lower() in ["rag on", "rag off"]:
            if user_input.lower() == "rag on":
                aria.enable_rag()
            else:
                aria.disable_rag()
            status = "🔊 ON" if aria.rag_enabled else "🔇 OFF"
            print(f"\n📚 RAG (knowledge base): {status}")
            continue

        if user_input.lower() == "rag list":
            docs = aria.list_kb_documents()
            if docs:
                print(f"\n📚 Dokumen di knowledge base ({len(docs)}):")
                for doc in docs:
                    print(f"   - {doc}")
            else:
                print("\n📚 Knowledge base masih kosong.")
            continue

        if user_input.lower() == "rag clear":
            aria.clear_kb()
            print("\n🗑️  Knowledge base sudah dikosongkan.")
            continue

        if user_input.lower().startswith("rag add "):
            filepath = user_input[len("rag add "):].strip().strip('"')
            if not os.path.isfile(filepath):
                print(f"\n⚠️  File tidak ditemukan: {filepath}")
                continue
            try:
                print("\n📚 Memproses dokumen (embedding bisa makan waktu beberapa detik)...")
                result = aria.add_document_to_kb(filepath)
                print(f"✅ Ditambahkan: {os.path.basename(filepath)} ({result['chunks']} chunks)")
                if result["flagged"] > 0:
                    print(f"⚠️  {result['flagged']} bagian dari dokumen ini mengandung pola yang mirip "
                          f"prompt injection. Aria tetap akan memperlakukannya sebagai referensi, bukan instruksi.")
            except Exception as e:
                print(f"\n⚠️  Gagal memproses dokumen: {e}")
            continue

        if user_input.lower() in ["tools on", "tools off"]:
            if user_input.lower() == "tools on":
                aria.enable_tools()
            else:
                aria.disable_tools()
            status = "🔊 ON" if aria.tools_enabled else "🔇 OFF"
            print(f"\n🛠️  Tools (calculator + web search): {status}")
            continue

        if user_input.lower() == "voice":
            filepath = record_audio(duration=5.0)
            try:
                transcribed = aria.transcribe_audio(filepath)
            except Exception as e:
                print(f"\n⚠️  Gagal transkripsi suara: {e}")
                os.remove(filepath)
                continue
            os.remove(filepath)

            if not transcribed.strip():
                print("\n⚠️  Tidak ada suara yang terdengar, coba lagi.")
                continue

            print(f'\n📝 Kamu bilang: "{transcribed.strip()}"')
            handle_message(transcribed)
            continue

        handle_message(user_input)


if __name__ == "__main__":
    main()