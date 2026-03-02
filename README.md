## Overview

This project implements a domain-restricted web crawler to scrape the MITRE eCTF 2026 rules website and then processes the collected documentation using a locally hosted large language model (LLM) through Ollama. The goal is to convert unstructured technical documentation into structured, machine-readable JSON that captures page summaries, inferred CLI commands, protocol terms, and operational constraints.

The pipeline combines traditional scraping techniques with LLM-based semantic extraction to build a structured knowledge base from raw HTML documentation.

## Motivation

Technical documentation is often lengthy, semi-structured, and difficult to query programmatically. While basic scraping can collect text, it does not provide structured insights such as implicit command usage, ordering constraints, or protocol-level details. This project addresses that limitation by augmenting rule-based extraction with an LLM that enforces a strict JSON schema, enabling downstream automation and analysis.

## System Design

The system operates in two stages. First, a breadth-first crawler traverses links under the target domain, normalizes URLs, prevents duplicate queue entries, and exports each page as a Markdown file. The crawler maintains separate seen and queued sets to prevent redundant processing and uses rate limiting to avoid overloading the target server.

In the second stage, a post-processing pipeline reads the saved Markdown files and performs two types of extraction. A regex-based pass identifies explicit CLI commands and normalizes them to reduce duplication. Then, each page is sent to a locally hosted LLM via the Ollama API, which returns structured JSON containing a page category, a short summary, inferred commands, key protocol terms, and notes on constraints such as timeouts or ordering rules. The JSON output is validated against an expected schema before being written to disk.

This separation between scraping and semantic processing makes the pipeline idempotent and resumable. Previously processed pages are skipped, and extracted commands are consolidated into a deduplicated index.

Example Output

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

The crawler is implemented in Python using requests and BeautifulSoup for HTML retrieval and parsing. A deque is used for efficient breadth-first traversal, and duplicate URLs are prevented using a dedicated queued set. Markdown files are stored locally for reproducibility and offline processing.

The semantic extraction layer communicates with a local Ollama server using the /api/generate endpoint. The model runs with temperature set to zero to encourage deterministic outputs, and the response is parsed and validated before being written to .ollama.json files. Command strings are normalized using whitespace compression to reduce redundant entries.

## Installation and Usage (PowerShell)

Before running this project, make sure **Ollama is installed** on your system. Ollama can be downloaded from:

[https://ollama.com](https://ollama.com)

After installing Ollama, open **PowerShell** inside your project directory and follow these steps.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

You should now see `(.venv)` at the beginning of your prompt.



### 2. Install the package in editable mode

```powershell
pip install -e .
```

This installs `ectf-scrape` as a CLI command linked to your local source code.

Verify installation:

```powershell
ectf-scrape --help
```

If that runs successfully, the CLI is ready.



### 3. Start Ollama

In a separate PowerShell window:

```powershell
ollama serve
```

If you have not already pulled the model:

```powershell
ollama pull llama3.1:8b
```

Leave `ollama serve` running.



### 4. Run the full pipeline

Back in your project directory (with the virtual environment activated):

```powershell
ectf-scrape `
  --start "https://rules.ectf.mitre.org/2026/" `
  --out output `
  --max-pages 800 `
  --delay 0.5 `
  --ollama `
  --ollama-model "llama3.1:8b"
```

Note: PowerShell uses the backtick (`) for line continuation.

This command will:

* Crawl documentation pages
* Extract regex-based CLI commands
* Call Ollama locally
* Generate `.ollama.json` files
* Build a consolidated `commands.txt` index



## Relevance

This project demonstrates practical experience with web scraping, crawl-state management, regex-based extraction, API-based integration of a locally hosted LLM, structured JSON validation, and pipeline design. It reflects the ability to combine traditional engineering techniques with modern language models to automate technical documentation mining.


