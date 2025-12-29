"""Report generation module."""

from pathlib import Path
from typing import Optional


class ReportGenerator:
    """
    Report generator for converting between formats.

    Generates comprehensive reports from scan results.
    """

    @staticmethod
    def generate_pdf(
        html_file: Path,
        output_file: Path,
        use_weasyprint: bool = True,
    ) -> bool:
        """
        Generate PDF from HTML report.

        Args:
            html_file: Path to HTML file
            output_file: Output PDF path
            use_weasyprint: Use weasyprint (else try wkhtmltopdf)

        Returns:
            True if successful, False otherwise
        """
        if use_weasyprint:
            try:
                import weasyprint

                weasyprint.HTML(str(html_file)).write_pdf(str(output_file))
                return True
            except ImportError:
                return False
            except Exception:
                return False
        else:
            # Try wkhtmltopdf
            try:
                import subprocess

                subprocess.run(
                    ["wkhtmltopdf", str(html_file), str(output_file)],
                    check=True,
                    capture_output=True,
                )
                return True
            except (ImportError, FileNotFoundError, subprocess.CalledProcessError):
                return False
