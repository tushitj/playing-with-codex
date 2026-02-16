# Finger Counter

A tiny, single-file web app that uses MediaPipe Hands to detect hand landmarks from your webcam and count how many fingers are up in real time.

## Features
- Live webcam preview with hand landmarks overlay
- Counts fingers across up to two hands
- Pause/Resume tracking
- Zero build steps (pure HTML/JS)

## Run
Because webcam access requires a secure context, use a local server (recommended). Two quick options:

### Python
```bash
python3 -m http.server 8000
```
Then open `http://localhost:8000` and allow camera access.

### Node (if installed)
```bash
npx serve .
```

You can also open `index.html` directly, but some browsers will block camera access for `file://` URLs.

## Tech
- MediaPipe Hands via CDN
- Plain HTML/CSS/JS

## Notes
- Best results in good lighting with your hand fully in frame.
- The thumb detection uses handedness (left/right) to determine whether it is extended.
