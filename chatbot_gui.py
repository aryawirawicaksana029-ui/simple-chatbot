"""
chatbot_gui.py
GUI version of ARIA chatbot using Tkinter.

Run with:
    python chatbot_gui.py
"""

import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime

from chatbot_core import AriaChatbot, PERSONAS
from voice_input import record_audio
import voice_output

# ---------- Colors & Fonts ----------
BG_COLOR = "#1e1f29"
CHAT_BG = "#282a36"
USER_COLOR = "#8be9fd"
ARIA_COLOR = "#50fa7b"
SYSTEM_COLOR = "#ffb86c"
TEXT_COLOR = "#f8f8f2"
ENTRY_BG = "#343746"
BTN_COLOR = "#6272a4"
BTN_HOVER = "#7284b8"

FONT_MAIN = ("Segoe UI", 11)
FONT_TITLE = ("Segoe UI", 14, "bold")


class AriaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 ARIA - AI Chatbot")
        self.root.geometry("650x650")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(500, 500)

        self.aria = AriaChatbot()
        self.is_waiting = False
        self.is_recording = False
        self.speak_enabled = False  # toggled via the 🔇/🔊 Speak button
        self.rag_enabled = False    # toggled via the RAG button

        self._build_ui()

    # ---------- UI Layout ----------
    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG_COLOR)
        header.pack(fill="x", padx=15, pady=(15, 5))

        title = tk.Label(
            header, text="🤖 ARIA - AI Chatbot",
            font=FONT_TITLE, bg=BG_COLOR, fg=TEXT_COLOR
        )
        title.pack(side="left")

        self.persona_var = tk.StringVar(value=self.aria.persona_name)
        persona_menu = ttk.Combobox(
            header, textvariable=self.persona_var,
            values=list(PERSONAS.keys()), state="readonly", width=10,
            font=FONT_MAIN
        )
        persona_menu.pack(side="left", padx=(12, 0))
        persona_menu.bind("<<ComboboxSelected>>", self.change_persona)

        clear_btn = tk.Button(
            header, text="Clear Chat", command=self.clear_chat,
            bg=BTN_COLOR, fg=TEXT_COLOR, font=FONT_MAIN,
            activebackground=BTN_HOVER, relief="flat", padx=10, pady=3,
            cursor="hand2"
        )
        clear_btn.pack(side="right")

        save_btn = tk.Button(
            header, text="💾 Save", command=self.save_chat,
            bg=BTN_COLOR, fg=TEXT_COLOR, font=FONT_MAIN,
            activebackground=BTN_HOVER, relief="flat", padx=10, pady=3,
            cursor="hand2"
        )
        save_btn.pack(side="right", padx=(0, 8))

        self.speak_btn = tk.Button(
            header, text="🔇 Speak", command=self.toggle_speak,
            bg=BTN_COLOR, fg=TEXT_COLOR, font=FONT_MAIN,
            activebackground=BTN_HOVER, relief="flat", padx=10, pady=3,
            cursor="hand2"
        )
        self.speak_btn.pack(side="right", padx=(0, 8))

        self.rag_btn = tk.Button(
            header, text="📚 RAG: Off", command=self.toggle_rag,
            bg=BTN_COLOR, fg=TEXT_COLOR, font=FONT_MAIN,
            activebackground=BTN_HOVER, relief="flat", padx=10, pady=3,
            cursor="hand2"
        )
        self.rag_btn.pack(side="right", padx=(0, 8))

        add_doc_btn = tk.Button(
            header, text="📎 Add Doc", command=self.add_document,
            bg=BTN_COLOR, fg=TEXT_COLOR, font=FONT_MAIN,
            activebackground=BTN_HOVER, relief="flat", padx=10, pady=3,
            cursor="hand2"
        )
        add_doc_btn.pack(side="right", padx=(0, 8))

        # Chat display area
        self.chat_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state="disabled",
            bg=CHAT_BG, fg=TEXT_COLOR, font=FONT_MAIN,
            relief="flat", padx=10, pady=10, borderwidth=0
        )
        self.chat_area.pack(fill="both", expand=True, padx=15, pady=10)

        # Tag styling for message roles
        self.chat_area.tag_config("user", foreground=USER_COLOR, font=(FONT_MAIN[0], 11, "bold"))
        self.chat_area.tag_config("aria", foreground=ARIA_COLOR, font=(FONT_MAIN[0], 11, "bold"))
        self.chat_area.tag_config("system", foreground=SYSTEM_COLOR, font=(FONT_MAIN[0], 10, "italic"))
        self.chat_area.tag_config("body", foreground=TEXT_COLOR)

        # Input area
        input_frame = tk.Frame(self.root, bg=BG_COLOR)
        input_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.mic_btn = tk.Button(
            input_frame, text="🎤", command=self.toggle_recording,
            bg=BTN_COLOR, fg=TEXT_COLOR, font=FONT_MAIN,
            activebackground=BTN_HOVER, relief="flat", padx=10, pady=6,
            cursor="hand2"
        )
        self.mic_btn.pack(side="left", padx=(0, 8))

        self.entry = tk.Entry(
            input_frame, font=FONT_MAIN, bg=ENTRY_BG, fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR, relief="flat"
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry.bind("<Return>", lambda event: self.send_message())
        self.entry.focus()

        self.send_btn = tk.Button(
            input_frame, text="Send", command=self.send_message,
            bg=BTN_COLOR, fg=TEXT_COLOR, font=FONT_MAIN,
            activebackground=BTN_HOVER, relief="flat", padx=15, pady=6,
            cursor="hand2"
        )
        self.send_btn.pack(side="right")

        self._append_system("Halo! Aku Aria 🤖. Ketik pesan lalu tekan Enter atau klik Send.")

    # ---------- Message rendering helpers ----------
    def _append_message(self, sender_label, sender_tag, message):
        self.chat_area.configure(state="normal")
        self.chat_area.insert(tk.END, f"{sender_label}: ", sender_tag)
        self.chat_area.insert(tk.END, f"{message}\n\n", "body")
        self.chat_area.configure(state="disabled")
        self.chat_area.see(tk.END)

    def _append_system(self, message):
        self.chat_area.configure(state="normal")
        self.chat_area.insert(tk.END, f"{message}\n\n", "system")
        self.chat_area.configure(state="disabled")
        self.chat_area.see(tk.END)

    # ---------- Actions ----------
    def send_message(self):
        if self.is_waiting:
            return

        user_text = self.entry.get().strip()
        if not user_text:
            return

        self.entry.delete(0, tk.END)
        self._append_message("You", "user", user_text)

        self.is_waiting = True
        self.send_btn.configure(state="disabled", text="...")
        self._append_system("Aria sedang mengetik...")

        # Run the API call in a background thread so the GUI doesn't freeze.
        # Chunks are streamed back to the main thread one by one via root.after,
        # since Tkinter widgets must only be touched from the main thread.
        threading.Thread(target=self._stream_response, args=(user_text,), daemon=True).start()

    def _stream_response(self, user_text):
        started = False
        full_reply = ""
        try:
            for chunk in self.aria.chat_stream(user_text):
                full_reply += chunk
                if not started:
                    self.root.after(0, self._start_aria_message)
                    started = True
                self.root.after(0, self._append_stream_chunk, chunk)
            self.root.after(0, self._finish_stream, None, full_reply)
        except Exception as e:
            self.root.after(0, self._finish_stream, str(e), full_reply)

    def _start_aria_message(self):
        """Called once, right when the first chunk of Aria's reply arrives."""
        self._remove_last_system_line()
        self.chat_area.configure(state="normal")
        self.chat_area.insert(tk.END, "Aria: ", "aria")
        self.chat_area.configure(state="disabled")

    def _append_stream_chunk(self, chunk):
        self.chat_area.configure(state="normal")
        self.chat_area.insert(tk.END, chunk, "body")
        self.chat_area.configure(state="disabled")
        self.chat_area.see(tk.END)

    def _finish_stream(self, error_msg, full_reply=""):
        # Safe to call even if the "mengetik..." line was already removed
        # (e.g. the request failed before any chunk arrived).
        self._remove_last_system_line()

        if error_msg:
            messagebox.showerror("Error", f"Gagal menghubungi Groq API:\n{error_msg}")
        else:
            self.chat_area.configure(state="normal")
            self.chat_area.insert(tk.END, "\n\n")
            self.chat_area.configure(state="disabled")
            self.chat_area.see(tk.END)

            if self.speak_enabled and full_reply.strip():
                # pyttsx3's runAndWait() blocks, so speak on a background
                # thread to keep the GUI responsive.
                threading.Thread(target=voice_output.speak, args=(full_reply,), daemon=True).start()

        self.is_waiting = False
        self.send_btn.configure(state="normal", text="Send")
        self.entry.focus()

    def _remove_last_system_line(self):
        """Removes the last 'Aria sedang mengetik...' placeholder line."""
        self.chat_area.configure(state="normal")
        content = self.chat_area.get("1.0", tk.END)
        marker = "Aria sedang mengetik...\n\n"
        idx = content.rfind(marker)
        if idx != -1:
            start = f"1.0+{idx}c"
            end = f"1.0+{idx + len(marker)}c"
            self.chat_area.delete(start, end)
        self.chat_area.configure(state="disabled")

    def toggle_speak(self):
        self.speak_enabled = not self.speak_enabled
        label = "🔊 Speak" if self.speak_enabled else "🔇 Speak"
        self.speak_btn.configure(text=label)

    def toggle_rag(self):
        self.rag_enabled = not self.rag_enabled
        if self.rag_enabled:
            self.aria.enable_rag()
        else:
            self.aria.disable_rag()
        label = "📚 RAG: On" if self.rag_enabled else "📚 RAG: Off"
        self.rag_btn.configure(text=label)
        self._append_system(f"📚 RAG (knowledge base) {'diaktifkan' if self.rag_enabled else 'dimatikan'}.")

    def add_document(self):
        filepath = filedialog.askopenfilename(
            title="Pilih dokumen untuk knowledge base",
            filetypes=[("Supported documents", "*.txt *.pdf *.docx"),
                       ("All files", "*.*")],
        )
        if not filepath:
            return  # user cancelled

        self._append_system(f"📚 Memproses dokumen: {filepath.split('/')[-1]} (bisa makan waktu beberapa detik)...")
        threading.Thread(target=self._add_document_thread, args=(filepath,), daemon=True).start()

    def _add_document_thread(self, filepath):
        try:
            result = self.aria.add_document_to_kb(filepath)
            self.root.after(0, self._on_document_added, filepath, result, None)
        except Exception as e:
            self.root.after(0, self._on_document_added, filepath, None, str(e))

    def _on_document_added(self, filepath, result, error):
        import os
        filename = os.path.basename(filepath)
        if error:
            messagebox.showerror("Error", f"Gagal memproses dokumen:\n{error}")
            return
        self._append_system(f"✅ '{filename}' ditambahkan ke knowledge base ({result['chunks']} chunks).")
        if result["flagged"] > 0:
            self._append_system(
                f"⚠️ {result['flagged']} bagian dari '{filename}' mengandung pola yang mirip prompt "
                f"injection. Aria tetap akan memperlakukannya sebagai referensi, bukan instruksi."
            )

    def toggle_recording(self):
        if self.is_waiting or self.is_recording:
            return  # ignore clicks while already busy

        self.is_recording = True
        self.mic_btn.configure(state="disabled", text="⏺")
        self._append_system("🎙️ Merekam suara selama 5 detik... silakan bicara!")

        threading.Thread(target=self._record_and_transcribe, daemon=True).start()

    def _record_and_transcribe(self):
        import os
        try:
            filepath = record_audio(duration=5.0)
            text = self.aria.transcribe_audio(filepath)
            os.remove(filepath)
            self.root.after(0, self._on_voice_transcribed, text, None)
        except Exception as e:
            self.root.after(0, self._on_voice_transcribed, None, str(e))

    def _on_voice_transcribed(self, text, error):
        self.is_recording = False
        self.mic_btn.configure(state="normal", text="🎤")

        if error:
            messagebox.showerror("Error", f"Gagal transkripsi suara:\n{error}")
            return

        if text and text.strip():
            self.entry.delete(0, tk.END)
            self.entry.insert(0, text.strip())
            self._append_system(f'🎙️ Transkrip: "{text.strip()}" — tekan Enter/Send untuk mengirim.')
        else:
            self._append_system("⚠️ Tidak ada suara yang terdengar, coba lagi.")

        self.entry.focus()

    def change_persona(self, event=None):
        selected = self.persona_var.get()
        self.aria.set_persona(selected)
        self._append_system(f"🎭 Persona diganti ke: {self.aria.persona_name}")

    def clear_chat(self):
        self.aria.clear_history()
        self.chat_area.configure(state="normal")
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.configure(state="disabled")
        self._append_system("✅ Riwayat percakapan sudah dihapus!")

    def save_chat(self):
        if not self.aria.has_messages():
            messagebox.showinfo("Save Chat", "Belum ada percakapan untuk disimpan.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = filedialog.asksaveasfilename(
            title="Simpan percakapan",
            initialfile=f"aria_chat_{timestamp}.txt",
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("JSON file", "*.json")],
        )

        if not filepath:
            return  # user cancelled the dialog

        fmt = "json" if filepath.lower().endswith(".json") else "txt"

        try:
            self.aria.save_to_file(filepath, fmt=fmt)
            self._append_system(f"💾 Percakapan disimpan ke: {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan file:\n{e}")


def main():
    root = tk.Tk()
    app = AriaGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()