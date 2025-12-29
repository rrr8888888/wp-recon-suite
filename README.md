# wp-recon-suite

Professional, safe-by-default WordPress reconnaissance and structure validation CLI tool for Kali Linux.

## ⚠️ Legal & Ethical Notice

**IMPORTANT:** This tool is designed for authorized security testing and reconnaissance ONLY.

- **Default mode is SAFE-ONLY**: Non-destructive GET/HEAD requests, REST API enumeration, and read-only discovery.
- **Aggressive features are DISABLED by default** and require explicit user confirmation.
- **You MUST have written permission from the target website owner** before running any aggressive scans.
- Every execution is logged with timestamps and legal acceptance confirmations for audit purposes.
- Unauthorized access to computer systems is illegal in most jurisdictions (CFAA in USA, Computer Misuse Act in UK, etc.).

**By using this tool, you accept full legal and ethical responsibility for your actions.**

---

## Features

### Safe-by-Default Scanning
- ✅ HTTP GET/HEAD requests with sensible timeouts
- ✅ WordPress REST API detection and enumeration (`/wp-json/`)
- ✅ XML-RPC discovery and analysis (`/xmlrpc.php`)
- ✅ Author enumeration via query parameters (`/?author=N`)
- ✅ Sensitive file discovery (safe detection, no payloads)
- ✅ Read-only directory fuzzing with ffuf (if available)
- ✅ WPScan integration for plugin/theme enumeration (optional)

### Aggressive Modules (Opt-In)
- ⚠️ Advanced fuzzing with payloads (requires `--aggressive --confirm-legal`)
- ⚠️ Brute-force attacks (requires explicit confirmation)
- ⚠️ Exploit testing (requires explicit confirmation)

### Output Formats
- 📊 Structured JSON with timestamps and module provenance
- 🎨 Pretty terminal output with rich formatting
- 📄 Optional HTML reports
- 📋 Audit logs with all invoked commands and timestamps

---

## Installation

### Requirements
- Python 3.11+
- Kali Linux (or similar Debian-based distribution)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/wp-recon-suite.git
cd wp-recon-suite

# Install in development mode
pip install -e .

# Install optional dependencies
pip install -e ".[pdf,dev]"
```

### Optional External Tools
For enhanced reconnaissance, install these tools:

```bash
# ffuf - Fast web fuzzer (recommended)
sudo apt-get install -y ffuf

# WPScan - WordPress vulnerability scanner
# https://github.com/wpscanteam/wpscan
gem install wpscan
```

---

## Usage

### Basic Safe Scan
```bash
wp-recon-suite scan --target https://example.com --out ./results
```

### With Custom Config
```bash
wp-recon-suite scan --target https://example.com --out ./results --config config.yaml
```

### Enable Aggressive Scanning (with legal confirmation)
```bash
wp-recon-suite scan \
  --target https://example.com \
  --out ./results \
  --aggressive \
  --confirm-legal "I have written permission from example-corp"
```

### Use Custom Wordlist
```bash
wp-recon-suite scan \
  --target https://example.com \
  --out ./results \
  --ffuf-wordlist /usr/share/seclists/Discovery/Web-Content/CMS/wordpress.txt
```

### Adjust Concurrency
```bash
wp-recon-suite scan \
  --target https://example.com \
  --out ./results \
  --concurrency 20
```

---

## Configuration

Create a `config.yaml` (see `config.example.yaml` for template):

```yaml
# Global timeouts in seconds
http:
  timeout: 10
  verify_ssl: true
  retries: 3
  retry_backoff: 1.0

# Sensitive paths to check
sensitive_files:
  paths:
    - /readme.html
    - /license.txt
    - /wp-config.php.bak
    - /.git/config
    - /debug.log

# Fuzzing options
ffuf:
  enabled: true
  wordlist: /usr/share/seclists/Discovery/Web-Content/CMS/wordpress.txt
  extensions: [php, txt, html, zip]
  threads: 40
  rate_limit: 0

# WPScan options
wpscan:
  enabled: true
  aggressive: false
  token: ${WPSCAN_API_TOKEN}  # Read from environment

# Output options
output:
  json: true
  html: true
  pretty_print: true
```

---

## Example Output

### Safe Scan Results
```json
{
  "target": "https://example.com",
  "timestamp": "2025-12-29T21:00:00Z",
  "modules": {
    "sensitive_files": [
      {"path": "/readme.html", "http_code": 200, "length": 1234, "note": "exposed"},
      {"path": "/license.txt", "http_code": 200, "length": 567, "note": "exposed"}
    ],
    "wp_json": {
      "root_found": true,
      "users_exposed": true,
      "users_count": 3
    },
    "author_enum": [
      {"id": 1, "redirect": "/author/admin/", "username": "admin"},
      {"id": 2, "redirect": "/author/editor/", "username": "editor"}
    ],
    "xmlrpc": {"found": true, "pingback_enabled": true},
    "ffuf": {"invoked": true, "top_results": [{"path": "/wp-admin/", "code": 301}]},
    "wpscan": {"invoked": false, "summary": null}
  },
  "legal_acceptance": {
    "safe_only": true,
    "aggressive": false,
    "confirmation_text": null
  }
}
```

---

## Architecture

```
wp-recon-suite/
├── wp_recon_suite/
│   ├── __init__.py
│   ├── cli.py                 # Click CLI entry point
│   ├── config.py              # Configuration management
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── http.py            # httpx client with retry logic
│   │   └── audit.py           # Audit logging
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── sensitive_files.py # Sensitive path discovery
│   │   ├── rest_xmlrpc.py     # REST API & XML-RPC detection
│   │   ├── author_enum.py     # Author enumeration
│   │   ├── ffuf_wrapper.py    # ffuf orchestration
│   │   └── wpscan_wrapper.py  # WPScan integration
│   └── output/
│       ├── __init__.py
│       ├── formatters.py      # JSON, HTML, text formatters
│       └── report.py          # Report generation
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # pytest fixtures
│   ├── fixtures/              # JSON/text fixtures
│   ├── test_http.py
│   ├── test_sensitive_files.py
│   ├── test_rest_xmlrpc.py
│   ├── test_author_enum.py
│   ├── test_ffuf_wrapper.py
│   └── test_wpscan_wrapper.py
├── examples/
│   ├── config.example.yaml
│   ├── sample_output.json
│   └── sample_report.html
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
├── README.md
├── LICENSE
└── CHANGELOG.md
```

---

## Security & Safety

- **No plaintext secrets**: API tokens are read from environment variables only.
- **Safe subprocess execution**: No `shell=True`, all commands logged to audit.log with masked secrets.
- **Sensible defaults**: Timeouts, retries, and rate limiting enabled by default.
- **Input validation**: URLs validated; file paths normalized.
- **Audit trail**: Every execution logged with timestamps and legal acceptance confirmations.

---

## Testing

Run the full test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=wp_recon_suite
```

Run specific tests:

```bash
pytest tests/test_sensitive_files.py -v
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Write tests for new features
4. Ensure all tests pass: `pytest`
5. Format code: `black . && ruff check . --fix`
6. Commit with clear messages: `git commit -m "feat(module): description"`
7. Push and create a Pull Request

---

## Development Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black wp_recon_suite tests

# Lint code
ruff check wp_recon_suite tests --fix

# Type checking
mypy wp_recon_suite

# Run tests
pytest
```

---

## License

MIT License - See LICENSE file for details

---

## Disclaimer

**Use of this tool is at your own risk.** The authors assume no liability for misuse, legal consequences, or damage caused by this tool. Always:

1. ✅ Obtain written permission before scanning any target
2. ✅ Follow your jurisdiction's laws and regulations
3. ✅ Respect robots.txt and site policies
4. ✅ Document your authorization for audit purposes
5. ✅ Use the tool responsibly and ethically

---

## عربي (Arabic)

### ⚠️ تحذير قانوني وأخلاقي

هذه الأداة مخصصة لاختبار الأمان المصرح به فقط.

- **الوضع الافتراضي آمن تماماً**: طلبات GET/HEAD غير مدمرة فقط
- **ميزات البرامج الكاشطة معطلة بشكل افتراضي** وتتطلب تأكيداً صريحاً من المستخدم
- **يجب أن تحصل على إذن خطي من مالك الموقع الهدف** قبل تشغيل أي فحص
- يتم تسجيل كل عملية تنفيذ مع الطوابع الزمنية

**باستخدام هذه الأداة، فإنك توافق على تحمل المسؤولية القانونية والأخلاقية الكاملة عن أفعالك.**

---

## Support

For issues, questions, or contributions:
- 📧 Email: [your-email]
- 🐛 GitHub Issues: https://github.com/yourusername/wp-recon-suite/issues
- 💬 Discussions: https://github.com/yourusername/wp-recon-suite/discussions

---

**Happy scanning! Remember to always act ethically and legally.**
