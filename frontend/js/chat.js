requireLogin();

let conversationId = null;
const log = document.getElementById("log");

function addBubble(text, cls) {
  const div = document.createElement("div");
  div.className = "msg " + cls;
  div.setAttribute("dir", "auto"); // Arabic answers align right, English left
  div.innerText = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

function greet() {
  addBubble(
    "Hi! Ask me anything about your organization's documents. You can write in English or Arabic.",
    "bot"
  );
}

function newChat() {
  conversationId = null;
  log.innerHTML = "";
  greet();
}

function addSourcesAndFeedback(sources, turnId) {
  if (sources.length) {
    const src = document.createElement("div");
    src.className = "msg-sources";
    src.innerText = "Sources: " + sources.join(", ");
    log.appendChild(src);
  }
  const fb = document.createElement("div");
  fb.className = "msg-sources";
  fb.innerHTML = `<span>Was this answer helpful?</span>
    <button onclick="rate(5, '${turnId}', this)">👍</button>
    <button onclick="rate(1, '${turnId}', this)">👎</button>`;
  log.appendChild(fb);
  log.scrollTop = log.scrollHeight;
}

async function rate(score, turnId, btn) {
  try {
    await apiSend("/feedback", "POST", { turn_id: turnId || null, score });
    btn.parentElement.innerText = "Thanks for your feedback ✅";
  } catch (e) {
    /* silent */
  }
}

async function sendQuestion() {
  const input = document.getElementById("question");
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  addBubble(question, "me");
  const thinking = addBubble("Searching...", "bot");

  try {
    const data = await apiSend("/ask", "POST", { conversation_id: conversationId, question });
    conversationId = data.conversation_id;
    thinking.remove();
    addBubble(data.answer, "bot" + (data.was_fallback ? " fallback" : ""));
    addSourcesAndFeedback(data.sources, data.turn_id);
  } catch (e) {
    thinking.remove();
    addBubble("Error: " + (typeof e.detail === "string" ? e.detail : "could not reach the server"), "bot fallback");
  }
}

document.getElementById("question").addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendQuestion();
});

// --- Voice input ---
let mediaRecorder,
  audioChunks = [];
document.getElementById("micBtn").addEventListener("click", async () => {
  const btn = document.getElementById("micBtn");
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    btn.innerText = "🎤";
    return;
  }

  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (err) {
    addBubble("Microphone access was denied or is not available in this browser.", "bot fallback");
    return;
  }

  mediaRecorder = new MediaRecorder(stream);
  audioChunks = [];
  mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
  mediaRecorder.onstop = async () => {
    stream.getTracks().forEach((t) => t.stop());
    const blob = new Blob(audioChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("file", blob, "voice.webm");
    try {
      const result = await apiUpload("/speech/transcribe", formData);
      document.getElementById("question").value = result.text || "";
    } catch (e) {
      addBubble("Could not transcribe the recording.", "bot fallback");
    }
  };
  mediaRecorder.start();
  btn.innerText = "⏹";
});

greet();
