"""Test fixtures for pytest."""

import pytest
import httpx


@pytest.fixture
def mock_wordpress_responses():
    """Mock responses for typical WordPress requests."""
    return {
        "/readme.html": (200, "WordPress readme content", {"content-type": "text/html"}),
        "/license.txt": (200, "GPL license", {"content-type": "text/plain"}),
        "/wp-config.php": (404, "", {}),
        "/wp-config.php.bak": (200, "<?php // config", {"content-type": "text/plain"}),
        "/.git/config": (404, "", {}),
        "/debug.log": (403, "", {}),
        "/.env": (404, "", {}),
        "/wp-json/": (200, '{"index":"..."}', {"content-type": "application/json"}),
    }


@pytest.fixture
def mock_http_client(mocker, mock_wordpress_responses):
    """Mock HTTP client that returns predefined responses."""
    from wp_recon_suite.engine.http import SafeHTTPClient

    client = SafeHTTPClient()

    def mock_get(url, **kwargs):
        # Extract path from URL
        path = url.split(":443", 1)[-1].split(":80", 1)[-1]  # Remove port
        if url.startswith("http"):
            path = "/" + url.split("/", 3)[-1]

        # Find matching response
        for key, (status, content, headers) in mock_wordpress_responses.items():
            if key in path or path == key:
                return httpx.Response(
                    status_code=status,
                    content=content.encode(),
                    headers=headers,
                    request=httpx.Request("GET", url),
                )

        # Default 404
        return httpx.Response(
            status_code=404,
            content=b"",
            request=httpx.Request("GET", url),
        )

    mocker.patch.object(client, "get", side_effect=mock_get)
    return client


@pytest.fixture
def sample_target():
    """Sample WordPress target URL."""
    return "https://example.com"
