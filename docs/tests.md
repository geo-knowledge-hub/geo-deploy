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

1. Open the relevant file in `geodeploy/`
2. Add a method using `self._get`, `self._post`, `self._put`, or `self._delete`,
   building the path with `self._resource_path(...)` — never hand-type the
   `base_path` again
3. Call it from your test

```python
# In geodeploy/packages.py (base_path = "/api/packages" is already set once
# at the top of the class)
def my_new_endpoint(self, package_id: str) -> Response:
    """GET /api/packages/{id}/something-new"""
    return self._get(self._resource_path(package_id, "something-new"))
```

No URLs ever appear in test files.

---
