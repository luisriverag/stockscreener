from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def test_roadmap_makes_api_and_mcp_high_priority():
    roadmap = read("docs/ROADMAP.md")

    assert "## High Priority - API & MCP" in roadmap
    assert "API and MCP work are now top-priority" in roadmap
    assert "### REST API" in roadmap
    assert "### MCP Server" in roadmap
    assert "GET /api/companies" in roadmap
    assert "GET /api/companies/<ticker>" in roadmap
    assert "list_companies" in roadmap
    assert "get_company" in roadmap


def test_roadmap_tracks_next_api_and_mcp_hardening_steps():
    roadmap = read("docs/ROADMAP.md")

    for item in [
        "OpenAPI specification",
        "API versioning strategy",
        "authentication",
        "rate limiting",
        "multiple MCP clients",
        "resource templates",
        "MCP client compatibility",
    ]:
        assert item in roadmap
