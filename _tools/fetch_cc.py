#!/usr/bin/env python3
"""Fetch a video's captions into a cleaned, citable transcript.

Retrieves the caption track for a URL (manual track preferred, auto-generated
fallback), flattens the rolling-cue VTT that YouTube emits, and writes a
markdown file holding source metadata plus the cleaned transcript.

Written for the cookbook workflow: the output is research material and belongs
in /tmp, never in the repository. Only the recipe .tex and .pdf enter the repo.

Usage:
    uv run _tools/fetch_cc.py <url> [--slug NAME] [--out DIR]
                             [--lang LANG] [--keep-music] [--quiet]

Output:
    <out>/<slug>-cc.md     metadata + cleaned transcript (default out: /tmp)
    <out>/<slug>.<lang>.vtt    the raw caption file, kept for traceability

Exit codes:
    0  transcript written
    1  no caption track produced (extractor changed, video has no captions,
       or yt-dlp is stale)
    2  yt-dlp not found on PATH
"""

import argparse
import datetime
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

DEFAULT_OUT = Path("/tmp")
DEFAULT_LANG = "en"
DEFAULT_SLUG = "captions"

# VTT furniture and YouTube's non-speech tokens.
VTT_HEADER_PREFIXES = ("WEBVTT", "Kind:", "Language:", "NOTE", "STYLE", "REGION")
TIMING_LINE = "-->"
TIMESTAMP_TAG = re.compile(r"<\d{2}:\d{2}:\d{2}\.\d{3}>")
ANY_TAG = re.compile(r"<[^>]*>")
NON_SPEECH_TOKEN = re.compile(r"\[[a-z][a-z ]*\]", re.IGNORECASE)

# A cue or metadata field is never this long; longer means the parse went wrong.
MAX_METADATA_LEN = 300


class FetchError(Exception):
    """Raised when caption retrieval fails in a way the operator must see."""


def run_yt_dlp(args: list[str]) -> str:
    """Invoke yt-dlp and return its stdout.

    Raises FetchError on a non-zero exit so a stale extractor surfaces as a
    failure rather than an empty transcript.
    """
    proc = subprocess.run(
        ["yt-dlp", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        detail = tail[-1] if tail else "no diagnostic output"
        raise FetchError(f"yt-dlp exited {proc.returncode}: {detail}")
    return proc.stdout


def slugify(text: str) -> str:
    """Reduce arbitrary text to a filesystem-safe slug."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return slug or DEFAULT_SLUG


def probe(url: str, lang: str) -> dict[str, str]:
    """Collect metadata and determine whether captions are manual or auto.

    yt-dlp lists manual tracks under "Available subtitles" and machine tracks
    under "Available automatic captions". Which section the language appears in
    decides the flag used to fetch it, because --write-subs alone returns
    nothing for a video that has only automatic captions.
    """
    field_template = "%(id)s\t%(title)s\t%(uploader)s\t%(duration)s\t%(upload_date)s"
    metadata_out = run_yt_dlp(
        ["--no-warnings", "--skip-download", "--print", field_template, url]
    )
    # Ignore any extractor chatter and take the first real field row.
    rows = [row for row in metadata_out.strip().splitlines() if row.strip() and not row.startswith("[")]
    if not rows:
        raise FetchError("yt-dlp returned no metadata for this URL")
    fields = rows[0].split("\t")
    video_id, title, uploader, duration, upload_date = (fields + [""] * 5)[:5]

    listing = run_yt_dlp(["--no-warnings", "--list-subs", url])
    track_kind = classify_track(listing, lang)

    return {
        "id": video_id,
        "title": title,
        "uploader": uploader,
        "duration": format_duration(duration),
        "upload_date": format_date(upload_date),
        "track_kind": track_kind,
        "url": url,
    }


def classify_track(listing: str, lang: str) -> str:
    """Return 'manual', 'auto', or 'none' for the requested language.

    yt-dlp prefixes its section headers with '[info] ', so match on content
    rather than line starts.
    """
    section = None
    manual = auto = False
    lang_column = re.compile(r"^" + re.escape(lang) + r"\s")
    for raw_line in listing.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "Available automatic captions" in line:
            section = "auto"
            continue
        if "Available subtitles" in line:
            section = "manual"
            continue
        if section and lang_column.match(line):
            if section == "manual":
                manual = True
            else:
                auto = True
    if manual:
        return "manual"
    if auto:
        return "auto"
    return "none"


def format_duration(seconds: str) -> str:
    """Render a duration in seconds as H:MM:SS or M:SS."""
    try:
        total = int(float(seconds))
    except (TypeError, ValueError):
        return "unknown"
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_date(raw: str) -> str:
    """Render yt-dlp's YYYYMMDD as YYYY-MM-DD."""
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return raw or "unknown"


def download_captions(url: str, slug: str, out_dir: Path, lang: str, kind: str) -> Path:
    """Fetch the caption track and return the path of the written VTT file."""
    flag = "--write-subs" if kind == "manual" else "--write-auto-subs"
    run_yt_dlp(
        [
            "--no-warnings",
            "--skip-download",
            flag,
            "--sub-langs",
            lang,
            "--sub-format",
            "vtt",
            "-o",
            str(out_dir / f"{slug}.%(ext)s"),
            url,
        ]
    )
    candidates = sorted(out_dir.glob(f"{slug}*.vtt"))
    if not candidates:
        raise FetchError(
            f"no caption file was written for language '{lang}'. The video may "
            "have no track in that language, or the extractor has changed. "
            "Update yt-dlp first, then re-run."
        )
    # Prefer the plain language file over regional variants when both exist.
    exact = [p for p in candidates if p.name == f"{slug}.{lang}.vtt"]
    return exact[0] if exact else candidates[0]


def flatten_vtt(vtt_text: str, keep_music: bool) -> tuple[str, dict[str, int]]:
    """Flatten YouTube's rolling-cue VTT into one readable transcript.

    Cues repeat the previous line as the next is revealed, so identical lines
    recur two or three times each. Exact-line dedupe removes that repetition.

    The dedupe is heuristic, not lossless: a line genuinely repeated verbatim in
    separate cues is kept only once. That trade is deliberate -- the repetition
    removed is two thirds of the file.
    """
    kept: list[str] = []
    seen: set[str] = set()
    raw_lines = 0
    dropped = 0

    for raw_line in vtt_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(VTT_HEADER_PREFIXES) or TIMING_LINE in line:
            continue
        # align:start position:0% and similar cue settings carry no speech.
        if line.startswith(("align:", "position:", "line:", "size:")):
            continue
        text = TIMESTAMP_TAG.sub("", line)
        text = ANY_TAG.sub("", text)
        if not keep_music:
            text = NON_SPEECH_TOKEN.sub("", text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        raw_lines += 1
        if text in seen:
            dropped += 1
            continue
        seen.add(text)
        kept.append(text)

    transcript = " ".join(kept)
    stats = {
        "raw_lines": raw_lines,
        "kept_lines": len(kept),
        "dropped_lines": dropped,
    }
    return transcript, stats


def build_markdown(meta: dict[str, str], transcript: str, stats: dict[str, int], vtt_path: Path) -> str:
    """Compose the transcript file: provenance first, then the flattened text."""
    kind = meta["track_kind"]
    if kind == "manual":
        provenance = "human-authored caption track"
        caveats = [
            "Punctuation and casing are approximate; wording follows the caption track.",
            "Quantities appear only where the speaker states them aloud.",
        ]
    else:
        provenance = "auto-generated caption track"
        caveats = [
            "Punctuation and casing are approximate, and proper nouns are frequently mangled.",
            "Quantities appear only where the speaker states them aloud; everything else is inferred, not sourced.",
        ]
    caveat_lines = "\n".join(f"- {item}" for item in caveats)

    return f"""# Source captions — {meta['title']}

**Source:** {meta['uploader']}
**URL:** {meta['url']}
**Duration:** {meta['duration']} · **Published:** {meta['upload_date']}
**Captions:** YouTube {provenance}, retrieved {datetime.date.today().isoformat()}
**Raw caption file:** `{vtt_path}`
**Flattening:** {stats['raw_lines']} raw cue lines reduced to {stats['kept_lines']} ({stats['dropped_lines']} exact duplicates dropped)

## Read this as evidence, not instruction

{caveat_lines}
- Recipe fidelity: reproduce the source as given and correct only clear errors.
- This file is research material. It is ephemeral and lives outside the repository by design.

## Transcript

{transcript}
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and flatten a video's captions into a citable transcript.",
    )
    parser.add_argument("url", help="video URL")
    parser.add_argument("--slug", default=None, help="output filename stem (default: derived from the title)")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help=f"output directory (default: {DEFAULT_OUT})")
    parser.add_argument("--lang", default=DEFAULT_LANG, help=f"caption language (default: {DEFAULT_LANG})")
    parser.add_argument("--keep-music", action="store_true", help="keep [music]-style non-speech tokens")
    parser.add_argument("--quiet", action="store_true", help="suppress progress output")
    return parser.parse_args(argv)


def progress(message: str, quiet: bool) -> None:
    """Emit progress on stderr, keeping stdout to the result path alone."""
    if not quiet:
        print(message, file=sys.stderr)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if shutil.which("yt-dlp") is None:
        print("error: yt-dlp is not on PATH. Install it with `uv tool install yt-dlp`.", file=sys.stderr)
        return 2

    out_dir = Path(args.out).expanduser().resolve()
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"error: cannot create output directory {out_dir}: {exc}", file=sys.stderr)
        return 1

    try:
        progress(f"probing {args.url}", args.quiet)
        meta = probe(args.url, args.lang)

        if meta["track_kind"] == "none":
            raise FetchError(
                f"no captions in language '{args.lang}'. Try another --lang, or "
                "confirm the video has captions at all."
            )

        slug = slugify(args.slug or meta["title"])
        if len(meta["title"]) > MAX_METADATA_LEN:
            raise FetchError("metadata field implausibly long; extractor output is not as expected")

        progress(f"caption track: {meta['track_kind']}", args.quiet)
        vtt_path = download_captions(args.url, slug, out_dir, args.lang, meta["track_kind"])

        transcript, stats = flatten_vtt(vtt_path.read_text(encoding="utf-8"), args.keep_music)
        if not transcript:
            raise FetchError(f"caption file {vtt_path} contained no usable text")

        md_path = out_dir / f"{slug}-cc.md"
        md_path.write_text(build_markdown(meta, transcript, stats, vtt_path), encoding="utf-8")
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    progress(f"flattened {stats['raw_lines']} cue lines to {stats['kept_lines']}", args.quiet)
    print(md_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
