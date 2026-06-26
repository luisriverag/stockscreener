"""Model Context Protocol server for Stock Screener data.

The server uses MCP's JSON-RPC-over-stdio transport and intentionally avoids
an MCP SDK dependency. Application imports are lazy so metadata-only MCP
methods, such as initialize and tools/list, still work in lightweight clients or
setup checks before Flask-SQLAlchemy is installed.
"""

import json
import sys
from contextlib import nullcontext
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SUPPORTED_PROTOCOL_VERSIONS = ["2025-03-26", "2024-11-05"]
DEFAULT_PROTOCOL_VERSION = SUPPORTED_PROTOCOL_VERSIONS[0]
SERVER_INFO = {"name": "stockscreener", "version": "1.0.0"}
JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603


class McpError(Exception):
    """JSON-RPC aware MCP exception."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def app_dependencies():
    """Import Flask app dependencies only when a data operation needs them."""
    try:
        from app import app, apply_company_api_filters, company_to_api_dict
        from models import Company
    except ModuleNotFoundError as exc:
        raise McpError(
            JSONRPC_INTERNAL_ERROR,
            f"Missing application dependency: {exc.name}. Run `pip install -r requirements.txt`.",
        ) from exc

    return app, apply_company_api_filters, company_to_api_dict, Company


def read_message():
    """Read one Content-Length framed JSON-RPC message from stdin."""
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        key, separator, value = line.decode("utf-8").partition(":")
        if not separator:
            raise McpError(JSONRPC_INVALID_REQUEST, "Malformed MCP header")
        headers[key.lower()] = value.strip()

    try:
        length = int(headers.get("content-length", "0"))
    except ValueError as exc:
        raise McpError(JSONRPC_INVALID_REQUEST, "Invalid Content-Length header") from exc

    if length <= 0:
        raise McpError(JSONRPC_INVALID_REQUEST, "Missing Content-Length header")

    try:
        return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise McpError(JSONRPC_PARSE_ERROR, f"Invalid JSON: {exc.msg}") from exc


def write_message(message):
    """Write one Content-Length framed JSON-RPC message to stdout."""
    body = json.dumps(message, separators=(",", ":"), default=str).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def tool_result(payload):
    """Return both text and structured content for broader MCP client support."""
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2, default=str)}],
        "structuredContent": payload,
    }


def coerce_int(arguments, name, default, minimum=None, maximum=None):
    value = arguments.get(name, default)
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise McpError(JSONRPC_INVALID_PARAMS, f"{name} must be an integer") from exc

    if minimum is not None:
        value = max(value, minimum)
    if maximum is not None:
        value = min(value, maximum)
    return value


def app_context(app):
    return app.app_context() if app else nullcontext()


def company_list(arguments):
    app, apply_company_api_filters, company_to_api_dict, Company = app_dependencies()
    page = coerce_int(arguments, "page", 1, minimum=1)
    per_page = coerce_int(arguments, "per_page", 25, minimum=1, maximum=100)
    sort_by = arguments.get("sort", "ticker")
    order = arguments.get("order", "asc")
    if order not in {"asc", "desc"}:
        raise McpError(JSONRPC_INVALID_PARAMS, "order must be 'asc' or 'desc'")

    allowed_sort_columns = {
        "ticker": Company.ticker,
        "name": Company.name,
        "sector": Company.sector,
        "industry": Company.industry,
        "pe_ratio": Company.pe_ratio,
        "market_cap": Company.market_cap,
        "debt_to_equity": Company.debt_to_equity,
        "total_debt": Company.total_debt,
    }
    if sort_by not in allowed_sort_columns:
        raise McpError(JSONRPC_INVALID_PARAMS, f"Unsupported sort field: {sort_by}")

    with app.test_request_context(
        query_string={
            key: value
            for key, value in {
                "search": arguments.get("search"),
                "sector": arguments.get("sector"),
                "industry": arguments.get("industry"),
                "max_debt_to_equity": arguments.get("max_debt_to_equity"),
                "max_debt_to_market_cap_pct": arguments.get(
                    "max_debt_to_market_cap_pct"
                ),
                "min_market_cap": arguments.get("min_market_cap"),
                "max_market_cap": arguments.get("max_market_cap"),
            }.items()
            if value
        }
    ):
        query = apply_company_api_filters(Company.query)
        sort_column = allowed_sort_columns[sort_by]
        query = query.order_by(
            sort_column.desc() if order == "desc" else sort_column.asc()
        )
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "companies": [company_to_api_dict(company) for company in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        }


def company_detail(arguments):
    app, _, company_to_api_dict, Company = app_dependencies()
    ticker = str(arguments.get("ticker", "")).upper()
    if not ticker:
        raise McpError(JSONRPC_INVALID_PARAMS, "ticker is required")

    with app_context(app):
        company = Company.query.filter_by(ticker=ticker).first()
        if not company:
            raise McpError(JSONRPC_INVALID_PARAMS, f"Company not found: {ticker}")
        return company_to_api_dict(company, include_details=True)


def list_tools():
    return [
        {
            "name": "list_companies",
            "description": "List Stock Screener companies with optional search, sector, industry, pagination, and sorting.",
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "page": {"type": "integer", "minimum": 1, "default": 1},
                    "per_page": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
                    "search": {"type": "string"},
                    "sector": {"type": "string"},
                    "industry": {"type": "string"},
                    "max_debt_to_equity": {"type": "number", "minimum": 0},
                    "max_debt_to_market_cap_pct": {"type": "number", "minimum": 0},
                    "min_market_cap": {"type": "number", "minimum": 0},
                    "max_market_cap": {"type": "number", "minimum": 0},
                    "sort": {
                        "type": "string",
                        "enum": [
                            "ticker",
                            "name",
                            "sector",
                            "industry",
                            "pe_ratio",
                            "market_cap",
                            "debt_to_equity",
                            "total_debt",
                        ],
                        "default": "ticker",
                    },
                    "order": {"type": "string", "enum": ["asc", "desc"], "default": "asc"},
                },
            },
            "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
        },
        {
            "name": "get_company",
            "description": "Get detailed Stock Screener data for one ticker, including latest report and latest price.",
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["ticker"],
                "properties": {"ticker": {"type": "string", "description": "Ticker symbol, e.g. MSFT"}},
            },
            "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
        },
    ]


def list_resources():
    return [
        {
            "uri": "stockscreener://docs/api",
            "name": "Stock Screener API documentation",
            "description": "Read-only REST API documentation for Stock Screener.",
            "mimeType": "text/markdown",
        },
        {
            "uri": "stockscreener://companies",
            "name": "Stock Screener companies",
            "description": "JSON list of companies. Supports query parameters such as ?search=software&per_page=10.",
            "mimeType": "application/json",
        },
    ]


def list_resource_templates():
    return [
        {
            "uriTemplate": "stockscreener://companies{?search,sector,industry,page,per_page,sort,order,min_market_cap,max_market_cap}",
            "name": "Filtered company list",
            "description": "List companies with common REST API query parameters.",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "stockscreener://companies{?sector,industry,max_debt_to_equity,max_debt_to_market_cap_pct}",
            "name": "Screened company list",
            "description": "List companies using sector, industry, and debt screening filters.",
            "mimeType": "application/json",
        },
    ]


def read_resource(uri):
    parsed = urlparse(uri)
    if uri == "stockscreener://docs/api":
        text = Path("docs/API.md").read_text(encoding="utf-8")
        return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]}

    if parsed.scheme == "stockscreener" and parsed.netloc == "companies":
        args = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(company_list(args), indent=2, default=str),
                }
            ]
        }

    raise McpError(JSONRPC_INVALID_PARAMS, f"Unknown resource: {uri}")


def negotiated_protocol_version(params):
    requested = params.get("protocolVersion")
    if requested in SUPPORTED_PROTOCOL_VERSIONS:
        return requested
    return DEFAULT_PROTOCOL_VERSION


def handle_request(message):
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        raise McpError(JSONRPC_INVALID_REQUEST, "Expected a JSON-RPC 2.0 request object")

    method = message.get("method")
    params = message.get("params") or {}

    if method == "initialize":
        return {
            "protocolVersion": negotiated_protocol_version(params),
            "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": "Use list_companies for screening data and get_company for ticker details.",
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": list_tools()}
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name == "list_companies":
            return tool_result(company_list(arguments))
        if name == "get_company":
            return tool_result(company_detail(arguments))
        raise McpError(JSONRPC_INVALID_PARAMS, f"Unknown tool: {name}")
    if method == "resources/list":
        return {"resources": list_resources()}
    if method == "resources/read":
        return read_resource(params.get("uri", ""))
    if method == "resources/templates/list":
        return {"resourceTemplates": list_resource_templates()}
    if method == "prompts/list":
        return {"prompts": []}

    raise McpError(JSONRPC_METHOD_NOT_FOUND, f"Unsupported method: {method}")


def error_response(message_id, code, message):
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def response_for_message(message):
    if not isinstance(message, dict):
        return error_response(None, JSONRPC_INVALID_REQUEST, "Expected a JSON-RPC request object")
    if "id" not in message:
        return None

    try:
        result = handle_request(message)
        return {"jsonrpc": "2.0", "id": message["id"], "result": result}
    except McpError as exc:
        return error_response(message.get("id"), exc.code, exc.message)
    except Exception as exc:
        return error_response(message.get("id"), JSONRPC_INTERNAL_ERROR, str(exc))


def main():
    while True:
        try:
            message = read_message()
        except McpError as exc:
            write_message(error_response(None, exc.code, exc.message))
            continue

        if message is None:
            break

        messages = message if isinstance(message, list) else [message]
        responses = [response for response in map(response_for_message, messages) if response]
        if not responses:
            continue
        write_message(responses if isinstance(message, list) else responses[0])


if __name__ == "__main__":
    main()
