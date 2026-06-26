# Stock Screener MCP Server

Stock Screener includes a minimal [Model Context Protocol](https://modelcontextprotocol.io/) server that lets MCP-compatible clients query the local stock database and read project API documentation over stdio.

## Running the server

Start the server from the repository root after installing the normal project dependencies:

```bash
python mcp_server.py
```

The server uses MCP's `Content-Length` framed JSON-RPC stdio transport. It does not open a network port and does not require an MCP SDK package. Application imports are lazy, so `initialize`, `ping`, `tools/list`, `resources/list`, `resources/templates/list`, and `prompts/list` can respond even before the Flask application dependencies are installed; data-returning calls still require `pip install -r requirements.txt`.

## Capabilities

The server advertises:

- `tools` for structured company queries.
- `resources` for API documentation and a company-list JSON resource.
- `ping`, empty `prompts/list`, and `resources/templates/list` handlers for compatibility with clients that probe optional MCP capabilities.
- Tool results with both `content` and `structuredContent`, so clients can either display text JSON or consume structured JSON directly.

## Tools

### `list_companies`

Lists companies with the same core fields exposed by `GET /api/companies`.

Input schema:

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `page` | integer | `1` | 1-based page number. |
| `per_page` | integer | `25` | Page size, capped at 100. |
| `search` | string | unset | Search ticker, name, sector, and industry. |
| `sector` | string | unset | Filter by sector. |
| `industry` | string | unset | Filter by industry. |
| `max_debt_to_equity` | number | unset | Exclude companies with missing debt/equity data or values above this limit. |
| `max_debt_to_market_cap_pct` | number | unset | Exclude companies with missing debt or market-cap data, or total debt above this percentage of market cap. |
| `min_market_cap` | number | unset | Minimum market capitalization in dollars. |
| `max_market_cap` | number | unset | Maximum market capitalization in dollars. |
| `sort` | string | `ticker` | One of `ticker`, `name`, `sector`, `industry`, `pe_ratio`, `market_cap`, `debt_to_equity`, or `total_debt`. |
| `order` | string | `asc` | `asc` or `desc`. |

Example MCP tool arguments:

```json
{
  "search": "software",
  "per_page": 10,
  "max_debt_to_equity": 100,
  "sort": "market_cap",
  "order": "desc"
}
```

### `get_company`

Returns detailed company data for one ticker, including the latest financial report and latest stock price.

Input schema:

| Argument | Type | Required | Description |
| --- | --- | --- | --- |
| `ticker` | string | yes | Ticker symbol, such as `MSFT`. |

Example MCP tool arguments:

```json
{
  "ticker": "MSFT"
}
```

## Resources

### `stockscreener://docs/api`

Returns `docs/API.md` as `text/markdown` so MCP clients can inspect the REST API contract.

### `stockscreener://companies`

Returns company list JSON. The resource accepts query parameters equivalent to the `list_companies` tool, for example:

```text
stockscreener://companies?search=software&per_page=10&max_debt_to_equity=100&sort=market_cap&order=desc
```

## Resource templates

`resources/templates/list` advertises reusable company-list URI templates for common search, sector, industry, market-cap, and debt-screening patterns. Example template expansion:

```text
stockscreener://companies?sector=Technology&min_market_cap=100000000000&sort=market_cap&order=desc
```

## Local MCP client setup example

A local MCP client can launch the server with a stdio command from the repository root:

```json
{
  "mcpServers": {
    "stockscreener": {
      "command": "python",
      "args": ["/workspace/stockscreener/mcp_server.py"],
      "cwd": "/workspace/stockscreener"
    }
  }
}
```

## Compatibility notes

- Supported protocol versions are `2025-03-26` and `2024-11-05`; the server negotiates either of those values and otherwise falls back to `2025-03-26`.
- JSON-RPC notifications, including `notifications/initialized`, are accepted without responses.
- JSON-RPC batches are accepted and answered with batched responses.
- Invalid tool arguments return JSON-RPC `-32602` errors, unsupported methods return `-32601`, and malformed requests return protocol-level errors.
- Tool schemas set `additionalProperties: false` and include read-only annotations for clients that understand MCP tool annotations.

## Example initialize request

MCP clients normally handle framing automatically. For low-level testing, send a `Content-Length` framed JSON-RPC request to `python mcp_server.py`:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "example", "version": "0.0.1"}
  }
}
```

The server responds with its protocol version, tool capability, resource capability, and server metadata.
