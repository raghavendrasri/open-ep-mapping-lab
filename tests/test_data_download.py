"""Downloads of real data: retries on transient server errors (epml.data)."""

import pytest


def test_downloads_retry_server_errors(monkeypatch):
    """PhysioNet sometimes answers 502; epml.data._get retries server errors but not client errors."""
    import urllib.error

    from epml import data

    calls = {"n": 0}

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"ok"

    def flaky(url, timeout=0):
        calls["n"] += 1
        if calls["n"] < 3:
            raise urllib.error.HTTPError(url, 502, "Bad Gateway", {}, None)
        return Resp()

    monkeypatch.setattr(data.urllib.request, "urlopen", flaky)
    assert data._get("https://example.org/x", wait_s=0) == b"ok" and calls["n"] == 3

    def missing(url, timeout=0):
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    monkeypatch.setattr(data.urllib.request, "urlopen", missing)
    with pytest.raises(urllib.error.HTTPError):
        data._get("https://example.org/y", wait_s=0)
