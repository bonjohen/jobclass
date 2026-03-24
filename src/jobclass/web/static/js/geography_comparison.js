/* JobClass — Geography comparison page */
"use strict";

(function() {
    var FETCH_TIMEOUT_MS = 10000;
    var socCode = document.querySelector(".geography-comparison-page").dataset.socCode;
    var chartContainer = document.getElementById("geo-chart-container");
    var tableContainer = document.getElementById("geo-table-container");

    function fetchWithTimeout(url) {
        var controller = new AbortController();
        var timer = setTimeout(function() { controller.abort(); }, FETCH_TIMEOUT_MS);
        return fetch(url, { signal: controller.signal }).finally(function() { clearTimeout(timer); });
    }

    function loadGeoComparison() {
        var metric = document.getElementById("geo-metric").value;
        chartContainer.className = "loading";
        chartContainer.setAttribute("aria-busy", "true");
        chartContainer.innerHTML = "Loading...";
        tableContainer.hidden = true;

        var url = "/api/trends/compare/geography?soc_code=" + encodeURIComponent(socCode) +
            "&metric=" + encodeURIComponent(metric);

        fetchWithTimeout(url)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                chartContainer.setAttribute("aria-busy", "false");
                chartContainer.className = "";

                if (!data.geographies || data.geographies.length === 0) {
                    chartContainer.innerHTML = "<p>No state-level data available.</p>";
                    return;
                }

                document.getElementById("page-title").textContent =
                    "Geography Comparison — " + socCode + " (" + data.year + ")";

                // Bar chart
                var maxVal = 0;
                data.geographies.forEach(function(g) {
                    if (g.value != null && g.value > maxVal) maxVal = g.value;
                });

                var html = '<div class="geo-bar-chart" role="img" aria-label="State comparison for ' + escapeAttr(socCode) + '">';
                data.geographies.forEach(function(g) {
                    var pct = maxVal > 0 && g.value != null ? (g.value / maxVal * 100) : 0;
                    var label = g.value != null ? formatNumber(g.value) : "N/A";
                    html += '<div class="bar-row">';
                    html += '<span class="bar-label">' + escapeHtml(g.geo_name || g.geo_code) + '</span>';
                    html += '<div class="bar-track"><div class="bar observed" style="width:' + pct + '%"></div></div>';
                    html += '<span class="bar-value">' + label + '</span>';
                    html += '</div>';
                });
                html += '</div>';
                chartContainer.innerHTML = html;

                // Table
                var thtml = '<table class="data-table"><thead><tr>';
                thtml += '<th>State</th><th>Value</th><th>Source</th>';
                thtml += '</tr></thead><tbody>';
                data.geographies.forEach(function(g) {
                    thtml += '<tr><td>' + escapeHtml(g.geo_name) + '</td>';
                    thtml += '<td>' + formatNumber(g.value) + '</td>';
                    thtml += '<td>' + escapeHtml(g.source_release_id) + '</td></tr>';
                });
                thtml += '</tbody></table>';
                tableContainer.innerHTML = thtml;
                tableContainer.hidden = false;
            })
            .catch(function() {
                chartContainer.setAttribute("aria-busy", "false");
                chartContainer.innerHTML = '<p class="error-message">Failed to load geography data.</p>';
                chartContainer.className = "";
            });
    }

    document.getElementById("geo-metric").addEventListener("change", loadGeoComparison);
    loadGeoComparison();
})();
