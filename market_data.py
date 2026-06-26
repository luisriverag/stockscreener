import json
import math
from datetime import datetime

from models import (
    EarningsEvent,
    InsiderTransaction,
    InstitutionalHolder,
    MajorHolder,
    MarketDataRefresh,
    OptionContract,
    SecFilingLink,
)


def json_default(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return str(value)


def dataframe_records(frame, max_rows=10):
    """Convert a pandas-like frame into JSON-safe row dictionaries."""
    if frame is None or getattr(frame, "empty", True):
        return []

    rows = frame.head(max_rows).reset_index().to_dict(orient="records")
    cleaned = []
    for row in rows:
        cleaned_row = {}
        for key, value in row.items():
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            elif isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                value = None
            elif value is not None:
                value = str(value) if not isinstance(value, (int, float, bool)) else value
            cleaned_row[str(key)] = value
        cleaned.append(cleaned_row)
    return cleaned


def sec_filing_links(ticker):
    sec_ticker = ticker.upper().replace(".", "-")
    return [
        {
            "label": "SEC company search",
            "url": f"https://www.sec.gov/edgar/search/#/q={sec_ticker}",
        },
        {
            "label": "Recent 10-K filings",
            "url": f"https://www.sec.gov/edgar/search/#/q={sec_ticker}&category=form-cat1&forms=10-K",
        },
        {
            "label": "Recent 10-Q filings",
            "url": f"https://www.sec.gov/edgar/search/#/q={sec_ticker}&category=form-cat1&forms=10-Q",
        },
    ]


def fetch_market_data(ticker):
    import yfinance as yf

    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.info or {}
    option_dates = list(getattr(ticker_obj, "options", []) or [])
    option_summary = {
        "expiration": None,
        "calls": [],
        "puts": [],
        "available_expirations": option_dates[:12],
    }

    if option_dates:
        chain = ticker_obj.option_chain(option_dates[0])
        option_summary = {
            "expiration": option_dates[0],
            "calls": dataframe_records(chain.calls, max_rows=8),
            "puts": dataframe_records(chain.puts, max_rows=8),
            "available_expirations": option_dates[:12],
        }

    return {
        "ownership": {
            "institutional_holders": dataframe_records(
                getattr(ticker_obj, "institutional_holders", None), max_rows=10
            ),
            "major_holders": dataframe_records(
                getattr(ticker_obj, "major_holders", None), max_rows=10
            ),
            "insider_transactions": dataframe_records(
                getattr(ticker_obj, "insider_transactions", None), max_rows=10
            ),
        },
        "options": option_summary,
        "earnings_calendar": dataframe_records(
            getattr(ticker_obj, "calendar", None), max_rows=10
        ),
        "sec_filings": sec_filing_links(ticker),
        "metadata": {
            "source": "Yahoo Finance / SEC EDGAR links",
            "market_cap": info.get("marketCap"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "fetch_status": "success",
            "last_refreshed_at": datetime.utcnow().isoformat(),
        },
    }


def dump_raw(row):
    return json.dumps(row, default=json_default)


def clear_market_data(company_id, session):
    for model in [
        InstitutionalHolder,
        MajorHolder,
        InsiderTransaction,
        OptionContract,
        EarningsEvent,
        SecFilingLink,
    ]:
        session.query(model).filter_by(company_id=company_id).delete()


def persist_market_data(company, session, payload, status="success", error_message=None):
    now = datetime.utcnow()
    clear_market_data(company.id, session)

    ownership = payload.get("ownership", {}) if payload else {}
    for row in ownership.get("institutional_holders", []):
        session.add(
            InstitutionalHolder(
                company_id=company.id,
                holder=str(row.get("Holder") or row.get("index") or row.get("Date Reported") or ""),
                raw_data=dump_raw(row),
                source="Yahoo Finance",
                fetch_status=status,
                last_refreshed_at=now,
            )
        )

    for row in ownership.get("major_holders", []):
        session.add(
            MajorHolder(
                company_id=company.id,
                holder=str(row.get("Breakdown") or row.get("index") or ""),
                raw_data=dump_raw(row),
                source="Yahoo Finance",
                fetch_status=status,
                last_refreshed_at=now,
            )
        )

    for row in ownership.get("insider_transactions", []):
        session.add(
            InsiderTransaction(
                company_id=company.id,
                insider=str(row.get("Insider") or row.get("Holder") or row.get("index") or ""),
                transaction_date=str(row.get("Start Date") or row.get("Date") or ""),
                raw_data=dump_raw(row),
                source="Yahoo Finance",
                fetch_status=status,
                last_refreshed_at=now,
            )
        )

    options = payload.get("options", {}) if payload else {}
    expiration = options.get("expiration")
    for option_type in ["calls", "puts"]:
        for row in options.get(option_type, []):
            session.add(
                OptionContract(
                    company_id=company.id,
                    expiration=expiration,
                    option_type=option_type[:-1],
                    contract_symbol=str(row.get("contractSymbol") or ""),
                    raw_data=dump_raw(row),
                    source="Yahoo Finance",
                    fetch_status=status,
                    last_refreshed_at=now,
                )
            )

    for row in payload.get("earnings_calendar", []) if payload else []:
        session.add(
            EarningsEvent(
                company_id=company.id,
                event=str(row.get("Earnings Date") or row.get("index") or ""),
                raw_data=dump_raw(row),
                source="Yahoo Finance",
                fetch_status=status,
                last_refreshed_at=now,
            )
        )

    for link in payload.get("sec_filings", []) if payload else []:
        session.add(
            SecFilingLink(
                company_id=company.id,
                label=link.get("label", ""),
                url=link.get("url", ""),
                source="SEC EDGAR",
                fetch_status=status,
                last_refreshed_at=now,
            )
        )

    refresh = session.query(MarketDataRefresh).filter_by(company_id=company.id).first()
    if not refresh:
        refresh = MarketDataRefresh(company_id=company.id)
        session.add(refresh)
    refresh.last_refreshed_at = now
    refresh.source = "Yahoo Finance / SEC EDGAR links"
    refresh.fetch_status = status
    refresh.error_message = error_message


def sanitize_value(value):
    """Recursively replace NaN/Inf with None in JSON-safe data."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_value(v) for v in value]
    return value


def parse_raw(row):
    try:
        data = json.loads(row.raw_data) if row.raw_data else {}
        return sanitize_value(data)
    except json.JSONDecodeError:
        return {}


def load_market_data(company, session):
    refresh = session.query(MarketDataRefresh).filter_by(company_id=company.id).first()
    options = session.query(OptionContract).filter_by(company_id=company.id).all()
    expiration = options[0].expiration if options else None

    return {
        "ownership": {
            "institutional_holders": [
                parse_raw(row)
                for row in session.query(InstitutionalHolder)
                .filter_by(company_id=company.id)
                .all()
            ],
            "major_holders": [
                parse_raw(row)
                for row in session.query(MajorHolder).filter_by(company_id=company.id).all()
            ],
            "insider_transactions": [
                parse_raw(row)
                for row in session.query(InsiderTransaction)
                .filter_by(company_id=company.id)
                .all()
            ],
        },
        "options": {
            "expiration": expiration,
            "calls": [parse_raw(row) for row in options if row.option_type == "call"],
            "puts": [parse_raw(row) for row in options if row.option_type == "put"],
            "available_expirations": [expiration] if expiration else [],
        },
        "earnings_calendar": [
            parse_raw(row)
            for row in session.query(EarningsEvent).filter_by(company_id=company.id).all()
        ],
        "sec_filings": [
            {"label": row.label, "url": row.url}
            for row in session.query(SecFilingLink).filter_by(company_id=company.id).all()
        ],
        "metadata": {
            "source": refresh.source if refresh else None,
            "fetch_status": refresh.fetch_status if refresh else "missing",
            "last_refreshed_at": refresh.last_refreshed_at.isoformat()
            if refresh and refresh.last_refreshed_at
            else None,
            "error_message": refresh.error_message if refresh else None,
            "from_database": True,
        },
    }


def has_market_data(company, session):
    refresh = session.query(MarketDataRefresh).filter_by(company_id=company.id).first()
    return bool(refresh and refresh.fetch_status == "success")
