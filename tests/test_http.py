"""Tests for the HTTP engine module."""

import pytest
from unittest.mock import Mock, patch
import httpx

from wp_recon_suite.engine.http import (
    SafeHTTPClient,
    AsyncHTTPClient,
    HTTPClientConfig,
)


class TestHTTPClientConfig:
    """Test HTTPClientConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = HTTPClientConfig()
        assert config.timeout == 10
        assert config.verify_ssl is True
        assert config.retries == 3
        assert config.retry_backoff == 1.0
        assert "wp-recon-suite" in config.user_agent

    def test_custom_config(self):
        """Test custom configuration."""
        config = HTTPClientConfig(
            timeout=20,
            verify_ssl=False,
            retries=5,
            retry_backoff=2.0,
            user_agent="CustomAgent/1.0",
        )
        assert config.timeout == 20
        assert config.verify_ssl is False
        assert config.retries == 5
        assert config.retry_backoff == 2.0
        assert config.user_agent == "CustomAgent/1.0"


class TestSafeHTTPClient:
    """Test SafeHTTPClient."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = SafeHTTPClient()
        assert client._client is not None
        assert isinstance(client.config, HTTPClientConfig)
        client.close()

    def test_client_with_custom_config(self):
        """Test client with custom config."""
        config = HTTPClientConfig(timeout=20, retries=5)
        client = SafeHTTPClient(config=config)
        assert client.config.timeout == 20
        assert client.config.retries == 5
        client.close()

    def test_get_request(self):
        """Test GET request."""
        with SafeHTTPClient() as client:
            # This would require mocking httpx or using a test server
            # For now, we test the structure
            assert hasattr(client, "get")
            assert callable(client.get)

    def test_head_request(self):
        """Test HEAD request."""
        with SafeHTTPClient() as client:
            assert hasattr(client, "head")
            assert callable(client.head)

    def test_context_manager(self):
        """Test context manager functionality."""
        with SafeHTTPClient() as client:
            assert client._client is not None

    def test_close_method(self):
        """Test explicit close method."""
        client = SafeHTTPClient()
        # Should not raise
        client.close()

    @patch("wp_recon_suite.engine.http.httpx.Client")
    def test_user_agent_header(self, mock_httpx_client):
        """Test that User-Agent header is set."""
        config = HTTPClientConfig(user_agent="TestAgent/1.0")
        client = SafeHTTPClient(config=config)
        
        # Verify httpx.Client was called with User-Agent header
        call_kwargs = mock_httpx_client.call_args[1]
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["User-Agent"] == "TestAgent/1.0"
        client.close()

    @patch("wp_recon_suite.engine.http.httpx.Client")
    def test_ssl_verification_enabled(self, mock_httpx_client):
        """Test that SSL verification is enabled by default."""
        config = HTTPClientConfig(verify_ssl=True)
        client = SafeHTTPClient(config=config)
        
        call_kwargs = mock_httpx_client.call_args[1]
        assert call_kwargs["verify"] is True
        client.close()

    @patch("wp_recon_suite.engine.http.httpx.Client")
    def test_ssl_verification_disabled(self, mock_httpx_client):
        """Test that SSL verification can be disabled."""
        config = HTTPClientConfig(verify_ssl=False)
        client = SafeHTTPClient(config=config)
        
        call_kwargs = mock_httpx_client.call_args[1]
        assert call_kwargs["verify"] is False
        client.close()


class TestAsyncHTTPClient:
    """Test AsyncHTTPClient."""

    def test_async_client_initialization(self):
        """Test async client initialization."""
        client = AsyncHTTPClient()
        assert client._client is not None
        assert isinstance(client.config, HTTPClientConfig)

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager."""
        async with AsyncHTTPClient() as client:
            assert client._client is not None

    def test_async_client_with_custom_config(self):
        """Test async client with custom config."""
        config = HTTPClientConfig(timeout=15, retries=4)
        client = AsyncHTTPClient(config=config)
        assert client.config.timeout == 15
        assert client.config.retries == 4

    @patch("wp_recon_suite.engine.http.httpx.AsyncClient")
    def test_async_user_agent_header(self, mock_httpx_client):
        """Test that User-Agent header is set in async client."""
        config = HTTPClientConfig(user_agent="AsyncAgent/1.0")
        client = AsyncHTTPClient(config=config)
        
        call_kwargs = mock_httpx_client.call_args[1]
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["User-Agent"] == "AsyncAgent/1.0"
