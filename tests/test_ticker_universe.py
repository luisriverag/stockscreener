from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def test_downloader_refreshes_sp500_universe_and_normalizes_yahoo_symbols():
    downloader = read("download_data.py")

    assert "def get_sp500_tickers():" in downloader
    assert "List_of_S%26P_500_companies" in downloader
    assert "tickers.update(get_sp500_tickers())" in downloader
    assert 'replace(".", "-")' in downloader
    assert "return sorted(tickers)" in downloader


def test_downloader_skips_unknown_symbols_before_creating_companies():
    downloader = read("download_data.py")

    assert "def has_provider_data(info):" in downloader
    assert "if not has_provider_data(info):" in downloader
    assert "no provider data found" in downloader
