/* JobClass — Ranked movers page */
"use strict";

(function() {
    var gainersContainer = document.getElementById("gainers-container");
    var losersContainer = document.getElementById("losers-container");
    var yearSelect = document.getElementById("movers-year");
    var yearsLoaded = false;

    function renderMovers(items, container, isGainer) {
        container.setAttribute("aria-busy", "false");
        if (!items || items.length === 0) {
            container.innerHTML = "<p>No data available.</p>";
            container.className = "";
            return;
        }

        var metric = document.getElementById("movers-metric").value;
        var absUnits = (metric === "employment_count") ? "count" : "dollars";

        var html = '<table class="data-table"><thead><tr>';
        html += '<th>Occupation</th><th>YoY Change</th><th>YoY %</th>';
        html += '</tr></thead><tbody>';
        items.forEach(function(m) {
            var sign = m.pct_change >= 0 ? "+" : "";
            var cls = m.pct_change >= 0 ? "positive" : "negative";
            var absSign = m.abs_change != null && m.abs_change >= 0 ? "+" : "";
            var absVal = "N/A";
            if (m.abs_change != null) {
                if (absUnits === "dollars") {
                    absVal = absSign + formatWage(Math.abs(m.abs_change));
                    if (m.abs_change < 0) absVal = "-" + formatWage(Math.abs(m.abs_change));
                } else {
                    absVal = absSign + formatNumber(m.abs_change);
                }
            }
            html += '<tr>';
            html += '<td><a href="/trends/explorer/' + escapeAttr(m.soc_code) + '">' +
                escapeHtml(m.soc_code) + ' ' + escapeHtml(m.title) + '</a></td>';
            html += '<td class="' + cls + '">' + absVal + '</td>';
            html += '<td class="' + cls + '">' + sign + (m.pct_change != null ? m.pct_change.toFixed(1) : 'N/A') + '%</td>';
            html += '</tr>';
        });
        html += '</tbody></table>';
        container.innerHTML = html;
        container.className = "";
    }

    function populateYears(availableYears, selectedYear) {
        if (yearsLoaded) return;
        yearsLoaded = true;
        yearSelect.innerHTML = "";
        availableYears.forEach(function(y) {
            var opt = document.createElement("option");
            opt.value = y;
            opt.textContent = y;
            if (y === selectedYear) opt.selected = true;
            yearSelect.appendChild(opt);
        });
    }

    function loadMovers() {
        var metric = document.getElementById("movers-metric").value;
        var yearParam = yearSelect.value ? "&year=" + yearSelect.value : "";
        gainersContainer.className = "loading";
        losersContainer.className = "loading";
        gainersContainer.setAttribute("aria-busy", "true");
        losersContainer.setAttribute("aria-busy", "true");
        gainersContainer.innerHTML = "Loading...";
        losersContainer.innerHTML = "Loading...";

        fetchWithTimeout("/api/trends/movers?metric=" + encodeURIComponent(metric) + yearParam + "&limit=20")
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.available_years && data.available_years.length > 0) {
                    populateYears(data.available_years, data.year);
                }
                renderMovers(data.gainers, gainersContainer, true);
                renderMovers(data.losers, losersContainer, false);
            })
            .catch(function() {
                gainersContainer.innerHTML = '<p class="error-message">Failed to load data.</p>';
                losersContainer.innerHTML = '<p class="error-message">Failed to load data.</p>';
                gainersContainer.className = "";
                losersContainer.className = "";
            });
    }

    document.getElementById("movers-metric").addEventListener("change", function() {
        yearsLoaded = false;
        loadMovers();
    });
    yearSelect.addEventListener("change", loadMovers);
    loadMovers();
})();
