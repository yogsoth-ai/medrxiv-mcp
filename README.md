# medrxiv-mcp

**MCP server that turns a medRxiv DOI into clean markdown full text — plus free, relevance-ranked preprint search.**

- 📄 **Full-text retrieval** — give it a DOI, get the whole paper as clean markdown (sections, tables, figure captions)
- 🔍 **Free search** — relevance-ranked medRxiv search via Europe PMC, returns DOI + title + abstract + date
- 🩺 **Source of truth** — full text comes from the official medRxiv `.meca` Text-and-Data-Mining archive, not scraped HTML
- ⚡ **Lazy local index** — a DOI→file index is built on demand and cached in sqlite, so repeat fetches in a month are instant
- 🔓 **Your data, your key** — full text reads a Requester-Pays S3 bucket with **your own** AWS key; nothing is shipped or shared

> bioRxiv has its own package: [`biorxiv-mcp`](https://github.com/yogsoth-ai/biorxiv-mcp).

## What is this?

This is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI assistants the full text of medRxiv preprints. Search is free (via the [Europe PMC](https://europepmc.org) REST API). Full text is resolved from the official `s3://medrxiv-src-monthly` archive: the server maps a DOI to its month, scans that month's `.meca` archives once to build a local DOI→file index, downloads the one matching archive, extracts its JATS XML, and converts it to GitHub-flavored markdown with pandoc.

Designed for AI assistants like Claude to read primary literature directly. Works with any MCP-compatible client (Claude Desktop, Claude Code, or custom integrations).

## Installation

```bash
uvx --from git+https://github.com/yogsoth-ai/medrxiv-mcp medrxiv-mcp
```

No manual install needed — `uvx` fetches and runs it. The bundled pandoc binary ships with the package, so you do **not** need a system pandoc.

## Quick Start

### 1. Add to your MCP client

**Claude Code** — `.mcp.json` in your project root
**Claude Desktop** — `claude_desktop_config.json` (`~/Library/Application Support/Claude/` on macOS, `%APPDATA%\Claude\` on Windows)

```json
{
  "mcpServers": {
    "medrxiv": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/yogsoth-ai/medrxiv-mcp", "medrxiv-mcp"],
      "env": {
        "AWS_ACCESS_KEY_ID": "<your key id>",
        "AWS_SECRET_ACCESS_KEY": "<your secret>",
        "AWS_DEFAULT_REGION": "us-east-1"
      }
    }
  }
}
```

### 2. Supply your AWS key

`search_preprints` is free and needs no key. `fetch_fulltext` reads a Requester-Pays bucket and **does** — see [below](#requires-your-own-aws-key-requester-pays).

### 3. Restart your MCP client

The server starts automatically when the client needs it.

## Requires your own AWS key (Requester-Pays)

medRxiv full text is only reliably reachable through the official `s3://medrxiv-src-monthly` Text-and-Data-Mining bucket, which is **[Requester-Pays](https://docs.aws.amazon.com/AmazonS3/latest/userguide/RequesterPaysBuckets.html)**: **you** supply an AWS key, and **your** account pays the (tiny) transfer cost. The package never ships a key — each user brings their own.

Costs are small:

| Action | Cost |
|--------|------|
| `search_preprints` | **free** (Europe PMC, no AWS) |
| First `fetch_fulltext` in a given month | ~$0.03 one-time (indexes that month) |
| Each `fetch_fulltext` after that | well under $0.01 |

**Setup:** in the [AWS IAM console](https://console.aws.amazon.com/iam/), create a user, attach the `AmazonS3ReadOnlyAccess` policy, create an access key, and put it in the `env` block above. Deactivate the key whenever you're done.

**Optional env:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `RXIV_CACHE_DIR` | `~/.cache/rxiv-mcp/` | where the local DOI→file sqlite cache lives |
| `RXIV_SCAN_CONCURRENCY` | `16` | threads used when indexing a month |

## Available Tools

| Tool | Description |
|------|-------------|
| `search_preprints` | Search medRxiv by keyword (relevance-ranked, free via Europe PMC). Returns `[{doi, title, abstract, date}]`. |
| `fetch_fulltext` | Given a DOI, return the preprint's full text as markdown (reads the Requester-Pays S3 archive). |

The intended workflow: `search_preprints` to find a paper and get its DOI cheaply, then `fetch_fulltext` on that DOI when you want to read it.

## Example Queries

Ask Claude things like:

- *"Search medRxiv for recent preprints on long-COVID cardiovascular outcomes and summarize the top 3 abstracts"*
- *"Fetch the full text of a medRxiv DOI and walk me through its statistical methods"*
- *"Find preprints on a vaccine-efficacy trial, then read the most relevant one in full"*

## For Developers

```bash
git clone https://github.com/yogsoth-ai/medrxiv-mcp.git
cd medrxiv-mcp
pip install -e .
python -m pytest -v          # offline suite — no AWS, no network
python -m medrxiv_mcp.server # run the server locally (needs AWS env for fetch)
```

The offline test suite covers the non-trivial logic (JATS→markdown conversion and the `.meca` DOI parser) against fixtures it builds itself — no AWS spend, no network. Live search and S3 fetch are smoke-tested manually.

## Links

- 🐙 [GitHub repository](https://github.com/yogsoth-ai/medrxiv-mcp)
- 🧬 [biorxiv-mcp](https://github.com/yogsoth-ai/biorxiv-mcp) — the bioRxiv twin
- 🌐 [Europe PMC REST API](https://europepmc.org/RestfulWebService)
- 📦 [medRxiv TDM / Open Access](https://www.medrxiv.org/tdm)
- 🔧 [Model Context Protocol](https://modelcontextprotocol.io)

## 📄 License

[Apache-2.0](LICENSE)
