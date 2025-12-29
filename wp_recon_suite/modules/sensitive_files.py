"""Sensitive file discovery module."""

import logging
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import urljoin

from wp_recon_suite.engine.http import SafeHTTPClient, HTTPClientConfig

logger = logging.getLogger(__name__)


@dataclass
class SensitiveFileResult:
    """Result of a sensitive file check."""

    path: str
    http_code: int
    length: int
    note: str = ""
    content_type: Optional[str] = None
    headers: dict = None

    def __post_init__(self):
        """Initialize headers if None."""
        if self.headers is None:
            self.headers = {}

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class SensitiveFilesModule:
    """
    Sensitive file discovery module.

    Checks a predefined list of sensitive paths to detect exposure:
    - readme.html
    - license.txt
    - wp-config.php.bak
    - .git/config
    - debug.log
    - etc.

    Features:
    - Safe GET/HEAD requests only
    - Records response code, content length, and headers
    - No payload injection or brute-force
    - Graceful handling of timeouts and errors

    Example:
        >>> module = SensitiveFilesModule(
        ...     http_client=client,
        ...     paths=['/readme.html', '/license.txt']
        ... )
        >>> results = module.scan('https://example.com')
        >>> for result in results:
        ...     print(f"{result.path}: {result.http_code}")
    """

    DEFAULT_PATHS = [
        "/readme.html",
        "/license.txt",
        "/wp-config.php",
        "/wp-config.php.bak",
        "/wp-config.php.old",
        "/wp-config.old",
        "/.git/config",
        "/.git/HEAD",
        "/debug.log",
        "/error.log",
        "/error_log",
        "/.env",
        "/.htaccess",
        "/web.config",
        "/composer.json",
        "/composer.lock",
        "/package.json",
        "/package-lock.json",
        "/Gemfile",
        "/Gemfile.lock",
    ]

    def __init__(
        self,
        http_client: Optional[SafeHTTPClient] = None,
        paths: Optional[list[str]] = None,
        http_config: Optional[HTTPClientConfig] = None,
    ):
        """
        Initialize sensitive files module.

        Args:
            http_client: SafeHTTPClient instance; creates one if None
            paths: List of paths to check; uses DEFAULT_PATHS if None
            http_config: HTTPClientConfig for creating a new client
        """
        if http_client is None:
            http_config = http_config or HTTPClientConfig()
            self.http_client = SafeHTTPClient(config=http_config)
            self.should_close_client = True
        else:
            self.http_client = http_client
            self.should_close_client = False

        self.paths = paths or self.DEFAULT_PATHS

    def scan(self, target: str) -> list[SensitiveFileResult]:
        """
        Scan target for sensitive files.

        Args:
            target: Target URL (e.g., https://example.com)

        Returns:
            List of SensitiveFileResult objects

        Raises:
            ValueError: If target is not a valid URL
        """
        if not target.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {target}")

        results = []

        for path in self.paths:
            try:
                full_url = urljoin(target, path)
                logger.debug(f"Checking {full_url}")

                response = self.http_client.get(full_url, follow_redirects=False)

                result = SensitiveFileResult(
                    path=path,
                    http_code=response.status_code,
                    length=len(response.content),
                    content_type=response.headers.get("content-type", ""),
                    headers=dict(response.headers),
                )

                # Determine if file is exposed
                if response.status_code == 200:
                    result.note = "exposed"
                elif response.status_code in (301, 302, 307, 308):
                    redirect_location = response.headers.get("location", "")
                    result.note = f"redirect to {redirect_location}"
                elif response.status_code == 403:
                    result.note = "forbidden (exists but not accessible)"
                elif response.status_code == 404:
                    result.note = "not found"
                else:
                    result.note = f"http {response.status_code}"

                results.append(result)
                logger.debug(
                    f"  {path}: {response.status_code} ({result.note})"
                )

            except Exception as e:
                logger.warning(f"Error checking {path}: {e}")
                # Add error result for tracking
                result = SensitiveFileResult(
                    path=path,
                    http_code=0,
                    length=0,
                    note=f"error: {str(e)[:50]}",
                )
                results.append(result)

        return results

    def close(self) -> None:
        """Close HTTP client if we created it."""
        if self.should_close_client:
            self.http_client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
