# Stock Analyzer - Financial Analysis Web Application

## Overview

A Flask-based web application that downloads financial data and stock prices for 700+ companies, filters them by various financial metrics, and displays interactive charts with detailed company analysis.

## Features

### 1. Data Download
- Downloads 10K reports (quarterly financial statements) for ~770 S&P companies and popular tickers
- Downloads 2 years of daily stock price history
- Stores data in SQLite database

### 2. Filtering (Web Configurable)
- **P/E Ratio**: Maximum P/E threshold (default: 25)
- **Revenue Growth**: Minimum quarterly revenue growth % (default: 10%)
- **P/E Type Toggle**: Use Yahoo P/E or Calculated P/E
- **P/E Spread**: Minimum spread between Calculated and Yahoo P/E

### 3. P/E Calculations

#### Yahoo P/E
- Fetched directly from Yahoo Finance API (`info.get("trailingPE")`)
- Trailing 12-month P/E based on reported earnings

#### Calculated P/E
```
Calculated P/E = Price / (TTM Net Income / Estimated Shares)

Where:
- Price = Latest closing price from database
- TTM Net Income = Sum of last 4 quarters net income
- Estimated Shares = Market Cap / Price (estimated from Yahoo data)
```

#### P/E Spread
```
Spread = Calculated P/E - Yahoo P/E

Interpretation:
- Positive spread: Calculated > Yahoo (potential overvaluation or accounting differences)
- Negative spread: Calculated < Yahoo (potential undervaluation or one-time earnings boost)
```

### 4. Web Interface
- **Homepage**: Filtered companies table with all metrics
- **Ticker Pages**: Detailed company analysis with charts
- **All Companies**: Browse all 770+ companies

## Project Structure

```
/home/coder/Projects/
├── app.py                 # Flask web server with all routes and logic
├── download_data.py       # Data download script (770+ tickers)
├── models.py             # SQLAlchemy database models
├── requirements.txt      # Python dependencies
├── README.md            # This documentation
├── SPEC.md              # Project specification
├── stocks.db            # SQLite database (created on first run)
├── templates/
│   ├── index.html       # Homepage with filters
│   ├── ticker.html     # Individual company page
│   └── all.html        # All companies list
└── venv/               # Virtual environment
```

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install flask-sqlalchemy
```

## Usage

### 1. Download Data

```bash
source venv/bin/activate
python download_data.py
```

This will:
- Fetch 770+ ticker symbols (S&P 500 + popular stocks/ETFs)
- For each company:
  - Download company info (name, sector, P/E, market cap, website)
  - Download 2 years of daily stock prices
  - Download quarterly financial reports (revenue, opex, capex, net income)

### 2. Run Web Server

```bash
source venv/bin/activate
python app.py
```

Server runs at: `http://localhost:5000`

## Database Schema

### Company
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| ticker | String | Stock symbol (unique, indexed) |
| name | String | Company name |
| sector | String | Business sector |
| industry | Industry classification |
| website_url | String | Company website |
| pe_ratio | Float | Yahoo trailing P/E ratio |
| market_cap | BigInteger | Market capitalization |

### FinancialReport
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| company_id | Integer | Foreign key to Company |
| quarter | Integer | Quarter (1-4) |
| year | Integer | Year |
| revenue | Float | Total revenue |
| opex | Float | Operating expenses |
| capex | Float | Capital expenditures |
| net_income | Float | Net income |

### StockPrice
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| company_id | Integer | Foreign key to Company |
| date | Date | Trading date |
| open_price | Float | Opening price |
| high | Float | High price |
| low | Float | Low price |
| close | Float | Closing price |
| volume | BigInteger | Trading volume |

## API Endpoints

### GET /
**Homepage** - Returns HTML page with filtered companies table.

Query Parameters:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| max_pe | float | 25 | Maximum P/E ratio filter |
| min_growth | float | 10 | Minimum revenue growth % |
| use_calc_pe | string | "false" | "true" to use calculated P/E |
| min_pe_spread | float | - | Minimum \|Calc - Yahoo\| P/E spread |

**Examples:**
```
/                              # Default: P/E < 25, Growth > 10%
/?max_pe=30&min_growth=5      # P/E < 30, Growth > 5%
/?use_calc_pe=true&max_pe=25  # Use calculated P/E
/?min_pe_spread=20            # Show only where spread > 20
```

### GET /all
**All Companies** - Returns HTML page with all companies (no filter).

### GET /ticker/<company_id>
**Ticker Detail Page** - Returns HTML page with detailed company information:
- Summary stats (P/E both methods, market cap, revenue, net income, growth)
- Financial charts (revenue, opex, capex over time)
- Stock price chart (1 year history)
- Latest news tab (via Yahoo Finance API)
- Competitors tab (same industry)

### GET /chart/<company_id>
**Chart Data API** - Returns JSON with financial data and price history.

Response:
```json
{
  "ticker": "DIS",
  "name": "Walt Disney Company (The)",
  "reports": [
    {
      "period": "2024 Q4",
      "revenue": 24.69,
      "opex": 5.206,
      "capex": 0
    }
  ],
  "prices": [
    {
      "date": "2024-02-26",
      "close": 105.54
    }
  ]
}
```

### GET /api/news/<ticker>
**News API** - Returns JSON with latest company news from Yahoo Finance.

## Filtering Logic

### Revenue Growth Calculation
```python
growth = ((current_quarter_revenue - previous_quarter_revenue) / previous_quarter_revenue) * 100
```

### Daily Price Change
```python
daily_change = ((latest_close - previous_close) / previous_close) * 100
```

### Calculated P/E Formula
```python
# Step 1: Get latest price
latest_price = StockPrice.query.filter_by(company_id=id).order_by(date.desc()).first()

# Step 2: Get TTM net income (last 4 quarters)
reports = FinancialReport.query.filter_by(company_id=id).order_by(year.desc(), quarter.desc()).limit(4).all()
ttm_net_income = sum(r.net_income for r in reports)

# Step 3: Estimate shares from market cap
estimated_shares = company.market_cap / latest_price.close

# Step 4: Calculate EPS and P/E
eps = ttm_net_income / estimated_shares
calculated_pe = latest_price.close / eps
```

### P/E Spread
```python
pe_spread = calculated_pe - yahoo_pe_ratio

# Filter: Show only companies with |spread| > min_pe_spread
if min_pe_spread and abs(pe_spread) < min_pe_spread:
    exclude_company()
```

## Chart Configuration

- **Financial Chart**: Revenue, OPEX, CAPEX in billions ($)
- **Price Chart**: Stock price with area fill
- **Interactive**: Zoom, pan, hover tooltips via Plotly

## Current Database Stats

- **Companies**: 772
- **Financial Reports**: 3,175+
- **Price Records**: 150,000+

## Current Filtered Results (Default Filters)

Companies matching criteria (P/E < 25, revenue growth > 10%):

| Ticker | P/E (Yahoo) | P/E (Calc) | Spread | Growth |
|--------|-------------|-------------|--------|--------|
| DIS | 15.62 | ~15.7 | -0.9 | 15.7% |
| SO | 23.83 | ~23.1 | -0.7 | 12.2% |
| DUK | 20.36 | ~19.8 | -0.6 | 13.8% |
| GD | 22.73 | ~22.1 | -0.6 | 11.4% |

## Understanding P/E Spread

Large spreads between calculated and Yahoo P/E can indicate:

| Scenario | Calculated vs Yahoo | Possible Reasons |
|----------|---------------------|------------------|
| Calculated >> Yahoo | Positive spread | One-time earnings boost, market cap outdated, accounting differences |
| Calculated << Yahoo | Negative spread | Expected earnings growth, conservative accounting, share count changes |
| Similar | Small spread | Healthy alignment between market price and reported earnings |

### Example: Companies with Large Spreads

| Ticker | Yahoo P/E | Calc P/E | Spread |
|--------|-----------|----------|--------|
| GLBE | 87.95 | 794.54 | +706.59 |
| LSCC | 4918.00 | 4362.62 | -555.38 |
| TWLO | 569.25 | 259.88 | -309.37 |
| GPC | 247.54 | 20.44 | -227.10 |
| HE | 7.23 | 157.84 | +150.62 |

These large spreads often indicate:
- Very high/low Yahoo P/E (exceptional cases)
- Significant differences in how earnings are calculated
- Recent share issuances or buybacks not reflected in market cap

## Ticker Page Features

### Summary Stats
- Current stock price
- Daily change %
- P/E (Yahoo)
- P/E (Calculated)
- Market Cap
- Quarterly Revenue
- Quarterly Net Income
- Revenue Growth %

### Tabs
1. **Financials**: Revenue, OPEX, CAPEX chart + quarterly table
2. **Stock Price**: 1-year price history chart
3. **News**: Latest 10 news articles from Yahoo Finance
4. **Competitors**: Other companies in same industry

## Dependencies

- **Flask** - Web framework
- **SQLAlchemy** - ORM
- **Flask-SQLAlchemy** - Flask integration for SQLAlchemy
- **yfinance** - Yahoo Finance data download
- **pandas** - Data manipulation
- **plotly** - Interactive charts
- **Bootstrap 5** - UI styling

## Extending

### Add More Companies
Modify `SAMPLE_TICKERS` list in `download_data.py` to add more tickers.

### Change Default Filter Values
Edit in `app.py`:
```python
max_pe = request.args.get("max_pe", 25, type=float)  # Change 25
min_growth = request.args.get("min_growth", 10, type=float)  # Change 10
```

### Add More Financial Metrics
1. Add columns to `FinancialReport` model in `models.py`
2. Update `download_data.py` to fetch new data
3. Update templates to display new data

### Modify Chart Display
Edit `templates/ticker.html` JavaScript section to change:
- Chart colors
- Line styles
- Axis labels
- Time periods

## Troubleshooting

### No companies showing
- Run `python download_data.py` to populate database
- Check database: `sqlite3 stocks.db "SELECT * FROM companies LIMIT 5;"`

### Chart not loading
- Check API: `curl http://localhost:5000/chart/1`
- Verify financial reports exist in database

### Import errors
- Ensure virtual environment is activated: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

### Calculated P/E showing as None
- Requires 4 quarters of financial data
- Requires valid market cap
- Company must have positive net income

## URLs

- Homepage: `http://localhost:5000/`
- All Companies: `http://localhost:5000/all`
- Ticker Example: `http://localhost:5000/ticker/30` (DIS)

## Design Decisions

1. **Calculated P/E uses market cap estimation** - Since exact share counts aren't always available, we estimate using market cap / price
2. **4-quarter TTM** - Uses last 4 quarters for trailing twelve months earnings
3. **P/E Spread filter is minimum** - Shows companies where the difference is larger (interesting anomalies)
4. **Green/Red colors**:
   - Green (negative spread): Calculated < Yahoo (potentially undervalued)
   - Red (positive spread): Calculated > Yahoo (potentially overvalued)
