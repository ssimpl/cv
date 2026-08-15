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


def as_text(value: object) -> str:
    """YAML `key: value` bullets become maps; flatten them back to a line."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "; ".join(f"{k}: {as_text(v)}" for k, v in value.items())
    if isinstance(value, list):
        return "; ".join(as_text(item) for item in value)
    return str(value)


def md(text: object) -> Markup:
    """Inline markdown: **bold**, *italic*, ***both***, __underline__, ~~strike~~."""
    raw = as_text(text)
    if not raw:
        return Markup("")
    escaped = str(Markup.escape(raw))
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


def paragraphs(value: object) -> list[str]:
    """Split summary into paragraphs: a YAML list, or blank lines in a string."""
    if not value:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(paragraphs(item))
        return out
    text = as_text(value).strip()
    parts = re.split(r"\n\s*\n", text)
    return [re.sub(r"[ \t]*\n[ \t]*", " ", p).strip() for p in parts if p.strip()]


LEVEL_DOTS = {
    "native": 5,
    "bilingual": 5,
    "fluent": 5,
    "c2": 5,
    "advanced": 4,
    "proficient": 4,
    "c1": 4,
    "intermediate": 3,
    "upper-intermediate": 3,
    "b2": 3,
    "b1": 3,
    "elementary": 2,
    "pre-intermediate": 2,
    "a2": 2,
    "beginner": 1,
    "basic": 1,
    "a1": 1,
}


def language_dots(lang: dict) -> int:
    if "dots" in lang:
        return max(0, min(5, int(lang["dots"])))
    level = re.sub(r"[\s_]+", "-", str(lang.get("level", "")).casefold().strip())
    return LEVEL_DOTS.get(level, 4)


def normalize_languages(langs: object) -> list[dict]:
    if not langs or not isinstance(langs, list):
        return []
    out = []
    for lang in langs:
        if not isinstance(lang, dict):
            lang = {"name": as_text(lang), "level": ""}
        out.append({
            "name": as_text(lang.get("name", "")),
            "level": as_text(lang.get("level", "")),
            "dots": language_dots(lang),
        })
    return out


def parse_page(value: object, default: int = 1) -> int:
    if value is None or value == "":
        return default
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return n if n >= 1 else 1


def _edu_position(value: object, default: str = "left") -> str:
    if value is None or value == "":
        return default
    return "right" if str(value).strip().lower() == "right" else "left"


def normalize_education(raw: object, fallback_position: str = "left") -> dict:
    items: list = []
    position = _edu_position(fallback_position)
    page = 1

    if isinstance(raw, list):
        items = [item for item in raw if isinstance(item, dict)]
    elif isinstance(raw, dict):
        position = _edu_position(raw.get("position"), position)
        page = parse_page(raw.get("page"), 1)
        nested = raw.get("items")
        if isinstance(nested, list):
            items = [item for item in nested if isinstance(item, dict)]

    return {"entries": items, "position": position, "page": page}


def group_jobs_by_page(experience: object) -> dict[int, list]:
    grouped: dict[int, list] = {}
    for job in experience or []:
        if not isinstance(job, dict):
            continue
        grouped.setdefault(parse_page(job.get("page")), []).append(job)
    return grouped


def main_column_sections(experience: object, edu: dict) -> list[dict]:
    grouped = group_jobs_by_page(experience)
    edu_left = bool(edu.get("entries") and edu.get("position") == "left")
    pages = set(grouped)
    if edu_left:
        pages.add(int(edu["page"]))
    sections: list[dict] = []
    current = 1
    for page in sorted(pages):
        jobs = grouped.get(page, [])
        breaks = max(0, page - current)
        if jobs:
            sections.append({"kind": "experience", "jobs": jobs, "breaks": breaks})
            current = page
            if edu_left and edu["page"] == page:
                sections.append({"kind": "education", "breaks": 0})
        elif edu_left and edu["page"] == page:
            sections.append({"kind": "education", "breaks": breaks})
            current = page
    return sections


def render_html(data: dict) -> str:
    env = Environment(loader=FileSystemLoader(ROOT), autoescape=True)
    env.filters["md"] = md
    photo = ROOT / data["photo"]
    css = ROOT / "styles.css"
    fallback_position = str(
        data.get("education_position", data.get("education_column", "left"))
    )
    edu = normalize_education(data.get("education"), fallback_position)
    ctx = {
        **data,
        "summary_paragraphs": paragraphs(data.get("summary")),
        "languages": normalize_languages(data.get("languages")),
        "edu": edu,
        "main_sections": main_column_sections(data.get("experience"), edu),
        "photo_uri": photo.resolve().as_uri() if photo.exists() else None,
        "css_uri": css.resolve().as_uri(),
    }
    return env.get_template("template.html").render(ctx)


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
