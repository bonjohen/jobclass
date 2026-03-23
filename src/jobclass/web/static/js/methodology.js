/* JobClass — Methodology page */
"use strict";

(function() {
    var FETCH_TIMEOUT_MS = 10000;

    function fetchWithTimeout(url) {
        var controller = new AbortController();
        var timer = setTimeout(function() { controller.abort(); }, FETCH_TIMEOUT_MS);
        return fetch(url, { signal: controller.signal }).finally(function() { clearTimeout(timer); });
    }

    // Load versions
    fetchWithTimeout("/api/metadata")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var html = '<table class="data-table"><thead><tr><th>Source</th><th>Version</th></tr></thead><tbody>';
            html += '<tr><td>SOC</td><td>' + escapeHtml(data.soc_version || 'N/A') + '</td></tr>';
            html += '<tr><td>OEWS</td><td>' + escapeHtml(data.oews_release_id || 'N/A') + '</td></tr>';
            html += '<tr><td>O*NET</td><td>' + escapeHtml(data.onet_version || 'N/A') + '</td></tr>';
            html += '<tr><td>Projections</td><td>' + escapeHtml(data.projections_cycle || 'N/A') + '</td></tr>';
            if (data.last_load_timestamp) {
                html += '<tr><td>Last Load</td><td>' + escapeHtml(data.last_load_timestamp) + '</td></tr>';
            }
            html += '</tbody></table>';
            document.getElementById("versions-content").innerHTML = html;
        })
        .catch(function() {
            document.getElementById("versions-content").innerHTML = '<p class="error-message">Version info unavailable.</p>';
        });

    // Load validation status
    fetchWithTimeout("/api/methodology/validation")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var html = '<p><strong>' + data.passed + '/' + data.total_checks + '</strong> checks passed</p>';
            html += '<table class="data-table"><thead><tr><th>Check</th><th>Status</th><th>Detail</th></tr></thead><tbody>';
            data.checks.forEach(function(c) {
                var status = c.passed ? '&#10003;' : '&#10007;';
                var cls = c.passed ? 'check-pass' : 'check-fail';
                html += '<tr><td>' + escapeHtml(c.check) + '</td>';
                html += '<td class="' + cls + '">' + status + '</td>';
                html += '<td>' + escapeHtml(c.detail) + '</td></tr>';
            });
            html += '</tbody></table>';
            document.getElementById("validation-content").innerHTML = html;
        })
        .catch(function() {
            document.getElementById("validation-content").innerHTML = '<p class="error-message">Validation status unavailable.</p>';
        });
})();
