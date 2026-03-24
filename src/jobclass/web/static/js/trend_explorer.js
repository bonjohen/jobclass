/* JobClass — Trend explorer page */
"use strict";

(function() {
    var socCode = document.querySelector(".trend-explorer-page").dataset.socCode;
    var chartContainer = document.getElementById("trend-chart-container");
    var tableContainer = document.getElementById("trend-table-container");
    var metaDiv = document.getElementById("trend-meta");

    function loadTrend() {
        var metric = document.getElementById("metric-select").value;
        var geoType = document.getElementById("geo-select").value;
        var mode = document.getElementById("mode-select").value;

        chartContainer.className = "loading";
        chartContainer.setAttribute("aria-busy", "true");
        chartContainer.innerHTML = "Loading trend data...";
        chartContainer.hidden = false;
        tableContainer.hidden = true;
        metaDiv.hidden = true;

        var url = "/api/trends/" + encodeURIComponent(socCode) +
            "?metric=" + encodeURIComponent(metric) +
            "&geo_type=" + encodeURIComponent(geoType) +
            "&comparability_mode=" + encodeURIComponent(mode);

        fetchWithTimeout(url)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                chartContainer.setAttribute("aria-busy", "false");
                chartContainer.className = "";

                if (!data.series || data.series.length === 0) {
                    chartContainer.innerHTML = "<p>No trend data available for this selection.</p>";
                    return;
                }

                var first = data.series[0];
                document.getElementById("page-title").textContent = "Trend Explorer — " + socCode;

                // Metadata
                document.getElementById("meta-metric").textContent = first.metric_name;
                document.getElementById("meta-units").textContent = "(" + first.units + ")";
                document.getElementById("meta-mode").textContent = mode === "comparable" ? "Comparable" : "As Published";
                document.getElementById("meta-lineage").textContent = "Source: " + (first.source_release_id || "");
                metaDiv.hidden = false;

                // Build simple bar chart using HTML
                var maxVal = 0;
                data.series.forEach(function(d) { if (d.value != null && d.value > maxVal) maxVal = d.value; });

                var chartHtml = '<div class="trend-bar-chart" role="img" aria-label="Trend chart for ' + escapeAttr(socCode) + '">';
                data.series.forEach(function(d) {
                    var pct = maxVal > 0 && d.value != null ? (d.value / maxVal * 100) : 0;
                    var isProjected = d.derivation_type !== "base" || metric.indexOf("projected") === 0;
                    var barClass = isProjected ? "bar projected" : "bar observed";
                    var label = d.value != null ? formatTrendValue(d.value, first.units) : "N/A";

                    chartHtml += '<div class="bar-row">';
                    chartHtml += '<span class="bar-label">' + d.year + '</span>';
                    chartHtml += '<div class="bar-track"><div class="' + barClass + '" style="width:' + pct + '%"></div></div>';
                    chartHtml += '<span class="bar-value">' + label;
                    if (d.yoy_pct_change != null) {
                        var sign = d.yoy_pct_change >= 0 ? "+" : "";
                        chartHtml += ' <span class="derived-badge" title="Derived: YoY change">' + sign + d.yoy_pct_change.toFixed(1) + '%</span>';
                    }
                    chartHtml += '</span>';
                    chartHtml += '</div>';
                });
                chartHtml += '</div>';

                if (data.series.some(function(d) { return d.derivation_type !== "base" || metric.indexOf("projected") === 0; })) {
                    chartHtml += '<div class="chart-legend"><span class="legend-observed">Observed</span> <span class="legend-projected">Projected</span></div>';
                }

                chartContainer.innerHTML = chartHtml;

                // Table
                var thtml = '<table class="data-table"><thead><tr>';
                thtml += '<th>Year</th><th>Value</th><th>YoY Change</th><th>YoY %</th><th>Source</th>';
                thtml += '</tr></thead><tbody>';
                data.series.forEach(function(d) {
                    thtml += '<tr>';
                    thtml += '<td>' + d.year + '</td>';
                    thtml += '<td>' + formatTrendValue(d.value, first.units) + '</td>';
                    thtml += '<td>' + formatTrendValue(d.yoy_change, first.units) + '</td>';
                    thtml += '<td>' + (d.yoy_pct_change != null ? d.yoy_pct_change.toFixed(1) + '%' : 'N/A') + '</td>';
                    thtml += '<td>' + escapeHtml(d.source_release_id) + '</td>';
                    thtml += '</tr>';
                });
                thtml += '</tbody></table>';
                tableContainer.innerHTML = thtml;
                tableContainer.hidden = false;
            })
            .catch(function() {
                chartContainer.setAttribute("aria-busy", "false");
                chartContainer.innerHTML = '<p class="error-message">Failed to load trend data.</p>';
                chartContainer.className = "";
            });
    }

    function formatTrendValue(value, units) {
        if (value == null) return "N/A";
        if (units === "dollars") return formatWage(value);
        if (units === "percent") return formatPercent(value);
        return formatNumber(value);
    }

    document.getElementById("metric-select").addEventListener("change", loadTrend);
    document.getElementById("geo-select").addEventListener("change", loadTrend);
    document.getElementById("mode-select").addEventListener("change", loadTrend);

    loadTrend();
})();
