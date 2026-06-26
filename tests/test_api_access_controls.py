def test_api_auth_is_optional_but_enforced_when_keys_configured(monkeypatch):
    import app as app_module

    app_module._api_response_cache.clear()
    app_module._api_rate_limits.clear()
    monkeypatch.setattr(app_module, "API_KEYS", {"secret"})
    client = app_module.app.test_client()

    assert client.get("/api/v1/companies?per_page=1").status_code == 401
    assert (
        client.get("/api/v1/companies?per_page=1", headers={"X-API-Key": "secret"}).status_code
        == 200
    )


def test_api_rate_limit_returns_429_when_window_is_exhausted(monkeypatch):
    import app as app_module

    app_module._api_response_cache.clear()
    app_module._api_rate_limits.clear()
    monkeypatch.setattr(app_module, "API_KEYS", set())
    monkeypatch.setattr(app_module, "API_RATE_LIMIT_PER_MINUTE", 1)
    client = app_module.app.test_client()

    assert client.get("/api/v1/companies?per_page=1&rate=test").status_code == 200
    response = client.get("/api/v1/companies?per_page=1&rate=test2")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


def test_api_get_responses_are_cached(monkeypatch):
    import app as app_module

    app_module._api_response_cache.clear()
    app_module._api_rate_limits.clear()
    monkeypatch.setattr(app_module, "API_KEYS", set())
    monkeypatch.setattr(app_module, "API_RATE_LIMIT_PER_MINUTE", 120)
    monkeypatch.setattr(app_module, "API_CACHE_TTL_SECONDS", 60)
    client = app_module.app.test_client()

    first = client.get("/api/v1/companies?per_page=1&cache=test")
    second = client.get("/api/v1/companies?per_page=1&cache=test")

    assert first.status_code == 200
    assert first.headers["X-Cache"] == "MISS"
    assert second.status_code == 200
    assert second.headers["X-Cache"] == "HIT"
