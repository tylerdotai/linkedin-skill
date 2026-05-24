# LinkedIn API Client

Reverse-engineered LinkedIn API client in Python. Posts, messages, engagement, feed, search, and jobs via a Python library or REST API.

Use it directly in Python or serve it as a FastAPI backend.

[![OpenClaw](https://img.shields.io/badge/Powered%20by-OpenClaw-ff6b00?style=for-the-badge)](https://openclaw.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE.txt)

## Install

```bash
pip install linkedin-api
```

Or from source:

```bash
git clone https://github.com/tylerdotai/linkedin-skill.git
cd linkedin-skill/linkedin_api
pip install -e .
```

## Quick Start

Set your vault key:

```bash
export LINKEDIN_VAULT_KEY="your-vault-passphrase"
```

Authenticate and post:

```python
from linkedin_api.core.auth import authenticate
from linkedin_api.capabilities.posting import post_text

authenticate("you@example.com", "your-password")
result = post_text("Hello from the LinkedIn API!")
print(result["post_url"])
```

`authenticate()` uses patchright to open a real Chromium browser, log in interactively, and capture session cookies. The cookies are stored encrypted with AES-256-GCM in `~/.config/linkedin_api/vault.enc`. You only need to call it once per session.

## For AI Agents

To install:

```bash
git clone https://github.com/tylerdotai/linkedin-skill.git
cd linkedin-skill/linkedin_api
pip install -e .
```

Required env var: `LINKEDIN_VAULT_KEY` (any passphrase — encrypts your session).

FlareSolverr must be running on `localhost:8191`.

Usage:

```python
from linkedin_api.capabilities.posting import post_text
post_text("Your post here")
```

## Features

- Post text (with optional image upload)
- Send direct messages
- Like and comment on posts
- Fetch your feed
- Search people and profiles
- Search and bookmark jobs
- Connection requests
- Post analytics (views, likes, comments, shares)

## Architecture Highlights

- FlareSolverr proxy browser (bypasses Cloudflare)
- AES-256-GCM encrypted vault for session cookies
- FastAPI REST server available
- Python 3.11+, no official LinkedIn API needed

## Documentation

See [linkedin_api/README.md](linkedin_api/README.md) for:

- Full API endpoints reference
- Authentication and Vault details
- Architecture deep-dive
- Current limitations
- Project structure

## Related

- [linkedin_api/](linkedin_api/) — Python package source
- [SKILL.md](SKILL.md) — OpenClaw agent skill (separate workflow)
- [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) — Cloudflare bypass proxy

## License

MIT
