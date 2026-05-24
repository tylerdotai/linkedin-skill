# LinkedIn API Client

Reverse-engineered LinkedIn API client in Python. Routes requests through FlareSolverr, a local proxy browser, to bypass Cloudflare anti-bot protection and interact with LinkedIn's internal Voyager API.

Provides posting, messaging, engagement, feed, search, and job search via both a Python library and a FastAPI REST server.

## Prerequisites

- **FlareSolverr** running locally on port 8191. Install from [https://github.com/FlareSolverr/FlareSolverr](https://github.com/FlareSolverr/FlareSolverr)
- Python 3.11+
- `LINKEDIN_VAULT_KEY` environment variable (any passphrase — used to derive an AES-256 encryption key)

## Quick Start

### Install

```bash
pip install linkedin-api
```

### Set your vault key

```bash
export LINKEDIN_VAULT_KEY="your-vault-passphrase"
```

### Authenticate and post

```python
from linkedin_api.core.auth import authenticate
from linkedin_api.capabilities.posting import post_text

# Authenticate — opens a browser, captures li_at and JSESSIONID cookies,
# encrypts and stores them in ~/.config/linkedin_api/vault.enc
authenticate("your-email@example.com", "your-password")

# Post text to LinkedIn
result = post_text("Hello from the LinkedIn API!")
print(result["post_url"])
```

`authenticate()` uses [patchright](https://github.com/nicholasgcotton/patchright) to open a real Chromium browser, log in interactively, and capture session cookies. The cookies are stored encrypted with AES-256-GCM. You only need to call it once — the vault persists until the session expires.

## For AI Agents

To install this package in your environment:

```bash
git clone https://github.com/tylerdotai/linkedin-skill.git
cd linkedin-skill/linkedin_api
pip install -e .
```

Then use it in your code:

```python
from linkedin_api.capabilities.posting import post_text
post_text("Your LinkedIn post text here")
```

Required env var: `LINKEDIN_VAULT_KEY` (set to any passphrase — it encrypts your session cookies).

The API client stores `li_at` and `JSESSIONID` cookies in an AES-256-GCM encrypted vault at `~/.config/linkedin_api/vault.enc`. FlareSolverr must be running on `localhost:8191`.

## Architecture

### Vault

AES-256-GCM encrypted storage for session cookies (`li_at` / `JSESSIONID`). The encryption key is derived from `LINKEDIN_VAULT_KEY` via SHA-256. Vault file lives at `~/.config/linkedin_api/vault.enc`. The `Vault` class handles save, load, and session validation against LinkedIn's `/voyager/api/me` endpoint.

### FlareSolverr

A local proxy that runs a real browser with proper cookie context. LinkedIn's API returns an HTML login page when requests lack proper browser signals — even with valid session cookies. FlareSolverr solves this by routing API calls through an actual Chrome/Chromium instance. All posting operations use `FlareLinkedInClient` which routes through FlareSolverr.

### LinkedInClient vs FlareLinkedInClient

Two HTTP clients exist for different operations:

- `LinkedInClient` — direct HTTP with retry logic. Used for messaging, engagement, feed, search, jobs, network operations. Retries 429s with backoff (30s, 60s, 120s), retries 500s once with 10s delay.
- `FlareLinkedInClient` — routes through FlareSolverr. Used for posting because LinkedIn's `/voyager/api/ugcPosts` endpoint requires browser context.

### Capabilities

| Module | Description |
|--------|-------------|
| `posting` | Text posts via FlareLinkedInClient. Image upload via `media.upload_image()`. |
| `messaging` | Send DMs, reply to thread |
| `engagement` | Like posts, comment |
| `feed` | Fetch your feed |
| `discovery` | Search people, get profile by URN or URL |
| `network` | Send/accept/reject connection requests |
| `jobs` | Search jobs, bookmark jobs |
| `analytics` | Post insights (views, likes, comments, shares) |

### FastAPI Service

REST wrapper around the capability modules. Run with:

```bash
python -m linkedin_api.service.main
```

Or install the package and run:

```bash
linkedin-api serve
```

CORS is enabled only for `localhost:3000` and `127.0.0.1:3000`.

## API Endpoints Reference

| Method | Endpoint | Description | Returns |
|--------|----------|-------------|---------|
| `GET` | `/api/health` | Health check | `{"status": "ok"}` |
| `POST` | `/api/auth/login?username=...&password=...` | Authenticate with LinkedIn credentials | `{"success": bool}` |
| `GET` | `/api/auth/status` | Check if current session is valid | `{valid, status_code, message}` |
| `POST` | `/api/post?text=...` | Create a text post | `{post_id, post_url}` |
| `POST` | `/api/post?text=...&image_path=...` | Create a post with an image | `{post_id, post_url}` |
| `POST` | `/api/comment?post_urn=...&text=...` | Comment on a post | `{comment_urn}` |
| `POST` | `/api/like?post_urn=...` | Like a post | `{success}` |
| `POST` | `/api/message?profile_urn=...&message=...` | Send a direct message | `{message_id}` |
| `POST` | `/api/connection?profile_urn=...&note=...` | Send a connection request | `{request_id}` |
| `GET` | `/api/feed?limit=20` | Fetch your LinkedIn feed | `{feed: [...]}` |
| `GET` | `/api/insights/{post_urn}` | Post analytics (views, likes, comments, shares) | `{views, likes, comments, shares}` |
| `GET` | `/api/search/people?q=...&limit=10` | Search for people | `{results: [...]}` |
| `GET` | `/api/profile/{urn_or_url}` | Get profile data by URN or URL | `{headline, about, experience, education}` |
| `GET` | `/api/jobs/search?q=...&location=...` | Search jobs | `{jobs: [...]}` |
| `POST` | `/api/jobs/{job_id}/bookmark` | Bookmark a job | `{success}` |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LINKEDIN_VAULT_KEY` | Passphrase to derive the AES-256 key for encrypted cookie storage. **Required.** |
| Vault file | `~/.config/linkedin_api/vault.enc` |

## Limitations

- **Image posting**: `media.upload_image()` works — it uploads the image and returns a `media_urn`. However, creating a post that attaches that image raises `NotImplementedError`. The upload flow is complete but the post-with-image creation step needs URN extraction from the upload response.
- **Video posting**: Not implemented.
- **Session expiry**: LinkedIn sessions expire and return 401. When this happens, re-call `authenticate()` with your credentials to capture new cookies and save them to the vault.
- **Rate limits**: LinkedIn returns 429 when rate limited. The client retries with backoff, but heavy usage may still trigger limits.

## Project Structure

```
linkedin_api/
├── src/linkedin_api/
│   ├── capabilities/
│   │   ├── analytics.py   # Post insights
│   │   ├── discovery.py   # People search, profile fetch
│   │   ├── engagement.py  # Like, comment
│   │   ├── feed.py        # My feed
│   │   ├── jobs.py        # Job search, bookmark
│   │   ├── media.py       # Image upload
│   │   ├── messaging.py   # DMs, reply to thread
│   │   ├── network.py     # Connection requests
│   │   └── posting.py    # Text posts
│   ├── core/
│   │   ├── auth.py        # patchright-based login
│   │   ├── client.py      # LinkedInClient (direct HTTP)
│   │   ├── error_handling.py  # Exception types, retry utilities
│   │   ├── errors.py      # SessionExpiredError, AuthError, MediaSizeError
│   │   ├── flaresolverr.py # FlareSolverr proxy, FlareLinkedInClient
│   │   ├── session.py     # SessionHealth (header injection, validation)
│   │   └── vault.py       # AES-256-GCM encrypted cookie storage
│   └── service/
│       └── main.py        # FastAPI REST server
├── tests/
│   ├── test_*.py          # pytest + respx mocking
├── pyproject.toml
└── README.md
```

## Dependencies

- `httpx>=0.27.0` — HTTP client with retry support
- `patchright>=1.0.0` — browser automation for authentication
- `cryptography>=42.0.0` — AES-256-GCM encryption
- `fastapi>=0.115.0` — REST API server
- `pydantic>=2.0.0` — request/response models
- `python-dotenv>=1.0.0` — env file support