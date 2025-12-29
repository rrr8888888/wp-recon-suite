# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-29

### Added
- Initial release of wp-recon-suite
- Safe-by-default WordPress reconnaissance scanning
- Sensitive file discovery module
- REST API and XML-RPC detection
- Author enumeration via query parameters
- Optional ffuf integration for directory fuzzing
- Optional WPScan integration for vulnerability scanning
- Comprehensive audit logging with legal acceptance tracking
- JSON, HTML, and text output formatters
- YAML configuration file support
- HTTP client with retry logic and sensible timeouts
- Full test suite with pytest fixtures
- GitHub Actions CI/CD workflow
- Comprehensive documentation and examples
- Legal warning banners and ethical guidelines

### Security
- Disabled aggressive scanning by default
- No plaintext secrets in logs or output
- Safe subprocess execution with masked secrets
- Input validation for URLs and file paths
- Optional SSL verification (enabled by default)
