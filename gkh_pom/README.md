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
gkh_pom/
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
Create a file named `.env` in the `gkh_pom/` folder with this content:

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

### Step 5 — Create `pytest.ini`
Create a file named `pytest.ini` in the `gkh_pom/` folder:

```ini
[pytest]
testpaths = tests
pythonpath = .
```

What each line does:
- `testpaths = tests` — tells pytest to look for tests inside the `tests/`
  folder only. Without this, pytest searches everywhere and may pick up
  unintended files.
- `pythonpath = .` — adds the `gkh_pom/` folder to Python's import path.
  This allows `conftest.py` to import `fixtures.py` and `factories.py`
  regardless of which subfolder pytest is currently collecting from.

### Step 6 — Create `.gitignore`
Create a file named `.gitignore` in the `gkh_pom/` folder:

```
# Never commit secrets
.env

# pytest and Python cache
.pytest_cache/
__pycache__/
*.pyc

# HTML reports
report.html
```

The `.env` file contains your API token which is a secret. This file ensures
it is never accidentally committed to Git and shared with others.

### Step 7 — Verify the structure
Your `gkh_pom/` folder should look like this:

```
gkh_pom/
├── .env            ← created in Step 4
├── .gitignore      ← created in Step 6
├── pytest.ini      ← created in Step 5
├── conftest.py
├── fixtures.py
├── factories.py
├── client/
│   ├── __init__.py
│   ├── base.py
│   ├── communities.py
│   ├── doi.py
│   ├── packages.py
│   ├── resources.py
│   └── search.py
└── tests/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── test_communities.py
    │   ├── test_doi.py
    │   ├── test_drafts.py
    │   ├── test_packages.py
    │   ├── test_resources.py
    │   └── test_search.py
    └── ui/
        ├── __init__.py
        ├── test_homepage.py
        └── test_login.py
```

---

## Running Tests

Always run from inside the `gkh_pom/` folder:

```powershell
cd gkh_pom
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

## Understanding the Output

```
tests/api/test_packages.py::TestPackageDraft::test_create_draft PASSED   [  5%]
tests/api/test_packages.py::TestPackageDraft::test_get_draft PASSED       [  6%]
tests/api/test_packages.py::TestPackageDraft::test_update_draft FAILED    [  7%]
```

| Symbol | Meaning |
|---|---|
| `PASSED` | Test ran and all assertions were correct |
| `FAILED` | Test ran but at least one assertion was wrong |
| `ERROR` | Test could not run — usually a fixture setup problem |
| `SKIPPED` | Test was intentionally skipped (e.g. DOI provider not configured) |
| `[ 7%]` | Progress indicator — how far through the total test run you are |

---

## Adding a New Test

1. Open the relevant file in `tests/api/` or `tests/ui/`
2. Inject the client fixture you need
3. Call client methods — never write URLs directly in test functions
4. Assert on the response

```python
def test_my_new_test(
    self,
    packages: PackagesClient,
    package_draft: dict,
) -> None:
    # Call a client method — not a raw URL
    r = packages.get_draft(package_draft["id"])

    # Assert on the result
    assert_ok(r, 200)
    assert r.json()["metadata"]["title"] is not None
```

---

## Adding a New API Endpoint

1. Open the relevant file in `client/`
2. Add a method using `self._get`, `self._post`, `self._put`, or `self._delete`
3. Call it from your test

```python
# In client/packages.py
def my_new_endpoint(self, package_id: str) -> Response:
    """GET /api/packages/{id}/something-new"""
    return self._get(f"/api/packages/{package_id}/something-new")
```

No URLs ever appear in test files.

---

## Changing a Required Metadata Field

If the API starts requiring a new field (e.g. `language`), add it to `factories.py`:

```python
def make_resource_payload(title=None):
    return {
        "metadata": {
            "title": title or f"pytest-resource-{_uid()}",
            "language": "eng",   # add new required field here
            ...
        }
    }
```

One change in `factories.py` applies to every test that creates a resource.

---

## Why Published Records Accumulate on the Server

InvenioRDM does not allow hard-deleting published records via the public API.
Only draft records can be deleted. This means every time a test publishes a
record, it remains on the server permanently.

To keep accumulation low:
- The `published_resource` and `published_package` fixtures are session-scoped,
  meaning they create **one** published record per test run and reuse it across
  all tests that need a published record
- Tests that specifically test the publish action create one additional record each
- Per full test run, approximately **5 to 8** published records are created

These records are named with the `pytest-` prefix. They can be identified and
deleted manually from the GKH admin interface if needed.

---

## Environment Variables Reference

| Variable | Required | Example | Description |
|---|---|---|---|
| `GEO_API_TOKEN` | Yes | `your_gkh_api_token` | Personal API token from GKH Settings → Applications |
| `GEO_BASE_URL` | Yes | `https://your_gkh_instance_url` | Root URL of your GKH instance, no trailing slash |
| `GEO_NO_VERIFY_TLS` | No | `true` | Skip TLS verification for self-signed certificates |

---

## Spatial Search Bounding Box Reference

The search client supports spatial filtering using a bounding box defined by
four coordinates — west, south, east, north — in decimal degrees (WGS84).

| Location | West | South | East | North |
|---|---|---|---|---|
| Ghana | -3.26 | 4.74 | 1.19 | 11.17 |
| Northern Ghana | -2.50 | 8.50 | 0.20 | 11.20 |
| Tamale | -0.849 | 9.393 | -0.829 | 9.413 |
| Accra | -0.197 | 5.593 | -0.177 | 5.613 |
| Africa | -20.00 | -35.00 | 55.00 | 38.00 |
| Global | -180.00 | -90.00 | 180.00 | 90.00 |

**Note:** This instance uses the `bounds` parameter for spatial search.
The standard `bbox` parameter causes a 500 error on this instance and must
not be used.

---

## Troubleshooting

### `CSRF token missing or incorrect` or `CSRF cookie not set`
Your API token has expired or is missing required scopes. Generate a new
token with all scopes selected and update `GEO_API_TOKEN` in your `.env` file.

### `No API token provided — skipping`
The `.env` file is missing, or `GEO_API_TOKEN` is not set inside it.
Check that `.env` exists in the `gkh_pom/` folder and contains your token.

### `SSL certificate verify failed`
Set `GEO_NO_VERIFY_TLS=true` in your `.env` file.

### `ModuleNotFoundError: No module named 'client'`
You are running pytest from the wrong folder. Always run from inside `gkh_pom/`:
```powershell
cd gkh_pom
pytest tests/ -v
```

### `collected 0 items`
pytest cannot find the tests. Check that `pytest.ini` exists in `gkh_pom/`
and contains `testpaths = tests`.

### Tests skipped with `DOI provider not configured`
Your instance does not have a DataCite or CrossRef DOI provider set up.
This is expected — the tests skip gracefully and it is not a failure.

### `Permission denied` (403) on `/api/user/*`
Your token is missing the `user:email` scope or has expired. Generate a new
token with all scopes selected.

### `[conftest] No .env file found`
You have not created the `.env` file yet. Follow Step 4 in First-Time Setup above.
