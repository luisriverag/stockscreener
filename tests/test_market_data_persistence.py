from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def test_market_data_models_exist_with_freshness_metadata():
    models = read("models.py")
    for model_name in [
        "MarketDataRefresh",
        "InstitutionalHolder",
        "MajorHolder",
        "InsiderTransaction",
        "OptionContract",
        "EarningsEvent",
        "SecFilingLink",
    ]:
        assert f"class {model_name}" in models

    for field in ["last_refreshed_at", "source", "fetch_status"]:
        assert field in models


def test_company_models_include_debt_filter_metrics():
    models = read("models.py")
    downloader = read("download_data.py")

    assert "debt_to_equity = db.Column(db.Float)" in models
    assert "total_debt = db.Column(db.BigInteger)" in models
    assert 'company.debt_to_equity = info.get("debtToEquity")' in downloader
    assert 'company.total_debt = info.get("totalDebt")' in downloader


def test_downloader_persists_market_data_refreshes():
    downloader = read("download_data.py")
    assert "from market_data import fetch_market_data, persist_market_data" in downloader
    assert "market_payload = fetch_market_data(ticker)" in downloader
    assert 'persist_market_data(company, session, market_payload, status="success")' in downloader
    assert 'status="failed"' in downloader


def test_market_data_api_reads_cache_before_live_fallback():
    app = read("app.py")
    assert '@app.route("/api/market-data/<ticker>")' in app
    assert "has_market_data(company, db.session)" in app
    assert "return jsonify(load_market_data(company, db.session))" in app
    assert "payload = fetch_market_data(ticker)" in app
    assert "persist_market_data(company, db.session, payload, status=\"success\")" in app


def test_market_data_helpers_cover_requested_payloads():
    helper = read("market_data.py")
    for token in [
        "institutional_holders",
        "major_holders",
        "insider_transactions",
        "option_chain",
        "earnings_calendar",
        "sec_filings",
        "MarketDataRefresh",
    ]:
        assert token in helper


def test_background_downloader_has_shutdown_path():
    app = read("app.py")
    assert "_downloader_stop_event = threading.Event()" in app
    assert "terminate_downloader_process" in app
    assert "shutdown_background_downloader" in app
    assert "atexit.register(shutdown_background_downloader)" in app
    assert "start_new_session" in app
    assert "shutdown_background_downloader()" in app
