# GEO Knowledge Hub — pytest Test Suite (POM Architecture)

A professional, maintainable pytest suite for the GEO Knowledge Hub API,
built using the **Page Object Model (POM)** pattern with separated
`conftest.py`, `fixtures.py`, and `factories.py`.

---

## Project Structure

```
gkh_pom/
├── conftest.py          # Thin: CLI options + SSL bypass + fixture re-exports
├── fixtures.py          # All @pytest.fixture definitions
├── factories.py         # All payload builders (make_*_payload functions)
│
├── client/              # Page Object Model — one class per API domain
│   ├── __init__.py
│   ├── base.py          # BaseClient: shared HTTP session + helpers
│   ├── resources.py     # ResourcesClient: /api/records
│   ├── packages.py      # PackagesClient: /api/packages
│   ├── communities.py   # CommunitiesClient: /api/communities
│   └── search.py        # SearchClient: /api/search
│
└── tests/
    ├── ui/              # UI smoke tests (no auth required)
    │   ├── test_homepage.py
    │   └── test_login.py
    └── api/             # API tests (token required)
        ├── test_resources.py
        ├── test_packages.py
        ├── test_communities.py
        ├── test_search.py
        └── test_drafts.py
```

---

## Why this structure?

| Layer | Responsibility | Change when... |
|---|---|---|
| `conftest.py` | pytest hooks, CLI options | Never (unless adding new CLI flags) |
| `fixtures.py` | Test setup/teardown | Adding new record types |
| `factories.py` | Payload data | API schema changes |
| `client/*.py` | API endpoint URLs | Endpoint URLs change |
| `tests/**` | Assertions only | Test logic changes |

**If an endpoint URL changes** → update only `client/packages.py` (for example).
**If a required field changes** → update only `factories.py`.
**If a fixture needs changing** → update only `fixtures.py`.
Tests themselves stay untouched.

---

## Prerequisites

```powershell
pip install pytest requests pytest-html
```

---

## Getting Your API Token

1. Log in to `https://179.237.84.212`
2. Click your avatar → **Settings** → **Applications**
3. Under **Personal access tokens** → click **New token**
4. Select scopes: `deposits:actions`, `deposits:metadata`, `deposits:files`
5. Copy the token (shown only once)

---

## Running Tests

### Run everything
```powershell
pytest tests/ -v --no-verify-tls --api-token "YOUR_TOKEN"
```

### Run only API tests
```powershell
pytest tests/api/ -v --no-verify-tls --api-token "YOUR_TOKEN"
```

### Run only UI tests
```powershell
pytest tests/ui/ -v --no-verify-tls --api-token "YOUR_TOKEN"
```

### Run a specific file
```powershell
pytest tests/api/test_packages.py -v --no-verify-tls --api-token "YOUR_TOKEN"
```

### Generate an HTML report
```powershell
pytest tests/ -v --no-verify-tls --api-token "YOUR_TOKEN" `
  --html=report.html --self-contained-html
```

### Use environment variable
```powershell
$env:GEO_API_TOKEN = "YOUR_TOKEN"
pytest tests/ -v --no-verify-tls
```

---

## CLI Options

| Option | Default | Description |
|---|---|---|
| `--base-url` | `https://179.237.84.212` | GEO Knowledge Hub URL |
| `--api-token` | *(GEO_API_TOKEN env var)* | Bearer token |
| `--no-verify-tls` | `False` | Skip TLS verification (self-signed certs) |

---

## Adding a New Test

1. Pick the right file under `tests/api/` or `tests/ui/`
2. Inject the client fixture (`packages`, `resources`, `communities`)
3. Call client methods — never write URLs in test functions
4. Assert on the response

```python
def test_my_new_test(
    self,
    packages: PackagesClient,
    package_draft: dict,
) -> None:
    r = packages.get_draft(package_draft["id"])
    assert_ok(r, 200)
    assert r.json()["metadata"]["title"] is not None
```

## Adding a New API Endpoint

1. Add a method to the relevant client in `client/`
2. Use `self._get / _post / _put / _delete`
3. Call the new method from your test

No URLs ever appear in test files.

---

## Test Coverage

| File | Tests | Covers |
|---|---|---|
| `tests/ui/test_homepage.py` | 10 | Homepage, search page, robots.txt, static assets |
| `tests/ui/test_login.py` | 10 | Login UI, token auth, rejection, user profile |
| `tests/api/test_resources.py` | 13 | Search, draft CRUD, publish, versions, file upload |
| `tests/api/test_packages.py` | 17 | Search, draft CRUD, publish, versions, file upload, association |
| `tests/api/test_communities.py` | 10 | Search, CRUD, members |
| `tests/api/test_search.py` | 3 | Unified search, pagination |
| `tests/api/test_drafts.py` | 14 | Draft flags, visibility, persistence, lifecycle |
| **Total** | **~77** | |
