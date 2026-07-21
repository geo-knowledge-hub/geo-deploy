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
├── pytest.ini             # Tells pytest where tests are and sets Python path
│
├── conftest.py            # Entry point: loads .env, registers CLI options, SSL bypass
├── fixtures.py            # All @pytest.fixture definitions (setup/teardown)
├── factories.py           # All payload builders (data sent to the API)
│
├── client/                # Page Object Model — one class per API domain
│   ├── base.py            # Shared HTTP session and helper methods
│   ├── resources.py       # All /api/records endpoints
│   ├── packages.py        # All /api/packages endpoints
│   ├── communities.py     # All /api/communities endpoints
│   ├── doi.py             # All DOI reservation endpoints
│   └── search.py          # /api/search with spatial support
│
└── tests/
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

### `conftest.py`
The entry point that pytest reads first before running any test.
It does three things:
1. Loads your `.env` file so your token and URL are available everywhere
2. Registers the CLI options (`--base-url`, `--api-token`, `--no-verify-tls`)
3. Patches SSL verification so self-signed certificates do not cause errors

**You should never need to edit this file.**

### `fixtures.py`
Contains all pytest fixtures — functions that set up resources before a test
and clean them up after. Examples:
- `http` — creates an authenticated HTTP session shared across all tests
- `package_draft` — creates a fresh package draft before a test, deletes it after
- `published_package` — creates and publishes one package per test run (reused)
- `community` — creates a community before a test, deletes it after

**Edit this file when:** you need a new shared resource (e.g. a new record type fixture).

### `factories.py`
Contains pure data builder functions that return the JSON payloads sent to the API.
Examples:
- `make_resource_payload()` — builds a minimal valid Knowledge Resource body
- `make_package_payload()` — builds a minimal valid Knowledge Package body
- `make_community_payload()` — builds a minimal valid Community body

These functions have no side effects — they just build and return a dictionary.

**Edit this file when:** the API schema changes (e.g. a new required field is added).

### `client/`
One class per API domain. Tests call methods on these classes instead of
building URLs directly. This means if an endpoint URL ever changes, you
update it in one place only.

- `base.py` — shared `_get`, `_post`, `_put`, `_delete` methods used by all clients
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

### `pytest.ini`
Tells pytest two things:
1. Where to find the tests (`testpaths = tests`)
2. That the project root should be on Python's import path (`pythonpath = .`)
   so that `conftest.py` can import from `fixtures.py` and `factories.py`

**You should never need to edit this file.**

---

## First-Time Setup

### Step 1 — Install uv (if not already installed)
```powershell
pip install uv
```

### Step 2 — Install dependencies
```powershell
uv add pytest requests python-dotenv pytest-html
```

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

### Run everything
```powershell
pytest tests/ -v
```

### Run only API tests (requires token)
```powershell
pytest tests/api/ -v
```

### Run only UI tests (no token needed for most)
```powershell
pytest tests/ui/ -v
```

### Run a specific file
```powershell
pytest tests/api/test_packages.py -v
pytest tests/api/test_doi.py -v
pytest tests/api/test_search.py -v
```

### Run a specific single test
```powershell
pytest tests/api/test_packages.py::TestPackageDraft::test_create_draft -v
```

### Generate an HTML report
```powershell
pytest tests/ -v --html=report.html --self-contained-html
```

### Override `.env` values for a single run
```powershell
pytest tests/ -v --base-url "https://other-instance.org" --api-token "other_token"
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



