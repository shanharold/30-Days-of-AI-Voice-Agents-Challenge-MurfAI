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