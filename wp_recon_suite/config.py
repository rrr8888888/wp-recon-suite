"""Configuration management for wp-recon-suite."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class HTTPConfig:
    """HTTP configuration."""

    timeout: int = 10
    verify_ssl: bool = True
    retries: int = 3
    retry_backoff: float = 1.0
    user_agent: str = "wp-recon-suite/0.1.0"


@dataclass
class SensitiveFilesConfig:
    """Sensitive files module configuration."""

    enabled: bool = True
    paths: list[str] = field(
        default_factory=lambda: [
            "/readme.html",
            "/license.txt",
            "/wp-config.php.bak",
            "/.git/config",
            "/debug.log",
        ]
    )


@dataclass
class RESTXMLRPCConfig:
    """REST/XML-RPC module configuration."""

    enabled: bool = True
    check_rest: bool = True
    enumerate_users: bool = True
    check_xmlrpc: bool = True


@dataclass
class AuthorEnumConfig:
    """Author enumeration module configuration."""

    enabled: bool = True
    start_id: int = 1
    end_id: int = 50
    follow_redirects: bool = True


@dataclass
class FfufConfig:
    """ffuf module configuration."""

    enabled: bool = True
    wordlist: Optional[str] = None
    extensions: list[str] = field(default_factory=lambda: ["php", "txt", "html"])
    threads: int = 40
    rate_limit: int = 0
    timeout: int = 10


@dataclass
class WPScanConfig:
    """WPScan module configuration."""

    enabled: bool = True
    aggressive: bool = False
    token: Optional[str] = None


@dataclass
class OutputConfig:
    """Output configuration."""

    json: bool = True
    html: bool = True
    pretty_print: bool = True
    include_raw_responses: bool = False


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    audit_log: bool = True
    log_commands: bool = True
    mask_secrets: bool = True


@dataclass
class Config:
    """Main configuration class."""

    http: HTTPConfig = field(default_factory=HTTPConfig)
    sensitive_files: SensitiveFilesConfig = field(
        default_factory=SensitiveFilesConfig
    )
    rest_xmlrpc: RESTXMLRPCConfig = field(default_factory=RESTXMLRPCConfig)
    author_enum: AuthorEnumConfig = field(default_factory=AuthorEnumConfig)
    ffuf: FfufConfig = field(default_factory=FfufConfig)
    wpscan: WPScanConfig = field(default_factory=WPScanConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_file(cls, config_file: Path) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            config_file: Path to configuration file

        Returns:
            Config instance
        """
        config = cls()

        if not config_file.exists():
            return config

        with open(config_file, "r") as f:
            data = yaml.safe_load(f) or {}

        # Update configuration from file
        if "http" in data:
            config.http = HTTPConfig(**{
                k: v for k, v in data["http"].items()
                if hasattr(HTTPConfig, k)
            })

        if "sensitive_files" in data:
            config.sensitive_files = SensitiveFilesConfig(**{
                k: v for k, v in data["sensitive_files"].items()
                if hasattr(SensitiveFilesConfig, k)
            })

        if "rest_xmlrpc" in data:
            config.rest_xmlrpc = RESTXMLRPCConfig(**{
                k: v for k, v in data["rest_xmlrpc"].items()
                if hasattr(RESTXMLRPCConfig, k)
            })

        if "author_enum" in data:
            config.author_enum = AuthorEnumConfig(**{
                k: v for k, v in data["author_enum"].items()
                if hasattr(AuthorEnumConfig, k)
            })

        if "ffuf" in data:
            config.ffuf = FfufConfig(**{
                k: v for k, v in data["ffuf"].items()
                if hasattr(FfufConfig, k)
            })

        if "wpscan" in data:
            config.wpscan = WPScanConfig(**{
                k: v for k, v in data["wpscan"].items()
                if hasattr(WPScanConfig, k)
            })

        if "output" in data:
            config.output = OutputConfig(**{
                k: v for k, v in data["output"].items()
                if hasattr(OutputConfig, k)
            })

        if "logging" in data:
            config.logging = LoggingConfig(**{
                k: v for k, v in data["logging"].items()
                if hasattr(LoggingConfig, k)
            })

        return config

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "http": vars(self.http),
            "sensitive_files": vars(self.sensitive_files),
            "rest_xmlrpc": vars(self.rest_xmlrpc),
            "author_enum": vars(self.author_enum),
            "ffuf": vars(self.ffuf),
            "wpscan": vars(self.wpscan),
            "output": vars(self.output),
            "logging": vars(self.logging),
        }
