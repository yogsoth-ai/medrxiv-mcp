import io
import zipfile

import pytest

from medrxiv_mcp.fetch import extract_jats


def _meca(xml_name="content/555889.xml"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(xml_name, "<article><body><sec><title>Intro</title></sec></body></article>")
        z.writestr("manifest.xml", "<manifest/>")
        z.writestr("transfer.xml", "<transfer/>")
    return buf.getvalue()


def test_extract_jats_returns_content_xml():
    xml = extract_jats(_meca())
    assert "<article>" in xml and "Intro" in xml


def test_extract_jats_raises_when_absent():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("manifest.xml", "<manifest/>")
    with pytest.raises(ValueError):
        extract_jats(buf.getvalue())
