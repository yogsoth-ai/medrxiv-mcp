from medrxiv_mcp.convert import jats_to_markdown

SAMPLE_JATS = """<?xml version="1.0"?>
<article>
  <front><article-meta>
    <title-group><article-title>A Test Preprint</article-title></title-group>
  </article-meta></front>
  <body>
    <sec><title>Introduction</title><p>Hello <italic>world</italic> of preprints.</p></sec>
    <sec><title>Methods</title><p>We did science.</p></sec>
  </body>
</article>"""


def test_converts_sections_to_markdown():
    md = jats_to_markdown(SAMPLE_JATS)
    assert "Introduction" in md
    assert "Methods" in md
    assert "Hello" in md and "world" in md


def test_degraded_fallback_on_pandoc_failure(monkeypatch):
    import medrxiv_mcp.convert as c
    def boom(*a, **k):
        raise RuntimeError("pandoc exploded")
    monkeypatch.setattr(c.pypandoc, "convert_text", boom)
    md = jats_to_markdown(SAMPLE_JATS)
    assert "We did science." in md           # body text survives via fallback
    assert md.lower().startswith("> note")    # degraded note present
