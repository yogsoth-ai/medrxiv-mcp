import re
import xml.etree.ElementTree as ET
import pypandoc


def jats_to_markdown(xml: str) -> str:
    """Convert JATS XML full text to gfm markdown.

    Primary path: pandoc (jats -> gfm). pandoc handles <sec>, <fig>/<table-wrap>
    captions, and MathML natively. On any pandoc failure, fall back to a
    tag-stripped dump of <body> so the caller still gets the text.
    """
    try:
        md = pypandoc.convert_text(xml, "gfm", format="jats")
        if md and md.strip():
            return md
        raise ValueError("pandoc returned empty output")
    except Exception as e:
        return _degraded(xml, e)


def _degraded(xml: str, err: Exception) -> str:
    note = f"> NOTE: pandoc conversion failed ({err}); showing tag-stripped text.\n\n"
    try:
        root = ET.fromstring(xml)
        body = root.find(".//body")
        parts = (t.strip() for t in (body.itertext() if body is not None else []) if t.strip())
        text = " ".join(parts)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", xml)
        text = re.sub(r"\s+", " ", text).strip()
    return note + text
