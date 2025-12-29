"""REST API and XML-RPC detection module."""

import logging
import json
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import urljoin

from wp_recon_suite.engine.http import SafeHTTPClient, HTTPClientConfig

logger = logging.getLogger(__name__)


@dataclass
class User:
    """WordPress user information."""

    id: int
    slug: str
    name: str
    link: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class RESTAPIResult:
    """Result of REST API detection."""

    root_found: bool
    root_url: str = ""
    users_exposed: bool = False
    users_count: int = 0
    users: list[User] = None

    def __post_init__(self):
        """Initialize users list if None."""
        if self.users is None:
            self.users = []

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data["users"] = [u.to_dict() for u in self.users]
        return data


@dataclass
class XMLRPCResult:
    """Result of XML-RPC detection."""

    found: bool
    pingback_enabled: bool = False
    http_code: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class RESTXMLRPCModule:
    """
    REST API and XML-RPC detection module.

    Checks for:
    - WordPress REST API endpoint (/wp-json/)
    - User enumeration via /wp-json/wp/v2/users
    - XML-RPC endpoint (/xmlrpc.php)

    Features:
    - Safe GET/HEAD requests only
    - User enumeration with optional rate limiting
    - No payloads or exploitation
    - Graceful handling of errors

    Example:
        >>> module = RESTXMLRPCModule(http_client=client)
        >>> rest_result = module.check_rest_api('https://example.com')
        >>> xmlrpc_result = module.check_xmlrpc('https://example.com')
    """

    def __init__(
        self,
        http_client: Optional[SafeHTTPClient] = None,
        http_config: Optional[HTTPClientConfig] = None,
    ):
        """
        Initialize REST/XML-RPC module.

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

    def check_rest_api(self, target: str) -> RESTAPIResult:
        """
        Check for WordPress REST API.

        Args:
            target: Target URL

        Returns:
            RESTAPIResult object
        """
        if not target.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {target}")

        result = RESTAPIResult(root_found=False)

        try:
            # Check for /wp-json/
            wp_json_url = urljoin(target, "/wp-json/")
            logger.debug(f"Checking {wp_json_url}")

            response = self.http_client.get(wp_json_url)

            if response.status_code == 200:
                result.root_found = True
                result.root_url = wp_json_url
                logger.info("WordPress REST API found")

                # Try to enumerate users
                users = self._enumerate_users(target)
                result.users = users
                result.users_count = len(users)
                result.users_exposed = len(users) > 0

                logger.info(f"Found {len(users)} users")

        except Exception as e:
            logger.warning(f"Error checking REST API: {e}")

        return result

    def _enumerate_users(self, target: str, max_users: int = 50) -> list[User]:
        """
        Enumerate WordPress users from REST API.

        Args:
            target: Target URL
            max_users: Maximum users to retrieve

        Returns:
            List of User objects
        """
        users = []

        try:
            users_url = urljoin(target, "/wp-json/wp/v2/users/")
            logger.debug(f"Enumerating users from {users_url}")

            response = self.http_client.get(users_url)

            if response.status_code == 200:
                try:
                    users_data = response.json()
                    if isinstance(users_data, list):
                        for user_data in users_data[:max_users]:
                            user = User(
                                id=user_data.get("id", 0),
                                slug=user_data.get("slug", ""),
                                name=user_data.get("name", ""),
                                link=user_data.get("link"),
                            )
                            users.append(user)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Error parsing user data: {e}")

        except Exception as e:
            logger.warning(f"Error enumerating users: {e}")

        return users

    def check_xmlrpc(self, target: str) -> XMLRPCResult:
        """
        Check for XML-RPC endpoint.

        Args:
            target: Target URL

        Returns:
            XMLRPCResult object
        """
        if not target.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {target}")

        result = XMLRPCResult(found=False)

        try:
            xmlrpc_url = urljoin(target, "/xmlrpc.php")
            logger.debug(f"Checking {xmlrpc_url}")

            response = self.http_client.head(xmlrpc_url)
            result.http_code = response.status_code

            if response.status_code == 200:
                result.found = True
                logger.info("XML-RPC endpoint found")

                # Check if pingback is enabled (look for X-Pingback header)
                if "X-Pingback" in response.headers:
                    result.pingback_enabled = True
                    logger.info("Pingback is enabled")

        except Exception as e:
            logger.warning(f"Error checking XML-RPC: {e}")

        return result

    def scan(self, target: str) -> dict:
        """
        Perform full REST/XML-RPC scan.

        Args:
            target: Target URL

        Returns:
            Dictionary with both REST and XML-RPC results
        """
        rest_result = self.check_rest_api(target)
        xmlrpc_result = self.check_xmlrpc(target)

        return {
            "rest_api": rest_result.to_dict(),
            "xmlrpc": xmlrpc_result.to_dict(),
        }

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
