# WordPress Recon Suite - Examples

## Installation

```bash
git clone https://github.com/yourusername/wp-recon-suite.git
cd wp-recon-suite

# Using setup script
bash setup.sh

# Or manual installation
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev,pdf]"
```

## Basic Usage

### Safe Reconnaissance (Default)

```bash
# Quick safe scan with default settings
wp-recon-suite scan --target https://example.com --out ./results

# With custom output formats
wp-recon-suite scan --target https://example.com --out ./results --json --html

# With timeout adjustment
wp-recon-suite scan --target https://example.com --out ./results --timeout 20

# With increased concurrency
wp-recon-suite scan --target https://example.com --out ./results --concurrency 20
```

### Advanced Reconnaissance

```bash
# Use custom configuration file
wp-recon-suite scan --target https://example.com --out ./results --config myconfig.yaml

# Run with ffuf directory fuzzing
wp-recon-suite scan \
  --target https://example.com \
  --out ./results \
  --ffuf-wordlist /usr/share/seclists/Discovery/Web-Content/CMS/wordpress.txt

# Enable WPScan with API token
WPSCAN_API_TOKEN="your-token" wp-recon-suite scan \
  --target https://example.com \
  --out ./results
```

### Aggressive Scanning (With Legal Confirmation)

```bash
# Requires explicit legal acceptance
wp-recon-suite scan \
  --target https://example.com \
  --out ./results \
  --aggressive \
  --confirm-legal "I have written permission from example-corp to perform this scan"
```

## Configuration Files

See `config.example.yaml` for all available options. Create a `config.yaml`:

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
    - /wp-config.php.bak

ffuf:
  enabled: true
  wordlist: /usr/share/seclists/Discovery/Web-Content/CMS/wordpress.txt
  extensions: [php, txt, html, zip, bak]
  threads: 50

output:
  json: true
  html: true
  pretty_print: true
```

Then run:

```bash
wp-recon-suite scan --target https://example.com --out ./results --config config.yaml
```

## Understanding Results

### Output Files

After a scan, the `results/` directory contains:

- **`YYYYMMDD_HHMMSS_results.json`** - Complete scan results in JSON format
- **`summary.txt`** - Human-readable summary
- **`report.html`** - HTML report (if `--html` enabled)
- **`audit.log`** - Detailed audit log with all actions and timestamps
- **`ffuf.json`** - ffuf output (if ffuf was run)
- **`wpscan_output.txt`** - WPScan output (if wpscan was run)

### Reading JSON Results

```bash
# Pretty print the results
cat results/*_results.json | jq .

# Get just the sensitive files
cat results/*_results.json | jq '.modules.sensitive_files'

# Get enumerated users
cat results/*_results.json | jq '.modules.rest_api.users'

# Get found authors
cat results/*_results.json | jq '.modules.author_enum'

# Check audit log
tail -f results/audit.log
```

## Security Best Practices

### Before Scanning

1. **Get Written Permission**: Always obtain written authorization from the target owner
2. **Document Scope**: Clearly define what targets and actions are authorized
3. **Know Your Laws**: Understand the legal implications in your jurisdiction
4. **Inform Stakeholders**: Let relevant teams know about the scan schedule

### During Scanning

1. **Monitor Progress**: Watch the scan output for issues
2. **Respect Rate Limits**: Use `--concurrency` to limit impact
3. **Review Findings**: Check results as they come in
4. **Stop if Needed**: Interrupt with Ctrl+C if issues arise

### After Scanning

1. **Secure Results**: Store reports in a secure location
2. **Review Findings**: Analyze and verify all results
3. **Verify Legal Acceptance**: Check audit.log for confirmation records
4. **Delete Sensitive Data**: Remove reports once processed

## Troubleshooting

### "ffuf not installed"
```bash
# Install ffuf
sudo apt-get install ffuf

# Or build from source
go install -v github.com/ffuf/ffuf@latest
```

### "wpscan not installed"
```bash
# Install wpscan with Ruby
gem install wpscan

# Or using apt
sudo apt-get install wpscan
```

### SSL Certificate Errors
```bash
# Disable SSL verification (NOT recommended for production!)
# Edit config.yaml:
http:
  verify_ssl: false
```

### Timeout Issues
```bash
# Increase timeout
wp-recon-suite scan --target https://example.com --timeout 30

# Or in config.yaml
http:
  timeout: 30
```

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_sensitive_files.py -v

# Run with coverage
pytest --cov=wp_recon_suite --cov-report=html
```

### Code Quality

```bash
# Format code
black wp_recon_suite tests

# Lint code
ruff check wp_recon_suite tests --fix

# Type checking
mypy wp_recon_suite
```

## Legal & Ethical Considerations

⚠️ **Important**: This tool is for authorized security testing only.

- Always obtain written permission before scanning
- Respect the target organization's security policies
- Follow your country's laws regarding computer access
- Document all scans in audit logs for compliance
- Never scan targets you don't own or have permission for

## Getting Help

- 📖 Read the [README.md](../README.md)
- 🐛 Check [GitHub Issues](https://github.com/yourusername/wp-recon-suite/issues)
- 💬 Join [GitHub Discussions](https://github.com/yourusername/wp-recon-suite/discussions)
- 📧 Email support: [your-email]

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Submit a pull request
5. Ensure all CI checks pass

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.
