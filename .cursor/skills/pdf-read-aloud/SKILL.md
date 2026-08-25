---
name: pdf-read-aloud
description: Read a PDF aloud with natural neural TTS. Use when the user asks to read, narrate, or listen to a PDF, document, paper, book, or article.
---

# PDF Read Aloud

When the user wants a PDF read aloud, use the repo tool — do not improvise with robotic system voices.

## Steps

1. Locate the PDF (attachment path, workspace path, or download URL).
2. Run:

```bash
python3 tools/pdf-read-aloud/read_aloud.py "$PDF" \
  -o /opt/cursor/artifacts/"$(basename "$PDF" .pdf)"-narration.mp3 \
  --text-out /tmp/pdf-narration-cleaned.txt
```

3. Share the MP3 artifact for playback. Mention the voice used and approximate duration.
4. Default voice: `en-US-AndrewMultilingualNeural` (warm, natural). Offer `en-US-AvaMultilingualNeural` if they prefer a female narrator.
5. For scanned PDFs with little extractable text, re-run with `--force-ocr` (and `--ocr-max-pages` for large docs).
6. For long documents (>~20 min of audio), narrate in sections and ask before continuing.

## Naturalness knobs

- Keep default `--rate -8%` for audiobook pacing.
- Do not dump raw PDF text into chat as a substitute for audio unless the user asks for text only.
- Prefer chapter/section chunking over one giant file when the PDF is book-length.
