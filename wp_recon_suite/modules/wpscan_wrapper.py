"""WPScan wrapper module for vulnerability scanning."""

import logging
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class WPScanResult:
    """Result from WPScan."""

    invoked: bool
    command: Optional[list[str]] = None
    output_file: Optional[str] = None
    summary: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class WPScanWrapperModule:
    """
    WPScan wrapper module for WordPress vulnerability scanning.

    Orchestrates WPScan for plugin/theme enumeration and vulnerability detection:
    - Checks if WPScan is installed
    - Reads API token from WPSCAN_API_TOKEN environment variable
    - Runs WPScan safely without aggressive exploits
    - Saves output for review

    Features:
    - Safe subprocess execution (no shell=True)
    - API token read from environment only
    - Graceful failure if wpscan not available
    - Output saved to file for audit trail

    Example:
        >>> module = WPScanWrapperModule()
        >>> result = module.scan('https://example.com', output_dir='./results')
    """

    def __init__(self):
        """Initialize WPScan wrapper module."""
        self.wpscan_available = self._check_wpscan_availability()

    @staticmethod
    def _check_wpscan_availability() -> bool:
        """
        Check if wpscan is available in PATH.

        Returns:
            True if wpscan is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["which", "wpscan"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Error checking wpscan availability: {e}")
            return False

    def scan(
        self,
        target: str,
        output_dir: Optional[Path] = None,
        api_token: Optional[str] = None,
        aggressive: bool = False,
    ) -> WPScanResult:
        """
        Perform WPScan vulnerability scan.

        Args:
            target: Target URL
            output_dir: Directory to save output
            api_token: WPScan API token (reads from WPSCAN_API_TOKEN if None)
            aggressive: Enable aggressive checks

        Returns:
            WPScanResult object
        """
        result = WPScanResult(invoked=False)

        # Check if wpscan is available
        if not self.wpscan_available:
            result.error = "wpscan not installed"
            logger.warning("wpscan not available in PATH")
            return result

        try:
            # Build wpscan command
            cmd = [
                "wpscan",
                "--url", target,
                "--random-user-agent",  # Use random User-Agent
                "--disable-tls-checks" if target.startswith("https") else "",
            ]

            # Remove empty strings from command
            cmd = [c for c in cmd if c]

            # Add API token if provided
            if api_token:
                cmd.extend(["--api-token", api_token])

            # Add aggressive checks if requested
            if aggressive:
                cmd.extend([
                    "--plugins-detection", "aggressive",
                    "--themes-detection", "aggressive",
                ])

            # Prepare output file if directory specified
            output_file = None
            if output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / "wpscan_output.txt"
                cmd.extend(["--format", "cli"])

            logger.info(f"Running wpscan: {' '.join(cmd)}")
            result.command = cmd

            # Run wpscan
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                check=False,
            )

            result.invoked = True

            # Save output
            if output_file:
                with open(output_file, "w") as f:
                    f.write(process.stdout)
                    if process.stderr:
                        f.write("\n--- STDERR ---\n")
                        f.write(process.stderr)
                result.output_file = str(output_file)
                logger.info(f"WPScan output saved to {output_file}")

            # Extract summary
            if process.returncode == 0:
                lines = process.stdout.split("\n")
                # Try to find summary lines
                summary_lines = [
                    l for l in lines
                    if any(kw in l for kw in ["Found", "WordPress", "Plugin", "Theme"])
                ]
                if summary_lines:
                    result.summary = "; ".join(summary_lines[:3])
                logger.info(f"WPScan completed successfully")

            else:
                result.error = f"wpscan failed with code {process.returncode}"
                logger.warning(f"WPScan error: {process.stderr[:200]}")

        except subprocess.TimeoutExpired:
            result.error = "wpscan scan timeout"
            logger.error("wpscan exceeded timeout")

        except Exception as e:
            result.error = f"wpscan execution error: {str(e)[:100]}"
            logger.error(f"Error running wpscan: {e}")

        return result
