# medrxiv-mcp

MCP server that turns a **medRxiv DOI into clean markdown full text**, plus free
relevance search. (bioRxiv has its own package, `biorxiv-mcp`.)

## Two tools

- `search_preprints(query, limit=20)` → `[{doi, title, abstract, date}]` — free, via Europe PMC.
- `fetch_fulltext(doi)` → markdown full text — reads the official Requester-Pays S3 bucket.

## Requires your own AWS key (Requester-Pays)

medRxiv full text is only reachable via the official `s3://medrxiv-src-monthly`
Text-and-Data-Mining bucket, which is **Requester-Pays**: **you** supply an AWS key
and **your** account pays. Costs are tiny: the first fetch in a given month indexes
that month once (~$0.03); each `fetch_fulltext` after that is well under $0.01;
`search_preprints` is free.

Set up an IAM user with `AmazonS3ReadOnlyAccess`, create an access key, and put it
in your `.mcp.json`:

```jsonc
{
  "mcpServers": {
    "medrxiv": {
      "command": "uvx",
      "args": ["medrxiv-mcp"],
      "env": {
        "AWS_ACCESS_KEY_ID": "<your key id>",
        "AWS_SECRET_ACCESS_KEY": "<your secret>",
        "AWS_DEFAULT_REGION": "us-east-1"
      }
    }
  }
}
```

Optional env: `RXIV_CACHE_DIR` (where the local DOI->UUID sqlite cache lives;
default `~/.cache/rxiv-mcp/`), `RXIV_SCAN_CONCURRENCY` (default 16).

## License

Apache-2.0.
