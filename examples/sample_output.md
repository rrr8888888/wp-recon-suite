# Sample JSON output from wp-recon-suite scan

```json
{
  "target": "https://example.com",
  "timestamp": "2025-12-29T21:00:00Z",
  "modules": {
    "sensitive_files": [
      {
        "path": "/readme.html",
        "http_code": 200,
        "length": 1234,
        "note": "exposed",
        "content_type": "text/html",
        "headers": {
          "content-type": "text/html; charset=UTF-8",
          "content-length": "1234"
        }
      },
      {
        "path": "/license.txt",
        "http_code": 200,
        "length": 567,
        "note": "exposed",
        "content_type": "text/plain",
        "headers": {}
      },
      {
        "path": "/wp-config.php",
        "http_code": 404,
        "length": 0,
        "note": "not found",
        "content_type": "",
        "headers": {}
      },
      {
        "path": "/.git/config",
        "http_code": 404,
        "length": 0,
        "note": "not found",
        "content_type": "",
        "headers": {}
      }
    ],
    "rest_api": {
      "root_found": true,
      "root_url": "https://example.com/wp-json/",
      "users_exposed": true,
      "users_count": 2,
      "users": [
        {
          "id": 1,
          "slug": "admin",
          "name": "Administrator",
          "link": "https://example.com/author/admin/"
        },
        {
          "id": 2,
          "slug": "editor",
          "name": "Editor",
          "link": "https://example.com/author/editor/"
        }
      ]
    },
    "xmlrpc": {
      "found": true,
      "pingback_enabled": true,
      "http_code": 200
    },
    "author_enum": [
      {
        "id": 1,
        "redirect": "/author/admin/",
        "username": "admin",
        "http_code": 301,
        "note": "author found (redirect)"
      },
      {
        "id": 2,
        "redirect": "/author/editor/",
        "username": "editor",
        "http_code": 301,
        "note": "author found (redirect)"
      }
    ],
    "ffuf": {
      "invoked": true,
      "command": [
        "ffuf",
        "-u",
        "https://example.com/FUZZ",
        "-w",
        "/usr/share/seclists/Discovery/Web-Content/CMS/wordpress.txt",
        "-e",
        "php,txt,html,zip",
        "-t",
        "40",
        "-timeout",
        "10"
      ],
      "wordlist": "/usr/share/seclists/Discovery/Web-Content/CMS/wordpress.txt",
      "top_results": [
        {
          "path": "/wp-admin/",
          "code": 301,
          "size": 0
        },
        {
          "path": "/wp-content/",
          "code": 301,
          "size": 0
        },
        {
          "path": "/wp-includes/",
          "code": 301,
          "size": 0
        },
        {
          "path": "/xmlrpc.php",
          "code": 200,
          "size": 42
        },
        {
          "path": "/index.php",
          "code": 200,
          "size": 5000
        }
      ],
      "total_results": 15,
      "error": null
    },
    "wpscan": {
      "invoked": false,
      "command": null,
      "output_file": null,
      "summary": null,
      "error": "wpscan not installed"
    }
  },
  "legal_acceptance": {
    "safe_only": true,
    "aggressive": false,
    "confirmation_text": null
  }
}
```

## Summary

This example shows the output of a **safe-only** WordPress reconnaissance scan on `https://example.com`.

### Key Findings:

1. **Sensitive Files**: 2 files exposed (readme.html, license.txt)
2. **REST API**: Accessible, 2 users enumerated (admin, editor)
3. **XML-RPC**: Enabled with pingback support
4. **Author Enumeration**: Found 2 authors via /?author=N redirects
5. **Directory Fuzzing**: 15 results found via ffuf, top 5 shown
6. **WPScan**: Not run (binary not installed)

### Legal Status:

- Safe-only mode: ✓ Enabled
- Aggressive mode: ✗ Disabled
- No explicit permission required for this scan
