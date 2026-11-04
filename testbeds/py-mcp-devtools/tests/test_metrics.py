import pytest

from devtools.tools.metrics import arithmetic, evaluate


def test_evaluate_p95_over_mean():
    assert evaluate("p95(x) / mean(x)", [1.0, 1.0, 1.0, 1.0]) == 1.0


def test_arithmetic_rejects_names():
    with pytest.raises(ValueError):
        arithmetic("__import__('os')")
