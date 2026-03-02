import argparse
from pathlib import Path

from ectf_scrape.crawler import crawl_site


def main():
    p = argparse.ArgumentParser(
        prog="ectf-scrape",
        description="Crawl a docs site and extract commands + cleaned markdown pages (optional local LLM via Ollama).",
    )
    p.add_argument("--start", required=True, help="Start URL (e.g., https://rules.ectf.mitre.org/2026/)")
    p.add_argument("--out", default="output", help="Output directory")
    p.add_argument("--max-pages", type=int, default=500, help="Max pages to crawl")
    p.add_argument("--delay", type=float, default=0.6, help="Delay between requests (seconds)")
    p.add_argument("--same-domain-only", action="store_true", default=True, help="Stay within same domain")
    p.add_argument("--no-same-domain-only", dest="same_domain_only", action="store_false")
    p.add_argument("--include-fragments", action="store_true", default=False, help="Treat #anchors as distinct pages")

    # Local LLM
    p.add_argument("--ollama", action="store_true", default=False, help="Enable local LLM enrichment via Ollama")
    p.add_argument("--ollama-model", default="llama3.1:8b", help="Ollama model name (default: llama3.1:8b)")

    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    crawl_site(
        start_url=args.start,
        out_dir=out_dir,
        max_pages=args.max_pages,
        delay_s=args.delay,
        same_domain_only=args.same_domain_only,
        include_fragments=args.include_fragments,
        use_ollama=args.ollama,
        ollama_model=args.ollama_model,
    )