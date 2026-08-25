# PDF Read Aloud

Narrate a PDF with natural neural text-to-speech (Microsoft Edge voices via `edge-tts`). No API key required.

## Setup

```bash
pip install -r tools/pdf-read-aloud/requirements.txt
# Optional but recommended for better extraction / scanned PDFs:
# sudo apt-get install -y poppler-utils tesseract-ocr
```

## Usage

```bash
python3 tools/pdf-read-aloud/read_aloud.py path/to/doc.pdf \
  -o /opt/cursor/artifacts/doc-narration.mp3 \
  --text-out /tmp/doc-cleaned.txt
```

List recommended voices:

```bash
python3 tools/pdf-read-aloud/read_aloud.py --list-voices
```

Useful options:

| Flag | Purpose |
|------|---------|
| `--voice en-US-AvaMultilingualNeural` | Alternate natural voice |
| `--rate -8%` | Slightly slower audiobook pacing (default) |
| `--force-ocr` | OCR scanned/image PDFs |
| `--ocr-max-pages 20` | Limit OCR cost on large scans |

## Voices (most natural)

- `en-US-AndrewMultilingualNeural` (default) — warm male narration
- `en-US-AvaMultilingualNeural` — warm female narration
- `en-US-EmmaMultilingualNeural` / `en-US-BrianMultilingualNeural`

## Agent workflow

1. Accept a PDF from the user (attachment or path).
2. Run `read_aloud.py` and write the MP3 under `/opt/cursor/artifacts/`.
3. Share the audio artifact so the user can play it.
4. For long books, narrate in chapters or page ranges and confirm before continuing.
