#!/usr/bin/env python3
"""Build resume.html + resume.pdf from resume.yaml."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
RESUME_YAML = ROOT / "resume.yaml"
RESUME_EXAMPLE = ROOT / "resume.example.yaml"
PHOTO = ROOT / "photo.png"
PHOTO_EXAMPLE = ROOT / "photo.example.png"
PDF = ROOT / "resume.pdf"
CHROME_CANDIDATES = [
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    Path("/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"),
]


def md(text: str | None) -> Markup:
    """Inline markdown: **bold**, *italic*, ***both***, __underline__, ~~strike~~."""
    if not text:
        return Markup("")
    escaped = str(Markup.escape(text))
    escaped = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"~~(.+?)~~", r"<s>\1</s>", escaped)
    escaped = re.sub(r"__(.+?)__", r"<u>\1</u>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    return Markup(escaped)


def find_chrome() -> Path | None:
    for path in CHROME_CANDIDATES:
        if path.exists():
            return path
    return shutil.which("google-chrome") and Path(shutil.which("google-chrome"))


def copy_if_missing(src: Path, dst: Path) -> bool:
    if dst.exists() or not src.exists():
        return False
    shutil.copy(src, dst)
    print(f"Created {dst.name} from {src.name}")
    return True


def bootstrap_user_files() -> None:
    copy_if_missing(RESUME_EXAMPLE, RESUME_YAML)
    copy_if_missing(PHOTO_EXAMPLE, PHOTO)
    if not RESUME_YAML.exists():
        raise SystemExit("resume.yaml not found. Copy resume.example.yaml to resume.yaml and edit it.")


def render_html(data: dict) -> str:
    env = Environment(loader=FileSystemLoader(ROOT), autoescape=True)
    env.filters["md"] = md
    page1 = [job for job in data["experience"] if job.get("page", 1) == 1]
    page2 = [job for job in data["experience"] if job.get("page", 1) == 2]
    photo = ROOT / data["photo"]
    css = ROOT / "styles.css"
    return env.get_template("template.html").render(
        **data,
        page1_jobs=page1,
        page2_jobs=page2,
        photo_uri=photo.resolve().as_uri() if photo.exists() else None,
        css_uri=css.resolve().as_uri(),
    )


def write_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = find_chrome()
    if chrome is None:
        raise SystemExit(
            "Chrome not found. Open dist/resume.html and print to PDF, "
            "or install Google Chrome."
        )
    cmd = [
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--no-margins",
        "--virtual-time-budget=8000",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build resume HTML and PDF")
    parser.add_argument("--html-only", action="store_true")
    args = parser.parse_args()

    bootstrap_user_files()
    data = yaml.safe_load(RESUME_YAML.read_text())
    DIST.mkdir(exist_ok=True)
    html_path = DIST / "resume.html"
    html_path.write_text(render_html(data), encoding="utf-8")
    print(f"HTML: {html_path}")

    if args.html_only:
        return

    write_pdf(html_path, PDF)
    print(f"PDF:  {PDF}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr.decode() if exc.stderr else str(exc))
        raise SystemExit(1)
