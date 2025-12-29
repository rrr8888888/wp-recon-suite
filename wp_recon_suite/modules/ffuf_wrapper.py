"""ffuf wrapper module for directory fuzzing."""

import logging
import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FfufResult:
    """Result from ffuf."""

    invoked: bool
    command: Optional[list[str]] = None
    wordlist: Optional[str] = None
    top_results: list[dict] = None
    total_results: int = 0
    error: Optional[str] = None

    def __post_init__(self):
        """Initialize top_results if None."""
        if self.top_results is None:
            self.top_results = []

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class FfufWrapperModule:
    """
    ffuf (Fast Web Fuzzer) wrapper module.

    Orchestrates ffuf for read-only directory discovery:
    - Checks if ffuf is installed
    - Supports custom wordlists
    - Filters and normalizes results
    - Records top findings

    Features:
    - Safe read-only fuzzing only
    - No payload injection
    - Subprocess safety (no shell=True)
    - Graceful failure if ffuf not available

    Example:
        >>> module = FfufWrapperModule()
        >>> result = module.fuzz(
        ...     'https://example.com',
        ...     wordlist='/usr/share/seclists/Discovery/Web-Content/CMS/wordpress.txt'
        ... )
    """

    def __init__(self):
        """Initialize ffuf wrapper module."""
        self.ffuf_available = self._check_ffuf_availability()

    @staticmethod
    def _check_ffuf_availability() -> bool:
        """
        Check if ffuf is available in PATH.

        Returns:
            True if ffuf is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["which", "ffuf"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Error checking ffuf availability: {e}")
            return False

    def fuzz(
        self,
        target: str,
        wordlist: Optional[str] = None,
        extensions: Optional[list[str]] = None,
        threads: int = 40,
        timeout: int = 10,
        output_file: Optional[Path] = None,
    ) -> FfufResult:
        """
        Perform ffuf fuzzing.

        Args:
            target: Target URL
            wordlist: Path to wordlist file
            extensions: File extensions to fuzz (e.g., ['php', 'txt', 'html'])
            threads: Number of parallel threads
            timeout: Request timeout in seconds
            output_file: Optional file to save JSON output

        Returns:
            FfufResult object
        """
        result = FfufResult(invoked=False)

        # Check if ffuf is available
        if not self.ffuf_available:
            result.error = "ffuf not installed"
            logger.warning("ffuf not available in PATH")
            return result

        # Validate wordlist
        if not wordlist:
            result.error = "No wordlist provided"
            logger.warning("No wordlist specified for ffuf")
            return result

        if not Path(wordlist).exists():
            result.error = f"Wordlist not found: {wordlist}"
            logger.warning(f"Wordlist file not found: {wordlist}")
            return result

        try:
            # Build ffuf command
            cmd = [
                "ffuf",
                "-u", f"{target}/FUZZ",
                "-w", wordlist,
                "-t", str(threads),
                "-timeout", str(timeout),
                "-sf",  # Skip filtering (don't filter by status code size)
                "-fc", "404",  # Filter out 404 responses
            ]

            # Add extensions if provided
            if extensions:
                extensions_str = ",".join(extensions)
                cmd.extend(["-e", extensions_str])

            # Add output file if specified
            if output_file:
                cmd.extend(["-of", "json", "-o", str(output_file)])
            else:
                cmd.extend(["-of", "json"])

            logger.info(f"Running ffuf: {' '.join(cmd)}")
            result.command = cmd
            result.wordlist = wordlist

            # Run ffuf
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for fuzzing
                check=False,
            )

            result.invoked = True

            if process.returncode == 0:
                try:
                    # Parse JSON output
                    ffuf_output = json.loads(process.stdout)

                    # Extract results
                    if "results" in ffuf_output:
                        all_results = ffuf_output["results"]
                        result.total_results = len(all_results)

                        # Sort by status code and take top 10
                        sorted_results = sorted(
                            all_results,
                            key=lambda x: (x.get("status", 0), -x.get("length", 0)),
                        )

                        result.top_results = [
                            {
                                "path": r.get("path", ""),
                                "code": r.get("status", 0),
                                "size": r.get("length", 0),
                            }
                            for r in sorted_results[:10]
                        ]

                        logger.info(
                            f"ffuf found {result.total_results} results, "
                            f"top 10 recorded"
                        )

                except json.JSONDecodeError as e:
                    result.error = f"Failed to parse ffuf output: {e}"
                    logger.error(result.error)

            else:
                result.error = f"ffuf failed with code {process.returncode}"
                logger.error(f"ffuf error: {process.stderr}")

        except subprocess.TimeoutExpired:
            result.error = "ffuf fuzzing timeout"
            logger.error("ffuf fuzzing exceeded timeout")

        except Exception as e:
            result.error = f"ffuf execution error: {str(e)[:100]}"
            logger.error(f"Error running ffuf: {e}")

        return result
