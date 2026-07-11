# 🤖 ARIA - AI Chatbot

An AI Chatbot powered by **Groq API** and **LLaMA 3.3 70B** model. Fast, intelligent, and supports multi-turn conversations with memory.

Now available in three versions:
- 🖥️ **Terminal (CLI)** version
- 🪟 **GUI** version (Tkinter)
- 🌐 **Web App** version (Flask)

---

## 📸 Preview on GIFT

<img width="800" height="450" alt="ezgif com-video-to-gif-converter" src="https://github.com/user-attachments/assets/59abb093-5404-43e1-9b59-ddcb969bdd4d" />

## 🚀 Features

- ✅ Powered by LLaMA 3.3 70B via Groq API (ultra-fast inference)
- ✅ Multi-turn conversation with memory (remembers context)
- ✅ **Streaming responses** — Aria's reply appears word by word in real time, ChatGPT-style, across all three interfaces
- ✅ **Save conversation history to file** — export as a readable `.txt` transcript or structured `.json`, from every interface
- ✅ **Custom AI personality/persona** — switch Aria's tone between `default`, `formal`, `santai`, `sarcastic`, or `mentor` (or set your own custom prompt), on the fly
- ✅ **Voice input** — speak to Aria instead of typing; audio is transcribed via Groq's Whisper (`whisper-large-v3`), across all three interfaces
- ✅ **Voice output** — Aria can read her replies aloud: browser `speechSynthesis` on the Web App, offline `pyttsx3` on CLI/GUI
- ✅ **RAG (Retrieval Augmented Generation)** — upload `.txt`/`.pdf`/`.docx` documents to a shared knowledge base (ChromaDB + local `sentence-transformers` embeddings); toggle it on to have Aria answer using your documents as context
- ✅ Supports any language including Bahasa Indonesia
- ✅ Clear conversation history (`clear` command / "Clear Chat" button)
- ✅ Clean terminal interface, a desktop GUI (Tkinter), **and** a browser-based Web App (Flask)
- ✅ Non-blocking GUI — API calls run in a background thread
- ✅ Web App runs per-browser sessions, so multiple users can chat with Aria independently
- ✅ API key secured via config file (not exposed on GitHub)

---

## 📸 Preview (CLI)

```
=============================================
  🤖 ARIA - AI Chatbot powered by Groq
=============================================
  Type 'quit' or 'exit' to stop
  Type 'clear' to clear history
=============================================
You: Hello! Who are you?
Aria: Hi there! I'm Aria, your AI assistant powered by Groq!
      How can I help you today?
You: Can you speak Bahasa Indonesia?
Aria: Tentu saja! Aku bisa berbahasa Indonesia.
      Ada yang bisa aku bantu?
You: clear
✅ Conversation history cleared!
You: exit
Aria: Goodbye! Have a great day! 👋
```

## 🖼️ Preview (GUI)

A dark-themed Tkinter chat window with:
- Scrollable chat log with color-coded messages (You / Aria / system)
- Text entry + Send button (or press Enter)
- "Clear Chat" button
- Aria's reply **streams in word by word** as it's generated, instead of appearing all at once

## 🌐 Preview (Web App)

A browser-based chat page styled like a terminal window:
- Terminal-style titlebar with an "online" status indicator
- Color-coded chat bubbles (You / Aria / system / error)
- Aria's reply **streams in live**, with a blinking cursor (▍) while it's still typing
- "clear" button to reset the conversation
- Fully responsive — works on desktop and mobile browsers

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.x |
| AI Model | LLaMA 3.3 70B (via Groq) |
| API | Groq API (free tier), streaming responses |
| Libraries | `groq`, `tkinter` (built-in), `flask` |
| Frontend (Web) | HTML, CSS, vanilla JavaScript (fetch API + ReadableStream) |
| Interface | Terminal (CLI), Desktop GUI (Tkinter), Web App (Flask) |

---

## ⚙️ How to Use

**1. Clone this repository:**
```bash
git clone https://github.com/aryawirawicaksana029-ui/simple-chatbot.git
cd simple-chatbot
```

**2. Install dependencies:**

For the CLI / GUI versions (run from the project root):
```bash
pip install -r requirements.txt
```
> Tkinter comes bundled with most Python installations. On some Linux distros you may need `sudo apt install python3-tk`.
> `sounddevice` needs a working system audio backend (PortAudio) — it's bundled on Windows/macOS; on Linux you may need `sudo apt install libportaudio2`.
> `sentence-transformers` downloads its embedding model (~80MB) the first time it runs, then caches it locally — the first document you add or first RAG-enabled message may take a bit longer.

For the Web App version (run from inside `flask_app/`):
```bash
cd flask_app
pip install -r requirements.txt
```

**3. Setup API Key:**
- Register for free at [Groq Console](https://console.groq.com)
- Get your API key from **API Keys** section
- Create a `config.py` file:
  - in the **project root** (used by `chatbot.py` and `chatbot_gui.py`)
  - **and** inside `flask_app/` (used by the Web App — it needs its own copy since it imports its own local `chatbot_core.py`)
```python
# config.py
GROQ_API_KEY = "your_api_key_here"
```
⚠️ **Never commit this file or share your key.** If a key is ever exposed (e.g. pasted in chat, committed by accident), revoke it immediately in the Groq Console and generate a new one.

**4. Run the chatbot:**

Terminal version:
```bash
python chatbot.py
```

GUI version:
```bash
python chatbot_gui.py
```

Web App version:
```bash
cd flask_app
python app.py
```
Then open **http://127.0.0.1:5000** in your browser.

---

## 💬 Commands (CLI)

| Command | Description |
|---------|-------------|
| Any text | Send message to Aria |
| `clear` | Clear conversation history |
| `save` / `save json` | Save conversation to `chat_history/` as `.txt` or `.json` |
| `persona` | List available personas |
| `persona <name>` | Switch persona (`default`, `formal`, `santai`, `sarcastic`, `mentor`, or any custom text) |
| `voice` | Record 5 seconds of audio and transcribe it as your message |
| `speak on` / `speak off` | Toggle Aria reading her replies aloud (offline, via pyttsx3) |
| `rag add <filepath>` | Add a `.txt`/`.pdf`/`.docx` file to Aria's knowledge base |
| `rag on` / `rag off` | Toggle whether Aria uses the knowledge base to answer |
| `rag list` | List documents currently in the knowledge base |
| `rag clear` | Wipe the entire knowledge base |
| `quit` / `exit` | Exit the chatbot |

## 🖱️ Controls (GUI)

| Action | Description |
|--------|-------------|
| Enter / Send button | Send message to Aria |
| Persona dropdown | Switch Aria's personality on the fly |
| 💾 Save button | Save conversation as `.txt` or `.json` via a file dialog |
| 🎤 Mic button | Record 5 seconds of audio, transcribe it into the entry box (review before sending) |
| 🔇/🔊 Speak button | Toggle Aria reading her replies aloud (offline, via pyttsx3) |
| 📎 Add Doc button | Upload a `.txt`/`.pdf`/`.docx` file to the knowledge base via a file dialog |
| 📚 RAG button | Toggle whether Aria uses the knowledge base to answer |
| Clear Chat button | Clear conversation history and chat log |

## 🌐 Controls (Web App)

| Action | Description |
|--------|-------------|
| Enter / Send button | Send message to Aria |
| Persona dropdown | Switch Aria's personality for your session |
| 💾 save button | Download the conversation as a `.txt` file |
| 🎤 mic button | Record a voice message; it's transcribed server-side via Groq Whisper and dropped into the input box |
| 🔇/🔊 speak button | Toggle Aria reading her replies aloud, using the browser's built-in speechSynthesis |
| 📎 upload button | Upload a `.txt`/`.pdf`/`.docx` file to the shared knowledge base |
| 📚 rag button | Toggle whether Aria uses the knowledge base for your session |
| clear button | Clear conversation history for your browser session |

---

## 🧠 How It Works

```
User Input
    ↓
Add to Conversation History
    ↓
Send to Groq API (LLaMA 3.3 70B, stream=True)
    ↓
Receive response as a stream of chunks
    ↓
Display each chunk to the user as it arrives (word by word)
    ↓
Once the stream ends, save the full reply to History
```

The core chat logic lives in `chatbot_core.py` and is shared by the CLI and GUI apps (project root). The Web App has its own copy of `chatbot_core.py` inside `flask_app/`, since it runs as a separate Flask project. All three interfaces call `chat_stream()`, which yields Aria's reply piece by piece instead of waiting for the full response:

- **CLI** prints each chunk to the terminal as it arrives.
- **GUI** streams chunks from a background thread into the Tkinter text widget via `root.after()`, so the window never freezes and text appears to "type itself."
- **Web App** streams the reply over a chunked HTTP response; the frontend reads it with `ReadableStream` and fills in the chat bubble live, with a blinking cursor while Aria is still "typing." Each browser also gets its own session (via a session cookie), so multiple people can chat with Aria at the same time without mixing up each other's conversation history.

**Voice input** works the same way conceptually across all three: record audio → send it to Groq's Whisper model (`whisper-large-v3`) via `transcribe_audio()` → get text back → treat it exactly like a typed message. The CLI/GUI record from the system mic with `sounddevice`; the Web App records in the browser with the `MediaRecorder` API and POSTs the audio blob to a `/transcribe` endpoint.

**Voice output** deliberately uses two different engines depending on environment: the Web App speaks replies with the browser's built-in `speechSynthesis` (free, client-side, zero extra dependencies), while the CLI and GUI — which have no browser — use `pyttsx3`, an offline Python TTS engine, so neither needs an API call or an internet connection to talk back.

**RAG** works like this: uploaded documents (`.txt`/`.pdf`/`.docx`) are split into ~500-character chunks, each chunk is turned into a vector with a local `sentence-transformers` model (`all-MiniLM-L6-v2` — Groq doesn't host embedding models, only chat/Whisper/TTS), and stored in a persistent ChromaDB collection. When RAG is toggled on, every user message is first embedded and matched against that collection; the top 3 most relevant chunks are injected as extra context in the system prompt before the request goes to Groq. The knowledge base is intentionally **shared and persistent across the whole app** — unlike conversation history, which is per-session — since it represents documents Aria "knows about" globally, not something tied to one particular chat.

---

## 📁 Project Structure

```
simple-chatbot/
│
├── chatbot_core.py     # Shared core logic (Groq client, history, chat(), transcribe_audio())
├── chatbot.py          # Terminal (CLI) version
├── chatbot_gui.py      # GUI version (Tkinter)
├── voice_input.py      # Mic recording helper (CLI/GUI only, uses sounddevice)
├── voice_output.py     # Offline text-to-speech helper (CLI/GUI only, uses pyttsx3)
├── rag_utils.py         # RAG knowledge base (ChromaDB + sentence-transformers)
├── requirements.txt    # groq, sounddevice, scipy, pyttsx3, chromadb, sentence-transformers, pypdf, python-docx
├── flask_app/          # Web App version (Flask)
│   ├── app.py           # Flask routes (/, /chat, /clear, /persona, /download, /transcribe, /rag/*)
│   ├── chatbot_core.py   # Local copy of the core logic
│   ├── rag_utils.py      # Local copy of the RAG knowledge base logic
│   ├── requirements.txt  # flask, groq, chromadb, sentence-transformers, pypdf, python-docx
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── style.css
│       └── script.js       # includes MediaRecorder (voice input) + speechSynthesis (voice output) + RAG upload/toggle
├── knowledge_base/      # ChromaDB persisted data (auto-created, git-ignored)
├── .gitignore          # Excludes config.py, __pycache__, knowledge_base/, chat_history/
└── README.md            # Project documentation
# Not uploaded to GitHub:
├── config.py           # Groq API key for CLI/GUI (keep secret!)
└── flask_app/config.py # Groq API key for the Web App (keep secret!)
```

---

## 🔒 Security Note

Both `config.py` files (project root and `flask_app/`) contain your API key and are excluded from GitHub via `.gitignore`. Never share or commit your API key publicly — and if it's ever exposed, revoke it right away in the Groq Console.

---

## 👨‍💻 Author

**Arya Wira Wicaksana**
🐍 Python Developer | AI Enthusiast
📧 aryawirawicaksana029@gmail.com
🔗 [GitHub](https://github.com/aryawirawicaksana029-ui)

---

## 🔮 Future Plans

- [x] GUI version with Tkinter
- [x] Web App version with Flask
- [x] Streaming response (word by word like ChatGPT)
- [x] Save conversation history to file
- [x] Custom AI personality/persona
- [x] Voice input and output
- [x] RAG (Retrieval Augmented Generation) support