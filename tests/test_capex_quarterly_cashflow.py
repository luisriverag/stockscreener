from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def test_downloader_uses_quarterly_cashflow_for_capex_without_annual_fallback():
    downloader = read("download_data.py")

    assert "quarterly_cashflow" in downloader
    assert "ticker_obj.cashflow" not in downloader
    assert "Annual CAPEX - estimate quarterly as 1/4" not in downloader
    assert "capex = capex / 4" not in downloader
