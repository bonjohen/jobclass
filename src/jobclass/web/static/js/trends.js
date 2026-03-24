/* JobClass — Trends landing page */
"use strict";

(function() {
    var FETCH_TIMEOUT_MS = 10000;

    function fetchWithTimeout(url) {
        var controller = new AbortController();
        var timer = setTimeout(function() { controller.abort(); }, FETCH_TIMEOUT_MS);
        return fetch(url, { signal: controller.signal }).finally(function() { clearTimeout(timer); });
    }

    function setupSearch(inputId, resultsId, urlPrefix) {
        var input = document.getElementById(inputId);
        var results = document.getElementById(resultsId);
        if (!input || !results) return;

        var debounceTimer = null;
        input.addEventListener("input", function() {
            clearTimeout(debounceTimer);
            var q = input.value.trim();
            if (q.length < 2) { results.innerHTML = ""; return; }
            debounceTimer = setTimeout(function() {
                fetchWithTimeout("/api/occupations/search?q=" + encodeURIComponent(q) + "&limit=8")
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (!data.results || data.results.length === 0) {
                            results.innerHTML = '<div class="search-item">No results</div>';
                            return;
                        }
                        var html = "";
                        data.results.forEach(function(occ) {
                            html += '<a class="search-item" href="' + urlPrefix + escapeAttr(occ.soc_code) + '" role="option">';
                            html += escapeHtml(occ.soc_code) + ' — ' + escapeHtml(occ.occupation_title);
                            html += '</a>';
                        });
                        results.innerHTML = html;
                    })
                    .catch(function() { results.innerHTML = ""; });
            }, 250);
        });
    }

    setupSearch("trend-search", "trend-search-results", "/trends/explorer/");
    setupSearch("geo-search", "geo-search-results", "/trends/geography/");
})();
