# Stock Screener - Financial Analysis Web Application

A comprehensive Flask-based web application for analyzing publicly traded companies. Download financial data from Yahoo Finance, filter by P/E ratio and revenue growth, and explore interactive charts and detailed company analysis.

![Stock Screener](https://img.shields.io/badge/Version-1.0-brightgreen) ![Python](https://img.shields.io/badge/Python-3.12-blue) ![Flask](https://img.shields.io/badge/Flask-3.1.x-red)

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Financial Calculations](#financial-calculations)
- [Frontend Features](#frontend-features)
- [Understanding P/E Metrics](#understanding-p/e-metrics)
- [Troubleshooting](#troubleshooting)
- [Technology Stack](#technology-stack)
- [Testing](#testing)
- [License](#license)
- [Additional Documentation](#additional-documentation)

---

## Features

### Core Functionality

- **Data Download**: Fetch financial data for 770+ companies from Yahoo Finance
- **SQLite Storage**: Local database for fast querying and offline analysis
- **Interactive Filtering**: Filter companies by P/E ratio, revenue growth, and P/E spread
- **Dual P/E Calculations**: Compare Yahoo P/E with custom calculated P/E
- **P/E Spread Analysis**: Identify anomalies between calculated and reported P/E ratios

### Data Visualization

- **Financial Charts**: Revenue, OPEX, and CAPEX trends over time
- **Price Charts**: 1-year stock price history
- **Combined Charts**: Dual-axis charts correlating financials with stock price
- **Competitor Comparison**: Side-by-side industry peer analysis

### Company Analysis

- **Summary Statistics**: P/E, market cap, revenue, net income, growth
- **Latest News**: Real-time news from Yahoo Finance
- **Risk Analysis**: Key risk metrics with Low/Medium/High ratings
- **Industry Peers**: Competitors in the same industry

---

## Quick Start

```bash
# 1. Clone and setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Download data (first time only - takes ~30 minutes for 770+ companies)
python download_data.py

# 3. Run the web server
python app.py

# 4. Open in browser
# http://localhost:5000
```

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Step-by-Step Setup

```bash
# Navigate to project directory
cd /home/coder/Projects

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install flask-sqlalchemy

# Verify installation
python -c "import flask; print(flask.__version__)"
```

### requirements.txt Contents

```
flask>=3.0.0
flask-sqlalchemy>=3.0.0
sqlalchemy>=2.0.0
yfinance>=0.2.0
pandas>=2.0.0
plotly>=5.0.0
```

---

## Usage

### Running the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run Flask app
python app.py
```

The application will start at `http://localhost:5000`

### Downloading Data

```bash
# Download data for all tickers
python download_data.py
```

This script will:
1. Fetch ~770 stock tickers (S&P 500 + popular stocks/ETFs)
2. Download company info (name, sector, P/E, market cap)
3. Download 2 years of daily stock prices
4. Download quarterly financial reports
5. Store everything in SQLite database

### Filtering Companies

Access the homepage with query parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| max_pe | Maximum P/E ratio | `?max_pe=20` |
| min_growth | Minimum revenue growth % | `?min_growth=15` |
| use_calc_pe | Use calculated P/E | `?use_calc_pe=true` |
| min_pe_spread_abs | Minimum absolute spread | `?min_pe_spread_abs=30` |
| min_pe_spread_pos | Minimum positive spread | `?min_pe_spread_pos=20` |
| min_pe_spread_neg | Minimum negative spread | `?min_pe_spread_neg=20` |

**Example URLs:**

```
# Default filters (P/E < 25, Growth > 10%)
http://localhost:5000/

# Stricter filters
http://localhost:5000/?max_pe=20&min_growth=15

# Use calculated P/E
http://localhost:5000/?use_calc_pe=true&max_pe=25

# Find P/E anomalies (large spread)
http://localhost:5000/?min_pe_spread_abs=50
```

---

## Project Structure

```
/home/coder/Projects/
├── app.py                  # Flask application - all routes and business logic
├── download_data.py        # Data download script - fetches from Yahoo Finance
├── models.py              # SQLAlchemy ORM models - database schema
├── market_data.py         # Market-data fetch/persist/load helpers
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── docs/                  # Project planning and technical documentation
│   ├── SPEC.md            # Technical specification document
│   ├── ROADMAP.md         # Planned enhancements
│   └── IDEAS.md           # Suggested improvements
├── stocks.db              # SQLite database (created at runtime)
├── .gitignore             # Git ignore patterns
├── templates/
│   ├── index.html        # Homepage - filter form and results table
│   ├── ticker.html       # Company detail page - 6 tabs
│   └── all.html          # All companies list page
├── tests/                # Regression tests
└── venv/                 # Python virtual environment
```

---

## Database Schema

### Companies Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| ticker | VARCHAR(20) | Stock symbol (unique, indexed) |
| name | VARCHAR(200) | Company name |
| sector | VARCHAR(100) | Business sector |
| industry | VARCHAR(100) | Industry classification |
| website_url | VARCHAR(500) | Company website |
| pe_ratio | FLOAT | Yahoo trailing P/E |
| market_cap | BIGINT | Market capitalization |

### Financial Reports Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| company_id | INTEGER | Foreign key to companies |
| quarter | INTEGER | Fiscal quarter (1-4) |
| year | INTEGER | Fiscal year |
| revenue | FLOAT | Total revenue |
| opex | FLOAT | Operating expenses |
| capex | FLOAT | Capital expenditures |
| net_income | FLOAT | Net profit |

### Stock Prices Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| company_id | INTEGER | Foreign key to companies |
| date | DATE | Trading date |
| open_price | FLOAT | Opening price |
| high | FLOAT | Intraday high |
| low | FLOAT | Intraday low |
| close | FLOAT | Closing price |
| volume | BIGINT | Trading volume |

### Database Indexes

```sql
CREATE INDEX idx_ticker ON companies(ticker);
CREATE INDEX idx_company_report ON financial_reports(company_id, year, quarter);
CREATE INDEX idx_company_date ON stock_prices(company_id, date);
```

---

## API Endpoints

### Homepage
- **Route:** `GET /`
- **Description:** Filtered companies table
- **Parameters:** max_pe, min_growth, use_calc_pe, min_pe_spread_*

### All Companies
- **Route:** `GET /all`
- **Description:** Complete company list without filters

### Ticker Detail
- **Route:** `GET /ticker/<company_id>`
- **Description:** Detailed company analysis page
- **Tabs:** Financials, Price, Combined, News, Risk Analysis, Competitors

### Companies API
- **Route:** `GET /api/companies`
- **Description:** Paginated JSON company list with search, sector/industry, debt, sorting, and pagination query parameters
- **Documentation:** See [API docs](docs/API.md)

### Company Detail API
- **Route:** `GET /api/companies/<ticker>`
- **Description:** JSON company detail with computed screening metrics, latest report, and latest price
- **Documentation:** See [API docs](docs/API.md)

### Chart Data
- **Route:** `GET /chart/<company_id>`
- **Description:** JSON with financial and price data for charts

### News API
- **Route:** `GET /api/news/<ticker>`
- **Description:** Latest company news from Yahoo Finance
- **Response:** JSON array of news articles

### Risks API
- **Route:** `GET /api/risks/<ticker>`
- **Description:** Risk metrics with Low/Medium/High ratings
- **Response:** JSON array of risk metrics

### Market Data API
- **Route:** `GET /api/market-data/<ticker>`
- **Description:** Cached market-data payload for ownership, insider transactions, options, earnings calendar, and SEC filing links. Falls back to a live fetch when cached data is missing.
- **Persistence:** Data is stored in dedicated tables and refreshed by `download_data.py` during scheduled background downloads.

---

## Financial Calculations

### Calculated P/E Ratio

```python
Calculated P/E = Price / (TTM Net Income / Estimated Shares)

Where:
- Price = Latest closing price from database
- TTM Net Income = Sum of last 4 quarters net income
- Estimated Shares = Market Cap / Price
```

### Revenue Growth

```python
growth = ((current_quarter_revenue - previous_quarter_revenue) 
          / previous_quarter_revenue) * 100
```

### Daily Price Change

```python
daily_change = ((latest_close - previous_close) / previous_close) * 100
```

---

## Frontend Features

### Homepage

- **Filter Form**: Adjustable inputs for P/E, growth, P/E spread
- **Results Table**: Sortable columns with color-coded values
- **Chart Modal**: Interactive Plotly chart with dual Y-axis
- **Quick Links**: Direct links to Yahoo Finance, company website

### Ticker Page

#### Summary Header
- Stock price and daily change
- P/E ratios (Yahoo and Calculated)
- Market cap, revenue, net income
- Revenue growth percentage

#### Tab: Financials
- Revenue/OPEX/CAPEX line chart
- Quarterly data table
- Notes on CAPEX interpretation

#### Tab: Stock Price
- 1-year price history
- 20-day and 50-day simple moving average overlays
- Area fill for visual appeal

#### Tab: Market Data
- Cached ownership, insider transaction, options, earnings calendar, and SEC filing data
- Displays source, fetch status, and last refresh metadata

#### Tab: Combined
- Dual-axis chart
- Financials on left axis
- Stock price on right axis

#### Tab: News
- Latest 10 news articles
- Links to full articles

#### Tab: Risk Analysis
- Beta (volatility)
- Debt to Equity
- Audit risk, Compensation risk
- Dividend metrics

#### Tab: Competitors
- Companies in same industry
- Revenue, OPEX, CAPEX, Net Income
- Percentage comparisons

---

## Understanding P/E Metrics

### Yahoo P/E vs Calculated P/E

| Source | Description |
|--------|-------------|
| Yahoo P/E | Official trailing P/E from Yahoo Finance based on reported earnings |
| Calculated P/E | Custom calculation using latest price and TTM net income |

### P/E Spread Interpretation

| Spread | Meaning | Potential Cause |
|--------|---------|------------------|
| Large Positive | Calculated >> Yahoo | One-time earnings boost, outdated market cap |
| Small Positive | Similar values | Healthy alignment |
| Small Negative | Similar values | Healthy alignment |
| Large Negative | Calculated << Yahoo | Expected growth, conservative accounting |

### Example: Identifying Anomalies

Companies with large P/E spreads may indicate:
- Exceptional one-time items
- Accounting method differences
- Recent share buybacks
- Data quality issues

---

## Troubleshooting

### No companies showing after running download_data.py

**Cause:** Database not populated

**Solution:**
```bash
python download_data.py
```

### Chart not loading on ticker page

**Cause:** Missing financial data for company

**Solution:** Check if company has financial reports in database
```bash
sqlite3 stocks.db "SELECT * FROM financial_reports WHERE company_id=1 LIMIT 5;"
```

### Calculated P/E showing as None

**Cause:** Insufficient data for calculation

**Requirements:**
- At least 4 quarters of net income data
- Valid market cap from Yahoo Finance
- Positive net income

### Import errors when running app

**Cause:** Virtual environment not activated

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Database locked error

**Cause:** Another process using database

**Solution:** Close other Flask instances and try again

---

## Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | Flask 3.1.x | HTTP routing, request handling |
| ORM | SQLAlchemy 2.x | Database abstraction |
| Database | SQLite 3.x | Local data storage |
| Data API | yfinance | Yahoo Finance data fetching |
| Data Processing | pandas | Data manipulation |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| UI Framework | Bootstrap 5.3 | Responsive design |
| Charts | Plotly.js 2.27 | Interactive visualizations |
| JavaScript | ES6+ | Client-side logic |
| Styling | CSS Variables | Dark theme |

---

## Current Statistics

As of the latest data download:

- **Companies**: 770+
- **Financial Reports**: 3,000+
- **Stock Prices**: 150,000+
- **CAPEX Records**: 500+

---

## Understanding the UI

### Color Coding

| Color | Meaning |
|-------|---------|
| Green | Positive values, undervaluation signals |
| Red | Negative values, overvaluation signals |
| Blue | Accent, interactive elements |

### Dark Theme

The application uses a dark theme inspired by GitHub's design:
- Background: `#0d1117`
- Cards: `#161b22`
- Borders: `#30363d`
- Text: `#e6edf3`

---

## Testing

```bash
python -m pytest
```

The test suite includes regression checks for market-data persistence models, downloader refresh wiring, API cache-first behavior, company API documentation coverage, MCP protocol metadata behavior, and an MCP stdio initialize smoke test.

---

## Additional Documentation

- [API reference](docs/API.md)
- [MCP server guide](docs/MCP.md)
- [Technical specification](docs/SPEC.md)
- [Roadmap](docs/ROADMAP.md)
- [Improvement ideas](docs/IDEAS.md)

---

## License

MIT License - Feel free to use and modify for your own purposes.

---

## Additional Resources

- [Yahoo Finance](https://finance.yahoo.com/) - Source of financial data
- [Flask Documentation](https://flask.palletsprojects.com/) - Web framework
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/) - ORM
- [Plotly JavaScript](https://plotly.com/javascript/) - Charting library
- [Bootstrap 5](https://getbootstrap.com/) - UI framework
