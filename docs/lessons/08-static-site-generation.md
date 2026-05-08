# Static Site Generation

## The Lesson

A server-side web application can be deployed to a static hosting platform by pre-rendering every page and API response as files, then injecting a JavaScript fetch shim that transparently redirects API calls to the corresponding JSON files. The application's JavaScript never knows it's running on a static site — but combinatorial query parameters expose the fundamental limits of this approach.

## Context

The JobClass web application uses FastAPI with server-side Jinja2 template rendering and JSON API endpoints. GitHub Pages serves only static files — no Python, no server-side logic. The goal was to publish the full site (HTML pages for ~870 occupations, all API responses, search functionality) to GitHub Pages without modifying the application code or its client-side JavaScript.

## What Happened

1. **A build script was written to pre-render every page.** `scripts/build_static.py` uses FastAPI's `TestClient` to request every HTML page and API endpoint from the application in-process, writing responses to files under `_site/`:

   ```
   HTML pages  → _site/occupation/11-1011/index.html
   API JSON    → _site/api/occupations/11-1011.json
   ```

2. **A fetch shim was injected into every HTML page.** The shim intercepts JavaScript `fetch()` calls to `/api/` URLs and redirects them to corresponding `.json` files. Query parameters are mapped to filename suffixes:

   ```
   fetch('/api/occupations/11-1011/wages?geo_type=state')
   → fetch('/api/occupations/11-1011/wages-state.json')
   ```

3. **Search was implemented client-side.** The shim downloads the full occupation index once, caches it in memory, and filters locally. No server-side search endpoint is needed in static mode.

4. **Geography comparison trends used parameter-to-filename mapping.** The shim maps the `soc_code` query parameter to a filename:

   ```
   fetch('/api/trends/compare/geography?soc_code=11-1011')
   → fetch('/api/trends/compare/geography-11-1011.json')
   ```

5. **Combinatorial endpoints hit the pre-generation wall.** The occupation comparison endpoint (`/api/trends/compare/occupations?soc_codes=11-1011,13-1011,15-1211`) accepts arbitrary combinations of SOC codes. With ~870 occupations, the number of possible combinations is astronomical and cannot be pre-generated. The static site accepts graceful degradation for these features.

6. **Path rewriting was handled at build time.** When served under a subpath (e.g., `/jobclass/`), every absolute URL in the HTML must include the base path. A `rewrite_paths()` function performs string replacements before shim injection. The shim itself extracts the base path at runtime from the URL using `u.indexOf('/api/')`.

7. **A checklist was established for adding new routes.** Every new route or API endpoint in the web app must also be added to `build_static.py`: HTML page generation (`write_html()`), API JSON generation (`write_json()`), path rewriting entries for new URL prefixes, and shim updates for query-parameter-to-filename mappings.

## Key Insights

- **The fetch shim is the key abstraction.** By intercepting `fetch()` at the browser level, the application's JavaScript code doesn't need to know whether it's talking to a live server or reading static files. This means zero code changes to the application for static deployment.
- **Static site generation is inherently limited for combinatorial endpoints.** Any endpoint that accepts arbitrary combinations of parameters cannot be fully pre-rendered. The choice is either graceful degradation (reduced functionality in static mode) or client-side composition (fetch individual pieces and combine them in JavaScript).
- **Search can work without a server.** Downloading the full index and filtering client-side is practical when the dataset is small enough (870 occupations ≈ a few hundred KB of JSON). This pattern breaks down for datasets with thousands or millions of entries.
- **Path rewriting is a build-time concern, not a runtime concern.** Baking the base path into HTML at build time is simpler and more reliable than runtime path resolution. The one exception is the shim itself, which must detect the base path at runtime because it processes URLs dynamically.

## Related Lessons

- [Testing and Deployment](09-testing-deployment.md) — CI and deployment pipeline that includes the static build
- [Fetch Shim Architecture](21-fetch-shim.md) — deeper treatment of the shim's URL mapping patterns
- [UI-Data Alignment](13-ui-data-alignment.md) — ensuring the static site's data matches what the live server would produce
