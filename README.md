# Homepage Tests (GKH)
The test_homepage.py test suite verifies the availability and basic integrity of the GEO Knowledge Hub public homepage and related public endpoints.

### Scope
Confirms the homepage loads successfully (200 OK) without authentication.
Validates the response format is HTML and key UI elements (search and navigation) are present.
Checks accessibility of /robots.txt, /static/, and ensures no server-side errors (no 5xx responses).
Verifies correct handling of URL variations and redirects (e.g., trailing slash behaviour).
Ensures API root (/api/) responds safely (no server errors).
Validates public search page (/search) is accessible and redirects correctly.
Confirms /api/search is publicly accessible and returns expected JSON structure.

This is a basic smoke test to ensure public-facing pages and core endpoints of the Knowledge Hub are reachable and functional after deployment.
