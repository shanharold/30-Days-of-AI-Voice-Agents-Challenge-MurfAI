// Futuristic Robot Avatar - Pupils track mouse
document.addEventListener('mousemove', function(e) {
    const leftEye = document.querySelector('.eye.left');
    const rightEye = document.querySelector('.eye.right');
    const leftEyeRect = leftEye.getBoundingClientRect();
    const rightEyeRect = rightEye.getBoundingClientRect();

    const mouseX = e.clientX;
    const mouseY = e.clientY;

    function movePupil(eyeRect, pupilId) {
        const pupil = document.getElementById(pupilId);
        const eyeCenterX = eyeRect.left + eyeRect.width / 2;
        const eyeCenterY = eyeRect.top + eyeRect.height / 2;
        let dx = mouseX - eyeCenterX;
        let dy = mouseY - eyeCenterY;
        const maxDist = 13;
        let dist = Math.sqrt(dx*dx + dy*dy);
        if (dist > maxDist) {
            dx = dx * maxDist / dist;
            dy = dy * maxDist / dist;
        }
        pupil.style.left = (17 + dx) + 'px';
        pupil.style.top = (17 + dy) + 'px';
    }

    movePupil(leftEyeRect, 'pupil-left');
    movePupil(rightEyeRect, 'pupil-right');
});

document.getElementById('generate-btn').onclick = async function() {
    const text = document.getElementById('input-box').value.trim();
    const statusDiv = document.getElementById('status');
    const audioContainer = document.getElementById('audio-container');
    const audioPlayer = document.getElementById('audio-player');
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
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                text,
                voice_id: "en-US-natalie",
                style: "Promo"
            })
        });
        const data = await res.json();
        if (data.success && data.audio_url) {
            audioPlayer.src = data.audio_url;
            audioContainer.style.display = "block";
            statusDiv.textContent = "Speech generated!";
            statusDiv.style.color = "#0ff";
        } else {
            statusDiv.textContent = data.message || "Failed to generate speech.";
            statusDiv.style.color = "#ff4d4f";
        }
    } catch (err) {
        statusDiv.textContent = "Error contacting backend!";
        statusDiv.style.color = "#ff4d4f";
    }
};

// Echo Bot logic
let mediaRecorder;
let audioChunks = [];

const startBtn = document.getElementById('start-recording');
const stopBtn = document.getElementById('stop-recording');
const audioPlayback = document.getElementById('audio-playback');
const recordingStatus = document.getElementById('recording-status');
const transcriptOutput = document.getElementById('transcript-output');

startBtn.addEventListener('click', async () => {
    recordingStatus.textContent = "Recording...";
    recordingStatus.style.color = "#fff";
    audioPlayback.style.display = "none";
    audioChunks = [];
    stopBtn.disabled = false;
    startBtn.disabled = true;
    transcriptOutput.textContent = ""; // Clear previous transcript

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (e) => {
            audioChunks.push(e.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const audioUrl = URL.createObjectURL(audioBlob);
            audioPlayback.src = audioUrl;
            audioPlayback.style.display = "block";
            recordingStatus.textContent = "Playback ready. Listen below!";
            recordingStatus.style.color = "#0ff";
            startBtn.disabled = false;
            stopBtn.disabled = true;

            // --- Upload Audio to Server ---
            recordingStatus.textContent = "Uploading recording...";
            recordingStatus.style.color = "#fff";
            const formData = new FormData();
            formData.append('audio', audioBlob, 'echo-recording.webm');
            fetch('/api/upload-audio', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                recordingStatus.textContent = `Upload successful! Name: ${data.name}, Type: ${data.content_type}, Size: ${data.size} bytes.`;
                recordingStatus.style.color = "#0ff";
            })
            .catch(err => {
                recordingStatus.textContent = "Upload failed.";
                recordingStatus.style.color = "#ff4d4f";
            });

            // --- Send Audio for Transcription ---
            transcriptOutput.textContent = "Transcribing audio...";
            const transcribeForm = new FormData();
            transcribeForm.append("file", audioBlob, "echo-recording.webm");
            fetch("/transcribe/file", {
                method: "POST",
                body: transcribeForm
            })
            .then(res => res.json())
            .then(data => {
                if (data.success && data.transcript) {
                    transcriptOutput.textContent = data.transcript;
                } else {
                    transcriptOutput.textContent = "Transcription failed: " + (data.error || "Unknown error");
                }
            })
            .catch(() => {
                transcriptOutput.textContent = "Transcription error. Please try again.";
            });
        };

        mediaRecorder.start();
    } catch (err) {
        recordingStatus.textContent = "Microphone access denied or unavailable.";
        recordingStatus.style.color = "#ff4d4f";
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
});

stopBtn.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        recordingStatus.textContent = "Processing recording...";
        recordingStatus.style.color = "#fff";
        stopBtn.disabled = true;
    }
});