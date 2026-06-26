from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def test_dashboard_filtering_uses_explicit_none_checks_and_spread_exclusion():
    app = read("app.py")

    assert "if pe is not None and pe < max_pe:" in app
    assert "if growth is not None and growth > min_growth:" in app
    assert "spread_filter_requested = any(" in app
    assert "if spread_filter_requested and pe_spread is None:" in app
    assert "use_calc_pe_param = \"true\" if use_calc_pe else \"false\"" in app


def test_dashboard_filter_links_preserve_lowercase_boolean_and_sort_state():
    template = read("templates/index.html")

    assert 'name="sort_by" value="{{ sort_by }}"' in template
    assert 'name="order" value="{{ order }}"' in template
    assert 'href="{{ sort_urls[' in template
    assert "/export/csv?{{ export_query }}" in template
    assert "use_calc_pe={{ use_calc_pe }}" not in template


def test_dashboard_ui_summarizes_active_filters_and_handles_zero_metrics():
    template = read("templates/index.html")

    assert "active-filter-bar" in template
    assert "filter-chip" in template
    assert "filter-help" in template
    assert "company.pe_ratio is not none" in template
    assert "company.pe_calc is not none" in template
    assert "company.pe_spread is not none" in template
    assert "company.revenue_growth is not none" in template
    assert "company.daily_change is not none" in template
    assert "min_pe_spread_abs if min_pe_spread_abs is not none else ''" in template
    assert "min_pe_spread_pos if min_pe_spread_pos is not none else ''" in template
    assert "min_pe_spread_neg if min_pe_spread_neg is not none else ''" in template


def test_dashboard_ui_exposes_quick_presets_and_results_context():
    template = read("templates/index.html")

    assert "quick-filter-grid" in template
    assert "preset-card" in template
    assert "Value shortlist" in template
    assert "Growth leaders" in template
    assert "P/E anomalies" in template
    assert "Calculated P/E" in template
    assert "filter-section-label" in template
    assert "results-meta" in template
    assert "Clear all" in template
    assert "Balance sheet filters" in template
    assert "Max Debt/Equity" in template
    assert "Max Debt/Market Cap (%)" in template
    assert "min_market_cap" in template
    assert "max_market_cap" in template
    assert "Min Market Cap ($)" in template
    assert "Max Market Cap ($)" in template
    assert "Debt/Equity" in template
