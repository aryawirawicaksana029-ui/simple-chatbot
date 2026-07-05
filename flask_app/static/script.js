const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = chatForm.querySelector(".send-btn");
const typingIndicator = document.getElementById("typing-indicator");
const clearBtn = document.getElementById("clear-btn");

function appendMessage(role, text) {
  const msg = document.createElement("div");
  msg.className = `msg msg-${role}`;

  const label = document.createElement("span");
  label.className = "msg-label";
  label.textContent = role === "user" ? "you" : role === "aria" ? "aria" : role;

  const p = document.createElement("p");
  p.textContent = text;

  msg.appendChild(label);
  msg.appendChild(p);
  chatLog.appendChild(msg);
  scrollToBottom();
}

function scrollToBottom() {
  chatLog.scrollTop = chatLog.scrollHeight;
}

function setLoading(isLoading) {
  sendBtn.disabled = isLoading;
  chatInput.disabled = isLoading;
  typingIndicator.classList.toggle("hidden", !isLoading);
  if (isLoading) scrollToBottom();
}

async function sendMessage(message) {
  setLoading(true);
  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await res.json();

    if (!res.ok) {
      appendMessage("error", data.error || "Terjadi kesalahan tak terduga.");
      return;
    }

    appendMessage("aria", data.reply);
  } catch (err) {
    appendMessage("error", "Tidak bisa menghubungi server. Cek koneksi/server Flask kamu.");
  } finally {
    setLoading(false);
    chatInput.focus();
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;

  appendMessage("user", text);
  chatInput.value = "";
  sendMessage(text);
});

clearBtn.addEventListener("click", async () => {
  try {
    await fetch("/clear", { method: "POST" });
  } catch (err) {
    // Even if the server call fails, still clear the visible log locally.
  }
  chatLog.innerHTML = "";
  appendMessage("system", "✅ Riwayat percakapan sudah dihapus!");
  chatInput.focus();
});

chatInput.focus();
