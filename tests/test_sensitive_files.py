"""Tests for the sensitive_files module."""

import pytest
from unittest.mock import Mock, patch
import httpx

from wp_recon_suite.modules.sensitive_files import (
    SensitiveFilesModule,
    SensitiveFileResult,
)
from wp_recon_suite.engine.http import SafeHTTPClient, HTTPClientConfig


class TestSensitiveFileResult:
    """Test SensitiveFileResult dataclass."""

    def test_result_creation(self):
        """Test creating a result."""
        result = SensitiveFileResult(
            path="/readme.html",
            http_code=200,
            length=1234,
            note="exposed",
        )
        assert result.path == "/readme.html"
        assert result.http_code == 200
        assert result.length == 1234
        assert result.note == "exposed"

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = SensitiveFileResult(
            path="/license.txt",
            http_code=200,
            length=567,
            note="exposed",
            content_type="text/plain",
        )
        result_dict = result.to_dict()
        assert result_dict["path"] == "/license.txt"
        assert result_dict["http_code"] == 200
        assert result_dict["content_type"] == "text/plain"


class TestSensitiveFilesModule:
    """Test SensitiveFilesModule."""

    def test_module_initialization_default(self):
        """Test module initialization with defaults."""
        module = SensitiveFilesModule()
        assert module.paths == SensitiveFilesModule.DEFAULT_PATHS
        assert module.http_client is not None
        assert module.should_close_client is True

    def test_module_initialization_custom_paths(self):
        """Test module initialization with custom paths."""
        custom_paths = ["/readme.html", "/license.txt"]
        module = SensitiveFilesModule(paths=custom_paths)
        assert module.paths == custom_paths

    def test_module_initialization_with_client(self):
        """Test module initialization with provided client."""
        client = SafeHTTPClient()
        module = SensitiveFilesModule(http_client=client)
        assert module.http_client == client
        assert module.should_close_client is False
        client.close()

    def test_scan_invalid_url(self):
        """Test scanning with invalid URL."""
        module = SensitiveFilesModule()
        with pytest.raises(ValueError, match="Invalid URL"):
            module.scan("not-a-url")
        module.close()

    def test_scan_with_mock_responses(self, mocker):
        """Test scanning with mocked HTTP responses."""
        # Create mock client
        mock_client = Mock(spec=SafeHTTPClient)

        # Define responses
        responses = {
            "https://example.com/readme.html": httpx.Response(
                200,
                content=b"readme",
                request=httpx.Request("GET", "https://example.com/readme.html"),
            ),
            "https://example.com/license.txt": httpx.Response(
                200,
                content=b"license",
                request=httpx.Request("GET", "https://example.com/license.txt"),
            ),
            "https://example.com/.git/config": httpx.Response(
                404,
                content=b"",
                request=httpx.Request("GET", "https://example.com/.git/config"),
            ),
            "https://example.com/debug.log": httpx.Response(
                403,
                content=b"",
                request=httpx.Request("GET", "https://example.com/debug.log"),
            ),
        }

        def get_side_effect(url, **kwargs):
            return responses.get(
                url,
                httpx.Response(
                    404,
                    content=b"",
                    request=httpx.Request("GET", url),
                ),
            )

        mock_client.get.side_effect = get_side_effect

        # Create module with mock client
        module = SensitiveFilesModule(
            http_client=mock_client,
            paths=["/readme.html", "/license.txt", "/.git/config", "/debug.log"],
        )

        # Scan
        results = module.scan("https://example.com")

        # Verify results
        assert len(results) == 4

        # Check specific results
        readme_result = next((r for r in results if r.path == "/readme.html"), None)
        assert readme_result is not None
        assert readme_result.http_code == 200
        assert readme_result.note == "exposed"
        assert readme_result.length == 6  # len(b"readme")

        not_found = next((r for r in results if r.path == "/.git/config"), None)
        assert not_found is not None
        assert not_found.http_code == 404
        assert not_found.note == "not found"

        forbidden = next((r for r in results if r.path == "/debug.log"), None)
        assert forbidden is not None
        assert forbidden.http_code == 403
        assert forbidden.note == "forbidden (exists but not accessible)"

    def test_scan_with_redirect(self, mocker):
        """Test scanning with redirect responses."""
        mock_client = Mock(spec=SafeHTTPClient)

        response = httpx.Response(
            301,
            content=b"",
            headers={"location": "/author/admin/"},
            request=httpx.Request("GET", "https://example.com/?author=1"),
        )
        mock_client.get.return_value = response

        module = SensitiveFilesModule(
            http_client=mock_client,
            paths=["/?author=1"],
        )

        results = module.scan("https://example.com")

        assert len(results) == 1
        assert results[0].http_code == 301
        assert "redirect" in results[0].note

    def test_scan_with_network_error(self, mocker):
        """Test scanning with network errors."""
        mock_client = Mock(spec=SafeHTTPClient)
        mock_client.get.side_effect = Exception("Connection timeout")

        module = SensitiveFilesModule(
            http_client=mock_client,
            paths=["/readme.html"],
        )

        results = module.scan("https://example.com")

        assert len(results) == 1
        assert results[0].http_code == 0
        assert "error" in results[0].note

    def test_context_manager(self):
        """Test module as context manager."""
        with SensitiveFilesModule() as module:
            assert module.http_client is not None

    def test_close_own_client(self):
        """Test that module closes its own client."""
        module = SensitiveFilesModule()
        assert module.should_close_client is True
        # Calling close should not raise
        module.close()

    def test_close_provided_client(self):
        """Test that module doesn't close provided client."""
        client = SafeHTTPClient()
        module = SensitiveFilesModule(http_client=client)
        assert module.should_close_client is False
        # Calling close should not close the client
        module.close()
        # Client should still be usable (mock would verify this)
        client.close()

    def test_default_paths_coverage(self):
        """Test that default paths cover important files."""
        important_files = [
            "/readme.html",
            "/license.txt",
            "/wp-config.php.bak",
            "/.git/config",
            "/debug.log",
            "/.env",
        ]
        for file in important_files:
            assert file in SensitiveFilesModule.DEFAULT_PATHS

    def test_result_headers_initialization(self):
        """Test that result headers initialize properly."""
        result = SensitiveFileResult(
            path="/test",
            http_code=200,
            length=0,
        )
        assert result.headers == {}
        assert result.headers is not None
