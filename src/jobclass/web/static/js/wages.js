/* JobClass — Wages comparison page */
"use strict";

(function() {
    var socCode = document.querySelector(".wages-comparison-page").dataset.socCode;

    fetch("/api/occupations/" + encodeURIComponent(socCode) + "/wages?geo_type=state")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var container = document.getElementById("wages-table-container");
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
            document.getElementById("wages-table-container").innerHTML = "<p>Failed to load wage data.</p>";
        });

})();
