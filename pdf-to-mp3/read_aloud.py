#!/usr/bin/env python3
"""Extract text from a PDF and narrate it with Hugging Face Kokoro-82M TTS."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_VOICE = "am_michael"
DEFAULT_SPEED = 0.95
DEFAULT_REPO = "hexgrad/Kokoro-82M"
DEFAULT_LANG = "a"
MIN_TEXT_CHARS_FOR_NATIVE = 40
SAMPLE_RATE = 24000


def extract_text_pypdf(pdf_path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def extract_text_pdftotext(pdf_path: Path) -> str:
    if not shutil.which("pdftotext"):
        return ""
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else ""


def extract_text_ocr(pdf_path: Path, max_pages: int | None = None) -> str:
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        return ""

    with tempfile.TemporaryDirectory(prefix="pdf-ocr-") as tmp:
        tmp_path = Path(tmp)
        prefix = tmp_path / "page"
        cmd = ["pdftoppm", "-png", "-r", "200", str(pdf_path), str(prefix)]
        if max_pages is not None:
            cmd[1:1] = ["-f", "1", "-l", str(max_pages)]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            return ""

        texts: list[str] = []
        for page in sorted(tmp_path.glob("page-*.png")):
            out = subprocess.run(
                ["tesseract", str(page), "stdout", "-l", "eng", "--psm", "1"],
                check=False,
                capture_output=True,
                text=True,
            )
            if out.returncode == 0 and out.stdout.strip():
                texts.append(out.stdout.strip())
        return "\n\n".join(texts)


def extract_pdf_text(
    pdf_path: Path, force_ocr: bool = False, ocr_max_pages: int | None = None
) -> str:
    if force_ocr:
        text = extract_text_ocr(pdf_path, ocr_max_pages)
        if text.strip():
            return text
        raise RuntimeError("OCR produced no text (is tesseract/poppler installed?)")

    candidates = [extract_text_pdftotext(pdf_path), extract_text_pypdf(pdf_path)]
    best = max(candidates, key=lambda t: len(re.sub(r"\s+", "", t or "")))
    if len(re.sub(r"\s+", "", best)) >= MIN_TEXT_CHARS_FOR_NATIVE:
        return best

    ocr = extract_text_ocr(pdf_path, ocr_max_pages)
    return ocr if ocr.strip() else best


def clean_narration_text(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    cleaned: list[str] = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            cleaned.append("")
            continue
        if re.fullmatch(r"\d{1,4}", s):
            continue
        if re.fullmatch(r"(?i)page\s+\d+(\s+of\s+\d+)?", s):
            continue
        cleaned.append(s)

    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned)).strip()


def synthesize_kokoro(
    text: str,
    voice: str,
    speed: float,
    lang_code: str,
    repo_id: str,
    out_wav: Path,
) -> int:
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    print(f"Loading Hugging Face model {repo_id} ...", flush=True)
    pipeline = KPipeline(lang_code=lang_code, repo_id=repo_id)

    chunks: list = []
    segments = 0
    generator = pipeline(
        text,
        voice=voice,
        speed=speed,
        split_pattern=r"\n+",
    )
    for i, (gs, _ps, audio) in enumerate(generator):
        segments += 1
        preview = (gs or "").replace("\n", " ")[:72]
        print(f"  segment {i + 1}: {preview}...", flush=True)
        chunks.append(audio)
        chunks.append(np.zeros(int(SAMPLE_RATE * 0.28), dtype=np.float32))

    if not chunks:
        raise RuntimeError("Kokoro produced no audio")

    audio = np.concatenate(chunks)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_wav), audio, SAMPLE_RATE)
    return segments


def wav_to_mp3(wav_path: Path, mp3_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(wav_path),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(mp3_path),
        ],
        check=True,
        capture_output=True,
    )


def probe_duration_seconds(path: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Read a PDF aloud with Hugging Face Kokoro-82M TTS."
    )
    p.add_argument("pdf", type=Path, nargs="?", default=None, help="Path to the PDF")
    p.add_argument("-o", "--output", type=Path, default=None, help="Output MP3 path")
    p.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Kokoro voice id (default: {DEFAULT_VOICE})",
    )
    p.add_argument(
        "--speed",
        type=float,
        default=DEFAULT_SPEED,
        help=f"Speaking speed (default: {DEFAULT_SPEED})",
    )
    p.add_argument(
        "--lang",
        default=DEFAULT_LANG,
        help="Kokoro lang_code: a=American, b=British (default: a)",
    )
    p.add_argument("--repo", default=DEFAULT_REPO, help="Hugging Face model repo id")
    p.add_argument("--text-out", type=Path, default=None, help="Write cleaned text here")
    p.add_argument("--force-ocr", action="store_true")
    p.add_argument("--ocr-max-pages", type=int, default=None)
    p.add_argument(
        "--list-voices",
        action="store_true",
        help="List recommended Kokoro English voices and exit",
    )
    p.add_argument(
        "--keep-wav",
        action="store_true",
        help="Also keep the intermediate WAV next to the MP3",
    )
    return p.parse_args(argv)


RECOMMENDED_VOICES = [
    ("am_michael", "American male — clear narrator"),
    ("am_fenrir", "American male — deeper"),
    ("am_adam", "American male"),
    ("af_heart", "American female — warm (flagship)"),
    ("af_bella", "American female"),
    ("af_sarah", "American female"),
    ("af_nicole", "American female"),
    ("bm_george", "British male"),
    ("bm_fable", "British male"),
    ("bf_emma", "British female"),
    ("bf_isabella", "British female"),
]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list_voices:
        for vid, desc in RECOMMENDED_VOICES:
            print(f"{vid:16}  {desc}")
        print(f"\nModel: {DEFAULT_REPO} (Hugging Face)")
        return 0

    if args.pdf is None:
        print("error: PDF path is required (or pass --list-voices)", file=sys.stderr)
        return 1

    pdf_path: Path = args.pdf
    if not pdf_path.is_file():
        print(f"error: PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    out_mp3 = args.output or pdf_path.with_name(f"{pdf_path.stem}-narration.mp3")
    out_mp3.parent.mkdir(parents=True, exist_ok=True)

    print(f"Extracting text from {pdf_path} ...", flush=True)
    raw = extract_pdf_text(
        pdf_path, force_ocr=args.force_ocr, ocr_max_pages=args.ocr_max_pages
    )
    text = clean_narration_text(raw)
    if not text:
        print("error: no text could be extracted from the PDF", file=sys.stderr)
        return 2

    if args.text_out:
        args.text_out.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote cleaned text → {args.text_out}")

    words = len(re.findall(r"\S+", text))
    print(
        f"Narrating ~{words} words with HF/{args.repo} voice={args.voice} speed={args.speed} ...",
        flush=True,
    )

    with tempfile.TemporaryDirectory(prefix="pdf-kokoro-") as tmp:
        wav_path = Path(tmp) / "narration.wav"
        segments = synthesize_kokoro(
            text,
            voice=args.voice,
            speed=args.speed,
            lang_code=args.lang,
            repo_id=args.repo,
            out_wav=wav_path,
        )
        if args.keep_wav:
            kept = out_mp3.with_suffix(".wav")
            shutil.copyfile(wav_path, kept)
            print(f"Kept WAV → {kept}")
        print(f"Encoding MP3 → {out_mp3} ...", flush=True)
        wav_to_mp3(wav_path, out_mp3)

    duration = probe_duration_seconds(out_mp3)
    dur_msg = f", {duration / 60:.1f} min" if duration and duration >= 60 else (
        f", {duration:.1f}s" if duration else ""
    )
    print(f"Done: {out_mp3} ({segments} segment(s){dur_msg})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
