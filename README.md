# 🤖 ARIA - AI Chatbot

A terminal-based AI Chatbot powered by **Groq API** and **LLaMA 3.3 70B** model. Fast, intelligent, and supports multi-turn conversations with memory.

---

## 🚀 Features

- ✅ Powered by LLaMA 3.3 70B via Groq API (ultra-fast inference)
- ✅ Multi-turn conversation with memory (remembers context)
- ✅ Supports any language including Bahasa Indonesia
- ✅ Clear conversation history with `clear` command
- ✅ Clean terminal interface
- ✅ API key secured via config file (not exposed on GitHub)

---

## 📸 Preview

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

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.x |
| AI Model | LLaMA 3.3 70B (via Groq) |
| API | Groq API (free tier) |
| Libraries | `groq` |
| Interface | Terminal / Command Line |

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

**3. Setup API Key:**

- Register for free at [Groq Console](https://console.groq.com)
- Get your API key from **API Keys** section
- Create a `config.py` file in the project folder:

```python
# config.py
GROQ_API_KEY = "your_api_key_here"
```

**4. Run the chatbot:**
```bash
python chatbot.py
```

---

## 💬 Commands

| Command | Description |
|---------|-------------|
| Any text | Send message to Aria |
| `clear` | Clear conversation history |
| `quit` / `exit` | Exit the chatbot |

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
Display to User
```

The chatbot maintains conversation history so Aria remembers what was said earlier in the session, enabling natural multi-turn conversations!

---

## 📁 Project Structure

```
simple-chatbot/
│
├── chatbot.py      # Main chatbot program
├── .gitignore      # Excludes config.py and __pycache__
└── README.md       # Project documentation

# Not uploaded to GitHub:
└── config.py       # Groq API key (keep secret!)
```

---

## 🔒 Security Note

The `config.py` file containing your API key is excluded from GitHub via `.gitignore`. Never share or commit your API key publicly!

---

## 👨‍💻 Author

**Arya Wira Wicaksana**
🐍 Python Developer | AI Enthusiast
📧 aryawirawicaksana029@gmail.com
🔗 [GitHub](https://github.com/aryawirawicaksana029-ui)

---

## 🔮 Future Plans

- [ ] GUI version with Tkinter
- [ ] Web App version with Flask
- [ ] Streaming response (word by word like ChatGPT)
- [ ] Save conversation history to file
- [ ] Custom AI personality/persona
- [ ] Voice input and output
- [ ] RAG (Retrieval Augmented Generation) support
