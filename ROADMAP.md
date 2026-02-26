# Stock Screener - Roadmap

This document outlines planned and proposed enhancements for the Stock Screener application.

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

- [ ] Export functionality
  - Export filtered results to CSV
  - Export to Excel with formatting
  - Export charts as PNG/SVG

- [ ] Email alerts
  - Set price alerts
  - Filter match notifications
  - Daily/weekly digest option

### Search & Navigation

- [ ] Global search (ticker/name)
- [ ] Sort by any column
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

### API Development

- [ ] RESTful API for third-party access
  - Authentication via API keys
  - Rate limiting
  - Documentation (OpenAPI/Swagger)

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

- [ ] _________________________
- [ ] _________________________
- [ ] _________________________

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

*Last Updated: February 2026*
