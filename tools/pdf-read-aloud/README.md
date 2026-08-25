# PDF Read Aloud (Hugging Face)

Narrate a PDF with **Kokoro-82M** from Hugging Face (`hexgrad/Kokoro-82M`) — natural neural TTS that runs on CPU.

## Setup

```bash
pip3 install -r tools/pdf-read-aloud/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
sudo apt-get install -y poppler-utils tesseract-ocr ffmpeg espeak-ng
```

Optional: set `HF_TOKEN` for higher Hugging Face Hub rate limits.

## Usage

```bash
python3 tools/pdf-read-aloud/read_aloud.py path/to/doc.pdf \
  -o /opt/cursor/artifacts/doc-narration.mp3 \
  --text-out /tmp/doc-cleaned.txt
```

List voices:

```bash
python3 tools/pdf-read-aloud/read_aloud.py --list-voices
```

| Flag | Purpose |
|------|---------|
| `--voice am_michael` | Kokoro voice (default narrator) |
| `--voice af_heart` | Warm female flagship voice |
| `--speed 0.95` | Speaking rate |
| `--force-ocr` | OCR scanned/image PDFs |
| `--repo hexgrad/Kokoro-82M` | Hugging Face model id |

## Sample

`samples/uno-guardians-treatment.pdf` — full film treatment (~1000 words).

## Agent workflow

1. Accept a PDF from the user.
2. Run `read_aloud.py` with Kokoro; write MP3 under `/opt/cursor/artifacts/`.
3. Share the audio for playback (full narration, not a short clip).
