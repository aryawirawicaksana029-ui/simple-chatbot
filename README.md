# 🤖 ARIA - AI Chatbot

An AI Chatbot powered by **Groq API** and **LLaMA 3.3 70B** model. Fast, intelligent, and supports multi-turn conversations with memory

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
- ✅ **RAG (Retrieval Augmented Generation)** — upload `.txt`/`.pdf`/`.docx` documents to a shared knowledge base (ChromaDB + local `sentence-transformers` embeddings); toggle it on to have Aria answer using your documents as context, with citations showing exactly which document(s) an answer drew from
- ✅ **Tool calling (calculator + web search)** — Aria can call a safe calculator and a free web search tool mid-conversation when a question calls for it, and shows exactly which tool ran and with what arguments
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
- Aria's reply **streams in live**, with a blinking cursor (▍) while it's still typing, then renders as formatted Markdown once complete — code blocks, lists, bold text, links, and headings all display properly instead of as raw `**`/`` ` ``/`-` syntax
- "clear" button to reset the conversation
- Fully responsive — works on desktop and mobile browsers

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.x |
| AI Model | LLaMA 3.3 70B (via Groq) |
| API | Groq API (free tier), streaming responses |
| Libraries | `groq`, `tkinter` (built-in), `flask`, `requests` (web search tool) |
| Frontend (Web) | HTML, CSS, vanilla JavaScript (fetch API + ReadableStream), `marked` (Markdown rendering), `DOMPurify` (HTML sanitization) |
| Interface | Terminal (CLI), Desktop GUI (Tkinter), Web App (Flask) |
| Containerization | Docker + Docker Compose (Web App only) |

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
| `voice` | Record a spoken message (stops automatically once you go quiet) and transcribe it |
| `speak on` / `speak off` | Toggle Aria reading her replies aloud (offline, via pyttsx3) |
| `rag add <filepath>` | Add a `.txt`/`.pdf`/`.docx` file to Aria's knowledge base |
| `rag on` / `rag off` | Toggle whether Aria uses the knowledge base to answer |
| `rag list` | List documents currently in the knowledge base |
| `rag clear` | Wipe the entire knowledge base |
| `tools on` / `tools off` | Toggle calculator + web search tool calling (on by default) |
| `quit` / `exit` | Exit the chatbot |

## 🖱️ Controls (GUI)

| Action | Description |
|--------|-------------|
| Enter / Send button | Send message to Aria |
| Persona dropdown | Switch Aria's personality on the fly |
| 💾 Save button | Save conversation as `.txt` or `.json` via a file dialog |
| 🎤 Mic button | Record a spoken message (stops automatically once you go quiet), transcribe it into the entry box (review before sending) |
| 🔇/🔊 Speak button | Toggle Aria reading her replies aloud (offline, via pyttsx3) |
| 📎 Add Doc button | Upload a `.txt`/`.pdf`/`.docx` file to the knowledge base via a file dialog |
| 📚 RAG button | Toggle whether Aria uses the knowledge base to answer |
| 🛠️ Tools button | Toggle calculator + web search tool calling (on by default) |
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
| 🛠️ tools button | Toggle calculator + web search tool calling for your session |
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

**Voice input** works the same way conceptually across all three: record audio → send it to Groq's Whisper model (`whisper-large-v3`) via `transcribe_audio()` → get text back → treat it exactly like a typed message. The CLI/GUI record from the system mic with `sounddevice`, using simple RMS-amplitude voice activity detection (`voice_input.py`) to start immediately and stop automatically once you've spoken and then gone quiet — rather than always recording for a fixed duration regardless of how long the message actually was. The Web App instead records in the browser with the `MediaRecorder` API (manual start/stop via the mic button) and POSTs the audio blob to a `/transcribe` endpoint.

**Voice output** deliberately uses two different engines depending on environment: the Web App speaks replies with the browser's built-in `speechSynthesis` (free, client-side, zero extra dependencies), while the CLI and GUI — which have no browser — use `pyttsx3`, an offline Python TTS engine, so neither needs an API call or an internet connection to talk back.

**RAG** works like this: uploaded documents (`.txt`/`.pdf`/`.docx`) are split into paragraphs, then sentences, then greedily packed into ~500-character chunks that never cut a sentence in half — a chunk boundary only falls between sentences, with the last sentence of each chunk carried into the next one so context isn't lost right at the cut. Each chunk is turned into a vector with a local `sentence-transformers` model (`all-MiniLM-L6-v2` — Groq doesn't host embedding models, only chat/Whisper/TTS), and stored in a persistent ChromaDB collection. Each chunk is also scanned with a heuristic regex for common prompt-injection phrasing (e.g. "ignore previous instructions", "you are now") and flagged accordingly — you're warned right after upload if anything suspicious was found, though this is a heuristic and not foolproof. When RAG is toggled on, every user message is first embedded and matched against that collection; the top 3 most relevant chunks are wrapped in `<untrusted_document_excerpts>` tags with an explicit system instruction that the content is reference data to consult, never commands to obey — even if a chunk contains text that looks like an instruction — before the request goes to Groq. Right alongside the reply, you'll also see which document(s) it drew from (e.g. "📚 Sumber: laporan.pdf (2 bagian)") — these citations come from the retrieval step itself (we already know exactly which chunks were fetched before the model even responds), not from asking the model to self-report, since a model can misremember or omit what it actually used. On the CLI and GUI, the knowledge base is one shared, persistent store — appropriate since those are single-user desktop apps. On the Web App, each browser session gets its **own** ChromaDB collection (named after that session's ID), so one person's uploaded documents are never visible to someone else's session — only the embedding *model* is shared process-wide (it's stateless, so reloading a fresh ~80MB copy per session would be pure waste); the *data* is fully isolated per session.

**Persistence (Web App)**: the Flask app keeps an in-memory `sessions` dict for speed (so most requests never touch disk), but `db_utils.py` mirrors every message, persona choice, and RAG toggle into a local SQLite database (`aria_chat.db`) as it happens. If the Flask process restarts — a crash, a gunicorn worker recycling, stopping and restarting `python app.py` locally — `get_chatbot()` notices the session is missing from memory and rebuilds it from SQLite instead of starting over. This is genuinely useful for local development and crash recovery, but it isn't a substitute for a real database in a multi-server production setup, and it won't survive a full container redeploy on hosting tiers with ephemeral disks (see Deployment section).

**Markdown rendering (Web App only)**: while Aria's reply is still streaming in, the chat bubble shows plain text with a blinking cursor — trying to render Markdown on a half-finished response is unreliable (an unclosed ` ``` ` code fence, for instance, looks broken until the rest of the text arrives). Once the stream finishes, the full text is run through [marked](https://github.com/markedjs/marked) to convert Markdown into HTML, then through [DOMPurify](https://github.com/cure53/DOMPurify) to strip anything unsafe before it's inserted into the page — the same defense-in-depth instinct as the RAG prompt-injection handling: don't trust text that ends up in the DOM, even if it's "just" the model's own reply, since it could echo something adversarial from an uploaded document. This is Web-App-only; the CLI and GUI aren't a natural fit for rendered Markdown (a terminal and a Tkinter text widget don't have an HTML renderer to hand off to), so they continue to show Aria's replies as plain text.

**Tool calling** gives Aria two abilities beyond plain chat: a `calculator` (safe arithmetic, evaluated via Python's `ast` module rather than `eval()` — no way for a crafted expression to run arbitrary code) and `web_search` (DuckDuckGo's free Instant Answer API, no API key needed, though it only reliably answers factual/definitional queries and often comes back empty for news or highly specific lookups). The flow is a **non-streamed decision round, then a streamed final answer**: Aria first asks Groq (without streaming) whether a tool is needed for this message; deciding needs the complete tool name and JSON arguments in one piece, which streaming would fragment across many chunks for little benefit here. If a tool is called, it runs locally, its result is added to the conversation, and only *then* does the final, tool-informed reply stream to the UI as usual. Tool calling only does one round per turn — no chained/recursive tool use — to keep the flow easy to follow. Like RAG's citations, which tool ran (and with what arguments) is shown directly in the UI rather than relying on the model to mention it, and it's on by default since both tools are safe/read-only; toggle it off if you'd rather avoid the extra round-trip latency it adds to every message.

---

## 📁 Project Structure

```
simple-chatbot/
│
├── Dockerfile                  # Web App image (built from project root — needs aria_core/ + flask_app/)
├── .dockerignore
├── docker-compose.yml          # local dev: build + run + persistent volumes in one command
├── .env.example                # copy to .env for docker-compose (GROQ_API_KEY, FLASK_SECRET_KEY, ENABLE_RAG)
├── aria_core/                 # Shared package — imported by ALL THREE interfaces, one copy of each file
│   ├── __init__.py             # explains how flask_app/ reaches this package (sys.path)
│   ├── chatbot_core.py         # Groq client, history, chat_stream(), RAG/tools orchestration
│   ├── rag_utils.py            # RAG knowledge base (ChromaDB + sentence-transformers)
│   └── tools_utils.py          # Tool calling: calculator + web search
├── chatbot.py                 # Terminal (CLI) version
├── chatbot_gui.py             # GUI version (Tkinter)
├── voice_input.py             # Mic recording helper (CLI/GUI only, uses sounddevice)
├── voice_output.py            # Offline text-to-speech helper (CLI/GUI only, uses pyttsx3)
├── tests/                     # Unit tests (unittest + unittest.mock, zero extra dependencies)
│   ├── test_rag_utils.py       # chunking, injection detection, KnowledgeBase isolation
│   ├── test_tools_utils.py     # calculator safety, web search (mocked network)
│   └── test_chatbot_core.py    # persona, history, RAG context injection, tool-call orchestration
├── requirements.txt           # groq, sounddevice, scipy, numpy, pyttsx3, chromadb, sentence-transformers, pypdf, python-docx
├── flask_app/                 # Web App version (Flask) — a separate project one directory down
│   ├── app.py                  # Flask routes; appends the project root to sys.path so it can `import aria_core`
│   ├── db_utils.py             # SQLite persistence for conversation history + session settings (Web-App-only, not shared)
│   ├── requirements.txt        # flask, groq, chromadb, sentence-transformers, pypdf, python-docx (full, for local dev)
│   ├── requirements-deploy.txt # flask, groq, gunicorn only — lean build for RAG-disabled cloud deployments
│   ├── Procfile                # gunicorn start command (used by platforms that read Procfiles)
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── style.css
│       └── script.js           # includes MediaRecorder (voice input) + speechSynthesis (voice output) + RAG upload/toggle
├── knowledge_base/            # ChromaDB persisted data (auto-created, git-ignored)
├── .gitignore                 # Excludes config.py, __pycache__, knowledge_base/, chat_history/, *.db
└── README.md                   # Project documentation
# Not uploaded to GitHub:
├── config.py                  # Groq API key for CLI/GUI (keep secret!)
└── flask_app/config.py        # Groq API key for the Web App (keep secret! — a separate key/file from the one above)
```

`aria_core/` used to be two hand-synced copies of the same three files (project root and `flask_app/`) — a real, recurring source of bugs, since any fix had to be applied twice and it was easy to forget one side. Now there's exactly one copy of each. The Web App reaches it by appending the project root to `sys.path` at the top of `app.py` (see the comment there); it's an *append*, not an *insert at index 0*, specifically so `flask_app/config.py` still takes priority over the root's `config.py` for that one directory — each interface keeps its own Groq API key.

---

## 🧪 Running Tests

`tests/` has 50 unit tests covering `aria_core`'s chat orchestration, RAG (chunking, prompt-injection detection, citations), and tool calling — using Python's built-in `unittest` and `unittest.mock`, so no extra dependency is needed just to run them.

```bash
python -m unittest discover -s tests -v
```

The tests mock out Groq, ChromaDB, and the embedding model, so they run in well under a second and need no API key, no network access, and no model download — what's under test is ARIA's own orchestration logic (does `chat_stream()` build the right messages? does a flagged RAG chunk add the security warning? does a malformed tool-call response get caught instead of crashing the reply?), not whether Groq or ChromaDB themselves work correctly.

---

## 🐳 Docker (Web App)

A `Dockerfile` and `docker-compose.yml` at the project root package the Web App for portable, consistent deployment on any Docker-capable host (a VPS, DigitalOcean, a bare-metal server, or a PaaS that accepts a Dockerfile instead of its own buildpack) — this is what "portable across providers" means here: skip the platform-specific quirks and card-verification friction described in the Deployment section below, and get the same container everywhere.

**Quick start with Docker Compose (recommended for local use):**
```bash
cp .env.example .env
# edit .env and fill in GROQ_API_KEY

docker compose up --build
```
Open `http://localhost:5000`. Compose also wires up two named volumes (`aria_knowledge_base`, `aria_data`) so the RAG knowledge base and SQLite chat history survive `docker compose down` / container restarts — this is the setup where the persistence work described earlier actually holds up across restarts, unlike the free tiers in the Deployment section below, whose disks get wiped on every redeploy.

**Plain Docker, without Compose:**
```bash
docker build -t aria-web .
docker run -p 5000:5000 -e GROQ_API_KEY=your_key_here aria-web
```

**Lean image (skip RAG's heavy dependencies)** — same tradeoff as `requirements-deploy.txt` in the Deployment section, now as a build arg:
```bash
docker build -t aria-web-lean --build-arg REQUIREMENTS_FILE=requirements-deploy.txt .
docker run -p 5000:5000 -e GROQ_API_KEY=your_key_here -e ENABLE_RAG=false aria-web-lean
```

**Notes:**
- The image is built from the **project root** (not from inside `flask_app/`), since it needs both `aria_core/` and `flask_app/` — the same reason `app.py` appends the project root to `sys.path` at runtime.
- `sentence-transformers` pulls in `torch`; the Dockerfile explicitly installs the CPU-only build (a few hundred MB) instead of letting pip resolve the default CUDA/GPU build (multiple GB) that this container has no use for.
- This is a single-stage build, not a multi-stage one — simpler to read and modify at the cost of a somewhat larger final image (build tools like `build-essential` stay in the image rather than being discarded after the `pip install` step). A multi-stage build would trim that, at the cost of being harder to follow; left as a possible future refinement rather than done now.
- CLI/GUI aren't containerized — they're desktop apps that want a real display and microphone, which doesn't map cleanly onto a container.

---

## ☁️ Deployment (Web App)

The Web App version (`flask_app/`) can be deployed to [Render](https://render.com) so it's reachable at a public URL, not just `localhost`.

**Note on RAG in production:** Render's free web service tier has 512MB of RAM. `sentence-transformers` pulls in `torch`, which alone can use several hundred MB just from being imported — regardless of whether RAG is actually used. To keep the deployed instance stable (and builds fast/cheap on credit-based platforms like Railway), RAG is switched off there via an environment variable (`ENABLE_RAG=false`), and the deploy build uses a separate lean `requirements-deploy.txt` that skips `chromadb`/`sentence-transformers`/`pypdf`/`python-docx` entirely — since `chatbot_core.py` never imports `rag_utils` when `ENABLE_RAG=false`, those packages genuinely aren't needed at runtime. Voice input/output, streaming chat, personas, and save/download all work exactly the same — only the RAG upload/toggle buttons are hidden. The RAG code itself is untouched and still fully usable when you run the project locally with the full `requirements.txt` (where `ENABLE_RAG` isn't set, so it defaults to on).

**Steps (Render):**

1. Push this repo to GitHub (already done ✅).
2. On [Render](https://render.com), create a **New → Web Service** and connect your GitHub repo.
3. Set these fields:
   - **Root Directory**: `flask_app`
   - **Build Command**: `pip install -r requirements-deploy.txt`
   - **Start Command**: `gunicorn app:app`
4. Add these **Environment Variables** in Render's dashboard (never commit these — that's what `config.py` + `.gitignore` are for locally):
   - `GROQ_API_KEY` — your Groq API key
   - `FLASK_SECRET_KEY` — any random string (used to sign session cookies)
   - `ENABLE_RAG` — set to `false` for the free tier; leave unset (or `true`) if you're on a paid tier with more RAM, and switch the build command back to `pip install -r requirements.txt`
5. Deploy. Render gives you a live HTTPS URL once the build finishes.

**Steps (Railway) — an alternative if Render's card verification doesn't go through:**

1. On [Railway](https://railway.app), sign up with GitHub (no card required for the free tier).
2. **New Project → Deploy from GitHub repo** → select this repo.
3. In **Settings**:
   - **Root Directory**: `flask_app`
   - **Custom Start Command**: `gunicorn app:app` (Railway's auto-detection doesn't always pick this up correctly for subfolder deployments, so set it explicitly)
   - Change the build step to install from `requirements-deploy.txt` instead of `requirements.txt` (check your builder's config options for a custom install command, e.g. `pip install -r requirements-deploy.txt`)
4. In **Variables**, add `GROQ_API_KEY`, `FLASK_SECRET_KEY`, and `ENABLE_RAG=false`.
5. Go to **Settings → Networking → Generate Domain** to get a public HTTPS URL (Railway doesn't do this automatically).
6. Railway's free tier runs on monthly credits rather than fixed hours — it pauses (not bills you) once the month's credit is used up, since no card is on file.

**Things to expect on the free tier:**
- The service spins down after a period of no traffic, and the next request triggers a cold start (roughly 30-60 seconds). Normal behavior, not a bug — mention it if you're demoing live.
- The container's disk is ephemeral: anything written to disk (temp audio files, temp document uploads) is deleted automatically after each request and wiped entirely on redeploy — this project's downloads (`/download`) generate the file on the fly rather than saving it server-side, so this doesn't cause any data loss. The SQLite chat history (`aria_chat.db`) is subject to the same redeploy wipe — it survives process restarts within a running container, but not a fresh redeploy, unless you attach a persistent disk.
- If you later want RAG enabled in production too, upgrade to a paid tier with more RAM, set `ENABLE_RAG=true`, and switch the build command back to the full `requirements.txt`.

---

## 🔒 Security Note

Both `config.py` files (project root and `flask_app/`) contain your API key and are excluded from GitHub via `.gitignore`. Never share or commit your API key publicly — and if it's ever exposed, revoke it right away in the Groq Console.

On a deployed instance, the API key instead comes from the `GROQ_API_KEY` environment variable set in your hosting provider's dashboard (see Deployment section above) — `chatbot_core.py` falls back to it automatically when `config.py` isn't present.

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
- [x] Harden RAG against prompt injection from uploaded documents
- [x] Persistent chat history with SQLite (survives process restarts)
- [x] Citations in RAG answers (show which document/chunk was used)
- [x] Markdown rendering in chat bubbles (code blocks, lists, etc.) — Web App only
- [x] Tool calling / function calling (e.g. web search, calculator)
- [x] Smarter RAG chunking (sentence/paragraph-aware, not fixed character count)
- [x] Per-user knowledge base isolation on the Web App (was shared across all sessions)
- [x] Refactor `chatbot_core.py` / `rag_utils.py` into a shared package instead of duplicated copies
- [x] Unit tests for core chat and RAG logic
- [x] Deployment guide so the Web App is reachable beyond localhost (Render)
- [x] Dockerize the project (for more portable/consistent deployment across providers)
- [x] Voice activity detection for voice input (instead of a fixed 5-second recording)
- [ ] "Regenerate response" button
- [ ] Migrate off `llama-3.3-70b-versatile` (Groq announced deprecation June 17, 2026) to a currently-supported model

---

## ⚠️ Known Limitations

Honest notes on where this project currently falls short of production-ready, for context on what the checklist above is addressing:

- **Prompt injection mitigation in RAG is heuristic, not foolproof**: uploaded document chunks are scanned for common injection phrasing (e.g. "ignore previous instructions") and flagged to the person uploading them, and all retrieved excerpts are wrapped in `<untrusted_document_excerpts>` tags with an explicit system instruction that the content is data, not commands. This meaningfully raises the bar, but a sufficiently creative rephrasing could still slip past the regex heuristics — defense in depth (flagging + framing), not a guarantee.
- **In-memory session cache, backed by SQLite**: the Flask app's `sessions` dict is still in-memory for speed, but every message, persona choice, and RAG toggle is also written to a local SQLite database (`db_utils.py`) and restored automatically the next time that session is accessed. This survives a Flask process crash/restart on the same machine. It does **not** survive a full container redeploy on free hosting tiers (Render/Railway typically wipe the disk on redeploy unless you attach a paid persistent volume) — for that, you'd need either a persistent disk add-on or an external managed database.
- **Per-session knowledge bases grow unbounded**: each Web App browser session gets its own ChromaDB collection now (fixing the old cross-session data leak), but nothing currently expires or cleans up old sessions' collections — over time, many one-off visitors each uploading documents would leave behind a lot of small, never-revisited collections on disk. Fine for a portfolio demo; a production version would want some kind of session expiry/cleanup job.
- **Test coverage is unit-level only, not end-to-end**: `tests/` covers `aria_core`'s own logic (chunking, injection detection, persona handling, RAG/tool orchestration) with Groq/ChromaDB/the embedding model mocked out — it doesn't cover the Flask routes, the GUI, or a real integration run against the actual Groq API. Good for catching regressions in ARIA's own code; it won't catch a Groq API contract change or a real network/auth issue.
- **VAD is amplitude-based, not ML-based**: CLI/GUI voice input now stops automatically based on a simple RMS-volume silence threshold rather than a fixed duration, but that means it can be thrown off by a noisy room (background noise never dips below the threshold, so it waits for `max_duration`) or a very quiet talker (speech never rises above the threshold, so it never "hears" them start). A proper ML-based VAD (e.g. Silero VAD) would be more robust, at the cost of another model dependency.
- **Tool calling adds latency and API usage**: since tools are on by default, every message pays for an extra non-streamed "decision" round-trip to Groq before the real answer streams — noticeable but usually small given Groq's speed. `web_search` is also limited to DuckDuckGo's free Instant Answer API, which only reliably covers factual/definitional queries; toggle tools off for pure chit-chat if you'd rather skip the extra round-trip, or if you're hitting Groq's rate limits.
- **`llama-3.3-70b-versatile` occasionally malforms a tool call**: instead of returning a proper structured tool request, it sometimes emits one as literal text (e.g. `<function=web_search {"query": "..."}></function>`), which Groq's API rejects with a 400 `tool_use_failed` error. `chat_stream()` catches this and falls back to answering that turn without tools rather than crashing the reply, but it does mean the tool silently didn't run for that message — if answers about current events seem to be using stale training knowledge instead of a fresh search, this is likely why.
