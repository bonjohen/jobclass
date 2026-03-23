/* JobClass — Landing page */
"use strict";

(function() {
    var FETCH_TIMEOUT_MS = 10000;

    function fetchWithTimeout(url) {
        var controller = new AbortController();
        var timer = setTimeout(function() { controller.abort(); }, FETCH_TIMEOUT_MS);
        return fetch(url, { signal: controller.signal }).finally(function() { clearTimeout(timer); });
    }

    // Load stats
    fetchWithTimeout("/api/stats")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var grid = document.getElementById("stats-grid");
            var html = '';
            html += statCard("Occupations", formatNumber(data.occupation_count));
            html += statCard("Geographies", formatNumber(data.geography_count));
            html += statCard("Skills Tracked", formatNumber(data.skill_count));
            html += statCard("Tasks Tracked", formatNumber(data.task_count));
            grid.innerHTML = html;
        })
        .catch(function() {
            document.getElementById("stats-grid").innerHTML = '<p class="error-message">Failed to load statistics.</p>';
        });

    // Load spotlight
    fetchWithTimeout("/api/occupations/15-1252")
        .then(function(r) { return r.ok ? r.json() : null; })
        .then(function(data) {
            if (!data) return;
            document.getElementById("spotlight").style.display = "block";
            var p = document.createElement("p");
            p.textContent = data.occupation_definition || '';
            var container = document.getElementById("spotlight-content");
            container.innerHTML = '';
            container.appendChild(p);
        })
        .catch(function() {});

    function statCard(label, value) {
        return '<div class="stat-card"><div class="stat-label">' + escapeHtml(label) + '</div><div class="stat-value">' + escapeHtml(value) + '</div></div>';
    }
})();
