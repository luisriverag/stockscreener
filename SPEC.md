# Financial Analysis Web Application

## Project Overview
- **Project name**: Stock Analyzer
- **Type**: Flask web application
- **Core functionality**: Download financial reports and stock prices, filter companies by P/E ratio and revenue growth, display interactive charts
- **Target users**: Investors and financial analysts

## Functionality Specification

### Data Download
1. **10K Reports**: Download financial data for ~10k companies using yfinance
2. **Stock Prices**: Download daily stock prices for all companies
3. **Data Storage**: SQLite database with SQLAlchemy

### Database Models
- `Company`: ticker, name, sector, industry, website_url, pe_ratio, market_cap
- `FinancialReport`: company_id, quarter, year, revenue, opex, capex, net_income
- `StockPrice`: company_id, date, open, high, low, close, volume

### Filtering Criteria
- P/E Ratio < 25
- Quarterly Revenue Growth > 10%

### Web Interface
- **Home page**: List of filtered companies with:
  - Ticker symbol
  - Daily price change %
  - Company website URL
  - Yahoo Finance URL
  - Interactive chart showing revenue, opex, capex over time with stock price on secondary y-axis

## Technical Stack
- Flask
- SQLAlchemy
- yfinance (for stock data)
- Plotly (for interactive charts)
- Bootstrap (for styling)

## Acceptance Criteria
1. Successfully downloads and stores data for 10k companies
2. Filters show companies with PER < 25 and revenue growth > 10%
3. Charts display revenue, opex, capex with stock price on secondary axis
4. All URLs are clickable and work correctly
