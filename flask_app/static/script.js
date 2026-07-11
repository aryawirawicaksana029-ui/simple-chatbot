const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = chatForm.querySelector(".send-btn");
const clearBtn = document.getElementById("clear-btn");
const saveBtn = document.getElementById("save-btn");
const personaSelect = document.getElementById("persona-select");
const micBtn = document.getElementById("mic-btn");
const speakToggleBtn = document.getElementById("speak-toggle-btn");
const uploadDocBtn = document.getElementById("upload-doc-btn");
const docFileInput = document.getElementById("doc-file-input");
const ragToggleBtn = document.getElementById("rag-toggle-btn");

const STREAM_ERROR_PREFIX = "__ARIA_STREAM_ERROR__:";

// ---------- Voice output (browser speechSynthesis) ----------
let speakEnabled = false;

speakToggleBtn.addEventListener("click", () => {
  speakEnabled = !speakEnabled;
  speakToggleBtn.textContent = speakEnabled ? "🔊 speak" : "🔇 speak";
  if (!speakEnabled) {
    window.speechSynthesis.cancel(); // stop mid-sentence if turned off
  }
});

function speakText(text) {
  if (!speakEnabled || !text.trim()) return;
  window.speechSynthesis.cancel(); // avoid overlapping utterances
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "id-ID"; // falls back to a default voice if unavailable
  window.speechSynthesis.speak(utterance);
}

// ---------- Voice input (MediaRecorder -> /transcribe) ----------
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      await sendAudioForTranscription(audioBlob);
    };

    mediaRecorder.start();
    isRecording = true;
    micBtn.textContent = "⏺";
    micBtn.classList.add("recording");
  } catch (err) {
    appendMessage("error", "Tidak bisa mengakses mikrofon. Pastikan izin mikrofon diaktifkan di browser.");
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    micBtn.textContent = "🎤";
    micBtn.classList.remove("recording");
  }
}

async function sendAudioForTranscription(audioBlob) {
  micBtn.disabled = true;
  appendMessage("system", "🎙️ Mentranskripsi suara...");

  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");

  try {
    const res = await fetch("/transcribe", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      appendMessage("error", data.error || "Gagal mentranskripsi suara.");
      return;
    }

    chatInput.value = (data.text || "").trim();
    chatInput.focus();
  } catch (err) {
    appendMessage("error", "Gagal menghubungi server untuk transkripsi.");
  } finally {
    micBtn.disabled = false;
  }
}

micBtn.addEventListener("click", () => {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

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
      speakText(fullText);
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

// ---------- RAG (knowledge base) ----------
let ragEnabled = false;

ragToggleBtn.addEventListener("click", async () => {
  ragEnabled = !ragEnabled;
  try {
    const res = await fetch("/rag/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: ragEnabled }),
    });
    const data = await res.json();
    ragEnabled = data.rag_enabled;
  } catch (err) {
    appendMessage("error", "Gagal menghubungi server untuk toggle RAG.");
    ragEnabled = !ragEnabled; // revert on failure
  }
  ragToggleBtn.textContent = ragEnabled ? "📚 rag: on" : "📚 rag";
  appendMessage("system", `📚 Knowledge base ${ragEnabled ? "diaktifkan" : "dimatikan"}.`);
});

uploadDocBtn.addEventListener("click", () => docFileInput.click());

docFileInput.addEventListener("change", async () => {
  const file = docFileInput.files[0];
  docFileInput.value = ""; // reset so selecting the same file again still fires 'change'
  if (!file) return;

  appendMessage("system", `📚 Memproses "${file.name}"... (bisa makan waktu beberapa detik)`);

  const formData = new FormData();
  formData.append("document", file);

  try {
    const res = await fetch("/rag/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      appendMessage("error", data.error || "Gagal memproses dokumen.");
      return;
    }

    appendMessage("system", `✅ "${data.filename}" ditambahkan ke knowledge base (${data.chunks} chunks).`);
  } catch (err) {
    appendMessage("error", "Gagal mengunggah dokumen ke server.");
  }
});