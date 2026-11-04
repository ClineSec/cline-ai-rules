from helpdesk.estimates import parse_saved_estimate


def test_parse_saved_estimate():
    assert parse_saved_estimate("2.5") == 2.5
