# UI-Data Alignment

## The Lesson

A web application that shows buttons, links, or filters for data that does not exist creates a worse experience than one that simply omits them. Every UI element that implies data availability must be backed by a runtime or build-time check that the data actually exists.

## Context

A labor market data warehouse powered a web application with occupation profiles, wage comparisons, trend explorers, and a static GitHub Pages deployment. Three bugs shared the same root cause: the UI assumed uniform data availability when the underlying data was sparse or partitioned by occupation level, time period, or deployment mode.

## What Happened

1. **Dead-end links to empty pages were discovered.** The occupation profile page displayed a "Compare by State" button for all 1,447 occupations. But 600 occupations — mostly broad groups, minor groups, and 49 detailed occupations — had no state-level OEWS wage data. Clicking the button led to a page saying "No state-level wage data available."

2. **A hide-and-reveal pattern was implemented.** The link was hidden by default and revealed only after a background fetch confirmed state data existed:

   ```javascript
   html += '<p id="compare-state-link" style="display:none;">' +
       '<a href="..." class="btn">Compare by State</a></p>';

   fetchWithTimeout("/api/occupations/" + code + "/wages?geo_type=state")
       .then(function(r) { return r.ok ? r.json() : null; })
       .then(function(stateData) {
           if (stateData && stateData.wages && stateData.wages.length > 0) {
               document.getElementById("compare-state-link").style.display = "";
           }
       });
   ```

3. **Time was displayed as a column instead of a filter.** The Ranked Movers page showed all years in one table with a "Year" column, mixing 2022 and 2023 movers together. The fix was adding a `year` query parameter to the API, defaulting to the latest year, and returning `available_years` so the UI could populate a dropdown:

   ```json
   {
       "year": 2023,
       "available_years": [2022, 2023],
       "gainers": [...],
       "losers": [...]
   }
   ```

4. **The static site shim had a gap.** The Compare Occupations page worked on the live server but always showed "Failed to load comparison data" on GitHub Pages. The fetch shim had no handler for `/api/trends/compare/occupations`. The fix was assembling the comparison response client-side from per-occupation pre-built JSON files:

   ```javascript
   if (p === '/api/trends/compare/occupations') {
       var codes = sp.get('soc_codes').split(',');
       return Promise.all(codes.map(function(c) {
           return fetch(base + '/api/trends/' + c + '.json')
               .then(function(r) { return r.json(); });
       })).then(function(arr) {
           return new Response(JSON.stringify({
               metric: metric,
               occupations: arr.map(...)
           }));
       });
   }
   ```

## Key Insights

- **Do not show navigation to views that will be empty.** A dead-end page erodes user trust more than a missing link. Hide-and-reveal after a background probe is the correct pattern when data availability varies.
- **When data has a time dimension, expose it as a filter, not a table column.** Default to the most recent period so users see current data immediately. Mixed-year tables force users to mentally filter while scanning.
- **Static site gaps are invisible until tested.** The live server and the static site are two different runtime environments. Every API endpoint must have a corresponding shim handler, or the static deployment silently breaks.
- **Client-side composition can replicate server-side joins.** When a static site cannot pre-generate an endpoint (because the query accepts arbitrary combinations), check whether the response can be assembled from existing pre-generated building blocks.

  | Scenario | Pattern | Example |
  |---|---|---|
  | Link to a view that may be empty | Hide-and-reveal after background probe | "Compare by State" link |
  | Data spans multiple time periods | Filter control, not table column | Year dropdown on Ranked Movers |
  | Dynamic query on static site | Client-side composition from pre-built data | Compare Occupations shim |
  | Metric with limited data availability | Default to the mode/metric where data exists | Trend Explorer defaulting to "comparable" |

## Related Lessons

- [Multi-Vintage Query Pitfalls](12-multi-vintage-queries.md)
- [Fetch Shim Architecture](21-fetch-shim.md)
- [Static Site Generation](08-static-site-generation.md)
