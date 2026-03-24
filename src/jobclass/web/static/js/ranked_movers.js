/* JobClass — Ranked movers page */
"use strict";

(function() {
    var FETCH_TIMEOUT_MS = 10000;
    var gainersContainer = document.getElementById("gainers-container");
    var losersContainer = document.getElementById("losers-container");

    function fetchWithTimeout(url) {
        var controller = new AbortController();
        var timer = setTimeout(function() { controller.abort(); }, FETCH_TIMEOUT_MS);
        return fetch(url, { signal: controller.signal }).finally(function() { clearTimeout(timer); });
    }

    function renderMovers(items, container, isGainer) {
        container.setAttribute("aria-busy", "false");
        if (!items || items.length === 0) {
            container.innerHTML = "<p>No data available.</p>";
            container.className = "";
            return;
        }

        var html = '<table class="data-table"><thead><tr>';
        html += '<th>Occupation</th><th>YoY % Change</th><th>Year</th>';
        html += '</tr></thead><tbody>';
        items.forEach(function(m) {
            var sign = m.pct_change >= 0 ? "+" : "";
            var cls = m.pct_change >= 0 ? "positive" : "negative";
            html += '<tr>';
            html += '<td><a href="/trends/explorer/' + escapeAttr(m.soc_code) + '">' +
                escapeHtml(m.soc_code) + ' ' + escapeHtml(m.title) + '</a></td>';
            html += '<td class="' + cls + '">' + sign + (m.pct_change != null ? m.pct_change.toFixed(1) : 'N/A') + '%</td>';
            html += '<td>' + (m.year || 'N/A') + '</td>';
            html += '</tr>';
        });
        html += '</tbody></table>';
        container.innerHTML = html;
        container.className = "";
    }

    function loadMovers() {
        var metric = document.getElementById("movers-metric").value;
        gainersContainer.className = "loading";
        losersContainer.className = "loading";
        gainersContainer.setAttribute("aria-busy", "true");
        losersContainer.setAttribute("aria-busy", "true");
        gainersContainer.innerHTML = "Loading...";
        losersContainer.innerHTML = "Loading...";

        fetchWithTimeout("/api/trends/movers?metric=" + encodeURIComponent(metric) + "&limit=20")
            .then(function(r) { return r.json(); })
            .then(function(data) {
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

    document.getElementById("movers-metric").addEventListener("change", loadMovers);
    loadMovers();
})();
