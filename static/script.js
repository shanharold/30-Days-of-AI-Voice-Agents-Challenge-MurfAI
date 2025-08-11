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

// --- Helpers ---
const MAX_LLM_LEN = 3000;

function sanitize(str) {
  if (typeof str !== "string") str = String(str);
  return str.replace(/\r/g, " ").replace(/\n/g, " ").replace(/\s+/g, " ").trim();
}

function setHiddenTranscript(text) {
  const hidden = document.getElementById("llm-transcript-hidden");
  const displayTop = document.getElementById("transcript-output");
  const displayLLM = document.getElementById("llm-transcript-output");
  const count = document.getElementById("llm-transcript-count");

  const clean = sanitize(text || "");
  hidden.value = clean;
  if (displayTop) displayTop.textContent = clean;
  if (displayLLM) displayLLM.textContent = clean;
  if (count) count.textContent = clean.length;
}

function clearHiddenTranscript(message) {
  const hidden = document.getElementById("llm-transcript-hidden");
  const displayTop = document.getElementById("transcript-output");
  const displayLLM = document.getElementById("llm-transcript-output");
  const count = document.getElementById("llm-transcript-count");

  hidden.value = "";
  if (displayTop) displayTop.textContent = "";
  if (displayLLM) displayLLM.textContent = message || "No transcript available. Please record first.";
  if (count) count.textContent = "0";
}

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
    player.style.display = "block";
    statusEl && (statusEl.textContent = `Playing segment ${i + 1}/${urls.length} ...`);
    player.onended = () => playIndex(i + 1);
    player.play().catch(() => {});
  }

  player.onended = null;
  playIndex(idx);
}

// --- Classic TTS ---
document.getElementById("generate-btn")?.addEventListener("click", async () => {
  const text = document.getElementById("input-box").value.trim();
  const statusDiv = document.getElementById("status");
  const audioContainer = document.getElementById("audio-container");
  const audioPlayer = document.getElementById("audio-player");
  statusDiv.style.color = "#fff";
  statusDiv.textContent = "";
  audioContainer.style.display = "none";

  if (!text) {
    statusDiv.textContent = "Please enter some text.";
    statusDiv.style.color = "#ff4d4f";
    return;
  }
  statusDiv.textContent = "Generating speech...";
  try {
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice_id: "en-US-natalie", style: "Promo" }),
    });
    const data = await res.json();
    if (data.success) {
      if (data.audio_urls && data.audio_urls.length) {
        audioContainer.style.display = "block";
        playAudioPlaylist(data.audio_urls, audioPlayer, statusDiv);
      } else if (data.audio_url) {
        audioPlayer.src = data.audio_url;
        audioContainer.style.display = "block";
        statusDiv.textContent = "Speech generated!";
        statusDiv.style.color = "#0ff";
      } else {
        statusDiv.textContent = "No audio URL(s) returned.";
        statusDiv.style.color = "#ff4d4f";
      }
    } else {
      statusDiv.textContent = data.message || "Failed to generate speech.";
      statusDiv.style.color = "#ff4d4f";
    }
  } catch (err) {
    statusDiv.textContent = "Error contacting backend!";
    statusDiv.style.color = "#ff4d4f";
  }
});

// --- Echo Bot recording/transcription ---
let mediaRecorder;
let audioChunks = [];

const startBtn = document.getElementById("start-recording");
const stopBtn = document.getElementById("stop-recording");
const audioPlayback = document.getElementById("audio-playback");
const recordingStatus = document.getElementById("recording-status");

const murfEchoPlayer = document.createElement("audio");
murfEchoPlayer.controls = true;
murfEchoPlayer.id = "murf-echo-player";
murfEchoPlayer.style.display = "none";
document.getElementById("echo-bot-section").appendChild(murfEchoPlayer);

startBtn?.addEventListener("click", async () => {
  recordingStatus.textContent = "Recording...";
  recordingStatus.style.color = "#fff";
  audioPlayback.style.display = "none";
  murfEchoPlayer.style.display = "none";
  audioChunks = [];
  stopBtn.disabled = false;
  startBtn.disabled = true;
  clearHiddenTranscript("");

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (e) => {
      audioChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      const audioUrl = URL.createObjectURL(audioBlob);
      audioPlayback.src = audioUrl;
      audioPlayback.style.display = "block";
      recordingStatus.textContent = "Playback ready. Listen below!";
      recordingStatus.style.color = "#0ff";
      startBtn.disabled = false;
      stopBtn.disabled = true;

      recordingStatus.textContent = "Uploading recording...";
      recordingStatus.style.color = "#fff";
      const formData = new FormData();
      formData.append("audio", audioBlob, "echo-recording.webm");
      fetch("/api/upload-audio", { method: "POST", body: formData })
        .then((res) => res.json())
        .then((data) => {
          recordingStatus.textContent = `Upload successful! Name: ${data.name}, Type: ${data.content_type}, Size: ${data.size} bytes.`;
          recordingStatus.style.color = "#0ff";
        })
        .catch(() => {
          recordingStatus.textContent = "Upload failed.";
          recordingStatus.style.color = "#ff4d4f";
        });

      const transcribeForm = new FormData();
      transcribeForm.append("file", audioBlob, "echo-recording.webm");

      const llmTranscriptOutput = document.getElementById("llm-transcript-output");
      if (llmTranscriptOutput) llmTranscriptOutput.textContent = "Transcribing audio...";

      fetch("/transcribe/file", { method: "POST", body: transcribeForm })
        .then((res) => res.json())
        .then((data) => {
          if (data.success && data.transcript) {
            setHiddenTranscript(data.transcript);
          } else {
            clearHiddenTranscript("Transcription failed: " + (data.error || "Unknown error"));
          }
        })
        .catch(() => {
          clearHiddenTranscript("Transcription error. Please try again.");
        });

      const murfEchoForm = new FormData();
      murfEchoForm.append("audio", audioBlob, "echo-recording.webm");
      fetch("/tts/echo", { method: "POST", body: murfEchoForm })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            if (data.audio_urls && data.audio_urls.length) {
              playAudioPlaylist(data.audio_urls, murfEchoPlayer, recordingStatus);
            } else if (data.audio_url) {
              murfEchoPlayer.src = data.audio_url;
              murfEchoPlayer.style.display = "block";
              recordingStatus.textContent = "Murf voice echo ready!";
              recordingStatus.style.color = "#0ff";
            } else {
              recordingStatus.textContent = "Murf echo returned no audio URLs.";
              recordingStatus.style.color = "#ff4d4f";
            }
          } else {
            recordingStatus.textContent = "Murf echo failed: " + (data.error || "Unknown error");
            recordingStatus.style.color = "#ff4d4f";
          }
        })
        .catch(() => {
          recordingStatus.textContent = "Error getting Murf echo.";
          recordingStatus.style.color = "#ff4d4f";
        });

      document.getElementById("llm-audio-query-btn").disabled = false;
      document.getElementById("llm-audio-query-status").textContent =
        "Ready to query LLM with your recording!";
    };

    mediaRecorder.start();
  } catch (err) {
    recordingStatus.textContent = "Microphone access denied or unavailable.";
    recordingStatus.style.color = "#ff4d4f";
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }
});

stopBtn?.addEventListener("click", () => {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    recordingStatus.textContent = "Processing recording...";
    recordingStatus.style.color = "#fff";
    stopBtn.disabled = true;
  }
});

// --- LLM Audio Query ---
const llmAudioBtn = document.getElementById("llm-audio-query-btn");
const llmAudioStatus = document.getElementById("llm-audio-query-status");
const llmAudioPlayer = document.getElementById("llm-audio-player");
const llmAudioPlaylistStatus = document.getElementById("llm-audio-playlist-status");
const llmTextOutput = document.getElementById("llm-text-output");

llmAudioBtn?.addEventListener("click", async () => {
  const hidden = document.getElementById("llm-transcript-hidden");
  let toSend = sanitize(hidden.value || "");

  if (!toSend) {
    llmAudioStatus.textContent = "No transcript available. Please record first.";
    llmAudioStatus.style.color = "#ff4d4f";
    return;
  }

  if (toSend.length > MAX_LLM_LEN) {
    toSend = toSend.slice(0, MAX_LLM_LEN);
  }
  document.getElementById("llm-transcript-count").textContent = toSend.length.toString();

  llmAudioStatus.textContent = `Sending transcript to LLM (${toSend.length} chars)...`;
  llmAudioStatus.style.color = "#fff";
  llmAudioBtn.disabled = true;

  try {
    const res = await fetch("/llm/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: toSend }),
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById("llm-transcript-output").textContent = data.transcript || toSend;
      document.getElementById("llm-transcript-count").textContent = String(
        (data.transcript || toSend).length
      );
      llmTextOutput.textContent = data.response || "";

      if (data.audio_urls && data.audio_urls.length) {
        playAudioPlaylist(data.audio_urls, llmAudioPlayer, llmAudioPlaylistStatus);
        llmAudioStatus.textContent = "LLM response generated (multiple segments).";
        llmAudioStatus.style.color = "#0ff";
      } else if (data.audio_url) {
        llmAudioPlayer.src = data.audio_url;
        llmAudioPlayer.style.display = "block";
        llmAudioStatus.textContent = "LLM response generated!";
        llmAudioStatus.style.color = "#0ff";
        llmAudioPlaylistStatus.textContent = "";
      } else {
        llmAudioStatus.textContent = "No audio URL(s) returned.";
        llmAudioStatus.style.color = "#ff4d4f";
        llmAudioPlaylistStatus.textContent = "";
      }
    } else {
      llmAudioStatus.textContent = "LLM audio query failed: " + (data.error || "Unknown error");
      llmAudioStatus.style.color = "#ff4d4f";
      llmAudioPlaylistStatus.textContent = "";
    }
  } catch (e) {
    llmAudioStatus.textContent = "Error querying LLM with transcript!";
    llmAudioStatus.style.color = "#ff4d4f";
    llmAudioPlaylistStatus.textContent = "";
  } finally {
    llmAudioBtn.disabled = false;
  }
});

// --- LLM Text Query (separate text box) ---
document.getElementById("llm-text-query-btn")?.addEventListener("click", async () => {
  const text = document.getElementById("llm-input-box").value.trim();
  const statusDiv = document.getElementById("llm-text-query-status");
  const audioPlayer = document.getElementById("llm-text-audio-player");
  const playlistStatus = document.getElementById("llm-text-playlist-status");
  const transcriptOut = document.getElementById("llm-text-transcript-output");
  const textOut = document.getElementById("llm-text-output2");
  statusDiv.style.color = "#fff";
  statusDiv.textContent = "";
  audioPlayer.style.display = "none";
  playlistStatus.textContent = "";
  transcriptOut.textContent = "";
  textOut.textContent = "";

  let toSend = sanitize(text);
  if (!toSend) {
    statusDiv.textContent = "Please enter some text.";
    statusDiv.style.color = "#ff4d4f";
    return;
  }
  if (toSend.length > MAX_LLM_LEN) {
    toSend = toSend.slice(0, MAX_LLM_LEN);
  }

  statusDiv.textContent = `Querying LLM (${toSend.length} chars)...`;
  try {
    const res = await fetch("/llm/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: toSend }),
    });
    const data = await res.json();
    if (data.success) {
      transcriptOut.textContent = data.transcript || toSend;
      textOut.textContent = data.response || "";
      if (data.audio_urls && data.audio_urls.length) {
        playAudioPlaylist(data.audio_urls, audioPlayer, playlistStatus);
        statusDiv.textContent = "LLM response generated (multiple segments).";
        statusDiv.style.color = "#0ff";
      } else if (data.audio_url) {
        audioPlayer.src = data.audio_url;
        audioPlayer.style.display = "block";
        statusDiv.textContent = "LLM response generated!";
        statusDiv.style.color = "#0ff";
        playlistStatus.textContent = "";
      } else {
        statusDiv.textContent = "No audio URL(s) returned.";
        statusDiv.style.color = "#ff4d4f";
      }
    } else {
      statusDiv.textContent = data.error || "Failed to get LLM response.";
      statusDiv.style.color = "#ff4d4f";
    }
  } catch (err) {
    statusDiv.textContent = "Error contacting backend!";
    statusDiv.style.color = "#ff4d4f";
  }
});

// --- Conversational Chat Section (Day 10) ---
let convoRecorder;
let convoAudioChunks = [];
const convoStartBtn = document.getElementById("convo-start-recording");
const convoStopBtn = document.getElementById("convo-stop-recording");
const convoAudioPlayer = document.getElementById("convo-audio-player");
const convoStatus = document.getElementById("convo-status");
const convoBotTextOutput = document.getElementById("convo-bot-text-output");

function startConvoRecording() {
  convoStatus.textContent = "Recording (conversation)...";
  convoStatus.style.color = "#fff";
  convoAudioPlayer.style.display = "none";
  convoBotTextOutput.textContent = "";
  convoAudioChunks = [];
  convoStopBtn.disabled = false;
  convoStartBtn.disabled = true;

  navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    convoRecorder = new MediaRecorder(stream);
    convoRecorder.ondataavailable = (e) => {
      convoAudioChunks.push(e.data);
    };
    convoRecorder.onstop = () => {
      const audioBlob = new Blob(convoAudioChunks, { type: "audio/webm" });
      const formData = new FormData();
      formData.append("audio", audioBlob, "convo-recording.webm");
      convoStatus.textContent = "Sending to bot...";
      convoStatus.style.color = "#fff";
      fetch(`/agent/chat/${sessionId}`, { method: "POST", body: formData })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            convoStatus.textContent = "Bot responding...";
            convoBotTextOutput.textContent = data.response || "";
            if (data.audio_urls && data.audio_urls.length) {
              playAudioPlaylist(data.audio_urls, convoAudioPlayer, convoStatus, () => {
                setTimeout(() => startConvoRecording(), 1000);
              });
            } else if (data.audio_url) {
              convoAudioPlayer.src = data.audio_url;
              convoAudioPlayer.style.display = "block";
              convoAudioPlayer.onended = () => {
                setTimeout(() => startConvoRecording(), 1000);
              };
              convoAudioPlayer.play();
            }
          } else {
            convoStatus.textContent = "Conversation failed: " + (data.error || "Unknown error");
            convoStatus.style.color = "#ff4d4f";
            convoStartBtn.disabled = false;
            convoStopBtn.disabled = true;
          }
        })
        .catch(() => {
          convoStatus.textContent = "Error contacting bot.";
          convoStatus.style.color = "#ff4d4f";
          convoStartBtn.disabled = false;
          convoStopBtn.disabled = true;
        });
    };
    convoRecorder.start();
  }).catch(() => {
    convoStatus.textContent = "Mic access denied.";
    convoStatus.style.color = "#ff4d4f";
    convoStartBtn.disabled = false;
    convoStopBtn.disabled = true;
  });
}

convoStartBtn?.addEventListener("click", startConvoRecording);

convoStopBtn?.addEventListener("click", () => {
  if (convoRecorder && convoRecorder.state === "recording") {
    convoRecorder.stop();
    convoStopBtn.disabled = true;
    convoStartBtn.disabled = false;
  }
});