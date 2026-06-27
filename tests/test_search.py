from medrxiv_mcp.search import _parse_epmc

CANNED = {
    "resultList": {"result": [
        {"doi": "10.1101/2024.01.01.111111", "title": "Paper One",
         "abstractText": "Abstract one.", "firstPublicationDate": "2024-01-01"},
        {"doi": "10.1101/2024.02.02.222222", "title": "Paper Two",
         "abstractText": "Abstract two.", "firstPublicationDate": "2024-02-02"},
        {"title": "No DOI paper", "abstractText": "skip me"},  # no doi -> dropped
    ]}
}


def test_parse_epmc_extracts_fields_and_drops_doi_less():
    rows = _parse_epmc(CANNED)
    assert len(rows) == 2
    assert rows[0] == {"doi": "10.1101/2024.01.01.111111", "title": "Paper One",
                       "abstract": "Abstract one.", "date": "2024-01-01"}
