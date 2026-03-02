from __future__ import annotations

import json
import time
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urldefrag, urlparse

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from tqdm import tqdm

from ectf_scrape.extract import extract_page_content, extract_commands_from_text
from ectf_scrape.io_utils import slugify_url, write_text
from ectf_scrape.ollama_processor import ollama_available, process_with_ollama

console = Console()
USER_AGENT = "ectf-scrape/0.2 (respectful crawler; docs indexing)"


@dataclass
class PageResult:
    url: str
    title: str
    out_path: str
    num_commands: int
    ollama_path: Optional[str] = None


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def _is_same_domain(url: str, base: str) -> bool:
    return urlparse(url).netloc == urlparse(base).netloc


def _normalize_url(href: str, base_url: str, include_fragments: bool) -> Optional[str]:
    if not href:
        return None
    href = href.strip()
    if href.startswith(("mailto:", "javascript:", "tel:")):
        return None

    abs_url = urljoin(base_url, href)
    if not include_fragments:
        abs_url, _ = urldefrag(abs_url)
    return abs_url


def _extract_links(html: str, base_url: str, include_fragments: bool) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.select("a[href]"):
        u = _normalize_url(a.get("href", ""), base_url, include_fragments)
        if u:
            links.append(u)

    seen = set()
    out = []
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _fetch_html(sess: requests.Session, url: str, timeout_s: float = 20.0) -> str:
    r = sess.get(url, timeout=timeout_s)
    r.raise_for_status()

    ctype = (r.headers.get("Content-Type") or "").lower()
    if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
        return ""
    return r.text


def crawl_site(
    start_url: str,
    out_dir: Path,
    max_pages: int = 500,
    delay_s: float = 0.6,
    same_domain_only: bool = True,
    include_fragments: bool = False,
    use_ollama: bool = False,
    ollama_model: str = "llama3.1:8b",
) -> None:
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    sess = _session()

    queue: list[str] = [start_url]
    seen: set[str] = set()
    results: list[PageResult] = []
    all_commands: set[str] = set()

    ollama_ok = use_ollama and ollama_available()
    if use_ollama and not ollama_ok:
        console.print("[yellow]Ollama not detected on http://localhost:11434. Continuing without LLM outputs.[/yellow]")

    pbar = tqdm(total=max_pages, desc="Crawling", unit="page")

    while queue and len(results) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)

        if same_domain_only and not _is_same_domain(url, start_url):
            continue

        if re.search(r"\.(pdf|png|jpg|jpeg|gif|svg|zip|tar|gz|7z|exe|bin)$", url, re.IGNORECASE):
            continue

        try:
            html = _fetch_html(sess, url)
            if not html:
                continue

            title, md = extract_page_content(html, base_url=url)

            cmds = extract_commands_from_text(md)
            for c in cmds:
                all_commands.add(c)

            slug = slugify_url(url)
            out_path = pages_dir / f"{slug}.md"
            write_text(out_path, md)

            ollama_path_str: Optional[str] = None
            if ollama_ok:
                llm_obj = process_with_ollama(md, model=ollama_model)
                ollama_path = pages_dir / f"{slug}.ollama.json"
                ollama_path.write_text(json.dumps(llm_obj, indent=2), encoding="utf-8")
                ollama_path_str = str(ollama_path)

                # Also merge any inferred commands into global command list
                for c in llm_obj.get("inferred_commands", []) or []:
                    if isinstance(c, str) and len(c.strip()) >= 6:
                        all_commands.add(re.sub(r"\s+", " ", c).strip())

            links = _extract_links(html, url, include_fragments)
            for u in links:
                if u not in seen and (not same_domain_only or _is_same_domain(u, start_url)):
                    if re.search(r"\.(pdf|png|jpg|jpeg|gif|svg|zip|tar|gz|7z|exe|bin)$", u, re.IGNORECASE):
                        continue
                    queue.append(u)

            results.append(PageResult(url=url, title=title, out_path=str(out_path), num_commands=len(cmds), ollama_path=ollama_path_str))

        except requests.HTTPError as e:
            console.print(f"[yellow]HTTP error[/yellow] {url}: {e}")
        except requests.RequestException as e:
            console.print(f"[yellow]Request error[/yellow] {url}: {e}")
        except Exception as e:
            console.print(f"[red]Error[/red] {url}: {e}")

        pbar.update(1)
        time.sleep(max(0.0, delay_s))

    pbar.close()

    commands_path = out_dir / "commands.txt"
    sorted_cmds = sorted(all_commands)
    write_text(commands_path, "\n".join(sorted_cmds) + ("\n" if sorted_cmds else ""))

    index_path = out_dir / "index.json"
    index_obj = {
        "start_url": start_url,
        "crawled_pages": len(results),
        "ollama_enabled": bool(ollama_ok),
        "pages": [
            {
                "url": r.url,
                "title": r.title,
                "out_path": r.out_path,
                "num_commands": r.num_commands,
                "ollama_path": r.ollama_path,
            }
            for r in results
        ],
    }
    index_path.write_text(json.dumps(index_obj, indent=2), encoding="utf-8")

    console.print(f"[green]Done.[/green] Pages: {len(results)}")
    console.print(f"[green]Wrote[/green] {commands_path}")
    console.print(f"[green]Wrote[/green] {index_path}")