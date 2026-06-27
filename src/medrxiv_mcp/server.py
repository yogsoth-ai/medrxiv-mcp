# src/biorxiv_mcp/server.py
from fastmcp import FastMCP

from . import config, search, index, fetch, convert

mcp = FastMCP(f"{config.SERVER}-mcp")


@mcp.tool
def search_preprints(query: str, limit: int = 20) -> list[dict]:
    """Search bioRxiv/medRxiv preprints by keyword (relevance-ranked, free).

    Returns a list of {doi, title, abstract, date}. Use the doi with
    fetch_fulltext to read the full text.
    """
    return search.search_preprints(query, limit)


@mcp.tool
def fetch_fulltext(doi: str) -> str:
    """Fetch the full text of a preprint as markdown, given its DOI.

    Downloads the paper's source package from the Requester-Pays S3 bucket
    (your AWS account pays a fraction of a cent), extracts the JATS XML, and
    converts it to markdown. First use of a given month is slower (it indexes
    that month once); later DOIs in the same month are fast.
    """
    s3_key = index.resolve(doi)
    if not s3_key:
        other = "medrxiv" if config.SERVER == "biorxiv" else "biorxiv"
        return (f"Could not find DOI {doi} in {config.SERVER}. "
                f"If this is a {other} preprint, use the {other}-mcp server instead.")
    meca = fetch.download_meca(s3_key)
    jats = fetch.extract_jats(meca)
    return convert.jats_to_markdown(jats)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
