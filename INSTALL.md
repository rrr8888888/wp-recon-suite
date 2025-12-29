# wp-recon-suite: Installation & Quick Start Guide

## Project Overview

`wp-recon-suite` is a professional, safe-by-default WordPress reconnaissance tool for Kali Linux. It automates non-destructive WordPress enumeration with full audit trails and legal safeguards.

**Key Features:**
- ✅ Safe-only mode by default (GET/HEAD requests only)
- ✅ Aggressive features disabled without explicit opt-in
- ✅ Comprehensive audit logging with legal acceptance tracking
- ✅ Multi-module architecture (sensitive files, REST API, XML-RPC, author enum, ffuf, WPScan)
- ✅ Multiple output formats (JSON, HTML, text)
- ✅ Full test coverage with pytest
- ✅ CI/CD with GitHub Actions

## Installation

### Option 1: Using setup.sh (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/wp-recon-suite.git
cd wp-recon-suite

# Run setup script (creates venv, installs dependencies, runs tests)
bash setup.sh

# Activate virtual environment
source venv/bin/activate
```

### Option 2: Manual Installation

```bash
# Create Python 3.11+ virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install in development mode with all dependencies
pip install -e ".[dev,pdf]"

# Run tests to verify installation
pytest tests/ -v
```

### Option 3: System-wide Installation (Linux)

```bash
# Clone and navigate
git clone https://github.com/yourusername/wp-recon-suite.git
cd wp-recon-suite

# Install system dependencies (Debian/Ubuntu)
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Install pip packages
sudo pip install -e .
```

## First Run

### Basic Syntax

```bash
wp-recon-suite scan --target <URL> --out <OUTPUT_DIR> [OPTIONS]
```

### Safe-Only Scan (Default)

```bash
# Minimal scan with all defaults
wp-recon-suite scan --target https://example.com --out ./results

# This will:
# 1. Check sensitive file paths (readme.html, wp-config.php.bak, etc.)
# 2. Query REST API endpoint (/wp-json/)
# 3. Check XML-RPC endpoint (/xmlrpc.php)
# 4. Enumerate authors via /?author=N parameter
# 5. Save results to ./results/ directory
```

### Examine Results

```bash
# View JSON results
cat results/*_results.json | jq .

# View summary
cat results/summary.txt

# View audit log
cat results/audit.log

# View HTML report (open in browser)
open results/report.html
```

## Project Structure

```
wp-recon-suite/
├── wp_recon_suite/              # Main package
│   ├── __init__.py
│   ├── cli.py                   # CLI entry point (Click)
│   ├── config.py                # Configuration management
│   ├── engine/                  # Core infrastructure
│   │   ├── http.py              # Safe HTTP client (httpx + tenacity)
│   │   └── audit.py             # Audit logging
│   ├── modules/                 # Reconnaissance modules
│   │   ├── sensitive_files.py   # Sensitive path discovery
│   │   ├── rest_xmlrpc.py       # REST API & XML-RPC detection
│   │   ├── author_enum.py       # Author enumeration
│   │   ├── ffuf_wrapper.py      # ffuf integration
│   │   └── wpscan_wrapper.py    # WPScan integration
│   └── output/                  # Output formatters
│       ├── formatters.py        # JSON, HTML, terminal formatters
│       └── report.py            # Report generation
├── tests/                       # Test suite
│   ├── conftest.py              # pytest fixtures
│   ├── test_http.py
│   ├── test_sensitive_files.py
│   ├── test_rest_xmlrpc.py
│   ├── test_author_enum.py
│   ├── test_modules.py
│   └── fixtures/
│       └── wordpress_responses.py
├── examples/                    # Example configurations and outputs
│   ├── config.example.yaml
│   ├── sample_output.md
│   └── README.md
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD
├── pyproject.toml              # Project configuration
├── config.example.yaml         # Configuration template
├── README.md                   # Main documentation
├── LICENSE                     # MIT License
├── CHANGELOG.md                # Version history
├── setup.sh                    # Setup automation script
└── .gitignore                  # Git ignore rules
```

## Core Modules

### 1. `engine.http` - Safe HTTP Client

```python
from wp_recon_suite.engine.http import SafeHTTPClient, HTTPClientConfig

config = HTTPClientConfig(timeout=10, verify_ssl=True, retries=3)
with SafeHTTPClient(config=config) as client:
    response = client.get("https://example.com")
    print(response.status_code)
```

**Features:**
- Configurable timeouts and retries
- Exponential backoff with tenacity
- SSL verification enabled by default
- No shell execution

### 2. `modules.sensitive_files` - File Discovery

```python
from wp_recon_suite.modules.sensitive_files import SensitiveFilesModule

module = SensitiveFilesModule(paths=[
    "/readme.html",
    "/wp-config.php.bak",
    "/.git/config",
])
results = module.scan("https://example.com")

for result in results:
    print(f"{result.path}: HTTP {result.http_code} - {result.note}")
```

### 3. `modules.rest_xmlrpc` - API Detection

```python
from wp_recon_suite.modules.rest_xmlrpc import RESTXMLRPCModule

module = RESTXMLRPCModule()
rest_result = module.check_rest_api("https://example.com")
xmlrpc_result = module.check_xmlrpc("https://example.com")

print(f"REST API: {rest_result.root_found}")
print(f"Users: {rest_result.users_count}")
print(f"XML-RPC: {xmlrpc_result.found}")
```

### 4. `modules.author_enum` - Author Enumeration

```python
from wp_recon_suite.modules.author_enum import AuthorEnumModule

module = AuthorEnumModule()
results = module.enumerate("https://example.com", start=1, end=50)

for author in results:
    if author.username:
        print(f"ID {author.id}: {author.username}")
```

### 5. `modules.ffuf_wrapper` - Directory Fuzzing

```python
from wp_recon_suite.modules.ffuf_wrapper import FfufWrapperModule

module = FfufWrapperModule()
result = module.fuzz(
    "https://example.com",
    wordlist="/usr/share/seclists/Discovery/Web-Content/CMS/wordpress.txt",
    extensions=["php", "txt", "html"],
    threads=40
)

print(f"Results: {result.total_results}")
for item in result.top_results:
    print(f"  {item['path']}: {item['code']}")
```

### 6. `modules.wpscan_wrapper` - Vulnerability Scanning

```python
from wp_recon_suite.modules.wpscan_wrapper import WPScanWrapperModule

module = WPScanWrapperModule()
result = module.scan("https://example.com", output_dir="./results")

if result.invoked:
    print(f"Output: {result.output_file}")
else:
    print(f"Error: {result.error}")
```

## Configuration

### Using config.yaml

```yaml
http:
  timeout: 15
  verify_ssl: true
  retries: 5

sensitive_files:
  enabled: true
  paths:
    - /readme.html
    - /license.txt

rest_xmlrpc:
  enabled: true
  check_rest: true
  enumerate_users: true
  check_xmlrpc: true

author_enum:
  enabled: true
  start_id: 1
  end_id: 100

ffuf:
  enabled: true
  wordlist: /usr/share/seclists/Discovery/Web-Content/CMS/wordpress.txt
  extensions: [php, txt, html]
  threads: 40

wpscan:
  enabled: true
  aggressive: false
  token: ${WPSCAN_API_TOKEN}

output:
  json: true
  html: true
```

Run with config:

```bash
wp-recon-suite scan --target https://example.com --config config.yaml --out ./results
```

## Advanced Usage

### With ffuf Integration

```bash
# Install ffuf first
sudo apt-get install ffuf

# Run with directory fuzzing
wp-recon-suite scan \
  --target https://example.com \
  --out ./results \
  --ffuf-wordlist /usr/share/seclists/Discovery/Web-Content/CMS/wordpress.txt
```

### With WPScan

```bash
# Install WPScan
gem install wpscan

# Run with API token
WPSCAN_API_TOKEN="your-api-key" wp-recon-suite scan \
  --target https://example.com \
  --out ./results
```

### Aggressive Mode (With Legal Confirmation)

```bash
# Requires explicit written permission confirmation
wp-recon-suite scan \
  --target https://example.com \
  --out ./results \
  --aggressive \
  --confirm-legal "I have written permission from example-corp to perform this scan"
```

## Testing

### Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests with coverage
pytest tests/ -v --cov=wp_recon_suite --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Test sensitive files module
pytest tests/test_sensitive_files.py -v

# Test with detailed output
pytest tests/test_http.py -vv -s

# Run only failed tests
pytest --lf
```

### Code Quality Checks

```bash
# Format code
black wp_recon_suite tests

# Lint code
ruff check wp_recon_suite tests --fix

# Type checking
mypy wp_recon_suite --ignore-missing-imports
```

## CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

1. **Lints** code with black and ruff
2. **Tests** across Python 3.11 and 3.12
3. **Checks Security** with bandit and safety
4. **Builds** distribution packages
5. **Integration Tests** to verify CLI functionality

## Security Checklist

- ✅ No plaintext secrets in logs (read from environment only)
- ✅ Subprocess safety (no shell=True, all commands logged)
- ✅ HTTP timeouts and retries configured
- ✅ Input validation for URLs and file paths
- ✅ Audit trails with legal acceptance tracking
- ✅ SSL verification enabled by default
- ✅ Comprehensive error handling

## Legal & Ethical Guidelines

**IMPORTANT:** This tool must be used ethically and legally.

Before using wp-recon-suite:

1. ✅ **Obtain Written Permission** from the target owner
2. ✅ **Know Your Laws** - understand CFAA, GDPR, and local regulations
3. ✅ **Document Scope** - clearly define authorized targets
4. ✅ **Review Audit Logs** - verify all actions after scanning
5. ✅ **Secure Results** - protect sensitive scan data

The tool will:
- Print a legal warning at startup
- Require explicit confirmation for aggressive features
- Log all actions with timestamps
- Record legal acceptance in audit.log

## Troubleshooting

### Module Not Found

```bash
# Verify installation
python -c "from wp_recon_suite import LEGAL_WARNING; print('OK')"

# Check pip packages
pip list | grep wp-recon-suite
```

### ffuf Not Available

```bash
# Install ffuf
sudo apt-get install ffuf

# Verify
which ffuf
ffuf --version
```

### SSL Verification Errors

```bash
# Option 1: Disable SSL (not recommended)
# Edit config.yaml:
# http:
#   verify_ssl: false

# Option 2: Update certificates
sudo update-ca-certificates
```

### Tests Failing

```bash
# Check Python version
python3 --version  # Should be 3.11+

# Reinstall dependencies
pip install -e ".[dev]" --upgrade

# Run tests with verbose output
pytest tests/ -vv -s
```

## Development Workflow

### Creating a Feature

1. Create feature branch:
   ```bash
   git checkout -b feat/your-feature
   ```

2. Write tests first:
   ```bash
   vim tests/test_your_feature.py
   ```

3. Implement feature:
   ```bash
   vim wp_recon_suite/modules/your_feature.py
   ```

4. Run tests:
   ```bash
   pytest tests/test_your_feature.py -v
   ```

5. Format and lint:
   ```bash
   black wp_recon_suite tests
   ruff check wp_recon_suite tests --fix
   ```

6. Commit:
   ```bash
   git commit -m "feat(module): description"
   ```

7. Push and create PR:
   ```bash
   git push origin feat/your-feature
   ```

## Contributing

Contributions are welcome! Please:

1. Follow PEP8 style guide
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass
5. Submit a pull request

## Support & Resources

- 📖 [Main README](README.md)
- 🔧 [Configuration Guide](config.example.yaml)
- 📊 [Example Output](examples/sample_output.md)
- 🚀 [Usage Examples](examples/README.md)
- 🐛 [GitHub Issues](https://github.com/yourusername/wp-recon-suite/issues)

## License

MIT License - See LICENSE file for details

---

**Happy Scanning!** Remember to always act ethically and legally.
