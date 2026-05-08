# Fetch Shim Architecture

## The Lesson

A static site can replicate a dynamic API by intercepting JavaScript `fetch()` calls and redirecting them to pre-built JSON files. The key technique is a monkey-patch of the global `fetch` function that routes API URLs to static file paths, with client-side filtering for search and client-side composition for endpoints that accept arbitrary parameter combinations.

## Context

A labor market data application ran on a FastAPI server with 18+ API endpoints that accepted query parameters, joined database tables, and returned JSON. The site needed to be deployed to GitHub Pages, which can only serve static files. Every JavaScript `fetch('/api/...')` call that worked on the live server would return 404 on the static site. The solution was a build-time process that pre-rendered every known API response to a `.json` file on disk, plus a JavaScript shim injected into every HTML page to intercept `fetch()` calls and translate dynamic URLs into static file paths.

## What Happened

1. **The global `fetch` function was monkey-patched.** The shim saves a reference to the original `fetch`, replaces it with a wrapper that inspects each URL, and routes API calls to the correct static JSON file. Non-API calls pass through untouched:

   ```javascript
   var originalFetch = window.fetch;
   window.fetch = function(url) {
       if (url.indexOf('/api/') < 0)
           return originalFetch(url);

       var path = url.split('?')[0];
       var params = new URLSearchParams(url.split('?')[1] || '');
       // ... pattern matching rules ...
       return originalFetch(path + '.json');
   };
   ```

2. **URL-to-file mapping rules were defined.** Query parameters become filename suffixes, keeping the mapping deterministic:

   | API URL Pattern | Static JSON File | Notes |
   |---|---|---|
   | /api/occupations/search?q=... | /api/occupations/search.json | Client-side filtering from full index |
   | /api/occupations/{soc}/wages?geo_type=X | /api/occupations/{soc}/wages-X.json | Separate file per geo_type |
   | /api/trends/movers?metric=M&year=Y | /api/trends/movers-Y_M.json | Per-metric, per-year |
   | /api/trends/{soc}?metric=M | /api/trends/{soc}-M.json | Per-metric trend data |
   | /api/trends/compare/geography?soc_code=X | /api/trends/compare/geography-X.json | Per-occupation file |

   The default metric (`employment_count`) maps to the bare filename; other metrics add a suffix.

3. **Client-side search was implemented with a cached index.** The full occupation index (1,447 entries) is small enough to download once and filter in JavaScript. A singleton Promise ensures only one network request is made, even across multiple search queries:

   ```javascript
   var searchCache = null;
   function loadSearch(basePath) {
       if (!searchCache)
           searchCache = originalFetch(basePath + '/api/occupations/search.json')
               .then(function(r) { return r.json(); });
       return searchCache;
   }

   loadSearch(basePath).then(function(data) {
       var query = params.get('q').toLowerCase();
       var results = data.results.filter(function(x) {
           return x.soc_code.indexOf(query) >= 0 ||
                  x.occupation_title.toLowerCase().indexOf(query) >= 0;
       });
       return new Response(JSON.stringify({
           results: results.slice(offset, offset + limit),
           total: results.length
       }));
   });
   ```

4. **Client-side composition handled the comparison endpoint.** The occupation comparison endpoint accepts an arbitrary list of SOC codes — no single pre-built file can cover every possible combination. The shim fetches per-occupation JSON files and assembles the response:

   ```javascript
   var codes = params.get('soc_codes').split(',');
   return Promise.all(codes.map(function(code) {
       return Promise.all([
           originalFetch('/api/trends/' + code + '.json'),
           originalFetch('/api/occupations/' + code + '.json')
       ]);
   })).then(function(results) {
       return new Response(JSON.stringify({
           metric: metric,
           occupations: assembledData
       }));
   });
   ```

5. **Path rewriting was split between build-time and runtime.** The build script rewrites HTML-level paths (links, script sources, stylesheet references) via string replacement. The shim handles API-level paths at runtime by extracting the base path from the current URL. This means the same shim code works both locally (base path `""`) and on GitHub Pages (base path `"/jobclass"`) without changes:

   ```python
   # Build-time rewrites in build_static.py:
   replacements = [
       ('"/api/',        '"/jobclass/api/'),
       ('"/occupation/', '"/jobclass/occupation/'),
       ('"/static/',     '"/jobclass/static/'),
       ('href="/"',      'href="/jobclass/"'),
   ]
   ```

## Key Insights

- **Monkey-patching `fetch` makes the static site invisible to the application.** The browser receives the same JSON either way — application JavaScript does not need to know whether it is running against a live server or static files.
- **Client-side composition is the static-site equivalent of a server-side JOIN.** When a pre-built endpoint cannot exist because the query accepts arbitrary parameter combinations, fetching building blocks and assembling the response client-side replicates the server behavior.
- **A cached Promise eliminates redundant network requests.** For search, the full index is fetched once and every subsequent keystroke filters against the already-loaded data. The singleton pattern ensures only one request is in flight regardless of timing.
- **Separate build-time and runtime path handling avoids coupling.** The build script owns HTML paths; the shim owns API paths. Neither needs to know about the other's work, and both support arbitrary base path configurations.

## Related Lessons

- [Static Site Generation](08-static-site-generation.md)
- [UI-Data Alignment](13-ui-data-alignment.md)
- [Testing and Deployment](09-testing-deployment.md)
