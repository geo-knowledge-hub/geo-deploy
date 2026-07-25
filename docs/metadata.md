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

> [!NOTE]
>
> InvenioRDM does not allow hard-deleting published records via the public
> API. Only draft records can be deleted. This means every time a test
> publishes a record, it remains on the server permanently.

To keep accumulation low:
- The `published_resource` and `published_package` fixtures are session-scoped,
  meaning they create **one** published record per test run and reuse it across
  all tests that need a published record
- Tests that specifically test the publish action create one additional record each
- Per full test run, approximately **5 to 8** published records are created

These records are named with the `pytest-` prefix. They can be identified and
deleted manually from the GKH admin interface if needed.

---