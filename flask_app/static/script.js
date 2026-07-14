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
const toolsToggleBtn = document.getElementById("tools-toggle-btn");

const STREAM_ERROR_PREFIX = "__ARIA_STREAM_ERROR__:";
const STREAM_CITATIONS_PREFIX = "__ARIA_CITATIONS__:";
const STREAM_TOOLS_PREFIX = "__ARIA_TOOLS__:";

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

  // Aria's replies get rendered as Markdown (code blocks, lists, bold, etc.),
  // so the body needs to be a <div> — a <p> can't legally contain block-level
  // elements like <pre> or <ul>. Every other role stays plain text.
  const body = document.createElement(role === "aria" ? "div" : "p");
  body.className = "msg-body";
  body.textContent = text;

  msg.appendChild(label);
  msg.appendChild(body);
  chatLog.appendChild(msg);
  scrollToBottom();
  return body;
}

// Creates an empty Aria bubble with a blinking cursor, to be filled in as
// streamed chunks arrive as PLAIN TEXT — rendering Markdown mid-stream is
// unreliable (e.g. an unclosed ``` code fence looks broken until the rest
// arrives). The full Markdown render happens once, in finalizeAriaStreamBubble.
function createAriaStreamBubble() {
  const body = appendMessage("aria", "");
  const cursor = document.createElement("span");
  cursor.className = "stream-cursor";
  cursor.textContent = "▍";
  body.appendChild(cursor);
  return body;
}

function updateAriaStreamBubble(body, text) {
  body.textContent = text;
  const cursor = document.createElement("span");
  cursor.className = "stream-cursor";
  cursor.textContent = "▍";
  body.appendChild(cursor);
  scrollToBottom();
}

// Converts Markdown -> HTML (marked), then strips anything unsafe (DOMPurify)
// before it's ever inserted into the page. Returns null if the CDN libraries
// didn't load (offline, blocked network, etc.) so the caller can fall back
// to plain text instead of breaking.
function renderMarkdown(text) {
  if (typeof marked === "undefined" || typeof DOMPurify === "undefined") {
    return null;
  }
  const rawHtml = marked.parse(text);
  return DOMPurify.sanitize(rawHtml);
}

function finalizeAriaStreamBubble(body, text) {
  const html = renderMarkdown(text);
  if (html !== null) {
    body.innerHTML = html;
  } else {
    body.textContent = text;
  }
  scrollToBottom();
}

function scrollToBottom() {
  chatLog.scrollTop = chatLog.scrollHeight;
}

function setLoading(isLoading) {
  sendBtn.disabled = isLoading;
  chatInput.disabled = isLoading;
}

function _earliestMarkerIndex(text) {
  const indices = [text.indexOf(STREAM_CITATIONS_PREFIX), text.indexOf(STREAM_TOOLS_PREFIX)].filter((i) => i !== -1);
  return indices.length ? Math.min(...indices) : -1;
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

      // Don't render the trailing citations/tools JSON as if it were reply text.
      const markerIndex = _earliestMarkerIndex(fullText);
      const displayText = markerIndex !== -1 ? fullText.slice(0, markerIndex) : fullText;
      updateAriaStreamBubble(bubble, displayText);
    }

    if (sawError) {
      bubble.closest(".msg").remove();
      appendMessage("error", fullText.replace(STREAM_ERROR_PREFIX, ""));
      return;
    }

    const markerIndex = _earliestMarkerIndex(fullText);
    let replyText = fullText;
    let citations = null;
    let toolCalls = null;

    if (markerIndex !== -1) {
      replyText = fullText.slice(0, markerIndex);
      const trailer = fullText.slice(markerIndex);

      const citationsIdx = trailer.indexOf(STREAM_CITATIONS_PREFIX);
      const toolsIdx = trailer.indexOf(STREAM_TOOLS_PREFIX);

      if (citationsIdx !== -1) {
        const end = toolsIdx !== -1 && toolsIdx > citationsIdx ? toolsIdx : trailer.length;
        try {
          citations = JSON.parse(trailer.slice(citationsIdx + STREAM_CITATIONS_PREFIX.length, end));
        } catch (err) {
          citations = null; // malformed — skip rather than break the reply
        }
      }

      if (toolsIdx !== -1) {
        try {
          toolCalls = JSON.parse(trailer.slice(toolsIdx + STREAM_TOOLS_PREFIX.length));
        } catch (err) {
          toolCalls = null;
        }
      }
    }

    finalizeAriaStreamBubble(bubble, replyText);
    speakText(replyText);

    if (toolCalls && toolCalls.length > 0) {
      const parts = toolCalls.map((t) => {
        if (t.name === "calculator") return `calculator(${t.arguments.expression})`;
        if (t.name === "web_search") return `web_search("${t.arguments.query}")`;
        return t.name;
      });
      appendMessage("system", `🛠️ Tools: ${parts.join(", ")}`);
    }

    if (citations && citations.length > 0) {
      const parts = citations.map((c) => `${c.source} (${c.chunks_used} bagian)`);
      appendMessage("system", `📚 Sumber: ${parts.join(", ")}`);
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

// ---------- Feature flags from the server ----------
// Some deployments (e.g. low-memory free hosting tiers) disable RAG entirely
// to save RAM, since even loading the embedding model costs a few hundred MB
// whether or not it's used. Hide the RAG UI instead of showing broken buttons.
(async () => {
  try {
    const res = await fetch("/config");
    const data = await res.json();
    if (!data.rag_enabled) {
      uploadDocBtn.style.display = "none";
      ragToggleBtn.style.display = "none";
    }
  } catch (err) {
    // If /config itself fails, leave the RAG buttons visible — worst case
    // the user sees a normal error message if they try to use them.
  }
})();

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

// ---------- Tool calling (calculator, web search) ----------
let toolsEnabled = true; // mirrors AriaChatbot's default (tools_enabled=True)

toolsToggleBtn.addEventListener("click", async () => {
  toolsEnabled = !toolsEnabled;
  try {
    const res = await fetch("/tools/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: toolsEnabled }),
    });
    const data = await res.json();
    toolsEnabled = data.tools_enabled;
  } catch (err) {
    appendMessage("error", "Gagal menghubungi server untuk toggle tools.");
    toolsEnabled = !toolsEnabled; // revert on failure
  }
  toolsToggleBtn.textContent = toolsEnabled ? "🛠️ tools: on" : "🛠️ tools: off";
  appendMessage("system", `🛠️ Tool calling (calculator + web search) ${toolsEnabled ? "diaktifkan" : "dimatikan"}.`);
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
    if (data.flagged > 0) {
      appendMessage("error", `⚠️ ${data.flagged} bagian dari dokumen ini mengandung pola yang mirip prompt injection. Aria tetap akan memperlakukannya sebagai referensi, bukan instruksi.`);
    }
  } catch (err) {
    appendMessage("error", "Gagal mengunggah dokumen ke server.");
  }
});