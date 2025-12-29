"""Tests for REST/XML-RPC module."""

import pytest
from unittest.mock import Mock
import httpx

from wp_recon_suite.modules.rest_xmlrpc import (
    RESTXMLRPCModule,
    RESTAPIResult,
    XMLRPCResult,
    User,
)
from wp_recon_suite.engine.http import SafeHTTPClient


class TestUser:
    """Test User dataclass."""

    def test_user_creation(self):
        """Test creating a user."""
        user = User(id=1, slug="admin", name="Administrator")
        assert user.id == 1
        assert user.slug == "admin"
        assert user.name == "Administrator"

    def test_user_to_dict(self):
        """Test converting user to dict."""
        user = User(id=1, slug="admin", name="Administrator", link="https://example.com/author/admin")
        data = user.to_dict()
        assert data["id"] == 1
        assert data["slug"] == "admin"


class TestRESTXMLRPCModule:
    """Test RESTXMLRPCModule."""

    def test_module_initialization(self):
        """Test module initialization."""
        module = RESTXMLRPCModule()
        assert module.http_client is not None
        module.close()

    def test_check_rest_api_invalid_url(self):
        """Test checking REST API with invalid URL."""
        module = RESTXMLRPCModule()
        with pytest.raises(ValueError, match="Invalid URL"):
            module.check_rest_api("not-a-url")
        module.close()

    def test_check_rest_api_found(self):
        """Test REST API detection when found."""
        mock_client = Mock(spec=SafeHTTPClient)
        
        # Mock REST API root found
        rest_root_response = httpx.Response(
            200,
            content=b'{"index":"..."}',
            request=httpx.Request("GET", "https://example.com/wp-json/"),
        )
        
        # Mock users endpoint
        users_response = httpx.Response(
            200,
            content=b'[{"id":1,"slug":"admin","name":"Administrator"}]',
            request=httpx.Request("GET", "https://example.com/wp-json/wp/v2/users/"),
        )
        
        def get_side_effect(url, **kwargs):
            if "wp-json/" in url:
                if "users" in url:
                    return users_response
                else:
                    return rest_root_response
            return httpx.Response(404, request=httpx.Request("GET", url))
        
        mock_client.get.side_effect = get_side_effect
        
        module = RESTXMLRPCModule(http_client=mock_client)
        result = module.check_rest_api("https://example.com")
        
        assert result.root_found is True
        assert result.users_count == 1
        assert result.users_exposed is True

    def test_check_xmlrpc_found(self):
        """Test XML-RPC detection when found."""
        mock_client = Mock(spec=SafeHTTPClient)
        
        response = httpx.Response(
            200,
            content=b"",
            headers={"X-Pingback": "https://example.com/xmlrpc.php"},
            request=httpx.Request("HEAD", "https://example.com/xmlrpc.php"),
        )
        mock_client.head.return_value = response
        
        module = RESTXMLRPCModule(http_client=mock_client)
        result = module.check_xmlrpc("https://example.com")
        
        assert result.found is True
        assert result.pingback_enabled is True

    def test_check_xmlrpc_not_found(self):
        """Test XML-RPC detection when not found."""
        mock_client = Mock(spec=SafeHTTPClient)
        
        response = httpx.Response(
            404,
            content=b"",
            request=httpx.Request("HEAD", "https://example.com/xmlrpc.php"),
        )
        mock_client.head.return_value = response
        
        module = RESTXMLRPCModule(http_client=mock_client)
        result = module.check_xmlrpc("https://example.com")
        
        assert result.found is False
        assert result.http_code == 404

    def test_scan_combined(self):
        """Test full scan with both REST and XML-RPC."""
        mock_client = Mock(spec=SafeHTTPClient)
        
        rest_response = httpx.Response(
            200,
            content=b'{}',
            request=httpx.Request("GET", "https://example.com/wp-json/"),
        )
        
        users_response = httpx.Response(
            200,
            content=b'[]',
            request=httpx.Request("GET", "https://example.com/wp-json/wp/v2/users/"),
        )
        
        xmlrpc_response = httpx.Response(
            404,
            content=b"",
            request=httpx.Request("HEAD", "https://example.com/xmlrpc.php"),
        )
        
        def get_side_effect(url, **kwargs):
            if "users" in url:
                return users_response
            elif "wp-json/" in url:
                return rest_response
            return httpx.Response(404, request=httpx.Request("GET", url))
        
        mock_client.get.side_effect = get_side_effect
        mock_client.head.return_value = xmlrpc_response
        
        module = RESTXMLRPCModule(http_client=mock_client)
        results = module.scan("https://example.com")
        
        assert "rest_api" in results
        assert "xmlrpc" in results
        assert results["rest_api"]["root_found"] is True
        assert results["xmlrpc"]["found"] is False


class TestRESTAPIResult:
    """Test RESTAPIResult dataclass."""

    def test_result_creation(self):
        """Test creating a REST API result."""
        result = RESTAPIResult(root_found=True)
        assert result.root_found is True
        assert result.users == []

    def test_result_with_users(self):
        """Test result with users."""
        users = [
            User(id=1, slug="admin", name="Administrator"),
            User(id=2, slug="editor", name="Editor"),
        ]
        result = RESTAPIResult(
            root_found=True,
            users_exposed=True,
            users_count=2,
            users=users,
        )
        
        data = result.to_dict()
        assert data["users_count"] == 2
        assert len(data["users"]) == 2


class TestXMLRPCResult:
    """Test XMLRPCResult dataclass."""

    def test_result_creation(self):
        """Test creating an XML-RPC result."""
        result = XMLRPCResult(found=True, pingback_enabled=True)
        assert result.found is True
        assert result.pingback_enabled is True

    def test_result_to_dict(self):
        """Test converting to dict."""
        result = XMLRPCResult(found=True, http_code=200)
        data = result.to_dict()
        assert data["found"] is True
        assert data["http_code"] == 200
