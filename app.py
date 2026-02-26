import os
import csv
import io
from flask import Flask, render_template, jsonify, request, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import db, Company, FinancialReport, StockPrice
import plotly.graph_objs as go
import json

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///stocks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


def calculate_pe(company):
    """Calculate P/E ratio from latest price and TTM earnings
    P/E = Price / (Net Income / Shares)
    Without shares, we estimate using market cap
    """
    latest_price = company.stock_prices.order_by(StockPrice.date.desc()).first()
    if not latest_price or latest_price.close <= 0:
        return None

    reports = (
        company.financial_reports.order_by(
            FinancialReport.year.desc(), FinancialReport.quarter.desc()
        )
        .limit(4)
        .all()
    )

    if not reports or len(reports) < 4:
        return None

    total_net_income = sum(r.net_income for r in reports if r.net_income)

    if not total_net_income or total_net_income <= 0:
        return None

    # Estimate shares using market cap and price
    # Market Cap = Price * Shares, so Shares = Market Cap / Price
    if company.market_cap and company.market_cap > 0:
        estimated_shares = company.market_cap / latest_price.close
        if estimated_shares > 0:
            eps = total_net_income / estimated_shares
            if eps > 0:
                return latest_price.close / eps

    return None


@app.route("/")
def index():
    max_pe = request.args.get("max_pe", 25, type=float)
    min_growth = request.args.get("min_growth", 10, type=float)
    use_calc_pe = request.args.get("use_calc_pe", "false") == "true"
    min_pe_spread_abs = request.args.get("min_pe_spread_abs", type=float)
    min_pe_spread_pos = request.args.get("min_pe_spread_pos", type=float)
    min_pe_spread_neg = request.args.get("min_pe_spread_neg", type=float)
    search = request.args.get("search", "").strip()

    companies = []
    all_companies = Company.query.all()

    for company in all_companies:
        calc_pe_val = calculate_pe(company)

        if use_calc_pe:
            pe = calc_pe_val
        else:
            pe = company.pe_ratio

        if pe and pe < max_pe:
            growth = company.revenue_growth
            if growth and growth > min_growth:
                if search:
                    search_match = False
                    search_lower = search.lower()
                    if company.ticker and search_lower in company.ticker.lower():
                        search_match = True
                    if company.name and search_lower in company.name.lower():
                        search_match = True
                    if company.industry and search_lower in company.industry.lower():
                        search_match = True
                    if company.sector and search_lower in company.sector.lower():
                        search_match = True
                    if not search_match:
                        continue

                pe_spread = None
                if calc_pe_val and company.pe_ratio:
                    pe_spread = calc_pe_val - company.pe_ratio

                if pe_spread is not None:
                    # Filter by absolute spread
                    if min_pe_spread_abs is not None:
                        if abs(pe_spread) < min_pe_spread_abs:
                            continue
                    # Filter by positive spread only (Calc > Yahoo)
                    if min_pe_spread_pos is not None:
                        if pe_spread < min_pe_spread_pos:
                            continue
                    # Filter by negative spread only (Calc < Yahoo)
                    if min_pe_spread_neg is not None:
                        if pe_spread > -min_pe_spread_neg:
                            continue

                companies.append(
                    {
                        "id": company.id,
                        "ticker": company.ticker,
                        "name": company.name,
                        "pe_ratio": pe,
                        "pe_calc": calc_pe_val,
                        "pe_spread": pe_spread,
                        "revenue_growth": growth,
                        "website_url": company.website_url,
                        "yahoo_finance_url": company.yahoo_finance_url,
                        "daily_change": company.daily_price_change_pct,
                    }
                )

    return render_template(
        "index.html",
        companies=companies,
        max_pe=max_pe,
        min_growth=min_growth,
        use_calc_pe=use_calc_pe,
        min_pe_spread_abs=min_pe_spread_abs,
        min_pe_spread_pos=min_pe_spread_pos,
        min_pe_spread_neg=min_pe_spread_neg,
        search=search,
    )


@app.route("/ticker/<int:company_id>")
def ticker_page(company_id):
    company = Company.query.get_or_404(company_id)

    reports = (
        FinancialReport.query.filter_by(company_id=company_id)
        .order_by(FinancialReport.year.desc(), FinancialReport.quarter.desc())
        .all()
    )

    prices = (
        StockPrice.query.filter_by(company_id=company_id)
        .order_by(StockPrice.date.desc())
        .limit(252)
        .all()
    )
    prices = list(reversed(prices))

    competitors = (
        Company.query.filter(
            Company.industry == company.industry, Company.id != company_id
        )
        .limit(5)
        .all()
    )

    report_data = []
    for r in reports:
        report_data.append(
            {
                "period": f"{r.year} Q{r.quarter}",
                "revenue": r.revenue / 1e9 if r.revenue else 0,
                "opex": r.opex / 1e9 if r.opex else 0,
                "capex": r.capex / 1e9 if r.capex else 0,
                "net_income": r.net_income / 1e9 if r.net_income else 0,
            }
        )

    price_data = [
        {"date": str(p.date), "close": p.close, "volume": p.volume} for p in prices
    ]

    latest_report = reports[0] if reports else None
    calc_pe = calculate_pe(company)

    eps_ttm = None
    if reports:
        total_ni = sum(r.net_income for r in reports[:4] if r.net_income)
        if total_ni:
            eps_ttm = total_ni / 1e9

    summary = {
        "ticker": company.ticker,
        "name": company.name,
        "sector": company.sector,
        "industry": company.industry,
        "website_url": company.website_url,
        "yahoo_url": company.yahoo_finance_url,
        "pe_ratio": company.pe_ratio,
        "pe_calc": calc_pe,
        "eps_ttm": eps_ttm,
        "market_cap": company.market_cap / 1e12 if company.market_cap else 0,
        "revenue": latest_report.revenue / 1e9
        if latest_report and latest_report.revenue
        else 0,
        "opex": latest_report.opex / 1e9 if latest_report and latest_report.opex else 0,
        "capex": latest_report.capex / 1e9
        if latest_report and latest_report.capex
        else 0,
        "net_income": latest_report.net_income / 1e9
        if latest_report and latest_report.net_income
        else 0,
        "revenue_growth": company.revenue_growth,
        "daily_change": company.daily_price_change_pct,
        "price": prices[-1].close if prices else 0,
    }

    competitor_list = []
    for c in competitors:
        comp_reports = (
            FinancialReport.query.filter_by(company_id=c.id)
            .order_by(FinancialReport.year.desc(), FinancialReport.quarter.desc())
            .first()
        )

        comp_revenue = (
            comp_reports.revenue / 1e9 if comp_reports and comp_reports.revenue else 0
        )
        comp_opex = comp_reports.opex / 1e9 if comp_reports and comp_reports.opex else 0
        comp_capex = (
            comp_reports.capex / 1e9 if comp_reports and comp_reports.capex else 0
        )
        comp_net_income = (
            comp_reports.net_income / 1e9
            if comp_reports and comp_reports.net_income
            else 0
        )

        main_revenue = (
            latest_report.revenue / 1e9
            if latest_report and latest_report.revenue
            else 1
        )
        main_opex = (
            latest_report.opex / 1e9 if latest_report and latest_report.opex else 1
        )
        main_capex = (
            latest_report.capex / 1e9 if latest_report and latest_report.capex else 1
        )
        main_net_income = (
            latest_report.net_income / 1e9
            if latest_report and latest_report.net_income
            else 1
        )

        competitor_list.append(
            {
                "id": c.id,
                "ticker": c.ticker,
                "name": c.name,
                "pe_ratio": c.pe_ratio,
                "pe_calc": calculate_pe(c),
                "yahoo_url": c.yahoo_finance_url,
                "revenue": comp_revenue,
                "opex": comp_opex,
                "capex": comp_capex,
                "net_income": comp_net_income,
                "revenue_pct": (comp_revenue / main_revenue * 100)
                if main_revenue
                else 0,
                "opex_pct": (comp_opex / main_opex * 100) if main_opex else 0,
                "capex_pct": (comp_capex / main_capex * 100) if main_capex else 0,
                "net_income_pct": (comp_net_income / main_net_income * 100)
                if main_net_income
                else 0,
            }
        )

    return render_template(
        "ticker.html",
        company=company,
        summary=summary,
        reports=report_data,
        prices=price_data,
        competitors=competitor_list,
    )


@app.route("/chart/<int:company_id>")
def chart(company_id):
    company = Company.query.get_or_404(company_id)

    reports = (
        FinancialReport.query.filter_by(company_id=company_id)
        .order_by(FinancialReport.year, FinancialReport.quarter)
        .all()
    )

    report_data = []
    for r in reports:
        report_data.append(
            {
                "period": f"{r.year} Q{r.quarter}",
                "revenue": r.revenue / 1e9 if r.revenue else 0,
                "opex": r.opex / 1e9 if r.opex else 0,
                "capex": r.capex / 1e9 if r.capex else 0,
            }
        )

    prices = (
        StockPrice.query.filter_by(company_id=company_id)
        .order_by(StockPrice.date)
        .all()
    )
    price_data = [{"date": str(p.date), "close": p.close} for p in prices]

    return jsonify(
        {
            "ticker": company.ticker,
            "name": company.name,
            "reports": report_data,
            "prices": price_data,
        }
    )


@app.route("/api/news/<ticker>")
def news(ticker):
    import yfinance as yf

    try:
        ticker_obj = yf.Ticker(ticker)
        news_items = ticker_obj.news

        news_list = []
        if news_items:
            for item in news_items[:10]:
                content = item.get("content", {})
                news_list.append(
                    {
                        "title": content.get("title", ""),
                        "link": content.get("clickThroughUrl", {}).get("url", "")
                        if content.get("clickThroughUrl")
                        else "",
                        "publisher": content.get("provider", {}).get("displayName", "")
                        if content.get("provider")
                        else "",
                        "published": content.get("pubDate", ""),
                    }
                )

        return jsonify({"news": news_list})
    except Exception as e:
        return jsonify({"news": [], "error": str(e)})


@app.route("/api/risks/<ticker>")
def risks(ticker):
    import yfinance as yf

    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info

        risk_data = {
            "beta": info.get("beta"),
            "volatility": info.get("volatility"),
            "overall_risk": info.get("overallRisk"),
            "audit_risk": info.get("auditRisk"),
            "board_risk": info.get("boardRisk"),
            "compensation_risk": info.get("compensationRisk"),
            "shareholder_risk": info.get("shareHolderRightsRisk"),
            "debt_to_equity": info.get("debtToEquity"),
            "total_debt": info.get("totalDebt"),
            "current_debt": info.get("currentDebt"),
            "long_term_debt": info.get("longTermDebt"),
            "peg_ratio": info.get("pegRatio"),
            "payout_ratio": info.get("payoutRatio"),
            "dividend_yield": info.get("dividendYield"),
            "dividend_rate": info.get("dividendRate"),
            "free_cash_flow": info.get("freeCashflow"),
            "operating_cashflow": info.get("operatingCashflow"),
            "ebitda": info.get("ebitda"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "gross_margin": info.get("grossMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
            "52w_change": info.get("52WeekChange"),
            "sBeta": info.get("sBeta"),
            "morningstar_risk": info.get("morningStarRiskRating"),
            "risk_rating": info.get("riskRatings"),
        }

        risk_items = []

        if risk_data.get("beta"):
            risk_level = (
                "Low"
                if risk_data["beta"] < 1.0
                else "Medium"
                if risk_data["beta"] < 1.5
                else "High"
            )
            risk_items.append(
                {
                    "metric": "Beta (Volatility)",
                    "value": f"{risk_data['beta']:.2f}",
                    "risk": risk_level,
                    "description": "Stock volatility relative to market. Higher = more volatile.",
                }
            )

        if risk_data.get("debt_to_equity"):
            risk_level = (
                "Low"
                if risk_data["debt_to_equity"] < 50
                else "Medium"
                if risk_data["debt_to_equity"] < 100
                else "High"
            )
            risk_items.append(
                {
                    "metric": "Debt to Equity",
                    "value": f"{risk_data['debt_to_equity']:.1f}%",
                    "risk": risk_level,
                    "description": "Financial leverage. Higher = more debt risk.",
                }
            )

        if risk_data.get("overall_risk"):
            risk_items.append(
                {
                    "metric": "Overall Risk Score",
                    "value": str(risk_data["overall_risk"]),
                    "risk": "Low"
                    if risk_data["overall_risk"] <= 2
                    else "Medium"
                    if risk_data["overall_risk"] <= 3
                    else "High",
                    "description": "Yahoo Finance overall risk rating (1-5)",
                }
            )

        if risk_data.get("audit_risk"):
            risk_items.append(
                {
                    "metric": "Audit Risk",
                    "value": str(risk_data["audit_risk"]),
                    "risk": "Low"
                    if risk_data["audit_risk"] <= 2
                    else "Medium"
                    if risk_data["audit_risk"] <= 3
                    else "High",
                    "description": "Risk related to audit and financial reporting",
                }
            )

        if risk_data.get("compensation_risk"):
            risk_items.append(
                {
                    "metric": "Compensation Risk",
                    "value": str(risk_data["compensation_risk"]),
                    "risk": "Low"
                    if risk_data["compensation_risk"] <= 2
                    else "Medium"
                    if risk_data["compensation_risk"] <= 3
                    else "High",
                    "description": "Risk related to executive compensation",
                }
            )

        if risk_data.get("shareholder_risk"):
            risk_items.append(
                {
                    "metric": "Shareholder Rights Risk",
                    "value": str(risk_data["shareholder_risk"]),
                    "risk": "Low"
                    if risk_data["shareholder_risk"] <= 2
                    else "Medium"
                    if risk_data["shareholder_risk"] <= 3
                    else "High",
                    "description": "Risk related to shareholder rights",
                }
            )

        if risk_data.get("dividend_yield"):
            risk_items.append(
                {
                    "metric": "Dividend Yield",
                    "value": f"{risk_data['dividend_yield'] * 100:.2f}%",
                    "risk": "N/A",
                    "description": "Annual dividend as % of price. Higher = income but may limit growth.",
                }
            )

        if risk_data.get("payout_ratio"):
            risk_level = (
                "Low"
                if risk_data["payout_ratio"] < 0.3
                else "Medium"
                if risk_data["payout_ratio"] < 0.6
                else "High"
            )
            risk_items.append(
                {
                    "metric": "Dividend Payout Ratio",
                    "value": f"{risk_data['payout_ratio'] * 100:.1f}%",
                    "risk": risk_level,
                    "description": "% of earnings paid as dividend. High = potential cut risk.",
                }
            )

        if risk_data.get("revenue_growth"):
            risk_items.append(
                {
                    "metric": "Revenue Growth (YoY)",
                    "value": f"{risk_data['revenue_growth'] * 100:.1f}%",
                    "risk": "High" if risk_data["revenue_growth"] < 0 else "N/A",
                    "description": "Year-over-year revenue growth. Negative = declining business.",
                }
            )

        if risk_data.get("profit_margin"):
            risk_level = (
                "High"
                if risk_data["profit_margin"] < 0
                else "Low"
                if risk_data["profit_margin"] > 0.15
                else "Medium"
            )
            risk_items.append(
                {
                    "metric": "Profit Margin",
                    "value": f"{risk_data['profit_margin'] * 100:.1f}%",
                    "risk": risk_level,
                    "description": "Net profit as % of revenue. Negative = unprofitable.",
                }
            )

        if risk_data.get("free_cash_flow") and risk_data["free_cash_flow"] < 0:
            risk_items.append(
                {
                    "metric": "Free Cash Flow",
                    "value": f"${risk_data['free_cash_flow'] / 1e9:.2f}B",
                    "risk": "High",
                    "description": "Negative FCF - company is spending more than earning.",
                }
            )

        return jsonify({"risks": risk_items, "raw_data": risk_data})
    except Exception as e:
        return jsonify({"risks": [], "error": str(e)})


@app.route("/all")
def all_companies():
    page = request.args.get("page", 1, type=int)
    per_page = 50
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "ticker")
    order = request.args.get("order", "asc")

    query = Company.query

    if search:
        query = query.filter(
            (Company.ticker.ilike(f"%{search}%"))
            | (Company.name.ilike(f"%{search}%"))
            | (Company.industry.ilike(f"%{search}%"))
            | (Company.sector.ilike(f"%{search}%"))
        )

    sort_column = getattr(Company, sort_by, Company.ticker)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    all_companies = pagination.items

    companies = []
    for company in all_companies:
        calc_pe = calculate_pe(company)
        pe_spread = None
        if calc_pe and company.pe_ratio:
            pe_spread = calc_pe - company.pe_ratio
        companies.append(
            {
                "id": company.id,
                "ticker": company.ticker,
                "name": company.name,
                "sector": company.sector,
                "industry": company.industry,
                "pe_ratio": company.pe_ratio,
                "pe_calc": calc_pe,
                "pe_spread": pe_spread,
                "market_cap": company.market_cap,
                "website_url": company.website_url,
                "daily_change": company.daily_price_change_pct,
            }
        )

    return render_template(
        "all.html",
        companies=companies,
        pagination=pagination,
        search=search,
        sort_by=sort_by,
        order=order,
    )


@app.route("/export/csv")
def export_csv():
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "ticker")
    order = request.args.get("order", "asc")

    max_pe = request.args.get("max_pe", 25, type=float)
    min_growth = request.args.get("min_growth", 10, type=float)
    use_calc_pe = request.args.get("use_calc_pe", "false") == "true"
    min_pe_spread_abs = request.args.get("min_pe_spread_abs", type=float)
    min_pe_spread_pos = request.args.get("min_pe_spread_pos", type=float)
    min_pe_spread_neg = request.args.get("min_pe_spread_neg", type=float)

    is_filtered = any(
        [
            request.args.get("max_pe"),
            request.args.get("min_growth"),
            request.args.get("use_calc_pe"),
            request.args.get("min_pe_spread_abs"),
            request.args.get("min_pe_spread_pos"),
            request.args.get("min_pe_spread_neg"),
        ]
    )

    if is_filtered:
        all_companies = Company.query.all()
        companies = []

        for company in all_companies:
            calc_pe_val = calculate_pe(company)

            if use_calc_pe:
                pe = calc_pe_val
            else:
                pe = company.pe_ratio

            if pe and pe < max_pe:
                growth = company.revenue_growth
                if growth and growth > min_growth:
                    if search:
                        search_match = False
                        search_lower = search.lower()
                        if company.ticker and search_lower in company.ticker.lower():
                            search_match = True
                        if company.name and search_lower in company.name.lower():
                            search_match = True
                        if (
                            company.industry
                            and search_lower in company.industry.lower()
                        ):
                            search_match = True
                        if company.sector and search_lower in company.sector.lower():
                            search_match = True
                        if not search_match:
                            continue

                    pe_spread = None
                    if calc_pe_val and company.pe_ratio:
                        pe_spread = calc_pe_val - company.pe_ratio

                    if pe_spread is not None:
                        if min_pe_spread_abs is not None:
                            if abs(pe_spread) < min_pe_spread_abs:
                                continue
                        if min_pe_spread_pos is not None:
                            if pe_spread < min_pe_spread_pos:
                                continue
                        if min_pe_spread_neg is not None:
                            if pe_spread > -min_pe_spread_neg:
                                continue

                    companies.append(
                        {
                            "company": company,
                            "calc_pe": calc_pe_val,
                            "pe_spread": pe_spread,
                        }
                    )
    else:
        query = Company.query

        if search:
            query = query.filter(
                (Company.ticker.ilike(f"%{search}%"))
                | (Company.name.ilike(f"%{search}%"))
                | (Company.industry.ilike(f"%{search}%"))
                | (Company.sector.ilike(f"%{search}%"))
            )

        sort_column = getattr(Company, sort_by, Company.ticker)
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        companies_list = query.all()
        companies = []
        for company in companies_list:
            calc_pe = calculate_pe(company)
            pe_spread = None
            if calc_pe and company.pe_ratio:
                pe_spread = calc_pe - company.pe_ratio
            companies.append(
                {
                    "company": company,
                    "calc_pe": calc_pe,
                    "pe_spread": pe_spread,
                }
            )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "Ticker",
            "Name",
            "Sector",
            "Industry",
            "P/E (Yahoo)",
            "P/E (Calculated)",
            "P/E Spread",
            "Market Cap",
            "Daily Change %",
        ]
    )

    for item in companies:
        company = item["company"]
        calc_pe = item["calc_pe"]
        pe_spread = item["pe_spread"]

        writer.writerow(
            [
                company.ticker,
                company.name or "",
                company.sector or "",
                company.industry or "",
                company.pe_ratio or "",
                calc_pe or "",
                pe_spread or "",
                company.market_cap or "",
                company.daily_price_change_pct or "",
            ]
        )

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=companies.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
