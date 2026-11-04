from helpdesk.assist import REPLY_STYLES, SUPPORTED_LANGUAGES, DraftRequest


def test_default_style_exists():
    assert DraftRequest(ticket_text="VPN drops").style in REPLY_STYLES


def test_english_is_supported():
    assert "en" in SUPPORTED_LANGUAGES
