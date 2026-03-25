/* JobClass — CPI landing page */
"use strict";

(function() {
    // --- Headline stats ---
    fetchWithTimeout("/api/cpi/search?q=a&limit=1")
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var el = document.getElementById("cpi-member-count");
            if (el && d.total != null) el.textContent = formatNumber(d.total);
        })
        .catch(function() {});

    fetchWithTimeout("/api/cpi/areas/0000")
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var el = document.getElementById("cpi-series-count");
            if (el && d.member_count != null) el.textContent = formatNumber(d.member_count);
        })
        .catch(function() {});

    // Area count: fetch national area and infer from it (simple approach)
    fetchWithTimeout("/api/cpi/areas/0000/members")
        .then(function(r) { return r.json(); })
        .then(function() {
            // We don't have an area list endpoint yet; use a known count placeholder
            var el = document.getElementById("cpi-area-count");
            if (el) el.textContent = "\u2014";
        })
        .catch(function() {});

    // --- Member search ---
    var searchInput = document.getElementById("cpi-member-search");
    var searchResults = document.getElementById("cpi-member-results");
    if (searchInput && searchResults) {
        var timer = null;
        searchInput.addEventListener("input", function() {
            clearTimeout(timer);
            var q = searchInput.value.trim();
            if (q.length < 2) { searchResults.innerHTML = ""; return; }
            timer = setTimeout(function() {
                fetchWithTimeout("/api/cpi/search?q=" + encodeURIComponent(q) + "&limit=10")
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (!data.results || data.results.length === 0) {
                            searchResults.innerHTML = '<div class="search-item">No results</div>';
                            return;
                        }
                        var html = "";
                        data.results.forEach(function(m) {
                            html += '<a class="search-item cpi-search-item" href="/cpi/member/' + encodeURIComponent(m.member_code) + '">';
                            html += '<span class="cpi-code">' + escapeHtml(m.member_code) + '</span> ';
                            html += escapeHtml(m.title);
                            if (m.semantic_role && m.semantic_role !== "hierarchy_node") {
                                html += ' <span class="cpi-role-badge">' + escapeHtml(m.semantic_role) + '</span>';
                            }
                            html += '</a>';
                        });
                        searchResults.innerHTML = html;
                    })
                    .catch(function() { searchResults.innerHTML = ""; });
            }, 250);
        });
    }

    // --- Hierarchy tree (top-level children of SA0) ---
    fetchWithTimeout("/api/cpi/members/SA0/children")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var container = document.getElementById("cpi-hierarchy-tree");
            if (!container) return;
            if (!data.children || data.children.length === 0) {
                container.innerHTML = '<p class="no-data-message">No hierarchy data available.</p>';
                return;
            }
            var html = '<ul class="cpi-tree-list">';
            data.children.forEach(function(c) {
                html += '<li class="cpi-tree-item">';
                html += '<span class="cpi-code">' + escapeHtml(c.member_code) + '</span> ';
                html += '<a href="/cpi/member/' + encodeURIComponent(c.member_code) + '" class="cpi-tree-link">';
                html += escapeHtml(c.title) + '</a>';
                html += '</li>';
            });
            html += '</ul>';
            container.innerHTML = html;
        })
        .catch(function() {
            var container = document.getElementById("cpi-hierarchy-tree");
            if (container) container.innerHTML = '<p class="no-data-message">Could not load hierarchy.</p>';
        });

    // --- Cross-cutting aggregates ---
    var crossCodes = ["SA0L1E", "SA0L1", "SA0E", "SAE", "SAC", "SAS", "SA0R"];
    Promise.all(crossCodes.map(function(code) {
        return fetchWithTimeout("/api/cpi/members/" + code)
            .then(function(r) { return r.ok ? r.json() : null; })
            .catch(function() { return null; });
    })).then(function(results) {
        var container = document.getElementById("cpi-cross-cutting");
        if (!container) return;
        var items = results.filter(Boolean);
        if (items.length === 0) {
            container.innerHTML = '<p class="no-data-message">No cross-cutting data available.</p>';
            return;
        }
        var html = '<ul class="cpi-cross-items">';
        items.forEach(function(m) {
            html += '<li>';
            html += '<a href="/cpi/member/' + encodeURIComponent(m.member_code) + '" class="cpi-cross-link">';
            html += '<span class="cpi-code">' + escapeHtml(m.member_code) + '</span> ';
            html += escapeHtml(m.title);
            html += '</a>';
            html += '</li>';
        });
        html += '</ul>';
        container.innerHTML = html;
    });

    // --- Area browser ---
    var areaBtn = document.getElementById("cpi-area-btn");
    var areaList = document.getElementById("cpi-area-list");
    if (areaBtn && areaList) {
        areaBtn.addEventListener("click", function() {
            if (areaList.style.display === "none") {
                areaList.style.display = "block";
                areaBtn.textContent = "Hide Areas";
                if (!areaList.dataset.loaded) {
                    fetchWithTimeout("/api/cpi/areas/0000")
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            areaList.dataset.loaded = "1";
                            var html = '<div class="cpi-area-detail">';
                            html += '<strong>' + escapeHtml(data.area_title) + '</strong>';
                            html += ' (' + escapeHtml(data.area_type) + ')';
                            html += ' &mdash; ' + formatNumber(data.member_count) + ' published members';
                            html += '</div>';
                            areaList.innerHTML = html;
                        })
                        .catch(function() {
                            areaList.innerHTML = '<p class="no-data-message">Could not load area data.</p>';
                        });
                }
            } else {
                areaList.style.display = "none";
                areaBtn.textContent = "Browse Areas";
            }
        });
    }

})();
