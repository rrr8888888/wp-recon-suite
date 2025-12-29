#!/bin/bash
# Setup script for wp-recon-suite development environment

set -e

echo "WordPress Recon Suite - Development Setup"
echo "=========================================="
echo ""

# Check Python version
echo "[*] Checking Python version..."
python_version=$(python3 --version | awk '{print $2}')
echo "    Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
else
    echo "[*] Virtual environment already exists, activating..."
    source venv/bin/activate
fi

# Upgrade pip
echo "[*] Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install package in development mode
echo "[*] Installing wp-recon-suite in development mode..."
pip install -e ".[dev,pdf]"

# Run tests
echo "[*] Running tests..."
pytest tests/ -v

# Format code
echo "[*] Formatting code with black..."
black wp_recon_suite tests

# Lint code
echo "[*] Linting with ruff..."
ruff check wp_recon_suite tests --fix || true

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate the environment: source venv/bin/activate"
echo "  2. Run the CLI: wp-recon-suite --help"
echo "  3. Run tests: pytest"
echo "  4. Run a scan: wp-recon-suite scan --target https://example.com --out ./results"
echo ""
