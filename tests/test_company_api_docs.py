from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def test_company_api_routes_use_shared_serialization_and_safe_query_controls():
    app = read("app.py")

    assert '@app.route("/api/companies")' in app
    assert '@app.route("/api/companies/<ticker>")' in app
    assert "def company_to_api_dict(company, include_details=False):" in app
    assert "def apply_company_api_filters(query):" in app
    assert 'per_page = min(max(per_page, 1), 100)' in app
    assert "allowed_sort_columns" in app
    for field in ["pe_calc", "pe_spread", "revenue_growth", "daily_change"]:
        assert field in app
    for detail_field in ["latest_report", "latest_price"]:
        assert detail_field in app


def test_api_docs_cover_rest_endpoints_parameters_and_error_shapes():
    docs = read("docs/API.md")

    for endpoint in [
        "GET /api/companies",
        "GET /api/companies/<ticker>",
        "GET /chart/<company_id>",
        "GET /api/news/<ticker>",
        "GET /api/risks/<ticker>",
        "GET /api/market-data/<ticker>",
    ]:
        assert endpoint in docs

    for parameter in [
        "page",
        "per_page",
        "search",
        "sector",
        "industry",
        "max_debt_to_equity",
        "max_debt_to_market_cap_pct",
        "sort",
        "order",
    ]:
        assert f"`{parameter}`" in docs

    assert "debt_to_equity" in docs
    assert "total_debt" in docs

    assert "HTTP `404`" in docs
    assert "Company not found" in docs
    assert "## MCP Server" in docs


def test_readme_and_spec_link_to_api_and_mcp_docs():
    readme = read("README.md")
    spec = read("docs/SPEC.md")

    assert "docs/API.md" in readme
    assert "docs/MCP.md" in readme
    assert "GET /api/companies" in readme
    assert "MCP" in readme

    assert "GET /api/companies" in spec
    assert "GET /api/companies/<ticker>" in spec
    assert "Model Context Protocol" in spec
