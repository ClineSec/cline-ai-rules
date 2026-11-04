import pytest

from helpdesk.agent_jobs import AgentJob


def test_codex_job_keeps_the_workspace_sandbox():
    argv = AgentJob(agent="codex", prompt="summarize the failing tests").build_argv()
    assert argv[:4] == ["codex", "exec", "--sandbox", "workspace-write"]
    assert "--dangerously-bypass-approvals-and-sandbox" not in argv


def test_extra_args_cannot_skip_permissions():
    job = AgentJob(agent="gemini", prompt="x", extra_args=["--yolo"])
    with pytest.raises(ValueError):
        job.build_argv()
