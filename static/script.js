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

// --- Conversational Bot Section (Day 12 UI) ---
let convoRecorder;
let convoAudioChunks = [];
const recordBtn = document.getElementById("convo-record-btn");
const audioPlayer = document.getElementById("convo-audio-player");
const statusDiv = document.getElementById("convo-status");
const botOutput = document.getElementById("convo-bot-text-output");
const recordingIndicator = document.getElementById("recording-indicator");

let isRecording = false;

function playAudioPlaylist(urls, player, statusEl, onFinish) {
  if (!urls || !urls.length) return;
  let idx = 0;

  function playIndex(i) {
    if (i >= urls.length) {
      statusEl && (statusEl.textContent = "Playback finished.");
      if (typeof onFinish === "function") onFinish();
      return;
    }
    const url = urls[i];
    player.src = url;
    player.style.display = "none";
    statusEl && (statusEl.textContent = `Playing segment ${i + 1}/${urls.length} ...`);
    player.onended = () => playIndex(i + 1);
    player.play().catch(() => {});
  }

  player.onended = null;
  playIndex(idx);
}

function playFallbackAudio(player, statusEl) {
  player.src = "/static/fallback.mp3";
  player.style.display = "none";
  statusEl.textContent = "Fallback audio: I'm having trouble connecting right now.";
  statusEl.style.color = "#fa0";
  player.play().catch(() => {});
}

async function startConvoRecording() {
  statusDiv.textContent = "Recording (conversation)...";
  statusDiv.style.color = "#fff";
  audioPlayer.style.display = "none";
  botOutput.textContent = "";
  convoAudioChunks = [];
  updateUI(true);

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    convoRecorder = new MediaRecorder(stream);
    convoRecorder.ondataavailable = (e) => {
      convoAudioChunks.push(e.data);
    };
    convoRecorder.onstop = () => {
      const audioBlob = new Blob(convoAudioChunks, { type: "audio/webm" });
      const formData = new FormData();
      formData.append("audio", audioBlob, "convo-recording.webm");
      statusDiv.textContent = "Sending to bot...";
      statusDiv.style.color = "#fff";
      fetch(`/agent/chat/${sessionId}`, { method: "POST", body: formData })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            statusDiv.textContent = "Bot responding...";
            botOutput.textContent = data.response || "";
            if (data.audio_urls && data.audio_urls.length) {
              playAudioPlaylist(data.audio_urls, audioPlayer, statusDiv, () => {
                updateUI(false);
              });
            } else if (data.audio_url) {
              audioPlayer.src = data.audio_url;
              audioPlayer.style.display = "none";
              audioPlayer.onended = () => {
                updateUI(false);
              };
              audioPlayer.play();
            } else {
              statusDiv.textContent = "No audio returned.";
              statusDiv.style.color = "#ff4d4f";
              updateUI(false);
            }
          } else {
            if (data.audio_url) {
              audioPlayer.src = data.audio_url;
              audioPlayer.style.display = "none";
              statusDiv.textContent = "Playing fallback audio.";
              statusDiv.style.color = "#fa0";
              audioPlayer.play();
            } else {
              playFallbackAudio(audioPlayer, statusDiv);
            }
            updateUI(false);
          }
        })
        .catch(() => {
          playFallbackAudio(audioPlayer, statusDiv);
          updateUI(false);
        });
    };
    convoRecorder.start();
  } catch (e) {
    statusDiv.textContent = "Mic access denied.";
    statusDiv.style.color = "#ff4d4f";
    updateUI(false);
  }
}

function stopConvoRecording() {
  if (convoRecorder && convoRecorder.state === "recording") {
    convoRecorder.stop();
    updateUI(false);
  }
}

function updateUI(recording) {
  isRecording = !!recording;
  if (isRecording) {
    recordBtn.textContent = "Stop Recording";
    recordBtn.classList.add("recording");
    recordingIndicator.style.display = "";
    statusDiv.textContent = "Recording...";
    statusDiv.style.color = "#0ff";
  } else {
    recordBtn.textContent = "Start Recording";
    recordBtn.classList.remove("recording");
    recordingIndicator.style.display = "none";
    if (!statusDiv.textContent.includes("Bot")) statusDiv.textContent = "";
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