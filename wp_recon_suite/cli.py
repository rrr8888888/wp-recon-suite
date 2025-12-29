"""Command-line interface for wp-recon-suite."""

import sys
import logging
from datetime import datetime
from pathlib import Path
from time import time

import click

from wp_recon_suite import LEGAL_WARNING
from wp_recon_suite.config import Config
from wp_recon_suite.engine.http import HTTPClientConfig
from wp_recon_suite.engine.audit import AuditLogger
from wp_recon_suite.modules.sensitive_files import SensitiveFilesModule
from wp_recon_suite.modules.rest_xmlrpc import RESTXMLRPCModule
from wp_recon_suite.modules.author_enum import AuthorEnumModule
from wp_recon_suite.modules.ffuf_wrapper import FfufWrapperModule
from wp_recon_suite.modules.wpscan_wrapper import WPScanWrapperModule
from wp_recon_suite.output.formatters import (
    JSONFormatter,
    TextFormatter,
    HTMLFormatter,
    TerminalFormatter,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def validate_url(ctx, param, value):
    """Validate target URL."""
    if not value:
        return value
    
    if not value.startswith(("http://", "https://")):
        raise click.BadParameter("Target must start with http:// or https://")
    
    return value


def validate_legal_confirmation(ctx, param, value):
    """Validate legal confirmation text."""
    if param.name == "aggressive" and value:
        # If aggressive is enabled, confirmation must be provided
        pass
    return value


@click.group()
def main():
    """WordPress Recon Suite - Professional WordPress reconnaissance tool."""
    pass


@main.command()
@click.option(
    "--target",
    required=True,
    callback=validate_url,
    help="Target WordPress URL (e.g., https://example.com)",
)
@click.option(
    "--out",
    type=click.Path(),
    default="./results",
    help="Output directory for results",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Configuration file (YAML)",
)
@click.option(
    "--safe-only",
    is_flag=True,
    default=True,
    help="Run in safe-only mode (default)",
)
@click.option(
    "--aggressive",
    is_flag=True,
    default=False,
    help="Enable aggressive scanning (requires legal confirmation)",
)
@click.option(
    "--confirm-legal",
    type=str,
    default=None,
    help='Legal confirmation text (e.g., "I have written permission from example-corp")',
)
@click.option(
    "--ffuf-wordlist",
    type=click.Path(exists=True),
    help="Custom wordlist for ffuf",
)
@click.option(
    "--wpscan-token",
    type=str,
    envvar="WPSCAN_API_TOKEN",
    help="WPScan API token (or set WPSCAN_API_TOKEN env var)",
)
@click.option(
    "--concurrency",
    type=int,
    default=10,
    help="Number of concurrent requests",
)
@click.option(
    "--timeout",
    type=int,
    default=10,
    help="Request timeout in seconds",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=True,
    help="Generate JSON output",
)
@click.option(
    "--html",
    "output_html",
    is_flag=True,
    default=False,
    help="Generate HTML report",
)
@click.option(
    "--no-banner",
    is_flag=True,
    default=False,
    help="Suppress legal warning banner",
)
def scan(
    target,
    out,
    config,
    safe_only,
    aggressive,
    confirm_legal,
    ffuf_wordlist,
    wpscan_token,
    concurrency,
    timeout,
    output_json,
    output_html,
    no_banner,
):
    """
    Perform WordPress reconnaissance scan.

    \b
    Examples:
      wp-recon-suite scan --target https://example.com
      wp-recon-suite scan --target https://example.com --aggressive --confirm-legal "I have written permission"
      wp-recon-suite scan --target https://example.com --html --ffuf-wordlist /path/to/wordlist.txt
    """
    # Print legal warning unless suppressed
    if not no_banner:
        click.echo(LEGAL_WARNING)

    # Validate aggressive mode
    if aggressive and not confirm_legal:
        click.echo(
            "[ERROR] Aggressive mode requires --confirm-legal with explicit permission text",
            err=True,
        )
        sys.exit(1)

    if aggressive and len(confirm_legal) < 10:
        click.echo(
            "[ERROR] Confirmation text must be meaningful (at least 10 characters)",
            err=True,
        )
        sys.exit(1)

    # Load configuration
    output_dir = Path(out)
    output_dir.mkdir(parents=True, exist_ok=True)

    config_obj = Config()
    if config:
        config_obj = Config.from_file(Path(config))

    # Update config from CLI arguments
    config_obj.http.timeout = timeout
    if ffuf_wordlist:
        config_obj.ffuf.wordlist = ffuf_wordlist
    if wpscan_token:
        config_obj.wpscan.token = wpscan_token
    config_obj.output.json = output_json
    config_obj.output.html = output_html

    # Initialize audit logger
    audit_log_path = output_dir / "audit.log"
    audit_logger = AuditLogger(audit_log_path)

    start_time = time()

    try:
        # Log execution start
        audit_logger.log_execution_start(
            target=target,
            cli_args={
                "safe_only": safe_only,
                "aggressive": aggressive,
                "timeout": timeout,
                "concurrency": concurrency,
            },
            safe_only=safe_only,
            aggressive=aggressive,
            confirmation_text=confirm_legal if aggressive else None,
        )

        click.echo(f"\n[*] Starting WordPress reconnaissance scan on {target}\n")

        # Initialize results
        results = {
            "target": target,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "modules": {},
            "legal_acceptance": {
                "safe_only": safe_only,
                "aggressive": aggressive,
                "confirmation_text": confirm_legal if aggressive else None,
            },
        }

        # Initialize HTTP client
        http_config = HTTPClientConfig(timeout=timeout)

        # Run sensitive files module
        if config_obj.sensitive_files.enabled:
            click.echo("[*] Running sensitive files module...")
            try:
                with SensitiveFilesModule(
                    http_config=http_config,
                    paths=config_obj.sensitive_files.paths,
                ) as module:
                    file_results = module.scan(target)
                    results["modules"]["sensitive_files"] = [
                        r.to_dict() for r in file_results
                    ]
                    audit_logger.log_module_invocation(
                        "sensitive_files",
                        findings_count=len(file_results),
                    )
                    click.echo(f"    Found {len(file_results)} paths checked")
            except Exception as e:
                click.echo(f"    [!] Error: {e}", err=True)
                audit_logger.log_error("sensitive_files", str(e))

        # Run REST/XML-RPC module
        if config_obj.rest_xmlrpc.enabled:
            click.echo("[*] Running REST API / XML-RPC module...")
            try:
                with RESTXMLRPCModule(http_config=http_config) as module:
                    rest_result = module.check_rest_api(target)
                    xmlrpc_result = module.check_xmlrpc(target)
                    results["modules"]["rest_api"] = rest_result.to_dict()
                    results["modules"]["xmlrpc"] = xmlrpc_result.to_dict()
                    audit_logger.log_module_invocation(
                        "rest_xmlrpc",
                        findings_count=len(rest_result.users),
                    )
                    click.echo(
                        f"    REST API: {rest_result.root_found}, "
                        f"XML-RPC: {xmlrpc_result.found}"
                    )
            except Exception as e:
                click.echo(f"    [!] Error: {e}", err=True)
                audit_logger.log_error("rest_xmlrpc", str(e))

        # Run author enumeration module
        if config_obj.author_enum.enabled:
            click.echo("[*] Running author enumeration module...")
            try:
                with AuthorEnumModule(http_config=http_config) as module:
                    author_results = module.enumerate(
                        target,
                        start=config_obj.author_enum.start_id,
                        end=config_obj.author_enum.end_id,
                    )
                    found_authors = [a for a in author_results if a.username]
                    results["modules"]["author_enum"] = [
                        a.to_dict() for a in found_authors
                    ]
                    audit_logger.log_module_invocation(
                        "author_enum",
                        findings_count=len(found_authors),
                    )
                    click.echo(f"    Found {len(found_authors)} authors")
            except Exception as e:
                click.echo(f"    [!] Error: {e}", err=True)
                audit_logger.log_error("author_enum", str(e))

        # Run ffuf module
        if config_obj.ffuf.enabled and config_obj.ffuf.wordlist:
            click.echo("[*] Running ffuf directory fuzzing...")
            try:
                ffuf_module = FfufWrapperModule()
                ffuf_result = ffuf_module.fuzz(
                    target,
                    wordlist=config_obj.ffuf.wordlist,
                    extensions=config_obj.ffuf.extensions,
                    threads=config_obj.ffuf.threads,
                    output_file=output_dir / "ffuf.json" if config_obj.output.json else None,
                )
                results["modules"]["ffuf"] = ffuf_result.to_dict()
                audit_logger.log_module_invocation("ffuf")
                if ffuf_result.invoked:
                    click.echo(
                        f"    Found {ffuf_result.total_results} results, "
                        f"top 10 recorded"
                    )
                else:
                    click.echo(f"    [!] {ffuf_result.error}")
            except Exception as e:
                click.echo(f"    [!] Error: {e}", err=True)
                audit_logger.log_error("ffuf", str(e))

        # Run WPScan module
        if config_obj.wpscan.enabled:
            click.echo("[*] Running WPScan module...")
            try:
                wpscan_module = WPScanWrapperModule()
                wpscan_result = wpscan_module.scan(
                    target,
                    output_dir=output_dir,
                    api_token=config_obj.wpscan.token,
                    aggressive=aggressive and config_obj.wpscan.aggressive,
                )
                results["modules"]["wpscan"] = wpscan_result.to_dict()
                audit_logger.log_module_invocation("wpscan")
                if wpscan_result.invoked:
                    click.echo(f"    Output saved to {wpscan_result.output_file}")
                else:
                    click.echo(f"    [!] {wpscan_result.error}")
            except Exception as e:
                click.echo(f"    [!] Error: {e}", err=True)
                audit_logger.log_error("wpscan", str(e))

        # Save results
        click.echo("\n[*] Saving results...")

        total_findings = 0

        # JSON output
        if config_obj.output.json:
            json_file = output_dir / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_results.json"
            JSONFormatter.save(results, json_file)
            click.echo(f"    JSON: {json_file}")

        # Text output
        text_file = output_dir / "summary.txt"
        TextFormatter.save(results, text_file)
        click.echo(f"    Text: {text_file}")

        # HTML output
        if config_obj.output.html:
            html_file = output_dir / "report.html"
            HTMLFormatter.save(results, html_file)
            click.echo(f"    HTML: {html_file}")

        # Display terminal summary
        click.echo("")
        TerminalFormatter.display_results(results)

        # Log execution end
        duration = time() - start_time
        audit_logger.log_execution_end(
            total_findings=total_findings,
            duration_seconds=duration,
        )

        # Save audit log
        audit_logger.save()
        click.echo(f"\n[✓] Scan completed in {duration:.2f}s")
        click.echo(f"[✓] Results saved to {output_dir}")

    except KeyboardInterrupt:
        click.echo("\n[!] Scan interrupted by user", err=True)
        sys.exit(130)

    except Exception as e:
        click.echo(f"\n[!] Fatal error: {e}", err=True)
        audit_logger.log_error("main", str(e))
        audit_logger.save()
        sys.exit(1)


@main.command()
def version():
    """Show version information."""
    from wp_recon_suite import __version__
    click.echo(f"WordPress Recon Suite v{__version__}")


if __name__ == "__main__":
    main()
