"""Output formatters for JSON, HTML, and terminal output."""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    import jinja2
except ImportError:
    jinja2 = None

from rich.console import Console
from rich.table import Table


class JSONFormatter:
    """Formatter for JSON output."""

    @staticmethod
    def format(data: dict, pretty: bool = True) -> str:
        """
        Format data as JSON.

        Args:
            data: Data to format
            pretty: Pretty-print the output

        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(data, indent=2, default=str, ensure_ascii=False)
        else:
            return json.dumps(data, default=str, ensure_ascii=False)

    @staticmethod
    def save(data: dict, filepath: Path) -> None:
        """
        Save data to JSON file.

        Args:
            data: Data to save
            filepath: Path to save to
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)


class TextFormatter:
    """Formatter for human-readable text output."""

    @staticmethod
    def format(data: dict) -> str:
        """
        Format data as human-readable text.

        Args:
            data: Scan results data

        Returns:
            Formatted text string
        """
        output = []

        # Header
        output.append("=" * 80)
        output.append("WordPress Recon Suite - Scan Results")
        output.append("=" * 80)
        output.append("")

        # Target and timestamp
        output.append(f"Target: {data.get('target', 'N/A')}")
        output.append(f"Timestamp: {data.get('timestamp', 'N/A')}")
        output.append("")

        # Legal status
        legal = data.get("legal_acceptance", {})
        output.append("Legal Status:")
        output.append(f"  Safe-only mode: {legal.get('safe_only', False)}")
        output.append(f"  Aggressive mode: {legal.get('aggressive', False)}")
        output.append("")

        # Modules
        modules = data.get("modules", {})

        # Sensitive files
        if "sensitive_files" in modules:
            output.append("Sensitive Files:")
            files = modules["sensitive_files"]
            if files:
                for file in files:
                    status = "✓" if file.get("http_code") == 200 else "✗"
                    output.append(
                        f"  {status} {file.get('path')} - "
                        f"HTTP {file.get('http_code')} ({file.get('note', '')})"
                    )
            else:
                output.append("  (none found)")
            output.append("")

        # REST API
        if "rest_api" in modules:
            rest = modules["rest_api"]
            output.append("REST API:")
            output.append(f"  Found: {rest.get('root_found', False)}")
            if rest.get("users_exposed"):
                output.append(f"  Users enumerated: {rest.get('users_count', 0)}")
                if rest.get("users"):
                    for user in rest["users"]:
                        output.append(f"    - {user.get('name')} ({user.get('slug')})")
            output.append("")

        # XML-RPC
        if "xmlrpc" in modules:
            xmlrpc = modules["xmlrpc"]
            output.append("XML-RPC:")
            output.append(f"  Found: {xmlrpc.get('found', False)}")
            output.append(f"  Pingback enabled: {xmlrpc.get('pingback_enabled', False)}")
            output.append("")

        # Authors
        if "author_enum" in modules:
            authors = modules["author_enum"]
            if authors:
                output.append("Authors Found:")
                for author in authors:
                    if author.get("username"):
                        output.append(
                            f"  ID {author.get('id')}: {author.get('username')}"
                        )
            output.append("")

        # Footer
        output.append("=" * 80)

        return "\n".join(output)

    @staticmethod
    def save(data: dict, filepath: Path) -> None:
        """
        Save formatted text to file.

        Args:
            data: Scan results data
            filepath: Path to save to
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            f.write(TextFormatter.format(data))


class HTMLFormatter:
    """Formatter for HTML report generation."""

    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WordPress Recon Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        header .meta {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        .section {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .finding {
            padding: 10px;
            margin: 8px 0;
            background: #f8f9fa;
            border-left: 3px solid #667eea;
            border-radius: 4px;
        }
        .finding.exposed {
            border-left-color: #e74c3c;
            background: #fadbd8;
        }
        .finding.found {
            border-left-color: #f39c12;
            background: #fdebd0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #667eea;
        }
        tr:hover { background: #f8f9fa; }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .badge.found {
            background: #d4edda;
            color: #155724;
        }
        .badge.notfound {
            background: #e2e3e5;
            color: #383d41;
        }
        .badge.error {
            background: #f8d7da;
            color: #721c24;
        }
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 WordPress Recon Report</h1>
            <div class="meta">
                <p>Target: <strong>{{ target }}</strong></p>
                <p>Timestamp: <strong>{{ timestamp }}</strong></p>
            </div>
        </header>

        <div class="warning">
            <strong>⚠️ Legal Notice:</strong> This scan was conducted with appropriate authorization.
            All findings should be verified and handled according to your organization's policies.
        </div>

        {% if modules.sensitive_files %}
        <div class="section">
            <h2>📁 Sensitive Files</h2>
            {% if modules.sensitive_files %}
                <table>
                    <tr>
                        <th>Path</th>
                        <th>HTTP Code</th>
                        <th>Size</th>
                        <th>Status</th>
                    </tr>
                    {% for file in modules.sensitive_files %}
                    <tr class="{% if file.http_code == 200 %}exposed{% endif %}">
                        <td><code>{{ file.path }}</code></td>
                        <td>{{ file.http_code }}</td>
                        <td>{{ file.length }} bytes</td>
                        <td>
                            {% if file.http_code == 200 %}
                                <span class="badge found">Exposed</span>
                            {% elif file.http_code == 404 %}
                                <span class="badge notfound">Not Found</span>
                            {% else %}
                                <span class="badge">{{ file.note }}</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p>No sensitive files checked.</p>
            {% endif %}
        </div>
        {% endif %}

        {% if modules.rest_api %}
        <div class="section">
            <h2>📡 REST API</h2>
            {% set rest = modules.rest_api %}
            <div class="finding {% if rest.root_found %}found{% endif %}">
                <strong>REST API Root:</strong>
                {% if rest.root_found %}
                    <span class="badge found">Found</span> at {{ rest.root_url }}
                {% else %}
                    <span class="badge notfound">Not Found</span>
                {% endif %}
            </div>
            {% if rest.users %}
            <div style="margin-top: 15px;">
                <strong>Users Enumerated ({{ rest.users_count }}):</strong>
                <ul>
                {% for user in rest.users %}
                    <li><code>{{ user.slug }}</code> - {{ user.name }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
        {% endif %}

        {% if modules.author_enum %}
        <div class="section">
            <h2>👥 Authors</h2>
            {% if modules.author_enum %}
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Redirect</th>
                    </tr>
                    {% for author in modules.author_enum %}
                    {% if author.username %}
                    <tr>
                        <td>{{ author.id }}</td>
                        <td><code>{{ author.username }}</code></td>
                        <td><code>{{ author.redirect }}</code></td>
                    </tr>
                    {% endif %}
                    {% endfor %}
                </table>
            {% else %}
                <p>No authors enumerated.</p>
            {% endif %}
        </div>
        {% endif %}

        <footer>
            <p>Generated by <strong>WordPress Recon Suite v0.1.0</strong></p>
            <p style="margin-top: 10px; font-size: 0.85em;">
                ⚠️ This report contains sensitive security information. 
                Handle according to your organization's data protection policies.
            </p>
        </footer>
    </div>
</body>
</html>
    """

    @staticmethod
    def format(data: dict) -> str:
        """
        Format data as HTML.

        Args:
            data: Scan results data

        Returns:
            HTML string
        """
        if jinja2 is None:
            return "<p>Jinja2 not available. Install with: pip install jinja2</p>"

        template = jinja2.Template(HTMLFormatter.HTML_TEMPLATE)
        return template.render(
            target=data.get("target", "Unknown"),
            timestamp=data.get("timestamp", "Unknown"),
            modules=data.get("modules", {}),
        )

    @staticmethod
    def save(data: dict, filepath: Path) -> None:
        """
        Save HTML report to file.

        Args:
            data: Scan results data
            filepath: Path to save to
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            f.write(HTMLFormatter.format(data))


class TerminalFormatter:
    """Formatter for rich terminal output."""

    @staticmethod
    def display_results(data: dict) -> None:
        """
        Display results in terminal using rich formatting.

        Args:
            data: Scan results data
        """
        console = Console()

        # Title
        console.print(
            "[bold magenta]WordPress Recon Suite - Scan Results[/bold magenta]"
        )
        console.print("")

        # Target info
        console.print(
            f"[cyan]Target:[/cyan] {data.get('target', 'N/A')}"
        )
        console.print(
            f"[cyan]Timestamp:[/cyan] {data.get('timestamp', 'N/A')}"
        )
        console.print("")

        # Modules summary
        modules = data.get("modules", {})

        if modules.get("sensitive_files"):
            table = Table(title="🔐 Sensitive Files", show_header=True)
            table.add_column("Path", style="cyan")
            table.add_column("HTTP Code", style="yellow")
            table.add_column("Status", style="green")

            exposed_count = 0
            for file in modules["sensitive_files"]:
                if file.get("http_code") == 200:
                    exposed_count += 1
                    table.add_row(
                        file.get("path", ""),
                        str(file.get("http_code", "")),
                        "[red]EXPOSED[/red]",
                    )
            console.print(table)
            console.print("")

        if modules.get("rest_api"):
            rest = modules["rest_api"]
            if rest.get("root_found"):
                console.print("[green]✓[/green] REST API endpoint found")
                if rest.get("users"):
                    console.print(f"  Found {rest.get('users_count')} users:")
                    for user in rest.get("users", []):
                        console.print(f"    - {user.get('slug')}")
            console.print("")

        if modules.get("author_enum"):
            authors = [a for a in modules["author_enum"] if a.get("username")]
            if authors:
                console.print(f"[yellow]✓[/yellow] Found {len(authors)} authors:")
                for author in authors:
                    console.print(
                        f"  - ID {author.get('id')}: [cyan]{author.get('username')}[/cyan]"
                    )
            console.print("")
