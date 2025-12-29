"""Audit logging for tracking invocations and legal acceptance."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger for tracking CLI invocations and legal acceptance.

    Every execution is logged with:
    - Timestamp
    - Invoked commands and arguments
    - Legal acceptance status
    - Any errors or warnings
    """

    def __init__(self, audit_log_path: Path):
        """
        Initialize audit logger.

        Args:
            audit_log_path: Path to audit.log file
        """
        self.audit_log_path = audit_log_path
        self.entries: list[dict] = []

    def log_execution_start(
        self,
        target: str,
        cli_args: dict,
        safe_only: bool,
        aggressive: bool,
        confirmation_text: Optional[str] = None,
    ) -> None:
        """
        Log the start of a scan execution.

        Args:
            target: Target URL
            cli_args: CLI arguments dictionary
            safe_only: Whether running in safe-only mode
            aggressive: Whether aggressive mode is enabled
            confirmation_text: User's legal confirmation text
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "execution_start",
            "target": target,
            "cli_args": cli_args,
            "safety": {
                "safe_only": safe_only,
                "aggressive": aggressive,
                "confirmation_text": confirmation_text,
            },
        }
        self.entries.append(entry)
        logger.info(f"Execution started: target={target}, safe_only={safe_only}")

    def log_module_invocation(
        self,
        module_name: str,
        command: Optional[list[str]] = None,
        findings_count: int = 0,
    ) -> None:
        """
        Log invocation of a specific module.

        Args:
            module_name: Name of the module (e.g., 'sensitive_files')
            command: Subprocess command list (if applicable)
            findings_count: Number of findings from module
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "module_invocation",
            "module": module_name,
            "command": command,
            "findings_count": findings_count,
        }
        self.entries.append(entry)
        logger.debug(f"Module invoked: {module_name}")

    def log_error(self, module_name: str, error_message: str) -> None:
        """
        Log an error from a module.

        Args:
            module_name: Name of the module
            error_message: Error message
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "error",
            "module": module_name,
            "error": error_message,
        }
        self.entries.append(entry)
        logger.error(f"Module error: {module_name}: {error_message}")

    def log_execution_end(self, total_findings: int, duration_seconds: float) -> None:
        """
        Log the end of a scan execution.

        Args:
            total_findings: Total number of findings
            duration_seconds: Duration of execution in seconds
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "execution_end",
            "total_findings": total_findings,
            "duration_seconds": duration_seconds,
        }
        self.entries.append(entry)
        logger.info(f"Execution completed: {total_findings} findings in {duration_seconds}s")

    def save(self) -> None:
        """Save audit log to file."""
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.audit_log_path, "w") as f:
            for entry in self.entries:
                f.write(json.dumps(entry) + "\n")
        logger.info(f"Audit log saved to {self.audit_log_path}")

    def mask_secrets(self, value: str, secret_patterns: Optional[list[str]] = None) -> str:
        """
        Mask secrets in a string.

        Args:
            value: String value
            secret_patterns: Patterns to mask (default: WPSCAN_API_TOKEN, etc.)

        Returns:
            Masked string
        """
        if secret_patterns is None:
            secret_patterns = [
                "WPSCAN_API_TOKEN",
                "API_KEY",
                "SECRET",
                "PASSWORD",
                "TOKEN",
            ]

        masked = value
        for pattern in secret_patterns:
            # Mask environment variable references
            masked = masked.replace(f"${{{pattern}}}", f"${{{pattern}}}***")
            # Mask direct values (simple heuristic)
            if pattern in masked:
                masked = masked.replace(pattern, f"{pattern}***")

        return masked
