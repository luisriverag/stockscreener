# Stock Screener - Technical Specification Document

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Database Design](#database-design)
4. [Data Flow & Processing](#data-flow--processing)
5. [API Endpoints Reference](#api-endpoints-reference)
6. [Financial Calculations](#financial-calculations)
7. [Frontend Architecture](#frontend-architecture)
8. [User Workflows](#user-workflows)
9. [Data Sources](#data-sources)
10. [Error Handling](#error-handling)
11. [Performance Considerations](#performance-considerations)

---

## Architecture Overview

The Stock Screener is a **full-stack web application** built with Flask that enables users to filter, analyze, and compare publicly traded companies based on financial metrics. It fetches data from Yahoo Finance and stores it locally in SQLite for fast querying and offline analysis.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (Browser)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  Homepage    │  │  Ticker Page │  │  All Companies Page │ │
│  │  (Filters)   │  │  (6 Tabs)    │  │  (Full List)        │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    HTTP Requests / JSON
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flask Application                          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Routes: /, /all, /ticker/<id>, /chart/<id>, /api/*       │ │
│  │  Business Logic: calculate_pe(), filter_companies()        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SQLAlchemy ORM                            │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │   Company    │  │ FinancialReport│  │   StockPrice     │  │
│  │    Model     │  │    Model       │  │    Model         │  │
│  └──────────────┘  └────────────────┘  └──────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SQLite Database                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  stocks.db (companies, financial_reports, stock_prices)   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Web Framework | Flask | 3.1.x | HTTP routing, request handling |
| ORM | SQLAlchemy | Latest | Database abstraction |
| Database | SQLite | 3.x | Local relational database |
| Data Fetching | yfinance | Latest | Yahoo Finance API wrapper |
| Data Processing | pandas | Latest | Data manipulation |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| UI Framework | Bootstrap | 5.3.x | Responsive layout, components |
| Charts | Plotly.js | 2.27.x | Interactive financial charts |
| JavaScript | Vanilla ES6+ | - | Client-side logic |
| CSS | Custom CSS Variables | - | Dark theme styling |

### Development

| Component | Technology | Purpose |
|-----------|------------|---------|
| Virtual Environment | Python venv | Dependency isolation |
| Package Manager | pip | Python package installation |

---

## Database Design

### Entity Relationship Diagram

```
┌─────────────────────┐       ┌──────────────────────┐
│      Company       │       │   FinancialReport    │
├─────────────────────┤       ├──────────────────────┤
│ id (PK)            │◄──────│ company_id (FK)       │
│ ticker (UQ, IDX)   │  1:N  │ quarter              │
│ name               │       │ year                 │
│ sector             │       │ revenue              │
│ industry           │       │ opex                 │
│ website_url        │       │ capex                │
│ pe_ratio           │       │ net_income           │
│ market_cap         │       └──────────────────────┘
│ pe_forward         │
│ shares_outstanding │       ┌──────────────────────┐
└─────────────────────┘       │    StockPrice       │
         │                    ├──────────────────────┤
         │ 1:N                │ id (PK)             │
         ▼                    │ company_id (FK)     │
┌─────────────────────┐        │ date                │
│   Relationships   │        │ open_price          │
├─────────────────────┤        │ high                │
│ financial_reports  │        │ low                 │
│ stock_prices       │        │ close               │
└─────────────────────┘        │ volume              │
                               └──────────────────────┘
```

### Table Specifications

#### companies

```sql
CREATE TABLE companies (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200),
    sector VARCHAR(100),
    industry VARCHAR(100),
    website_url VARCHAR(500),
    pe_ratio FLOAT,
    market_cap BIGINT,
    pe_forward FLOAT,
    shares_outstanding BIGINT
);

CREATE INDEX idx_ticker ON companies(ticker);
```

**Field Descriptions:**

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| id | Integer | Auto-increment primary key | Auto |
| ticker | String | Stock symbol (unique) | User-defined list |
| name | String | Company legal name | Yahoo Finance `shortName`/`longName` |
| sector | String | Business sector classification | Yahoo Finance `sector` |
| industry | String | Industry within sector | Yahoo Finance `industry` |
| website_url | String | Official company website | Yahoo Finance `website` |
| pe_ratio | Float | Trailing P/E ratio (TTM) | Yahoo Finance `trailingPE` |
| market_cap | BigInteger | Total market capitalization | Yahoo Finance `marketCap` |
| pe_forward | Float | Forward P/E ratio (estimated) | Yahoo Finance `forwardPE` |
| shares_outstanding | BigInteger | Total shares issued | Yahoo Finance `sharesOutstanding` |

#### financial_reports

```sql
CREATE TABLE financial_reports (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL,
    quarter INTEGER,
    year INTEGER,
    revenue FLOAT,
    opex FLOAT,
    capex FLOAT,
    net_income FLOAT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX idx_company_report ON financial_reports(company_id, year, quarter);
```

**Field Descriptions:**

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| id | Integer | Auto-increment primary key | Auto |
| company_id | Integer | Foreign key to companies | Auto |
| quarter | Integer | Fiscal quarter (1-4) | Derived from report date |
| year | Integer | Fiscal year | Derived from report date |
| revenue | Float | Total quarterly revenue | Yahoo Finance `quarterly_financials` |
| opex | Float | Operating expenses | Yahoo Finance `quarterly_financials` |
| capex | Float | Capital expenditures | Yahoo Finance `cashflow` |
| net_income | Float | Net profit after taxes | Yahoo Finance `quarterly_financials` |

**Note on CAPEX:** Capital expenditure data is fetched from the `cashflow` section of Yahoo Finance, not from quarterly financials. CAPEX values from Yahoo Finance are negative (representing cash outflows) and are stored as-is; the application displays them as absolute values for chart visualization.

#### stock_prices

```sql
CREATE TABLE stock_prices (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL,
    date DATE NOT NULL,
    open_price FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume BIGINT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX idx_company_date ON stock_prices(company_id, date);
```

**Field Descriptions:**

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| id | Integer | Auto-increment primary key | Auto |
| company_id | Integer | Foreign key to companies | Auto |
| date | Date | Trading date | Yahoo Finance history |
| open_price | Float | Opening price | Yahoo Finance history |
| high | Float | Intraday high | Yahoo Finance history |
| low | Float | Intraday low | Yahoo Finance history |
| close | Float | Closing price | Yahoo Finance history |
| volume | BigInteger | Trading volume | Yahoo Finance history |

---

## Data Flow & Processing

### Data Download Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    download_data.py                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Get Ticker List (SAMPLE_TICKERS - ~1000 tickers)          │
│     - S&P 500 components                                       │
│     - Popular ETFs                                             │
│     - Large-cap growth stocks                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         │ For each ticker:                       │
         ▼                                        ▼
┌─────────────────────┐               ┌─────────────────────────┐
│ 2a. Company Info    │               │ 2b. Stock Price History │
│ - name, sector     │               │ - 2 years daily data   │
│ - P/E, market cap  │               │ - OHLC + volume        │
│ - website          │               │ - Deduplication by date│
└─────────────────────┘               └─────────────────────────┘
         │                                        │
         └───────────────────┬────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Quarterly Financials                                       │
│  - Revenue, OPEX, Net Income from quarterly_financials         │
│  - CAPEX from cashflow (separate API call)                     │
│  - Deduplication by (year, quarter)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Store in SQLite                                           │
│  - Transaction per company                                      │
│  - Batch inserts for prices                                    │
│  - Upsert logic for reports                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Data Processing at Runtime

#### Company Filtering Flow

```
User Request (HTTP GET /)
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Parse Query Parameters                                        │
│  - max_pe (default: 25)                                       │
│  - min_growth (default: 10)                                    │
│  - use_calc_pe (default: false)                                │
│  - min_pe_spread_abs / pos / neg                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Fetch All Companies from Database                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         │ For each company:                     │
         ▼                                        ▼
┌─────────────────────┐               ┌─────────────────────────────┐
│ Calculate P/E      │               │ Check Filters               │
│ - Fetch latest price│              │ - P/E < max_pe?            │
│ - Sum 4Q net income│               │ - Growth > min_growth?     │
│ - Calc from market │               │ - Spread filter matches?   │
│   cap              │               │                             │
└─────────────────────┘               └─────────────────────────────┘
         │                                        │
         └───────────────────┬────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Render Template with Filtered Results                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints Reference

### HTTP Endpoints

#### GET /

**Purpose:** Homepage with filtered companies list

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| max_pe | float | 25 | Maximum P/E ratio (Yahoo or calculated) |
| min_growth | float | 10 | Minimum quarterly revenue growth (%) |
| use_calc_pe | string | "false" | Use calculated P/E instead of Yahoo P/E |
| min_pe_spread_abs | float | - | Minimum absolute spread (\|Calc - Yahoo\|) |
| min_pe_spread_pos | float | - | Minimum positive spread (Calc > Yahoo) |
| min_pe_spread_neg | float | - | Minimum negative spread (Calc < Yahoo) |

**Example Requests:**

```bash
# Default filter
GET /

# Custom P/E and growth threshold
GET /?max_pe=30&min_growth=5

# Use calculated P/E
GET /?use_calc_pe=true&max_pe=25

# Filter by large spread (anomalies)
GET /?min_pe_spread_abs=50
```

**Response:** HTML page with filtered companies table

---

#### GET /all

**Purpose:** Display all companies without filtering

**Response:** HTML page with all companies in database

---

#### GET /ticker/<company_id>

**Purpose:** Detailed company analysis page

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| company_id | int | Primary key of company in database |

**Response:** HTML page with 6 tabs:
1. **Financials** - Revenue, OPEX, CAPEX charts + data table
2. **Stock Price** - 1-year price history chart
3. **Combined** - Dual-axis chart (financials + price)
4. **News** - Latest news articles (loaded via API)
5. **Risk Analysis** - Risk metrics with ratings (loaded via API)
6. **Competitors** - Companies in same industry with comparison metrics

---

#### GET /chart/<company_id>

**Purpose:** JSON endpoint for financial and price data

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| company_id | int | Primary key of company |

**Response (JSON):**

```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "reports": [
    {
      "period": "2024 Q4",
      "revenue": 94.93,
      "opex": 14.19,
      "capex": 6.42
    },
    {
      "period": "2024 Q3",
      "revenue": 85.78,
      "opex": 13.79,
      "capex": 5.37
    }
  ],
  "prices": [
    {
      "date": "2024-02-26",
      "close": 182.63
    }
  ]
}
```

---

#### GET /api/news/<ticker>

**Purpose:** Fetch latest company news from Yahoo Finance

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| ticker | string | Stock symbol |

**Response (JSON):**

```json
{
  "news": [
    {
      "title": "Apple Reports Q1 2024 Results",
      "link": "https://finance.yahoo.com/...",
      "publisher": "Apple Inc.",
      "published": "2024-02-01T21:30:00.000Z"
    }
  ]
}
```

**Implementation Notes:**
- Uses `yfinance.Ticker.news` property
- News data is nested under `content` key
- Returns up to 10 articles
- Gracefully handles API failures

---

#### GET /api/risks/<ticker>

**Purpose:** Fetch risk metrics and generate risk analysis

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| ticker | string | Stock symbol |

**Response (JSON):**

```json
{
  "risks": [
    {
      "metric": "Beta (Volatility)",
      "value": "1.28",
      "risk": "Medium",
      "description": "Stock volatility relative to market. Higher = more volatile."
    },
    {
      "metric": "Debt to Equity",
      "value": "185.2%",
      "risk": "High",
      "description": "Financial leverage. Higher = more debt risk."
    }
  ],
  "raw_data": {
    "beta": 1.28,
    "debtToEquity": 185.2,
    "auditRisk": 1,
    ...
  }
}
```

**Risk Levels:**

| Metric | Low | Medium | High |
|--------|-----|--------|------|
| Beta | < 1.0 | 1.0 - 1.5 | > 1.5 |
| Debt/Equity | < 50% | 50-100% | > 100% |
| Overall Risk | 1-2 | 3 | 4-5 |
| Payout Ratio | < 30% | 30-60% | > 60% |

---

## Financial Calculations

### P/E Ratio Calculations

#### Yahoo P/E (Trailing)

```
Yahoo P/E = info.get("trailingPE")
```

This is the official trailing P/E ratio from Yahoo Finance, calculated as:
```
Trailing P/E = Current Price / (Trailing 12-Month EPS)
```

The trailing 12-month EPS is based on the last 4 quarters of reported earnings.

#### Calculated P/E (Custom)

```
Calculated P/E = Price / EPS_TTM

Where:
- Price = Latest closing price from database
- EPS_TTM = TTM Net Income / Estimated Shares
- Estimated Shares = Market Cap / Price
```

**Step-by-Step Calculation:**

```python
# Step 1: Get latest price
latest_price = StockPrice.query.filter_by(company_id=company_id)\
    .order_by(StockPrice.date.desc()).first()

# Step 2: Get TTM net income (last 4 quarters)
reports = FinancialReport.query.filter_by(company_id=company_id)\
    .order_by(FinancialReport.year.desc(), FinancialReport.quarter.desc())\
    .limit(4).all()
ttm_net_income = sum(r.net_income for r in reports if r.net_income)

# Step 3: Estimate shares from market cap
estimated_shares = company.market_cap / latest_price.close

# Step 4: Calculate EPS and P/E
eps = ttm_net_income / estimated_shares
calculated_pe = latest_price.close / eps
```

**Why Calculate Our Own P/E?**
1. Verify Yahoo Finance data accuracy
2. Use most recent quarterly data
3. Identify discrepancies that may indicate:
   - One-time earnings items
   - Accounting method differences
   - Outdated market cap data
   - Share buyback programs

#### P/E Spread

```
P/E Spread = Calculated P/E - Yahoo P/E
```

**Interpretation:**

| Spread Value | Interpretation | Potential Causes |
|--------------|----------------|------------------|
| Large Positive | Calculated >> Yahoo | One-time earnings boost, outdated market cap, accounting differences |
| Small Positive | Similar values | Healthy alignment |
| Large Negative | Calculated << Yahoo | Expected earnings growth, conservative accounting, recent share issuance |
| Small Negative | Similar values | Healthy alignment |

---

### Growth Calculations

#### Revenue Growth (Quarter-over-Quarter)

```python
growth = ((current_quarter_revenue - previous_quarter_revenue) 
          / previous_quarter_revenue) * 100
```

**Requirements:**
- At least 2 quarters of revenue data
- Previous quarter revenue > 0

---

### Derived Metrics

#### Daily Price Change

```python
latest_price = StockPrice.query.filter_by(company_id=company_id)\
    .order_by(StockPrice.date.desc()).first()

previous_price = StockPrice.query.filter_by(company_id=company_id)\
    .filter(StockPrice.date < latest_price.date)\
    .order_by(StockPrice.date.desc()).first()

daily_change = ((latest_price.close - previous_price.close) 
                / previous_price.close) * 100
```

---

## Frontend Architecture

### Page Structure

#### Homepage (index.html)

```
┌─────────────────────────────────────────────────────────────┐
│  Navbar: Logo | "View All Companies" link                   │
├─────────────────────────────────────────────────────────────┤
│  Filter Card                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Max P/E | Min Growth | Use Calc P/E | Apply Button │   │
│  │ P/E Spread filters (abs/pos/neg)                   │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Results Table                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Ticker | Name | P/E | Calc P/E | Spread | Growth   │   │
│  │ AAPL   | Apple| 28.5| 27.2   | -1.3  | +8.2%      │   │
│  │ MSFT   | ...  | ...  | ...    | ...   | ...        │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Chart Modal (hidden, triggered by button)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Interactive Plotly Chart                            │   │
│  │ Revenue, OPEX, CAPEX (left axis)                     │   │
│  │ Stock Price (right axis)                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### Ticker Detail Page (ticker.html)

```
┌─────────────────────────────────────────────────────────────┐
│  Header: Ticker | Name | Sector/Industry                    │
│  Stats: Price | Daily Change | P/E | Market Cap | Revenue   │
├─────────────────────────────────────────────────────────────┤
│  Tab Navigation                                            │
│  ┌──────────┬──────────┬──────────┬──────┬────────┬───────┐│
│  │Financials│ Stock   │ Combined │ News │ Risks  │Compete-│
│  │          │ Price   │          │      │        │ tors   ││
│  └──────────┴──────────┴──────────┴──────┴────────┴───────┘│
├─────────────────────────────────────────────────────────────┤
│  Tab Content (changes on selection)                         │
│                                                             │
│  [Financials Tab]                                          │
│  - Revenue/OPEX/CAPEX line chart                          │
│  - Quarterly data table                                    │
│                                                             │
│  [Stock Price Tab]                                        │
│  - 1-year price history with area fill                    │
│                                                             │
│  [Combined Tab]                                            │
│  - Dual-axis chart (financials + price)                  │
│                                                             │
│  [News Tab]                                                │
│  - Latest news articles (loaded async)                    │
│                                                             │
│  [Risk Analysis Tab]                                      │
│  - Risk metrics table with Low/Medium/High badges         │
│                                                             │
│  [Competitors Tab]                                        │
│  - Industry competitors table                             │
│  - % comparison columns                                   │
└─────────────────────────────────────────────────────────────┘
```

### Chart Implementation

#### Plotly Configuration

**Financial Chart:**
```javascript
{
  x: periods,           // ["2024 Q1", "2024 Q2", ...]
  y: revenues,          // Revenue in billions
  type: 'scatter',
  mode: 'lines+markers',
  name: 'Revenue ($B)',
  line: { color: '#58a6ff', width: 2 }
}
```

**Combined Dual-Axis Chart:**
```javascript
// Financials (left axis)
{
  yaxis: 'y',
  name: 'Revenue ($B)',
  // ...
}

// Stock Price (right axis)
{
  yaxis: 'y2',
  name: 'Stock Price ($)',
  line: { dash: 'dot' }
}

// Y-axis configuration
yaxis: {
  title: 'Financial Metrics ($B)',
  side: 'left'
},
yaxis2: {
  title: 'Stock Price ($)',
  overlaying: 'y',
  side: 'right'
}
```

#### Color Scheme

| Element | Color Code | Usage |
|---------|------------|-------|
| Revenue | #58a6ff | Blue - Primary financial metric |
| OPEX | #f85149 | Red - Cost indicator |
| CAPEX | #f0883e | Orange - Investment indicator |
| Stock Price | #3fb950 | Green - Positive market sentiment |
| Positive Values | #3fb950 | Green |
| Negative Values | #f85149 | Red |
| Accent | #58a6ff | Interactive elements |

---

## User Workflows

### Workflow 1: Filter Companies by Criteria

1. User opens homepage (`/`)
2. Default filters applied (P/E < 25, Growth > 10%)
3. User sees table of filtered companies
4. User adjusts filter values (e.g., max_pe=15)
5. Form submits, page refreshes with new results
6. User clicks "Chart" button to view detailed chart

### Workflow 2: Analyze Individual Company

1. User clicks on ticker in any table
2. Navigates to `/ticker/{company_id}`
3. Views summary stats in header
4. Explores different tabs:
   - Financials: Reviews revenue/OPEX/CAPEX trends
   - Price: Views stock price history
   - Combined: Correlates financials with price
   - News: Reads latest company news
   - Risks: Evaluates risk profile
   - Competitors: Compares with industry peers

### Workflow 3: Compare Competitors

1. User navigates to company ticker page
2. Clicks "Competitors" tab
3. Views table of companies in same industry
4. Analyzes percentage comparisons:
   - Revenue %: Competitor revenue / Company revenue
   - OPEX %: Competitor OPEX / Company OPEX
   - etc.
5. Clicks competitor ticker to explore further

### Workflow 4: Identify P/E Anomalies

1. User applies P/E spread filter:
   - `min_pe_spread_abs=50` to find large discrepancies
2. Reviews companies where calculated P/E differs greatly from Yahoo P/E
3. Investigates causes (one-time items, accounting differences)
4. May indicate mispricing or data quality issues

---

## Data Sources

### Primary Source: Yahoo Finance (yfinance)

The application uses the `yfinance` Python library to fetch data from Yahoo Finance.

#### Data Points Retrieved

| Data Type | yfinance Property | Description |
|-----------|-------------------|--------------|
| Company Info | `info` dict | Name, sector, industry, website, P/E, market cap |
| Price History | `history(period="2y")` | Daily OHLCV data |
| Quarterly Financials | `quarterly_financials` | Revenue, OPEX, Net Income |
| Cash Flow | `cashflow` | Capital Expenditures (CAPEX) |
| News | `news` property | Latest news articles |

#### Data Refresh Strategy

- **Stock Prices:** Downloaded fresh on each run of `download_data.py`
- **Financial Reports:** Appended for new quarters; existing data preserved
- **Company Info:** Updated on each download (may change with restatements)

---

## Error Handling

### Backend Error Handling

| Scenario | Handling |
|----------|----------|
| Database connection failure | Flask returns 500 with error message |
| Invalid company_id | Returns 404 via `get_or_404()` |
| yfinance API failure | Returns empty data with error logged |
| Missing financial data | Returns None, filters exclude company |
| Division by zero | Returns None, avoids crash |

### Frontend Error Handling

| Scenario | Handling |
|----------|----------|
| API fetch failure | Shows error message in container |
| No data available | Shows "No data available" message |
| Chart rendering error | Shows error alert in chart container |
| Invalid ticker | API returns empty array |

### Example Error Responses

**News API Error:**
```json
{
  "news": [],
  "error": "No data available for ticker XYZ"
}
```

**Risks API Error:**
```json
{
  "risks": [],
  "error": "Connection timeout"
}
```

---

## Performance Considerations

### Database Optimizations

1. **Indexes:**
   - `idx_ticker` on companies.ticker
   - `idx_company_report` on financial_reports(company_id, year, quarter)
   - `idx_company_date` on stock_prices(company_id, date)

2. **Query Optimization:**
   - Use `limit(4)` for TTM calculations
   - Use `limit(252)` for 1-year price data
   - Fetch only needed columns

### Application-Level Optimizations

1. **Caching Considerations (Future):**
   - Cache yfinance API responses
   - Cache calculated P/E values
   - Implement database connection pooling

2. **Pagination:**
   - All companies page should paginate for large datasets
   - Consider lazy loading for charts

### Client-Side Optimizations

1. **Lazy Loading:**
   - News and Risks tabs load on click (not on page load)
   - Reduces initial page load time

2. **Chart Rendering:**
   - Plotly handles large datasets efficiently
   - Responsive mode enabled for window resizing

---

## File Structure

```
/home/coder/Projects/
├── app.py                    # Flask application (main entry point)
├── download_data.py          # Data download script
├── models.py                 # SQLAlchemy database models
├── requirements.txt          # Python dependencies
├── README.md                 # User documentation
├── SPEC.md                   # Technical specifications
├── stocks.db                 # SQLite database (runtime)
├── .gitignore                # Git ignore rules
├── templates/
│   ├── index.html           # Homepage with filters
│   ├── ticker.html          # Company detail page
│   └── all.html             # All companies list
└── venv/                    # Python virtual environment
```

---

## Security Considerations

1. **No Authentication:** Application is for analysis only, no user accounts
2. **Read-Only Database:** Users cannot modify data
3. **External Links:** Open in new tabs (target="_blank")
4. **No Sensitive Data:** No credentials stored in application

---

## Future Enhancements

Potential improvements for future development:

1. **Data Updates:**
   - Background job to update data periodically
   - Incremental updates (only new data)

2. **Additional Metrics:**
   - EBITDA, Free Cash Flow
   - Dividend history
   - Analyst ratings

3. **User Features:**
   - Save filter presets
   - Export to CSV/Excel
   - Email alerts for filter matches

4. **Performance:**
   - Redis caching
   - Database connection pooling
   - Pagination for large result sets

5. **Visualization:**
   - More chart types
   - Comparison overlays
   - Technical indicators

---

*Document Version: 1.0*
*Last Updated: February 2026*
