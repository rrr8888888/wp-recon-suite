"""Author enumeration module."""

import logging
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import urljoin, urlparse

from wp_recon_suite.engine.http import SafeHTTPClient, HTTPClientConfig

logger = logging.getLogger(__name__)


@dataclass
class AuthorResult:
    """Result of author enumeration."""

    id: int
    redirect: Optional[str] = None
    username: Optional[str] = None
    http_code: int = 404
    note: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class AuthorEnumModule:
    """
    Author enumeration module.

    Enumerates WordPress authors by:
    - Testing /?author=N parameter
    - Following redirects to extract author slugs
    - Extracting usernames from redirect locations

    Features:
    - Safe GET requests only
    - Automatic redirect following
    - Username extraction from redirects
    - Configurable ID range

    Example:
        >>> module = AuthorEnumModule(http_client=client)
        >>> results = module.enumerate('https://example.com', start=1, end=50)
        >>> for author in results:
        ...     print(f"ID {author.id}: {author.username}")
    """

    def __init__(
        self,
        http_client: Optional[SafeHTTPClient] = None,
        http_config: Optional[HTTPClientConfig] = None,
    ):
        """
        Initialize author enumeration module.

        Args:
            http_client: SafeHTTPClient instance
            http_config: HTTPClientConfig for creating a new client
        """
        if http_client is None:
            http_config = http_config or HTTPClientConfig()
            self.http_client = SafeHTTPClient(config=http_config)
            self.should_close_client = True
        else:
            self.http_client = http_client
            self.should_close_client = False

    def enumerate(
        self,
        target: str,
        start: int = 1,
        end: int = 50,
    ) -> list[AuthorResult]:
        """
        Enumerate authors by ID.

        Args:
            target: Target URL
            start: Starting author ID
            end: Ending author ID (inclusive)

        Returns:
            List of AuthorResult objects
        """
        if not target.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {target}")

        results = []

        for author_id in range(start, end + 1):
            try:
                # Construct author query parameter
                author_url = f"{target}/?author={author_id}"
                logger.debug(f"Checking {author_url}")

                # Make request without following redirects initially
                response = self.http_client.get(author_url, follow_redirects=False)

                result = AuthorResult(id=author_id, http_code=response.status_code)

                # Check for redirect (common in WordPress)
                if response.status_code in (301, 302, 307, 308):
                    redirect_location = response.headers.get("location", "")
                    result.redirect = redirect_location

                    # Extract username from redirect
                    if redirect_location:
                        username = self._extract_username_from_redirect(
                            redirect_location, target
                        )
                        result.username = username

                        result.note = "author found (redirect)"
                        logger.debug(
                            f"  Author {author_id}: {username} (redirect: {redirect_location})"
                        )
                    else:
                        result.note = "redirect without location"

                elif response.status_code == 200:
                    result.note = "author found (direct)"
                    logger.debug(f"  Author {author_id}: found at /?author={author_id}")

                else:
                    result.note = f"not found ({response.status_code})"

                results.append(result)

            except Exception as e:
                logger.warning(f"Error checking author {author_id}: {e}")
                result = AuthorResult(
                    id=author_id,
                    http_code=0,
                    note=f"error: {str(e)[:50]}",
                )
                results.append(result)

        return results

    @staticmethod
    def _extract_username_from_redirect(redirect_url: str, target: str) -> Optional[str]:
        """
        Extract username from a redirect URL.

        Handles common patterns:
        - https://example.com/author/admin/
        - https://example.com/author/john/
        - https://example.com/users/admin/

        Args:
            redirect_url: The redirect URL
            target: Original target URL (for relative URL handling)

        Returns:
            Extracted username or None
        """
        # Handle relative redirects
        if redirect_url.startswith("/"):
            target_parsed = urlparse(target)
            redirect_url = f"{target_parsed.scheme}://{target_parsed.netloc}{redirect_url}"

        # Parse the redirect URL
        parsed = urlparse(redirect_url)
        path = parsed.path.rstrip("/")

        # Common patterns: /author/username, /users/username, /member/username
        for pattern in ["/author/", "/users/", "/member/", "/profiles/"]:
            if pattern in path:
                parts = path.split(pattern)
                if len(parts) > 1 and parts[1]:
                    username = parts[1].split("/")[0]
                    if username:
                        return username

        return None

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
