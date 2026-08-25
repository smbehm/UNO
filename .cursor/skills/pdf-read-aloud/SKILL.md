---
name: pdf-read-aloud
description: Read a PDF aloud with Hugging Face Kokoro-82M natural TTS. Use when the user asks to read, narrate, listen to, or convert a PDF to speech.
---

# PDF Read Aloud (Hugging Face Kokoro)

Use `tools/pdf-read-aloud/read_aloud.py` with **hexgrad/Kokoro-82M** — not Edge TTS, not system `espeak`.

## Steps

1. Locate the user's PDF (required — do not substitute a tiny demo).
2. Run:

```bash
python3 tools/pdf-read-aloud/read_aloud.py "$PDF" \
  -o /opt/cursor/artifacts/"$(basename "$PDF" .pdf)"-narration.mp3 \
  --text-out /tmp/pdf-narration-cleaned.txt
```

3. Share the full MP3. Report voice, model (`hexgrad/Kokoro-82M`), and duration.
4. Default voice: `am_michael`. Offer `af_heart` for a female narrator.
5. Scanned PDFs: `--force-ocr` (and `--ocr-max-pages` for large scans).
6. For book-length PDFs, narrate in sections and confirm before continuing.
