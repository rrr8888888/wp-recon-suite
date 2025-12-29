# QUICK START REFERENCE

## Installation (< 2 minutes)

```bash
cd wp-recon-suite
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## First Scan (< 5 minutes)

```bash
# Safe scan on target
wp-recon-suite scan --target https://example.com --out results

# View results
cat results/summary.txt
cat results/*_results.json | jq .
```

## Key Commands

```bash
# Help
wp-recon-suite --help
wp-recon-suite scan --help

# Safe scan (default)
wp-recon-suite scan --target HTTPS://DOMAIN --out ./results

# Add ffuf wordlist
wp-recon-suite scan --target HTTPS://DOMAIN --out ./results \
  --ffuf-wordlist /path/to/wordlist.txt

# Generate HTML report
wp-recon-suite scan --target HTTPS://DOMAIN --out ./results --html

# With WPScan
WPSCAN_API_TOKEN=TOKEN wp-recon-suite scan --target HTTPS://DOMAIN --out ./results

# Aggressive mode (requires permission)
wp-recon-suite scan --target HTTPS://DOMAIN --out ./results \
  --aggressive --confirm-legal "I have written permission"

# View results
cat results/summary.txt
jq . results/*_results.json
tail -f results/audit.log
```

## Project Layout

```
wp-recon-suite/
├── wp_recon_suite/         # Main package
├── tests/                  # Test suite (pytest)
├── examples/               # Example configs and outputs
├── .github/workflows/      # CI/CD (GitHub Actions)
├── pyproject.toml          # Project config
├── README.md               # Main docs
├── INSTALL.md              # Installation guide
└── LICENSE                 # MIT License
```

## Core Features

| Feature | Safe? | Enabled? | Notes |
|---------|-------|----------|-------|
| Sensitive files | ✅ | Default | GET requests only |
| REST API enum | ✅ | Default | /wp-json/ enumeration |
| XML-RPC check | ✅ | Default | HEAD requests |
| Author enum | ✅ | Default | /?author=N parameter |
| Directory fuzz | ✅ | Optional | ffuf integration |
| Vuln scan | ✅ | Optional | WPScan integration |
| Aggressive | ❌ | Disabled | Requires explicit opt-in |

## Output Files

After scan, in `results/` directory:

- `YYYYMMDD_HHMMSS_results.json` - Full JSON results
- `summary.txt` - Human-readable summary
- `report.html` - HTML report (if --html)
- `audit.log` - Audit trail with timestamps
- `ffuf.json` - ffuf results (if run)
- `wpscan_output.txt` - WPScan results (if run)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=wp_recon_suite

# Test specific module
pytest tests/test_sensitive_files.py -v

# Code quality
black wp_recon_suite tests
ruff check wp_recon_suite tests --fix
mypy wp_recon_suite
```

## Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -e ".[dev]"` |
| ffuf not found | `sudo apt-get install ffuf` |
| WPScan not found | `gem install wpscan` |
| SSL errors | Check certificates or set `verify_ssl: false` |
| Timeout | Increase with `--timeout 30` |

## Environment Variables

```bash
# WPScan API token
export WPSCAN_API_TOKEN="your-api-key"

# Python path (if needed)
export PYTHONPATH=/path/to/wp-recon-suite:$PYTHONPATH

# Enable debug logging
export LOGLEVEL=DEBUG
```

## Legal Reminders

- ⚠️ Always get written permission before scanning
- ⚠️ Know your local laws (CFAA, GDPR, etc.)
- ⚠️ Document all authorized targets
- ⚠️ Secure and protect scan results
- ⚠️ Review audit.log for legal compliance

## Example Workflow

```bash
# 1. Get authorization (documented in writing!)
# 2. Create config.yaml with target specifics
# 3. Run scan
wp-recon-suite scan --target HTTPS://TARGET --config config.yaml --out results

# 4. Review findings
cat results/summary.txt
cat results/audit.log

# 5. Generate report
# (HTML already generated with --html flag)

# 6. Secure results
chmod 600 results/*
tar czf results-backup.tar.gz results/

# 7. Clean up if needed
rm -rf results/
```

## More Information

- Full documentation: [README.md](README.md)
- Installation guide: [INSTALL.md](INSTALL.md)
- Examples: [examples/README.md](examples/README.md)
- Configuration: [config.example.yaml](config.example.yaml)

---

**Tip:** Always test on your own infrastructure first before scanning client targets!
