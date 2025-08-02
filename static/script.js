// Futuristic Robot Avatar - Pupils track mouse
document.addEventListener('mousemove', function(e) {
    const avatar = document.getElementById('avatar');
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
        const maxDist = 18;
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