"""HTTP client abstraction with retry logic, timeouts, and safe defaults."""

import logging
from typing import Optional

import httpx
from tenacity import (
    after_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    Retrying,
)

logger = logging.getLogger(__name__)


class HTTPClientConfig:
    """Configuration for HTTP client."""

    def __init__(
        self,
        timeout: int = 10,
        verify_ssl: bool = True,
        retries: int = 3,
        retry_backoff: float = 1.0,
        user_agent: str = "wp-recon-suite/0.1.0",
    ):
        """
        Initialize HTTP client configuration.

        Args:
            timeout: Request timeout in seconds
            verify_ssl: Verify SSL certificates
            retries: Number of retries for failed requests
            retry_backoff: Backoff multiplier between retries
            user_agent: User-Agent header value
        """
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.retries = retries
        self.retry_backoff = retry_backoff
        self.user_agent = user_agent


class SafeHTTPClient:
    """
    HTTP client with safe defaults.

    Features:
    - Configurable timeouts
    - Retry logic with exponential backoff
    - Sensible User-Agent
    - SSL verification enabled by default
    - Connection pooling

    Example:
        >>> client = SafeHTTPClient(config=HTTPClientConfig(timeout=10))
        >>> response = client.get("https://example.com")
        >>> print(response.status_code)
    """

    def __init__(self, config: Optional[HTTPClientConfig] = None):
        """
        Initialize safe HTTP client.

        Args:
            config: HTTPClientConfig instance; uses defaults if None
        """
        self.config = config or HTTPClientConfig()
        self._client = httpx.Client(
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
            headers={"User-Agent": self.config.user_agent},
            follow_redirects=True,
        )

    def get(
        self,
        url: str,
        follow_redirects: bool = True,
        **kwargs,
    ) -> httpx.Response:
        """
        Perform GET request with retry logic.

        Args:
            url: Target URL
            follow_redirects: Follow HTTP redirects
            **kwargs: Additional arguments to pass to httpx.Client.get()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        retry_strategy = Retrying(
            retry=retry_if_exception_type(httpx.HTTPError),
            stop=stop_after_attempt(self.config.retries),
            wait=wait_exponential(multiplier=self.config.retry_backoff, min=1, max=10),
            after=after_log(logger, logging.DEBUG),
            reraise=True,
        )

        for attempt in retry_strategy:
            with attempt:
                logger.debug(f"GET {url} (attempt {attempt.retry_state.attempt_number})")
                return self._client.get(url, follow_redirects=follow_redirects, **kwargs)

    def head(self, url: str, **kwargs) -> httpx.Response:
        """
        Perform HEAD request with retry logic.

        Args:
            url: Target URL
            **kwargs: Additional arguments to pass to httpx.Client.head()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        retry_strategy = Retrying(
            retry=retry_if_exception_type(httpx.HTTPError),
            stop=stop_after_attempt(self.config.retries),
            wait=wait_exponential(multiplier=self.config.retry_backoff, min=1, max=10),
            after=after_log(logger, logging.DEBUG),
            reraise=True,
        )

        for attempt in retry_strategy:
            with attempt:
                logger.debug(f"HEAD {url} (attempt {attempt.retry_state.attempt_number})")
                return self._client.head(url, **kwargs)

    def close(self) -> None:
        """Close the HTTP client connection pool."""
        self._client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class AsyncHTTPClient:
    """
    Async HTTP client with safe defaults.

    Features:
    - Configurable timeouts
    - Retry logic with exponential backoff
    - Sensible User-Agent
    - SSL verification enabled by default
    - Connection pooling

    Example:
        >>> async with AsyncHTTPClient(config=HTTPClientConfig()) as client:
        ...     response = await client.get("https://example.com")
        ...     print(response.status_code)
    """

    def __init__(self, config: Optional[HTTPClientConfig] = None):
        """
        Initialize async HTTP client.

        Args:
            config: HTTPClientConfig instance; uses defaults if None
        """
        self.config = config or HTTPClientConfig()
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
            headers={"User-Agent": self.config.user_agent},
            follow_redirects=True,
        )

    async def get(
        self,
        url: str,
        follow_redirects: bool = True,
        **kwargs,
    ) -> httpx.Response:
        """
        Perform async GET request with retry logic.

        Args:
            url: Target URL
            follow_redirects: Follow HTTP redirects
            **kwargs: Additional arguments to pass to httpx.AsyncClient.get()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        retry_strategy = Retrying(
            retry=retry_if_exception_type(httpx.HTTPError),
            stop=stop_after_attempt(self.config.retries),
            wait=wait_exponential(multiplier=self.config.retry_backoff, min=1, max=10),
            after=after_log(logger, logging.DEBUG),
            reraise=True,
        )

        for attempt in retry_strategy:
            with attempt:
                logger.debug(f"GET {url} (attempt {attempt.retry_state.attempt_number})")
                return await self._client.get(url, follow_redirects=follow_redirects, **kwargs)

    async def head(self, url: str, **kwargs) -> httpx.Response:
        """
        Perform async HEAD request with retry logic.

        Args:
            url: Target URL
            **kwargs: Additional arguments to pass to httpx.AsyncClient.head()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        retry_strategy = Retrying(
            retry=retry_if_exception_type(httpx.HTTPError),
            stop=stop_after_attempt(self.config.retries),
            wait=wait_exponential(multiplier=self.config.retry_backoff, min=1, max=10),
            after=after_log(logger, logging.DEBUG),
            reraise=True,
        )

        for attempt in retry_strategy:
            with attempt:
                logger.debug(f"HEAD {url} (attempt {attempt.retry_state.attempt_number})")
                return await self._client.head(url, **kwargs)

    async def close(self) -> None:
        """Close the HTTP client connection pool."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
