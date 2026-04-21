document.addEventListener('DOMContentLoaded', () => {
    const modeDisplay = document.getElementById('mode-display');
    const fpsValue = document.getElementById('fps-value');
    const fpsPill = document.getElementById('fps-pill');
    const lockOverlay = document.getElementById('lock-overlay');
    const gestureStatus = document.getElementById('gesture-status');
    const videoFeed = document.getElementById('video-feed');

    if (!videoFeed) return; // Only run on dashboard

    async function updateStatus() {
        try {
            const response = await fetch('/status');
            const data = await response.json();

            // Update Mode
            modeDisplay.textContent = data.mode;
            gestureStatus.textContent = getFriendlyStatus(data.mode);

            // Update FPS
            fpsValue.textContent = data.fps;
            fpsPill.textContent = `FPS: ${data.fps}`;

            // Update Lock status
            if (data.locked) {
                lockOverlay.classList.add('active');
            } else {
                lockOverlay.classList.remove('active');
            }

        } catch (error) {
            console.error('Error fetching status:', error);
        }
    }

    function getFriendlyStatus(mode) {
        const mappings = {
            'READY': 'Monitoring gestures...',
            'CURSOR MOVE': 'Index finger detected. Moving cursor.',
            'CLICK': 'Click gesture detected.',
            'MOVE SLICE': 'Left-drag engaged. Adjusting slice.',
            'ROTATE 3D': 'Right-drag engaged. Rotating 3D view.',
            'SCROLL MODE': 'Vertical movement mapped to scroll.',
            'VOICE TYPING': 'Voice dictation active.',
            'ZOOM MODE': 'Two-hand zoom active.',
            'LOCKED': 'Interface frozen. Hold fist to unlock.',
            'INITIALIZING': 'Preparing system...'
        };
        return mappings[mode] || mode;
    }

    // Poll every 100ms for status updates
    setInterval(updateStatus, 100);
});
