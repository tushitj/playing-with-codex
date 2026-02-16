# Multi-Language Flashcards

Single-file, browser-only flashcard app that translates English into selected languages using Transformers.js.

## Run
Open `index.html` in a browser. If model loading fails in `file://` mode, run a local server:

```bash
cd /Users/tushitjain/dev/playing-with-codex/multi-lang-flashcards
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Features
- In-browser translation (no backend)
- Searchable dropdown of FLORES-200 language codes (defaults to 5, saved in `localStorage`)
- Flip cards to quiz yourself
- Local deck saved in `localStorage`
- Export saved deck as JSON

## Notes
- First load is slower due to model download.
- Model: `Xenova/nllb-200-distilled-600M`
