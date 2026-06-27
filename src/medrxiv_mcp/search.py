import httpx

from . import config

_EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def _parse_epmc(payload: dict) -> list[dict]:
    rows = []
    for r in payload.get("resultList", {}).get("result", []):
        doi = r.get("doi")
        if not doi:
            continue
        rows.append({
            "doi": doi,
            "title": r.get("title", ""),
            "abstract": r.get("abstractText", ""),
            "date": r.get("firstPublicationDate", ""),
        })
    return rows


def search_preprints(query: str, limit: int = 20) -> list[dict]:
    """Relevance-ranked preprint search via Europe PMC (free, no S3)."""
    q = f'({query}) AND SRC:PPR AND PUBLISHER:"{config.PUBLISHER}"'
    params = {"query": q, "resultType": "core", "format": "json", "pageSize": str(limit)}
    with httpx.Client(timeout=30) as client:
        resp = client.get(_EPMC, params=params)
        resp.raise_for_status()
        return _parse_epmc(resp.json())
