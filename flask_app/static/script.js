const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = chatForm.querySelector(".send-btn");
const clearBtn = document.getElementById("clear-btn");
const saveBtn = document.getElementById("save-btn");
const personaSelect = document.getElementById("persona-select");

const STREAM_ERROR_PREFIX = "__ARIA_STREAM_ERROR__:";

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
  return p;
}

// Creates an empty Aria bubble with a blinking cursor, to be filled in
// as streamed chunks arrive.
function createAriaStreamBubble() {
  const p = appendMessage("aria", "");
  const cursor = document.createElement("span");
  cursor.className = "stream-cursor";
  cursor.textContent = "▍";
  p.appendChild(cursor);
  return p;
}

function updateAriaStreamBubble(p, text) {
  p.textContent = text;
  const cursor = document.createElement("span");
  cursor.className = "stream-cursor";
  cursor.textContent = "▍";
  p.appendChild(cursor);
  scrollToBottom();
}

function finalizeAriaStreamBubble(p, text) {
  p.textContent = text;
  scrollToBottom();
}

function scrollToBottom() {
  chatLog.scrollTop = chatLog.scrollHeight;
}

function setLoading(isLoading) {
  sendBtn.disabled = isLoading;
  chatInput.disabled = isLoading;
}

async function sendMessage(message) {
  setLoading(true);

  const bubble = createAriaStreamBubble();
  let fullText = "";
  let sawError = false;

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) {
      const data = await res.json();
      bubble.closest(".msg").remove();
      appendMessage("error", data.error || "Terjadi kesalahan tak terduga.");
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      fullText += decoder.decode(value, { stream: true });

      if (fullText.includes(STREAM_ERROR_PREFIX)) {
        sawError = true;
        continue; // keep draining the stream, but stop rendering it as a reply
      }

      updateAriaStreamBubble(bubble, fullText);
    }

    if (sawError) {
      bubble.closest(".msg").remove();
      appendMessage("error", fullText.replace(STREAM_ERROR_PREFIX, ""));
    } else {
      finalizeAriaStreamBubble(bubble, fullText);
    }
  } catch (err) {
    bubble.closest(".msg").remove();
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

saveBtn.addEventListener("click", async () => {
  try {
    const res = await fetch("/download");
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      appendMessage("error", data.error || "Belum ada percakapan untuk disimpan.");
      return;
    }

    // Turn the response into a downloadable file in the browser.
    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : "aria_chat.txt";

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    appendMessage("system", `💾 Percakapan disimpan sebagai ${filename}`);
  } catch (err) {
    appendMessage("error", "Gagal mengunduh percakapan. Cek koneksi/server Flask kamu.");
  }
});

chatInput.focus();

personaSelect.addEventListener("change", async () => {
  const persona = personaSelect.value;
  try {
    const res = await fetch("/persona", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ persona }),
    });
    const data = await res.json();
    if (!res.ok) {
      appendMessage("error", data.error || "Gagal mengganti persona.");
      return;
    }
    appendMessage("system", `🎭 Persona diganti ke: ${data.current}`);
  } catch (err) {
    appendMessage("error", "Gagal menghubungi server untuk ganti persona.");
  }
});