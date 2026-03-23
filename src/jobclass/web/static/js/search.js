/* JobClass — Search page */
"use strict";

(function() {
    var FETCH_TIMEOUT_MS = 10000;
    var input = document.getElementById("search-input");
    var resultsDiv = document.getElementById("search-results");
    var debounceTimer = null;
    var abortController = null;

    input.addEventListener("input", function() {
        clearTimeout(debounceTimer);
        var q = input.value.trim();
        if (q.length < 2) {
            if (abortController) abortController.abort();
            resultsDiv.innerHTML = '<p class="search-hint">Type at least 2 characters to search.</p>';
            return;
        }
        debounceTimer = setTimeout(function() { doSearch(q); }, 250);
    });

    function doSearch(q) {
        if (abortController) abortController.abort();
        abortController = new AbortController();
        var timeoutId = setTimeout(function() { abortController.abort(); }, FETCH_TIMEOUT_MS);

        fetch("/api/occupations/search?q=" + encodeURIComponent(q), { signal: abortController.signal })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                clearTimeout(timeoutId);
                if (!data.results || data.results.length === 0) {
                    resultsDiv.innerHTML = '<p class="search-hint">No occupations found.</p>';
                    return;
                }
                var html = '<table class="data-table"><thead><tr><th>SOC Code</th><th>Title</th><th>Level</th></tr></thead><tbody>';
                data.results.forEach(function(r) {
                    html += '<tr><td><a href="/occupation/' + escapeAttr(r.soc_code) + '">' + escapeHtml(r.soc_code) + '</a></td>';
                    html += '<td><a href="/occupation/' + escapeAttr(r.soc_code) + '">' + escapeHtml(r.occupation_title) + '</a></td>';
                    html += '<td>' + escapeHtml(r.occupation_level_name) + '</td></tr>';
                });
                html += '</tbody></table>';
                resultsDiv.innerHTML = html;
            })
            .catch(function(err) {
                clearTimeout(timeoutId);
                if (err.name === 'AbortError') return;
                resultsDiv.innerHTML = '<p class="error-message">Search failed. Please try again.</p>';
            });
    }

    input.focus();
})();
