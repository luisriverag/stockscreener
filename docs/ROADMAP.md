# Stock Screener - Roadmap

This document outlines planned and proposed enhancements for the Stock Screener application.

---

## High Priority - API & MCP

API and MCP work are now top-priority integration tracks because external tools, automations, and MCP-compatible clients need stable machine-readable access to screening data.

### REST API

- [x] Initial read-only Companies JSON API
  - `GET /api/companies` with pagination, search, filters, and safe sorting
  - `GET /api/companies/<ticker>` with computed metrics, latest report, and latest price
  - Human-readable documentation in `docs/API.md`
- [ ] Add route-level tests with Flask's test client once app dependencies are available in CI
- [ ] Publish an OpenAPI specification for generated clients and interactive docs
- [ ] Add API versioning strategy, for example `/api/v1/...`, before adding write endpoints
- [ ] Add optional API authentication, rate limiting, and response caching for third-party usage
- [ ] Expand endpoints for sectors, industries, chart payloads, and market-data refresh metadata

### MCP Server

- [x] Initial stdio MCP server
  - `list_companies` and `get_company` tools
  - `stockscreener://docs/api` and `stockscreener://companies` resources
  - Protocol negotiation, batching, notifications, ping, and structured tool content
  - Human-readable documentation in `docs/MCP.md`
- [ ] Validate against multiple MCP clients and record compatibility notes
- [ ] Add resource templates for common company-list query patterns
- [ ] Add packaging/config examples for local MCP client setup
- [ ] Add integration tests for data-returning MCP tools once app dependencies are available in CI
- [ ] Keep MCP tool schemas aligned with REST API query parameters and response shapes

---

## Version 2.0 - Planned Features

### Data Updates

- [ ] Background job to update data periodically
  - Scheduled tasks using APScheduler or Celery
  - Hourly/daily refresh of stock prices
  - Weekly refresh of financial reports

- [ ] Incremental updates (only new data)
  - Track last update timestamp per company
  - Fetch only new quarters/price data
  - Reduce API calls and processing time

### Additional Financial Metrics

- [ ] EBITDA (Earnings Before Interest, Taxes, Depreciation, Amortization)
- [ ] Free Cash Flow (FCF)
- [ ] EBITDA Margin
- [ ] Dividend history tracking
- [ ] Analyst ratings and price targets
- [ ] Earnings per Share (EPS) - quarterly
- [ ] Return on Equity (ROE)
- [ ] Return on Assets (ROA)
- [ ] Debt/Assets ratio

### Performance Improvements

- [ ] Redis caching for API responses
- [ ] Database connection pooling
- [ ] Pagination for large result sets (all companies page)
- [ ] Lazy loading for charts
- [ ] Query optimization with SQLAlchemy eager loading

---

## Version 2.1 - User Features

### User Experience

- [ ] Save filter presets
  - Save custom filter combinations
  - Name and manage presets
  - Quick access from homepage

- [x] Export functionality
  - [x] Export filtered results to CSV
  - [ ] Export to Excel with formatting
  - [ ] Export charts as PNG/SVG

- [ ] Email alerts
  - Set price alerts
  - Filter match notifications
  - Daily/weekly digest option

### Search & Navigation

- [x] Global search (ticker/name)
- [x] Sort by any column
- [ ] Industry/sector filtering
- [ ] Market cap range filter

---

## Version 2.2 - Visualization Enhancements

### Chart Improvements

- [ ] Technical indicators overlay
  - Moving averages (SMA, EMA)
  - RSI (Relative Strength Index)
  - MACD
  - Bollinger Bands

- [ ] Comparison overlays
  - Overlay multiple companies
  - Normalized price comparison (% change)
  - Sector index comparison

- [ ] Additional chart types
  - Candlestick charts
  - Volume bars
  - Financial ratios over time

### Dashboard

- [ ] Customizable dashboard
  - Add/remove widgets
  - Drag and drop layout
  - Multiple dashboard tabs

---

## Version 2.3 - Data & Integrations

### Data Sources

- [ ] Multiple data source support
  - Alpha Vantage integration
  - FMP (Financial Modeling Prep) integration
  - Polygon.io integration

- [ ] 10K/10Q report parsing
  - Extract key sections
  - Parse MD&A (Management Discussion)
  - Track executive comments

### API & MCP Development

- [ ] Continue high-priority REST API and MCP hardening from the dedicated section above
  - Authentication via API keys
  - Rate limiting
  - Documentation (OpenAPI/Swagger)
  - MCP client compatibility validation

### Export/Import

- [ ] Database backup/restore
- [ ] Import custom ticker lists
- [ ] Share portfolios

---

## Version 3.0 - Advanced Features

### Portfolio Management

- [ ] Watchlist functionality
  - Add companies to watchlist
  - Multiple watchlists
  - Notes per company

- [ ] Portfolio tracking
  - Track holdings
  - Calculate portfolio performance
  - Allocation charts

### Analysis Tools

- [ ] DCF (Discounted Cash Flow) calculator
- [ ] Relative valuation models
- [ ] Altman Z-Score calculation
- [ ] Piotroski F-Score

### AI/ML Features (Future)

- [ ] Anomaly detection
- [ ] Sentiment analysis on news
- [ ] Price prediction models
- [ ] Recommendation engine

---

## Ideas & Suggestions

Have an idea? Submit a feature request!

### Community Suggestions

*Add your suggestions here:*

- [ ] Watchlist/favorites functionality
- [ ] Portfolio tracking
- [ ] Price alerts
- [ ] Sector performance dashboard
- [ ] Customizable dashboard widgets
- [ ] Dark/light theme toggle
- [ ] Mobile app
- [ ] Real-time price updates via WebSocket
- [ ] **Comparison workspace**: Select multiple companies and compare valuation, growth, margins, and price performance side by side.
- [x] Technical analysis charts
- [x] Insider trading data
- [x] Institutional ownership data
- [x] Options chain data
- [x] SEC filings integration
- [x] Earnings calendar
- [ ] Stock screener with more criteria
- [ ] **Incremental refreshes**: Fetch only new stock-price rows and recently reported quarters instead of reprocessing the full ticker universe
- [ ] **Data-source fallback**: Add alternate providers for missing Yahoo Finance values and mark source provenance per field.
- [ ] **Margin charts**: Add gross, operating, and net-margin trends beside revenue and expense charts.
- [ ] **Background job dashboard**: Show whether the downloader is idle, running, failed, or disabled.
- [ ] **Automated tests**: Add unit tests for calculations, downloader parsing, route responses, and chart payload shapes.

---

## Completed Features

### Version 1.0 (Current)

- [x] Data download from Yahoo Finance (770+ companies)
- [x] SQLite database storage
- [x] Company filtering by P/E ratio
- [x] Revenue growth filtering
- [x] Calculated P/E vs Yahoo P/E
- [x] P/E spread analysis
- [x] Interactive financial charts
- [x] Stock price history charts
- [x] Dual-axis combined charts
- [x] Company detail pages
- [x] News integration
- [x] Risk analysis metrics
- [x] Competitor comparison
- [x] Dark theme UI
- [x] Responsive design
- [x] All companies listing
- [x] Companies JSON API foundation
- [x] MCP stdio server foundation
- [x] API and MCP documentation
- [x] Dashboard quick filter presets and active filter summary

### Version 1.1 (Recent Updates)

- [x] Pagination for all companies page (50 per page)
- [x] Search functionality (ticker, name, sector, industry)
- [x] Sort by columns (ticker, sector, P/E, market cap)
- [x] CSV export for filtered results
- [x] CSV export for all companies

---

## Contributing

Contributions are welcome! Please see the main README for setup instructions.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Implement the feature
4. Add tests if applicable
5. Submit a pull request

---

*Last Updated: June 2026*
