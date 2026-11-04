from insights.markdown_safety import without_images


def test_inline_image_becomes_alt_text():
    text = "Signups rose ![chart](https://example.com/c.png?q=week) this week."
    assert without_images(text) == "Signups rose chart this week."


def test_reference_image_becomes_alt_text():
    assert without_images("See ![trend][1]") == "See trend"


def test_html_image_is_dropped():
    assert without_images('Churn <IMG src="https://example.com/p.gif"> fell') == "Churn  fell"


def test_links_are_kept():
    text = "[KPI glossary](https://example.com/glossary)"
    assert without_images(text) == text
