from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200))
    sector = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    website_url = db.Column(db.String(500))
    pe_ratio = db.Column(db.Float)
    market_cap = db.Column(db.BigInteger)

    financial_reports = db.relationship(
        "FinancialReport", backref="company", lazy="dynamic"
    )
    stock_prices = db.relationship("StockPrice", backref="company", lazy="dynamic")

    @property
    def yahoo_finance_url(self):
        return f"https://finance.yahoo.com/quote/{self.ticker}"

    @property
    def daily_price_change_pct(self):
        latest_price = self.stock_prices.order_by(StockPrice.date.desc()).first()
        if latest_price:
            prev_price = (
                self.stock_prices.filter(StockPrice.date < latest_price.date)
                .order_by(StockPrice.date.desc())
                .first()
            )
            if prev_price and prev_price.close > 0:
                return (
                    (latest_price.close - prev_price.close) / prev_price.close
                ) * 100
        return 0

    @property
    def revenue_growth(self):
        reports = (
            self.financial_reports.order_by(
                FinancialReport.year.desc(), FinancialReport.quarter.desc()
            )
            .limit(2)
            .all()
        )
        if len(reports) >= 2:
            current = reports[0].revenue
            previous = reports[1].revenue
            if previous and previous > 0:
                return ((current - previous) / previous) * 100
        return 0


class FinancialReport(db.Model):
    __tablename__ = "financial_reports"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    quarter = db.Column(db.Integer)
    year = db.Column(db.Integer)
    revenue = db.Column(db.Float)
    opex = db.Column(db.Float)
    capex = db.Column(db.Float)
    net_income = db.Column(db.Float)

    __table_args__ = (db.Index("idx_company_report", "company_id", "year", "quarter"),)


class StockPrice(db.Model):
    __tablename__ = "stock_prices"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open_price = db.Column(db.Float)
    high = db.Column(db.Float)
    low = db.Column(db.Float)
    close = db.Column(db.Float)
    volume = db.Column(db.BigInteger)

    __table_args__ = (db.Index("idx_company_date", "company_id", "date"),)
