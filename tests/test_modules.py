"""Tests for module wrappers (ffuf and wpscan)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from wp_recon_suite.modules.ffuf_wrapper import FfufWrapperModule, FfufResult
from wp_recon_suite.modules.wpscan_wrapper import WPScanWrapperModule, WPScanResult


class TestFfufWrapperModule:
    """Test FfufWrapperModule."""

    def test_module_initialization(self):
        """Test module initialization."""
        module = FfufWrapperModule()
        # Module should check if ffuf is available
        assert hasattr(module, "ffuf_available")

    def test_ffuf_not_available(self):
        """Test ffuf when not installed."""
        with patch.object(FfufWrapperModule, "_check_ffuf_availability", return_value=False):
            module = FfufWrapperModule()
            result = module.fuzz("https://example.com")
            
            assert result.invoked is False
            assert result.error == "ffuf not installed"

    def test_ffuf_no_wordlist(self):
        """Test ffuf without wordlist."""
        with patch.object(FfufWrapperModule, "_check_ffuf_availability", return_value=True):
            module = FfufWrapperModule()
            result = module.fuzz("https://example.com")
            
            assert result.invoked is False
            assert "wordlist" in result.error.lower()

    def test_ffuf_wordlist_not_found(self):
        """Test ffuf with non-existent wordlist."""
        with patch.object(FfufWrapperModule, "_check_ffuf_availability", return_value=True):
            module = FfufWrapperModule()
            result = module.fuzz(
                "https://example.com",
                wordlist="/non/existent/wordlist.txt"
            )
            
            assert result.invoked is False
            assert "not found" in result.error.lower()

    def test_ffuf_result_structure(self):
        """Test FfufResult dataclass."""
        result = FfufResult(
            invoked=True,
            command=["ffuf", "-u", "https://example.com/FUZZ"],
            total_results=10,
            top_results=[
                {"path": "/wp-admin/", "code": 301, "size": 0},
            ]
        )
        
        data = result.to_dict()
        assert data["invoked"] is True
        assert data["total_results"] == 10


class TestWPScanWrapperModule:
    """Test WPScanWrapperModule."""

    def test_module_initialization(self):
        """Test module initialization."""
        module = WPScanWrapperModule()
        assert hasattr(module, "wpscan_available")

    def test_wpscan_not_available(self):
        """Test wpscan when not installed."""
        with patch.object(WPScanWrapperModule, "_check_wpscan_availability", return_value=False):
            module = WPScanWrapperModule()
            result = module.scan("https://example.com")
            
            assert result.invoked is False
            assert result.error == "wpscan not installed"

    def test_wpscan_result_structure(self):
        """Test WPScanResult dataclass."""
        result = WPScanResult(
            invoked=True,
            command=["wpscan", "--url", "https://example.com"],
            output_file="/path/to/output.txt",
            summary="Found 1 plugin"
        )
        
        data = result.to_dict()
        assert data["invoked"] is True
        assert data["summary"] == "Found 1 plugin"
