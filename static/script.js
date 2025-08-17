// --- Futuristic Robot Avatar - Pupils track mouse ---
document.addEventListener("mousemove", function (e) {
  const leftEye = document.querySelector(".eye.left");
  const rightEye = document.querySelector(".eye.right");
  if (!leftEye || !rightEye) return;

  const leftEyeRect = leftEye.getBoundingClientRect();
  const rightEyeRect = rightEye.getBoundingClientRect();
  const mouseX = e.clientX;
  const mouseY = e.clientY;

  function movePupil(eyeRect, pupilId) {
    const pupil = document.getElementById(pupilId);
    if (!pupil) return;
    const eyeCenterX = eyeRect.left + eyeRect.width / 2;
    const eyeCenterY = eyeRect.top + eyeRect.height / 2;
    let dx = mouseX - eyeCenterX;
    let dy = mouseY - eyeCenterY;
    const maxDist = 13;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > maxDist) {
      dx = (dx * maxDist) / dist;
      dy = (dy * maxDist) / dist;
    }
    pupil.style.left = 17 + dx + "px";
    pupil.style.top = 17 + dy + "px";
  }

  movePupil(leftEyeRect, "pupil-left");
  movePupil(rightEyeRect, "pupil-right");
});

// --- Session ID Management ---
function getSessionId() {
  const params = new URLSearchParams(window.location.search);
  let session_id = params.get("session_id");
  if (!session_id) {
    session_id = crypto.randomUUID();
    params.set("session_id", session_id);
    window.history.replaceState({}, "", `${window.location.pathname}?${params}`);
  }
  return session_id;
}
const sessionId = getSessionId();

// --- Conversational Bot Section (Day 16: Streaming Audio via WebSocket) ---
let convoRecorder;
let ws; // WebSocket instance for streaming
const recordBtn = document.getElementById("convo-record-btn");
const audioPlayer = document.getElementById("convo-audio-player");
const statusDiv = document.getElementById("convo-status");
const botOutput = document.getElementById("convo-bot-text-output");
const recordingIndicator = document.getElementById("recording-indicator");

let isRecording = false;

// No playlist or TTS for Day 16 - just audio streaming

function playFallbackAudio(player, statusEl) {
  player.src = "/static/fallback.mp3";
  player.style.display = "none";
  statusEl.textContent = "Fallback audio: I'm having trouble connecting right now.";
  statusEl.style.color = "#fa0";
  player.play().catch(() => {});
}

async function startConvoRecording() {
  statusDiv.textContent = "Recording (streaming audio)...";
  statusDiv.style.color = "#fff";
  audioPlayer.style.display = "none";
  botOutput.textContent = "";
  updateUI(true);

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    convoRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });

    // Open WebSocket connection to /ws/stream
    ws = new WebSocket("ws://localhost:8000/ws/stream");

    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      statusDiv.textContent = "Recording and streaming audio to server...";
      statusDiv.style.color = "#0ff";
      convoRecorder.start(250); // Collect audio in 250ms chunks
    };

    ws.onerror = (e) => {
      statusDiv.textContent = "WebSocket error!";
      statusDiv.style.color = "#ff4d4f";
      updateUI(false);
      playFallbackAudio(audioPlayer, statusDiv);
    };

    ws.onclose = () => {
      statusDiv.textContent = "WebSocket closed.";
      statusDiv.style.color = "#fa0";
      updateUI(false);
    };

    convoRecorder.ondataavailable = (e) => {
      if (e.data.size > 0 && ws && ws.readyState === WebSocket.OPEN) {
        // Send audio chunk as ArrayBuffer
        e.data.arrayBuffer().then(buffer => {
          ws.send(buffer);
        });
      }
    };

    convoRecorder.onstop = () => {
      // Tell server we're done (optional: you can skip this if not handled on backend)
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send("close"); // backend can ignore or use as a flag
        ws.close();
      }
      statusDiv.textContent = "Recording stopped. Audio saved on server!";
      statusDiv.style.color = "#0f0";
      updateUI(false);
    };

  } catch (e) {
    statusDiv.textContent = "Mic access denied.";
    statusDiv.style.color = "#ff4d4f";
    updateUI(false);
  }
}

function stopConvoRecording() {
  if (convoRecorder && convoRecorder.state === "recording") {
    convoRecorder.stop();
    // WebSocket will be closed in onstop
  } else {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
    updateUI(false);
  }
}

function updateUI(recording) {
  isRecording = !!recording;
  if (isRecording) {
    recordBtn.textContent = "Stop Streaming";
    recordBtn.classList.add("recording");
    recordingIndicator.style.display = "";
    statusDiv.textContent = "Recording and streaming...";
    statusDiv.style.color = "#0ff";
  } else {
    recordBtn.textContent = "Start Streaming";
    recordBtn.classList.remove("recording");
    recordingIndicator.style.display = "none";
    if (!statusDiv.textContent.includes("saved")) statusDiv.textContent = "";
    statusDiv.style.color = "#fff";
  }
}

recordBtn?.addEventListener("click", () => {
  if (!isRecording) {
    startConvoRecording();
  } else {
    stopConvoRecording();
  }
});

// Optional: Immediately update button to correct state on load
updateUI(false);