import io, zipfile
from medrxiv_mcp import index

TRANSFER_XML = (
    '<?xml version="1.0"?>'
    '<transfer xmlns="http://www.manuscriptexchange.org" '
    'reference="/medrxiv/early/2024/04/12/2023.09.01.555889.atom"></transfer>'
)


def _make_meca_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("content/555889.xml", "<article/>" * 5000)  # bulk, like a real paper
        z.writestr("manifest.xml", "<manifest/>")
        z.writestr("transfer.xml", TRANSFER_XML)
    return buf.getvalue()


def test_doi_suffix_from_tail_recovers_doi():
    data = _make_meca_bytes()
    tail = data[-65536:] if len(data) > 65536 else data
    assert index.doi_suffix_from_tail(tail) == "2023.09.01.555889"


def test_doi_suffix_from_tail_returns_none_on_junk():
    assert index.doi_suffix_from_tail(b"not a zip tail") is None
