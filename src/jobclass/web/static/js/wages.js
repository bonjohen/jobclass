/* JobClass — Wages comparison page */
"use strict";

(function() {
    var FETCH_TIMEOUT_MS = 10000;
    var socCode = document.querySelector(".wages-comparison-page").dataset.socCode;
    var container = document.getElementById("wages-table-container");

    function fetchWithTimeout(url) {
        var controller = new AbortController();
        var timer = setTimeout(function() { controller.abort(); }, FETCH_TIMEOUT_MS);
        return fetch(url, { signal: controller.signal }).finally(function() { clearTimeout(timer); });
    }

    fetchWithTimeout("/api/occupations/" + encodeURIComponent(socCode) + "/wages?geo_type=state")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            container.setAttribute("aria-busy", "false");
            if (!data.wages || data.wages.length === 0) {
                container.innerHTML = "<p>No state-level wage data available.</p>";
                container.className = "";
                return;
            }

            // Update title
            document.getElementById("page-title").textContent = "Wages by State — " + socCode;

            var html = '<table class="data-table"><thead><tr>';
            html += '<th>State</th><th>Employment</th><th>Mean Annual</th><th>Median Annual</th>';
            html += '<th>P10 Hourly</th><th>P25 Hourly</th><th>P75 Hourly</th><th>P90 Hourly</th>';
            html += '</tr></thead><tbody>';
            data.wages.forEach(function(w) {
                html += '<tr>';
                html += '<td>' + escapeHtml(w.geo_name || w.geo_code) + '</td>';
                html += '<td>' + formatNumber(w.employment_count) + '</td>';
                html += '<td>' + formatWage(w.mean_annual_wage) + '</td>';
                html += '<td>' + formatWage(w.median_annual_wage) + '</td>';
                html += '<td>' + formatWage(w.p10_hourly_wage) + '</td>';
                html += '<td>' + formatWage(w.p25_hourly_wage) + '</td>';
                html += '<td>' + formatWage(w.p75_hourly_wage) + '</td>';
                html += '<td>' + formatWage(w.p90_hourly_wage) + '</td>';
                html += '</tr>';
            });
            html += '</tbody></table>';

            if (data.wages[0].source_release_id) {
                html += '<div class="lineage-badge">OEWS ' + escapeHtml(data.wages[0].source_release_id) + '</div>';
            }

            container.innerHTML = html;
            container.className = "";
        })
        .catch(function() {
            container.setAttribute("aria-busy", "false");
            container.innerHTML = '<p class="error-message">Failed to load wage data. Please try again later.</p>';
            container.className = "";
        });

})();
