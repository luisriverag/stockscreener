from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def load_mcp_server_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("mcp_server", ROOT / "mcp_server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mcp_server_docs_and_static_capabilities_exist():
    server = read("mcp_server.py")
    docs = read("docs/MCP.md")
    api_docs = read("docs/API.md")

    for token in [
        "SUPPORTED_PROTOCOL_VERSIONS",
        "def read_message",
        "def write_message",
        'method == "tools/list"',
        'method == "tools/call"',
        'method == "resources/list"',
        'method == "resources/read"',
        '"list_companies"',
        '"get_company"',
        "stockscreener://docs/api",
        "structuredContent",
        "additionalProperties",
        "max_debt_to_equity",
        "max_debt_to_market_cap_pct",
    ]:
        assert token in server

    assert "# Stock Screener MCP Server" in docs
    assert "Compatibility notes" in docs
    assert "list_companies" in docs
    assert "get_company" in docs
    assert "stockscreener://companies" in docs
    assert "## MCP Server" in api_docs


def test_mcp_server_metadata_methods_work_without_app_dependencies():
    mcp_server = load_mcp_server_module()

    initialize = mcp_server.response_for_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        }
    )
    assert initialize["result"]["protocolVersion"] == "2024-11-05"
    assert "tools" in initialize["result"]["capabilities"]
    assert "resources" in initialize["result"]["capabilities"]

    assert mcp_server.response_for_message(
        {"jsonrpc": "2.0", "id": 2, "method": "ping"}
    )["result"] == {}
    assert mcp_server.response_for_message(
        {"jsonrpc": "2.0", "method": "notifications/initialized"}
    ) is None

    tools = mcp_server.response_for_message(
        {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
    )["result"]["tools"]
    assert tools[0]["inputSchema"]["additionalProperties"] is False
    assert tools[0]["annotations"]["readOnlyHint"] is True


def test_mcp_server_reports_compatible_errors_and_batch_responses():
    mcp_server = load_mcp_server_module()

    invalid = mcp_server.response_for_message(
        {"jsonrpc": "2.0", "id": 4, "method": "missing/method"}
    )
    assert invalid["error"]["code"] == mcp_server.JSONRPC_METHOD_NOT_FOUND

    batch = [
        {"jsonrpc": "2.0", "id": 5, "method": "ping"},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
    ]
    responses = [response for response in map(mcp_server.response_for_message, batch) if response]
    assert responses == [{"jsonrpc": "2.0", "id": 5, "result": {}}]


def test_mcp_server_stdio_initialize_smoke():
    import json
    import subprocess
    import sys

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2025-03-26", "capabilities": {}},
    }
    body = json.dumps(payload).encode()
    frame = b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
    result = subprocess.run(
        [sys.executable, "mcp_server.py"],
        input=frame,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
        check=True,
    )

    assert b"Content-Length:" in result.stdout
    assert b"serverInfo" in result.stdout
    assert b"2025-03-26" in result.stdout
