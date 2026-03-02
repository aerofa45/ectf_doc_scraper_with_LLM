from __future__ import annotations

import re
from typing import Tuple
from bs4 import BeautifulSoup

COMMAND_PATTERNS = [
    r"^\s*uvx\s+ectf\b.*$",
    r"^\s*ectf\b.*$",
    r"^\s*python(\.exe)?\s+.*\.py\b.*$",
    r"^\s*docker\s+run\b.*$",
    r"^\s*docker\s+build\b.*$",
    r"^\s*make\b.*$",
    r"^\s*openocd\b.*$",
    r"^\s*arm-none-eabi-gdb\b.*$",
    r"^\s*gdb\b.*$",
    r"^\s*git\b.*$",
    r"^\s*curl\b.*$",
    r"^\s*wget\b.*$",
]

CMD_RE = re.compile("|".join(f"(?:{p})" for p in COMMAND_PATTERNS), re.IGNORECASE)


def _pick_main_container(soup: BeautifulSoup):
    candidates = [
        soup.select_one("main"),
        soup.select_one("div[role='main']"),
        soup.select_one("div.document"),
        soup.select_one("div.md-content"),
        soup.select_one("article"),
    ]
    for c in candidates:
        if c and c.get_text(strip=True):
            return c
    return soup.body or soup


def _clean_text_for_md(text: str) -> str:
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def extract_page_content(html: str, base_url: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    title = (soup.title.get_text(strip=True) if soup.title else base_url).strip()

    main = _pick_main_container(soup)

    for sel in ["nav", "header", "footer", "aside", "script", "style"]:
        for tag in main.select(sel):
            tag.decompose()

    code_blocks = []
    for pre in main.select("pre"):
        code = pre.get_text("\n", strip=False).rstrip()
        if code:
            code_blocks.append(code)

    text = main.get_text("\n", strip=True)
    text = _clean_text_for_md(text)

    md_parts = [f"# {title}\n", f"Source: {base_url}\n\n", "## Text\n\n", text, "\n"]
    if code_blocks:
        md_parts.append("\n## Code blocks\n\n")
        for cb in code_blocks:
            md_parts.append("```text\n")
            md_parts.append(cb.rstrip() + "\n")
            md_parts.append("```\n\n")

    md = "".join(md_parts)
    return title, md


def extract_commands_from_text(text: str) -> list[str]:
    cmds = []
    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if CMD_RE.search(line):
            norm = re.sub(r"\s+", " ", line).strip()
            if len(norm) >= 8:
                cmds.append(norm)

    seen = set()
    out = []
    for c in cmds:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out