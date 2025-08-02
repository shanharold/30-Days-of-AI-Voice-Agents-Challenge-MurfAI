document.addEventListener('mousemove', function(e) {
    const avatar = document.getElementById('avatar');
    const rect = avatar.getBoundingClientRect();

    // Eye centers
    const leftEye = document.querySelector('.eye.left');
    const rightEye = document.querySelector('.eye.right');
    const leftEyeRect = leftEye.getBoundingClientRect();
    const rightEyeRect = rightEye.getBoundingClientRect();

    // Mouse position relative to viewport
    const mouseX = e.clientX;
    const mouseY = e.clientY;

    function movePupil(eyeRect, pupilId) {
        const pupil = document.getElementById(pupilId);
        // Eye center
        const eyeCenterX = eyeRect.left + eyeRect.width / 2;
        const eyeCenterY = eyeRect.top + eyeRect.height / 2;
        // Calculate angle to mouse
        const dx = mouseX - eyeCenterX;
        const dy = mouseY - eyeCenterY;
        // Limit pupil movement
        const maxDist = 16;
        let dist = Math.sqrt(dx*dx + dy*dy);
        if (dist > maxDist) {
            dx = dx * maxDist / dist;
            dy = dy * maxDist / dist;
        }
        // Move pupil within eye
        pupil.style.left = (16 + dx) + 'px';
        pupil.style.top = (16 + dy) + 'px';
    }

    movePupil(leftEyeRect, 'pupil-left');
    movePupil(rightEyeRect, 'pupil-right');
});