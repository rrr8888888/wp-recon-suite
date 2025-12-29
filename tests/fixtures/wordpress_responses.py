"""Example test fixtures - WordPress REST API responses."""

# This file contains example responses for mocking tests

WORDPRESS_REST_ROOT = """
{
  "index": "https://example.com/index.html",
  "name": "Example",
  "description": "Just another WordPress site",
  "url": "https://example.com",
  "home": "https://example.com",
  "gmt_offset": 0,
  "timezone_string": "UTC",
  "namespaces": [
    "wp/v2",
    "wp-site-health/v1"
  ],
  "authentication": {},
  "_links": {
    "self": [{"href": "https://example.com/wp-json/"}],
    "wp:post": [{"href": "https://example.com/wp-json/wp/v2/posts"}]
  }
}
"""

WORDPRESS_USERS = """
[
  {
    "id": 1,
    "username": "admin",
    "name": "Administrator",
    "first_name": "Admin",
    "last_name": "User",
    "email": "admin@example.com",
    "url": "https://example.com",
    "description": "Site administrator",
    "link": "https://example.com/author/admin/",
    "locale": "en_US",
    "nickname": "admin",
    "slug": "admin",
    "roles": ["administrator"]
  },
  {
    "id": 2,
    "username": "editor",
    "name": "Editor",
    "first_name": "Edit",
    "last_name": "User",
    "email": "editor@example.com",
    "link": "https://example.com/author/editor/",
    "slug": "editor",
    "roles": ["editor"]
  }
]
"""

SENSITIVE_FILES_RESPONSES = {
    "/readme.html": ("200", "WordPress readme content", "text/html"),
    "/license.txt": ("200", "GPL-2.0+ license", "text/plain"),
    "/wp-config.php": ("404", "", ""),
    "/wp-config.php.bak": ("200", "<?php // backup config", "text/plain"),
    "/.git/config": ("404", "", ""),
    "/debug.log": ("403", "", ""),
}

FFUF_SAMPLE_OUTPUT = """
{
  "commandline": "ffuf -u https://example.com/FUZZ -w wordlist.txt",
  "started": "2025-12-29T21:00:00Z",
  "duration": 12345,
  "results": [
    {"path": "/wp-admin/", "status": 301, "length": 0, "words": 0, "lines": 0},
    {"path": "/wp-content/", "status": 301, "length": 0, "words": 0, "lines": 0},
    {"path": "/wp-includes/", "status": 301, "length": 0, "words": 0, "lines": 0},
    {"path": "/xmlrpc.php", "status": 200, "length": 42, "words": 0, "lines": 0},
    {"path": "/index.php", "status": 200, "length": 5000, "words": 100, "lines": 150}
  ]
}
"""

WPSCAN_SAMPLE_OUTPUT = """
_______________________________________________________________
         __          _______   _____
         \\ \\        / /  __ \\ / ____|
          \\ \\  /\\  / /| |__) | (___
           \\ \\/  \\/ / |  ___/ \\___ \\
            \\  /\\  /  | |     ____) |
             \\/  \\/   |_|    |_____/

         WordPress Security Scanner by the WPScan Team
                     Version X.X.X
          Sponsored by Automattic - https://automattic.com/
         @_WPScan, @ethicalhack3r, @erwan_lr, et al.

_______________________________________________________________

[+] URL: https://example.com/ [IP: 192.168.1.1]
[+] Started: 2025-12-29 21:00:00 UTC

[+] Interesting Finding(s):

[+] WordPress version 6.4.1 identified (Insecure, released 2023-11-28).
[!] Title: WordPress <= 6.4.1 - Unauthenticated Arbitrary Options Update

[+] WordPress theme in use: twentytwentythree
[!] The version could not be determined.

[+] Enumerating All Plugins (via Passive Methods)
[+] Plugins found:
[+] wp-super-cache
[!] 1 vulnerability identified

[+] Enumerating Users (via Passive and aggressive Methods)
[+] User(s) Identified:
[+] admin | Found by: Author Posts - Author Num Enum (http://example.com/wp-json/wp/v2/users)
[+] editor | Found by: Author Posts - Author Num Enum (http://example.com/?author=2)

[+] Finished: 2025-12-29 21:00:30 UTC
[+] Requests Done: 100
[+] Cached Requests: 0
[+] Data Sent: 50 KB
[+] Data Received: 2 MB
[+] Execution time: 0m 30s
"""
