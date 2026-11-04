from insights import formatting, metrics


def test_kpi_tile_escapes_label_and_value():
    tile = formatting.kpi_tile("<b>signups</b>", "1,024")
    assert "&lt;b&gt;signups&lt;/b&gt;" in tile
    assert "<b>1,024</b>" in tile


def test_pct_keeps_sign():
    assert formatting.pct(0.25) == "+25%"
    assert formatting.pct(-0.1) == "-10%"


def test_last_week_flags_churn_spike():
    anomalies = metrics.find_anomalies(metrics.load_kpis())
    assert "churned_accounts" in {a.metric for a in anomalies}


def test_sparkline_is_svg():
    svg = metrics.sparkline_svg(metrics.load_kpis(), "signups")
    assert svg.startswith("<svg") and svg.endswith("</svg>")
