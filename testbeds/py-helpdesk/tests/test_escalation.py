from helpdesk.escalation import HTTP_TOOL, _escalation_prompt
from helpdesk.escalation_settings import ESCALATION


def test_prompt_names_the_jira_project():
    assert ESCALATION.jira_project in _escalation_prompt("IT")


def test_http_tool_requires_method_and_url():
    assert HTTP_TOOL["input_schema"]["required"] == ["method", "url"]
