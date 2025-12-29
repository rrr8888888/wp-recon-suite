"""Tests for author enumeration module."""

import pytest
from unittest.mock import Mock
import httpx

from wp_recon_suite.modules.author_enum import (
    AuthorEnumModule,
    AuthorResult,
)
from wp_recon_suite.engine.http import SafeHTTPClient


class TestAuthorResult:
    """Test AuthorResult dataclass."""

    def test_result_creation(self):
        """Test creating a result."""
        result = AuthorResult(id=1, username="admin")
        assert result.id == 1
        assert result.username == "admin"

    def test_result_to_dict(self):
        """Test converting to dict."""
        result = AuthorResult(
            id=1,
            redirect="/author/admin/",
            username="admin",
            http_code=301,
        )
        data = result.to_dict()
        assert data["id"] == 1
        assert data["username"] == "admin"


class TestAuthorEnumModule:
    """Test AuthorEnumModule."""

    def test_module_initialization(self):
        """Test module initialization."""
        module = AuthorEnumModule()
        assert module.http_client is not None
        module.close()

    def test_enumerate_invalid_url(self):
        """Test enumeration with invalid URL."""
        module = AuthorEnumModule()
        with pytest.raises(ValueError, match="Invalid URL"):
            module.enumerate("not-a-url")
        module.close()

    def test_enumerate_with_redirects(self):
        """Test author enumeration with redirects."""
        mock_client = Mock(spec=SafeHTTPClient)
        
        # Author 1: redirect to /author/admin/
        response1 = httpx.Response(
            301,
            content=b"",
            headers={"location": "/author/admin/"},
            request=httpx.Request("GET", "https://example.com/?author=1"),
        )
        
        # Author 2: not found
        response2 = httpx.Response(
            404,
            content=b"",
            request=httpx.Request("GET", "https://example.com/?author=2"),
        )
        
        responses = {
            "https://example.com/?author=1": response1,
            "https://example.com/?author=2": response2,
        }
        
        def get_side_effect(url, **kwargs):
            return responses.get(
                url,
                httpx.Response(
                    404,
                    request=httpx.Request("GET", url),
                ),
            )
        
        mock_client.get.side_effect = get_side_effect
        
        module = AuthorEnumModule(http_client=mock_client)
        results = module.enumerate("https://example.com", start=1, end=2)
        
        assert len(results) == 2
        assert results[0].username == "admin"
        assert results[0].http_code == 301

    def test_extract_username_from_redirect(self):
        """Test username extraction from redirect."""
        # Test /author/ pattern
        username = AuthorEnumModule._extract_username_from_redirect(
            "/author/john/",
            "https://example.com"
        )
        assert username == "john"
        
        # Test /users/ pattern
        username = AuthorEnumModule._extract_username_from_redirect(
            "/users/jane/",
            "https://example.com"
        )
        assert username == "jane"
        
        # Test full URL
        username = AuthorEnumModule._extract_username_from_redirect(
            "https://example.com/author/admin/",
            "https://example.com"
        )
        assert username == "admin"

    def test_enumerate_range(self):
        """Test enumeration with custom ID range."""
        mock_client = Mock(spec=SafeHTTPClient)
        mock_client.get.return_value = httpx.Response(
            404,
            request=httpx.Request("GET", "https://example.com"),
        )
        
        module = AuthorEnumModule(http_client=mock_client)
        results = module.enumerate("https://example.com", start=10, end=15)
        
        assert len(results) == 6  # 10 through 15 inclusive
        assert results[0].id == 10
        assert results[-1].id == 15
