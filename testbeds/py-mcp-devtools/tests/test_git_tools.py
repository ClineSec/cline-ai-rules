from devtools.tools import git_tools


def test_checkout_refuses_option_like_branch():
    assert git_tools.git_checkout("--orphan").startswith("Refusing")


def test_show_requires_sha():
    assert git_tools.git_show("HEAD~1").startswith("Expected a commit SHA")
