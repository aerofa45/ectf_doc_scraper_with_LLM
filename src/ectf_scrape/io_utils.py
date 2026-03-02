from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse


def slugify_url(url: str) -> str:
    p = urlparse(url)
    path = p.path.strip("/") or "root"
    slug = f"{p.netloc}_{path}"
    slug = slug.replace("/", "_")
    slug = re.sub(r"[^a-zA-Z0-9_\-\.]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug[:180]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")