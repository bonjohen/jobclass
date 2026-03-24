/* JobClass — Search page */
"use strict";

(function() {
    var input = document.getElementById("search-input");
    var resultsDiv = document.getElementById("search-results");
    var debounceTimer = null;
    var currentAbort = null;

    input.addEventListener("input", function() {
        clearTimeout(debounceTimer);
        var q = input.value.trim();
        if (q.length < 2) {
            if (currentAbort) { currentAbort.abort(); currentAbort = null; }
            resultsDiv.innerHTML = '<p class="search-hint">Type at least 2 characters to search.</p>';
            return;
        }
        debounceTimer = setTimeout(function() { doSearch(q); }, 250);
    });

    function doSearch(q) {
        if (currentAbort) { currentAbort.abort(); currentAbort = null; }
        var controller = new AbortController();
        currentAbort = controller;

        fetchWithTimeout("/api/occupations/search?q=" + encodeURIComponent(q))
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (controller.signal.aborted) return;
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
                if (err.name === 'AbortError') return;
                resultsDiv.innerHTML = '<p class="error-message">Search failed. Please try again.</p>';
            });
    }

    input.focus();
})();
