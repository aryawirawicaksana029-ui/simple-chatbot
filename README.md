# 🤖 ARIA - AI Chatbot

An AI Chatbot powered by **Groq API** and **LLaMA 3.3 70B** model. Fast, intelligent, and supports multi-turn conversations with memory.

Now available in two versions:
- 🖥️ **Terminal (CLI)** version
- 🪟 **GUI** version (Tkinter)

---

## 🚀 Features

- ✅ Powered by LLaMA 3.3 70B via Groq API (ultra-fast inference)
- ✅ Multi-turn conversation with memory (remembers context)
- ✅ Supports any language including Bahasa Indonesia
- ✅ Clear conversation history (`clear` command / "Clear Chat" button)
- ✅ Clean terminal interface **and** a desktop GUI (Tkinter)
- ✅ Non-blocking GUI — API calls run in a background thread
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
- "Aria sedang mengetik..." indicator while waiting for a response

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.x |
| AI Model | LLaMA 3.3 70B (via Groq) |
| API | Groq API (free tier) |
| Libraries | `groq`, `tkinter` (built-in) |
| Interface | Terminal (CLI) & Desktop GUI (Tkinter) |

---

## ⚙️ How to Use

**1. Clone this repository:**
```bash
git clone https://github.com/aryawirawicaksana029-ui/simple-chatbot.git
cd simple-chatbot
```

**2. Install dependencies:**
```bash
pip install groq
```
> Tkinter comes bundled with most Python installations. On some Linux distros you may need `sudo apt install python3-tk`.

**3. Setup API Key:**
- Register for free at [Groq Console](https://console.groq.com)
- Get your API key from **API Keys** section
- Create a `config.py` file in the project folder:
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

---

## 💬 Commands (CLI)

| Command | Description |
|---------|-------------|
| Any text | Send message to Aria |
| `clear` | Clear conversation history |
| `quit` / `exit` | Exit the chatbot |

## 🖱️ Controls (GUI)

| Action | Description |
|--------|-------------|
| Enter / Send button | Send message to Aria |
| Clear Chat button | Clear conversation history and chat log |

---

## 🧠 How It Works

```
User Input
    ↓
Add to Conversation History
    ↓
Send to Groq API (LLaMA 3.3 70B)
    ↓
Receive AI Response
    ↓
Add Response to History
    ↓
Display to User (Terminal or GUI)
```

The core chat logic lives in `chatbot_core.py` and is shared by both the CLI and GUI apps, so conversation history and behavior stay consistent across both. In the GUI, the API call runs on a background thread so the window never freezes while waiting for a response.

---

## 📁 Project Structure

```
simple-chatbot/
│
├── chatbot_core.py   # Shared core logic (Groq client, history, chat())
├── chatbot.py         # Terminal (CLI) version
├── chatbot_gui.py     # GUI version (Tkinter)
├── .gitignore         # Excludes config.py and __pycache__
└── README.md          # Project documentation
# Not uploaded to GitHub:
└── config.py          # Groq API key (keep secret!)
```

---

## 🔒 Security Note

The `config.py` file containing your API key is excluded from GitHub via `.gitignore`. Never share or commit your API key publicly — and if it's ever exposed, revoke it right away in the Groq Console.

---

## 👨‍💻 Author

**Arya Wira Wicaksana**
🐍 Python Developer | AI Enthusiast
📧 aryawirawicaksana029@gmail.com
🔗 [GitHub](https://github.com/aryawirawicaksana029-ui)

---

## 🔮 Future Plans

- [x] GUI version with Tkinter
- [ ] Web App version with Flask
- [ ] Streaming response (word by word like ChatGPT)
- [ ] Save conversation history to file
- [ ] Custom AI personality/persona
- [ ] Voice input and output
- [ ] RAG (Retrieval Augmented Generation) support