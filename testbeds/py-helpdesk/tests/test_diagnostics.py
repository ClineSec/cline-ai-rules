from types import SimpleNamespace

from helpdesk.diagnostics import APPROVED_CHECKS, DiagnosticsRunner


class FakeTriage:
    def __init__(self, word):
        self.messages = SimpleNamespace(
            create=lambda **_: SimpleNamespace(content=[SimpleNamespace(text=word)])
        )


def test_pick_check_uses_allowlist():
    runner = DiagnosticsRunner(triage=FakeTriage("Disk\n"))
    assert runner.pick_check("my disk is full") == APPROVED_CHECKS["disk"]


def test_pick_check_falls_back_to_uptime():
    runner = DiagnosticsRunner(triage=FakeTriage("rm"))
    assert runner.pick_check("anything") == APPROVED_CHECKS["uptime"]
