# GEO Knowledge Hub — API Test Suite

A professional pytest test suite for the GEO Knowledge Hub (InvenioRDM-based)
API, built using the **Page Object Model (POM)** pattern.

---

## What This Suite Tests

Every endpoint from the official GEO Knowledge Hub API documentation:

| Area | Endpoints |
|---|---|
| Knowledge Package search & discovery | `GET /api/packages`, `GET /api/packages/{id}`, `GET /api/user/packages` |
| Knowledge Package drafts | `POST`, `GET`, `PUT`, `DELETE /api/packages/{id}/draft` |
| Knowledge Package files | Init, upload, commit, list, delete |
| Knowledge Package publish | `POST /api/packages/{id}/draft/actions/publish` |
| Knowledge Package versions | List, create new, get latest, import resources |
| Resource association | Associate, dissociate, add to draft, remove from draft |
| Knowledge Resource search | `GET /api/records`, `GET /api/records/{id}`, `GET /api/user/records` |
| Knowledge Resource drafts | `POST`, `GET`, `PUT`, `DELETE /api/records/{id}/draft` |
| Knowledge Resource files | Init, upload, commit, list, delete |
| Knowledge Resource publish & versions | Publish, list versions, create new version |
| Digital Object Identifiers (DOI) | Reserve, discard, publish with DOI, external DOI |
| Communities | Search, create, update, delete, members |
| Unified search | Full-text, spatial/bounding box, resource type filter, combined |
| Homepage & UI | Homepage, search page, robots.txt, static assets |
| Authentication | Valid token, invalid token, missing token, user profile |

---

## Project Structure

```
geo-deploy/
│
├── .env                   # Your private settings (never commit this)
├── .env.example           # Template showing what goes in .env
├── .gitignore             # Prevents .env from being committed to Git
├── .python-version        # Python version uv provisions (3.12)
├── pyproject.toml         # Project metadata & dependencies
├── uv.lock                # Exact pinned dependency versions — run `uv sync`
│                          # (.venv/ is created here by uv; not committed)
│
├── geodeploy/             # Page Object Model — one class per API domain
│   ├── base.py            # Shared HTTP session, base_path/_path helpers
│   ├── resources.py       # All /api/records endpoints
│   ├── packages.py        # All /api/packages endpoints
│   ├── communities.py     # All /api/communities endpoints
│   ├── doi.py             # All DOI reservation endpoints
│   └── search.py          # /api/search with spatial support
│
├── docs/                  # Contributor notes (not needed to just run tests)
│   ├── metadata.md        # How to add a required metadata field
│   └── tests.md           # How to add a new test / endpoint
│
└── tests/
    ├── conftest.py        # Entry point: loads .env, registers CLI options, SSL bypass
    ├── fixtures.py        # All @pytest.fixture definitions (setup/teardown)
    ├── factories.py       # All payload builders (data sent to the API)
    │
    ├── ui/                # Tests that do not require authentication
    │   ├── test_homepage.py
    │   └── test_login.py
    └── api/               # Tests that require a valid API token
        ├── test_resources.py
        ├── test_packages.py
        ├── test_communities.py
        ├── test_drafts.py
        ├── test_doi.py
        └── test_search.py
```

---

## What Each File Does

### `tests/conftest.py`
The entry point that pytest reads first before running any test.
It does three things:
1. Loads your `.env` file so your token and URL are available everywhere
2. Registers the CLI options (`--base-url`, `--api-token`, `--no-verify-tls`)
3. Patches SSL verification so self-signed certificates do not cause errors

**You should never need to edit this file.**

### `tests/fixtures.py`
Contains all pytest fixtures — functions that set up resources before a test
and clean them up after. Examples:
- `http` — creates an authenticated HTTP session shared across all tests
- `package_draft` — creates a fresh package draft before a test, deletes it after
- `published_package` — creates and publishes one package per test run (reused)
- `community` — creates a community before a test, deletes it after

**Edit this file when:** you need a new shared resource (e.g. a new record type fixture).

### `tests/factories.py`
Contains pure data builder functions that return the JSON payloads sent to the API.
Examples:
- `make_resource_payload()` — builds a minimal valid Knowledge Resource body
- `make_package_payload()` — builds a minimal valid Knowledge Package body
- `make_community_payload()` — builds a minimal valid Community body

These functions have no side effects — they just build and return a dictionary.

**Edit this file when:** the API schema changes (e.g. a new required field is added).

### `geodeploy/`
One class per API domain. Tests call methods on these classes instead of
building URLs directly. This means if an endpoint URL ever changes, you
update it in one place only.

- `base.py` — shared `_get`/`_post`/`_put`/`_delete` methods, plus `base_path` /
  `_resource_path()` helpers so URL segments never need to be hand-typed
- `resources.py` — `ResourcesClient`: all Knowledge Resource API calls
- `packages.py` — `PackagesClient`: all Knowledge Package API calls
- `communities.py` — `CommunitiesClient`: all Community API calls
- `doi.py` — `DOIClient`: reserve, discard, and publish DOIs
- `search.py` — `SearchClient`: full-text, spatial bounding box, and filtered search

**Edit these files when:** an API endpoint URL changes.

### `tests/`
Contains the actual test functions. Tests only contain assertions — they never
build URLs or construct payloads directly. All API calls go through the client
classes, and all data comes from the factories.

**Edit these files when:** you want to add, remove, or change a test.

### `docs/`
Short contributor notes, not required just to run the suite:
- [`docs/metadata.md`](docs/metadata.md) — how to add a new required metadata field
- [`docs/tests.md`](docs/tests.md) — how to add a new test or a new client method

### Where's `pytest.ini`?
There isn't one. Pytest finds `tests/` because it's passed explicitly on the
command line (`pytest tests/ -v`), and imports like `from geodeploy.packages
import PackagesClient` resolve because every test package (`tests/`,
`tests/api/`, `tests/ui/`) has an `__init__.py`, which makes pytest add the
project root to `sys.path` automatically. No config file needed.

---

## First-Time Setup

This project is managed with **[uv](https://docs.astral.sh/uv/)**, not plain
`pip`. Dependencies are pinned in `uv.lock`, and the required Python version
(3.12) is pinned in `.python-version` — uv reads both automatically.

### Step 1 — Install uv (if not already installed)
```powershell
pip install uv
```
Or use the standalone installer (no existing Python/pip required):
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### Step 2 — Install dependencies
This project already ships a `pyproject.toml` and `uv.lock`, so there's
nothing to add — just sync the environment they describe:
```powershell
uv sync
```
This creates a `.venv/` folder in `geo-deploy/` with exactly the pinned
versions from `uv.lock` (pytest, requests, python-dotenv, urllib3, plus
ruff for linting). You don't need to activate it — prefix commands with
`uv run` instead (see **Running Tests** below).

Only use `uv add <package>` later if you need to introduce a *new*
dependency — it updates both `pyproject.toml` and `uv.lock` for you.

### Step 3 — Get your API token
1. Open your GKH instance in a browser
2. Click your avatar (top right) → **Settings** → **Applications**
3. Under **Personal access tokens** → click **New token**
4. Give it a name (e.g. `pytest`)
5. Select **all available scopes**
6. Click **Create** and copy the token immediately (shown only once)

### Step 4 — Create your `.env` file
Create a file named `.env` in the `geo-deploy/` folder with this content:

```
GEO_API_TOKEN=paste_your_token_here
GEO_BASE_URL=https://your_instance_url
GEO_NO_VERIFY_TLS=true
```

What each variable does:
- `GEO_API_TOKEN` — your personal API token for authentication. Every API
  request is sent with this token in the Authorization header. Without it,
  the server rejects all write operations with 401 or 403.
- `GEO_BASE_URL` — the root URL of your GEO Knowledge Hub instance. All API
  endpoints are built on top of this (e.g. `GEO_BASE_URL/api/records`).
- `GEO_NO_VERIFY_TLS` — set to `true` if your instance uses a self-signed
  TLS certificate (common for local or Kubernetes deployments). When `true`,
  the suite skips certificate verification so HTTPS connections succeed.


---

## Running Tests

Always run from inside the `geo-deploy/` folder:

```powershell
cd geo-deploy
```

Every command below is prefixed with `uv run` — that runs it inside the
project's `.venv/` without you needing to activate it manually. (If you'd
rather activate the venv yourself, `.venv\Scripts\activate` then drop the
`uv run` prefix from any command.)

### Run everything
```powershell
uv run pytest tests/ -v
```

### Run only API tests (requires token)
```powershell
uv run pytest tests/api/ -v
```

### Run only UI tests (no token needed for most)
```powershell
uv run pytest tests/ui/ -v
```

### Run a specific file
```powershell
uv run pytest tests/api/test_packages.py -v
uv run pytest tests/api/test_doi.py -v
uv run pytest tests/api/test_search.py -v
```

### Run a specific single test
```powershell
uv run pytest tests/api/test_packages.py::TestPackageDraft::test_create_draft -v
```

### Override `.env` values for a single run
```powershell
uv run pytest tests/ -v --base-url "https://other-instance.org" --api-token "other_token"
```

CLI flags always take priority over `.env` values.

---



## Environment Variables Reference

| Variable | Required | Example | Description |
|---|---|---|---|
| `GEO_API_TOKEN` | Yes | `your_gkh_api_token` | Personal API token from GKH Settings → Applications |
| `GEO_BASE_URL` | Yes | `https://your_gkh_instance_url` | Root URL of your GKH instance, no trailing slash |
| `GEO_NO_VERIFY_TLS` | No | `true` | Skip TLS verification for self-signed certificates |

---



