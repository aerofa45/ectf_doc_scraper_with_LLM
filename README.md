Here is the revised README with your “How to Run” section added in a clean, natural style consistent with the rest of the document.

---

# eCTF Documentation Scraper with LLM-Based Semantic Extraction

## Overview

This project implements a domain-restricted web crawler to scrape the MITRE eCTF 2026 rules website and then processes the collected documentation using a locally hosted large language model (LLM) through Ollama. The goal is to convert unstructured technical documentation into structured, machine-readable JSON that captures page summaries, inferred CLI commands, protocol terms, and operational constraints.

The pipeline combines traditional scraping techniques with LLM-based semantic extraction to build a structured knowledge base from raw HTML documentation.

## Motivation

Technical documentation is often lengthy, semi-structured, and difficult to query programmatically. While basic scraping can collect text, it does not provide structured insights such as implicit command usage, ordering constraints, or protocol-level details. This project addresses that limitation by augmenting rule-based extraction with an LLM that enforces a strict JSON schema, enabling downstream automation and analysis.

## System Design

The system operates in two stages. First, a breadth-first crawler traverses links under the target domain, normalizes URLs, prevents duplicate queue entries, and exports each page as a Markdown file. The crawler maintains separate `seen` and `queued` sets to prevent redundant processing and uses rate limiting to avoid overloading the target server.

In the second stage, a post-processing pipeline reads the saved Markdown files and performs two types of extraction. A regex-based pass identifies explicit CLI commands and normalizes them to reduce duplication. Then, each page is sent to a locally hosted LLM via the Ollama API, which returns structured JSON containing a page category, a short summary, inferred commands, key protocol terms, and notes on constraints such as timeouts or ordering rules. The JSON output is validated against an expected schema before being written to disk.

This separation between scraping and semantic processing makes the pipeline idempotent and resumable. Previously processed pages are skipped, and extracted commands are consolidated into a deduplicated index.

## Example Output

For each documentation page, the LLM generates a JSON object similar to the following:

{
"page_category": "remote_scenario",
"short_summary": [
"Describes TCP-based transfer interface",
"Explains 120-second execution window",
"Defines interrogate and receive command order"
],
"inferred_commands": [
"uvx ectf api remote connect <MGMT_PORT> <TRANSFER_PORT> <team>"
],
"key_terms": [
"interrogate",
"receive",
"transfer interface",
"slot"
],
"notes": [
"Scenario terminates after 120 seconds"
]
}

## Technical Details

The crawler is implemented in Python using `requests` and `BeautifulSoup` for HTML retrieval and parsing. A `deque` is used for efficient breadth-first traversal, and duplicate URLs are prevented using a dedicated `queued` set. Markdown files are stored locally for reproducibility and offline processing.

The semantic extraction layer communicates with a local Ollama server using the `/api/generate` endpoint. The model runs with temperature set to zero to encourage deterministic outputs, and the response is parsed and validated before being written to `.ollama.json` files. Command strings are normalized using whitespace compression to reduce redundant entries.

## How to Run

First install the required dependencies:

pip install -r requirements.txt

Start the Ollama server and pull the model:

ollama serve
ollama pull llama3.1:8b

Run the crawler to collect and store documentation pages:

python crawler.py

Finally, execute the LLM post-processing step to generate structured JSON outputs:

python postpass_ollama.py

## Relevance

This project demonstrates hands-on experience with web scraping, crawl-state management, regex-based extraction, API-based integration of locally hosted LLMs, structured JSON validation, and pipeline design. It reflects an understanding of how traditional software engineering techniques can be combined with modern language models to automate knowledge extraction from technical documentation.
