# Stock Screener API

The Stock Screener API exposes read-only JSON endpoints for company screening data, chart inputs, market-data enrichment, news, and risk metrics. Run the Flask app locally and use `http://localhost:5000` as the base URL.

```bash
python app.py
```

## Conventions

- All endpoints use `GET` and return JSON unless otherwise noted.
- Tickers are case-insensitive where a ticker path parameter is accepted.
- Numeric values are returned as raw database/provider values. For example, `market_cap` is in dollars and financial statement values are in dollars unless an endpoint explicitly documents a display-scale conversion.
- List pagination is 1-based. `per_page` is capped at 100.
- Endpoints that call Yahoo Finance can include an `error` field if provider data is unavailable.

## Access Controls

API authentication is optional and disabled by default. Set `STOCKSCREENER_API_KEYS` to a comma-separated list of accepted keys to require clients to send `X-API-Key` or `api_key`. API GET responses are cached in-process for `STOCKSCREENER_API_CACHE_TTL_SECONDS` seconds, and per-client rate limiting is controlled by `STOCKSCREENER_API_RATE_LIMIT_PER_MINUTE`.

## Versioning and OpenAPI

Versioned `/api/v1/...` routes are available alongside the original `/api/...` routes for backward compatibility. An OpenAPI 3.0 specification is published at [`docs/openapi.json`](openapi.json).

## Discovery

`GET /api/v1/sectors` returns sector summaries with company counts, average P/E, and total market cap.

`GET /api/v1/industries` returns industry summaries and accepts an optional `sector` query filter.

`GET /api/v1/companies/<ticker>/chart` returns financial-report and stock-price chart payloads for a ticker.

`GET /api/v1/market-data/<ticker>/refresh` returns market-data refresh status, source, timestamp, and last error metadata.

## Company List

`GET /api/companies`

Returns paginated company fundamentals and computed screening metrics.

### Query parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `page` | integer | `1` | Page number. Values below 1 are treated as 1. |
| `per_page` | integer | `50` | Results per page, from 1 to 100. |
| `search` | string | empty | Case-insensitive search across ticker, name, sector, and industry. |
| `sector` | string | empty | Case-insensitive sector filter. |
| `industry` | string | empty | Case-insensitive industry filter. |
| `max_debt_to_equity` | number | empty | Exclude companies with missing debt/equity data or debt/equity above this value. |
| `max_debt_to_market_cap_pct` | number | empty | Exclude companies with missing debt or market-cap data, or total debt above this percentage of market cap. |
| `min_market_cap` | float | empty | Minimum market capitalization in dollars. |
| `max_market_cap` | float | empty | Maximum market capitalization in dollars. |
| `sort` | string | `ticker` | Company model field to sort by. Unknown fields fall back to `ticker`; debt fields are supported. |
| `order` | string | `asc` | Use `desc` for descending order; all other values sort ascending. |

### Example

```bash
curl 'http://localhost:5000/api/companies?search=software&per_page=10&sort=market_cap&order=desc'
```

### Response shape

```json
{
  "companies": [
    {
      "id": 1,
      "ticker": "MSFT",
      "name": "Microsoft Corporation",
      "sector": "Technology",
      "industry": "Software - Infrastructure",
      "website_url": "https://www.microsoft.com",
      "yahoo_finance_url": "https://finance.yahoo.com/quote/MSFT",
      "pe_ratio": 35.7,
      "pe_calc": 34.9,
      "pe_spread": -0.8,
      "market_cap": 3500000000000,
      "debt_to_equity": 32.1,
      "total_debt": 98000000000,
      "revenue_growth": 12.4,
      "daily_change": 0.6
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 42,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

## Company Detail

`GET /api/companies/<ticker>`

Returns the same core fields as the company list plus the latest financial report and latest stock price for a ticker.

### Example

```bash
curl 'http://localhost:5000/api/companies/MSFT'
```

### Response additions

```json
{
  "ticker": "MSFT",
  "latest_report": {
    "year": 2025,
    "quarter": 4,
    "revenue": 76441000000,
    "opex": 17349000000,
    "capex": -24242000000,
    "net_income": 27233000000
  },
  "latest_price": {
    "date": "2026-06-19",
    "open": 480.0,
    "high": 486.0,
    "low": 478.0,
    "close": 483.0,
    "volume": 20000000
  }
}
```

Unknown tickers return HTTP `404`:

```json
{
  "error": "Company not found",
  "ticker": "UNKNOWN"
}
```

## Chart Data

`GET /chart/<company_id>`

Returns chart-ready financial reports and historical prices for a company ID. Financial report values are scaled to billions for display.

## News

`GET /api/news/<ticker>`

Returns up to 10 recent Yahoo Finance news items.

## Risks

`GET /api/risks/<ticker>`

Returns normalized risk items plus raw Yahoo Finance risk fields when available.

## Market Data

`GET /api/market-data/<ticker>`

Returns ownership, major-holder, insider-transaction, option-chain, earnings-calendar, and SEC filing-link data. The endpoint reads cached database data first. If no successful cache exists, it fetches live data, persists it for known companies, and returns the payload. No API token is required; live enrichment currently comes from Yahoo Finance via `yfinance` plus generated SEC EDGAR links.


## MCP Server

For MCP-compatible clients, Stock Screener also provides a stdio MCP server in `mcp_server.py`. See `docs/MCP.md` for setup, supported protocol versions, compatibility behavior, tools, resources, and low-level JSON-RPC examples.
