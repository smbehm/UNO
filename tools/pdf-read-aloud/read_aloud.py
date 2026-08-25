#!/usr/bin/env python3
"""Extract text from a PDF and narrate it with natural neural TTS.

Outputs an MP3 (and optional VTT cues) suitable for playback in Cursor artifacts.
Uses Microsoft Edge neural voices via edge-tts — no API key required.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"
# Slightly slower reads feel more natural for long-form narration.
DEFAULT_RATE = "-8%"
DEFAULT_PITCH = "+0Hz"
# Soft ceiling per TTS request; paragraphs are kept intact when possible.
MAX_CHUNK_CHARS = 2800
MIN_TEXT_CHARS_FOR_NATIVE = 40


def extract_text_pypdf(pdf_path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


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
    """OCR fallback for scanned/image PDFs (requires poppler + tesseract)."""
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

        pages = sorted(tmp_path.glob("page-*.png"))
        texts: list[str] = []
        for page in pages:
            out = subprocess.run(
                ["tesseract", str(page), "stdout", "-l", "eng", "--psm", "1"],
                check=False,
                capture_output=True,
                text=True,
            )
            if out.returncode == 0 and out.stdout.strip():
                texts.append(out.stdout.strip())
        return "\n\n".join(texts)


def extract_pdf_text(pdf_path: Path, force_ocr: bool = False, ocr_max_pages: int | None = None) -> str:
    if force_ocr:
        text = extract_text_ocr(pdf_path, ocr_max_pages)
        if text.strip():
            return text
        raise RuntimeError("OCR produced no text (is tesseract/poppler installed?)")

    candidates = [
        extract_text_pdftotext(pdf_path),
        extract_text_pypdf(pdf_path),
    ]
    best = max(candidates, key=lambda t: len(re.sub(r"\s+", "", t or "")))
    if len(re.sub(r"\s+", "", best)) >= MIN_TEXT_CHARS_FOR_NATIVE:
        return best

    ocr = extract_text_ocr(pdf_path, ocr_max_pages)
    if ocr.strip():
        return ocr
    return best


def clean_narration_text(raw: str) -> str:
    """Normalize PDF extraction artifacts into speakable prose."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Join hyphenated line breaks: "swim-\ning" -> "swimming"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Collapse soft wrap newlines inside paragraphs into spaces
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            cleaned_lines.append("")
            continue
        # Drop lone page numbers / running folio lines
        if re.fullmatch(r"\d{1,4}", s):
            continue
        if re.fullmatch(r"(?i)page\s+\d+(\s+of\s+\d+)?", s):
            continue
        cleaned_lines.append(s)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def split_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        # Oversized paragraph: split on sentences
        pieces = [para] if len(para) <= max_chars else _split_sentences(para, max_chars)
        for piece in pieces:
            if not current:
                current = piece
            elif len(current) + 2 + len(piece) <= max_chars:
                current = f"{current}\n\n{piece}"
            else:
                chunks.append(current)
                current = piece
    if current:
        chunks.append(current)
    return chunks


def _split_sentences(text: str, max_chars: int) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for part in parts:
        if not current:
            current = part
        elif len(current) + 1 + len(part) <= max_chars:
            current = f"{current} {part}"
        else:
            chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    # Hard-wrap any remaining giants
    final: list[str] = []
    for c in chunks:
        if len(c) <= max_chars:
            final.append(c)
        else:
            for i in range(0, len(c), max_chars):
                final.append(c[i : i + max_chars])
    return final


async def synthesize_chunk(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    out_path: Path,
) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(str(out_path))


async def synthesize_document(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    out_mp3: Path,
    work_dir: Path,
) -> int:
    chunks = split_into_chunks(text)
    if not chunks:
        raise RuntimeError("No speakable text after cleanup.")

    part_paths: list[Path] = []
    for i, chunk in enumerate(chunks):
        part = work_dir / f"part-{i:04d}.mp3"
        await synthesize_chunk(chunk, voice, rate, pitch, part)
        part_paths.append(part)
        # Brief pause between paragraphs/sections for natural pacing
        if i < len(chunks) - 1:
            silence = work_dir / f"silence-{i:04d}.mp3"
            _write_silence_mp3(silence, duration_ms=320)
            part_paths.append(silence)

    _concat_mp3(part_paths, out_mp3)
    return len(chunks)


def _write_silence_mp3(path: Path, duration_ms: int = 320) -> None:
    # Generate tiny silence with ffmpeg so concat stays in one container format.
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=24000:cl=mono",
            "-t",
            f"{duration_ms / 1000:.3f}",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "48k",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def _concat_mp3(parts: list[Path], out_path: Path) -> None:
    """Concatenate parts (or re-encode a single part) to a clear 192k MP3."""
    list_file = out_path.with_suffix(".concat.txt")
    list_file.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
                str(out_path),
            ],
            check=True,
            capture_output=True,
        )
    finally:
        list_file.unlink(missing_ok=True)


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
        description="Read a PDF aloud with natural neural TTS (edge-tts)."
    )
    p.add_argument(
        "pdf",
        type=Path,
        nargs="?",
        default=None,
        help="Path to the PDF file",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output MP3 path (default: <pdf-stem>-narration.mp3)",
    )
    p.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"edge-tts voice (default: {DEFAULT_VOICE})",
    )
    p.add_argument("--rate", default=DEFAULT_RATE, help='Speaking rate, e.g. "-8%"')
    p.add_argument("--pitch", default=DEFAULT_PITCH, help='Pitch, e.g. "+0Hz"')
    p.add_argument(
        "--text-out",
        type=Path,
        default=None,
        help="Also write the cleaned narration text to this path",
    )
    p.add_argument(
        "--force-ocr",
        action="store_true",
        help="Force OCR even if the PDF has extractable text",
    )
    p.add_argument(
        "--ocr-max-pages",
        type=int,
        default=None,
        help="Limit OCR to the first N pages (useful for large scans)",
    )
    p.add_argument(
        "--list-voices",
        action="store_true",
        help="List recommended English narration voices and exit",
    )
    return p.parse_args(argv)


async def list_recommended_voices() -> None:
    import edge_tts

    prefer = [
        "en-US-AndrewMultilingualNeural",
        "en-US-AvaMultilingualNeural",
        "en-US-EmmaMultilingualNeural",
        "en-US-BrianMultilingualNeural",
        "en-US-AndrewNeural",
        "en-US-AriaNeural",
        "en-GB-SoniaNeural",
        "en-GB-RyanNeural",
        "en-AU-NatashaNeural",
    ]
    voices = {v["ShortName"]: v for v in await edge_tts.list_voices()}
    for name in prefer:
        v = voices.get(name)
        if v:
            print(f"{v['ShortName']:40} {v['Locale']:8} {v['Gender']}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list_voices:
        asyncio.run(list_recommended_voices())
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
        f"Narrating ~{words} words with {args.voice} (rate {args.rate}) ...",
        flush=True,
    )

    with tempfile.TemporaryDirectory(prefix="pdf-tts-") as tmp:
        chunks = asyncio.run(
            synthesize_document(
                text,
                voice=args.voice,
                rate=args.rate,
                pitch=args.pitch,
                out_mp3=out_mp3,
                work_dir=Path(tmp),
            )
        )

    duration = probe_duration_seconds(out_mp3)
    dur_msg = f", {duration:.1f}s" if duration is not None else ""
    print(f"Done: {out_mp3} ({chunks} chunk(s){dur_msg})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
