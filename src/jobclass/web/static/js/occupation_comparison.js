/* JobClass — Occupation comparison page */
"use strict";

(function() {
    var selectedCodes = [];
    var tagsContainer = document.getElementById("selected-occupations");
    var searchInput = document.getElementById("compare-search");
    var searchResults = document.getElementById("compare-search-results");
    var compareBtn = document.getElementById("compare-btn");
    var chartContainer = document.getElementById("compare-chart-container");
    var tableContainer = document.getElementById("compare-table-container");

    function updateTags() {
        var html = "";
        selectedCodes.forEach(function(code) {
            html += '<span class="tag">' + escapeHtml(code) +
                ' <button data-code="' + escapeAttr(code) + '" class="tag-remove">&times;</button></span>';
        });
        tagsContainer.innerHTML = html;
        compareBtn.disabled = selectedCodes.length === 0;

        tagsContainer.querySelectorAll(".tag-remove").forEach(function(btn) {
            btn.addEventListener("click", function() {
                selectedCodes = selectedCodes.filter(function(c) { return c !== btn.dataset.code; });
                updateTags();
            });
        });
    }

    var debounceTimer = null;
    searchInput.addEventListener("input", function() {
        clearTimeout(debounceTimer);
        var q = searchInput.value.trim();
        if (q.length < 2) { searchResults.innerHTML = ""; return; }
        debounceTimer = setTimeout(function() {
            fetchWithTimeout("/api/occupations/search?q=" + encodeURIComponent(q) + "&limit=8")
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (!data.results || data.results.length === 0) {
                        searchResults.innerHTML = '<div class="search-item">No results</div>';
                        return;
                    }
                    var html = "";
                    data.results.forEach(function(occ) {
                        html += '<div class="search-item" data-code="' + escapeAttr(occ.soc_code) + '" role="option">';
                        html += escapeHtml(occ.soc_code) + ' — ' + escapeHtml(occ.occupation_title);
                        html += '</div>';
                    });
                    searchResults.innerHTML = html;
                    searchResults.querySelectorAll(".search-item[data-code]").forEach(function(item) {
                        item.addEventListener("click", function() {
                            if (selectedCodes.indexOf(item.dataset.code) === -1 && selectedCodes.length < 5) {
                                selectedCodes.push(item.dataset.code);
                                updateTags();
                            }
                            searchResults.innerHTML = "";
                            searchInput.value = "";
                        });
                    });
                })
                .catch(function() { searchResults.innerHTML = ""; });
        }, 250);
    });

    compareBtn.addEventListener("click", function() {
        if (selectedCodes.length === 0) return;

        var metric = document.getElementById("compare-metric").value;
        var url = "/api/trends/compare/occupations?soc_codes=" +
            encodeURIComponent(selectedCodes.join(",")) +
            "&metric=" + encodeURIComponent(metric);

        chartContainer.hidden = false;
        chartContainer.className = "loading";
        chartContainer.setAttribute("aria-busy", "true");
        chartContainer.innerHTML = "Loading...";
        tableContainer.hidden = true;

        fetchWithTimeout(url)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                chartContainer.setAttribute("aria-busy", "false");
                chartContainer.className = "";

                if (!data.occupations || data.occupations.length === 0) {
                    chartContainer.innerHTML = "<p>No data found.</p>";
                    return;
                }

                // Build table
                var allYears = [];
                data.occupations.forEach(function(occ) {
                    occ.series.forEach(function(d) {
                        if (allYears.indexOf(d.year) === -1) allYears.push(d.year);
                    });
                });
                allYears.sort();

                var html = '<table class="data-table"><thead><tr><th>Occupation</th>';
                allYears.forEach(function(y) { html += '<th>' + y + '</th>'; });
                html += '</tr></thead><tbody>';

                data.occupations.forEach(function(occ) {
                    var byYear = {};
                    occ.series.forEach(function(d) { byYear[d.year] = d.value; });
                    html += '<tr><td><a href="/trends/explorer/' + escapeAttr(occ.soc_code) + '">' +
                        escapeHtml(occ.soc_code) + ' ' + escapeHtml(occ.title) + '</a></td>';
                    allYears.forEach(function(y) {
                        html += '<td>' + formatNumber(byYear[y]) + '</td>';
                    });
                    html += '</tr>';
                });
                html += '</tbody></table>';

                chartContainer.innerHTML = html;
                tableContainer.hidden = true;
            })
            .catch(function() {
                chartContainer.setAttribute("aria-busy", "false");
                chartContainer.innerHTML = '<p class="error-message">Failed to load comparison data.</p>';
                chartContainer.className = "";
            });
    });

    updateTags();
})();
