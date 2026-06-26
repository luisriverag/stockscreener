import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def test_openapi_spec_documents_versioned_discovery_routes():
    spec = json.loads(read("docs/openapi.json"))
    for path in [
        "/api/v1/companies",
        "/api/v1/companies/{ticker}",
        "/api/v1/companies/{ticker}/chart",
        "/api/v1/sectors",
        "/api/v1/industries",
        "/api/v1/market-data/{ticker}/refresh",
    ]:
        assert path in spec["paths"]


def test_api_docs_cover_versioning_openapi_and_market_cap_filters():
    docs = read("docs/API.md")
    for token in [
        "Versioned `/api/v1/...` routes",
        "docs/openapi.json",
        "GET /api/v1/sectors",
        "GET /api/v1/industries",
        "GET /api/v1/companies/<ticker>/chart",
        "GET /api/v1/market-data/<ticker>/refresh",
        "`min_market_cap`",
        "`max_market_cap`",
    ]:
        assert token in docs


def test_app_exposes_versioned_and_discovery_routes():
    app_py = read("app.py")
    for token in [
        '@app.route("/api/v1/companies")',
        '@app.route("/api/v1/companies/<ticker>")',
        '@app.route("/api/v1/sectors")',
        '@app.route("/api/v1/industries")',
        '@app.route("/api/v1/companies/<ticker>/chart")',
        '@app.route("/api/v1/market-data/<ticker>/refresh")',
        'request.args.get("min_market_cap", type=float)',
        'request.args.get("max_market_cap", type=float)',
    ]:
        assert token in app_py


def test_mcp_resource_templates_and_schema_track_api_filters():
    mcp = read("mcp_server.py")
    assert "def list_resource_templates():" in mcp
    assert "resources/templates/list" in mcp
    assert "min_market_cap" in mcp
    assert "max_market_cap" in mcp


def test_flask_client_smoke_checks_read_only_routes():
    from app import app

    client = app.test_client()
    for path in ["/api/v1/companies?per_page=1", "/api/v1/sectors", "/api/v1/industries"]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.is_json
