/* JobClass — Ranked movers page */
"use strict";

(function() {
    var gainersContainer = document.getElementById("gainers-container");
    var losersContainer = document.getElementById("losers-container");
    var yearSelect = document.getElementById("movers-year");
    var yearsLoaded = false;

    // Track raw data for sorting
    var gainersData = [];
    var losersData = [];

    function sortData(items, col, asc) {
        return items.slice().sort(function(a, b) {
            var va, vb;
            if (col === "occupation") {
                va = (a.title || "").toLowerCase();
                vb = (b.title || "").toLowerCase();
                return asc ? (va < vb ? -1 : va > vb ? 1 : 0)
                           : (va > vb ? -1 : va < vb ? 1 : 0);
            } else if (col === "abs_change") {
                va = a.abs_change != null ? a.abs_change : -Infinity;
                vb = b.abs_change != null ? b.abs_change : -Infinity;
            } else {
                va = a.pct_change != null ? a.pct_change : -Infinity;
                vb = b.pct_change != null ? b.pct_change : -Infinity;
            }
            return asc ? va - vb : vb - va;
        });
    }

    function attachSort(container, getData) {
        var sortState = { col: null, asc: true };
        container.addEventListener("click", function(e) {
            var th = e.target.closest("th[data-sort]");
            if (!th) return;
            var col = th.getAttribute("data-sort");
            if (sortState.col === col) {
                sortState.asc = !sortState.asc;
            } else {
                sortState.col = col;
                sortState.asc = col === "occupation";  // alpha asc default, numeric desc default
            }
            var sorted = sortData(getData(), col, sortState.asc);
            renderTable(sorted, container, sortState.col, sortState.asc);
        });
    }

    function renderTable(items, container, sortCol, sortAsc) {
        var metric = document.getElementById("movers-metric").value;
        var absUnits = (metric === "employment_count") ? "count" : "dollars";

        function arrow(col) {
            if (col !== sortCol) return ' <span class="sort-arrow">⇅</span>';
            return sortAsc ? ' <span class="sort-arrow sort-active">▲</span>'
                           : ' <span class="sort-arrow sort-active">▼</span>';
        }

        var html = '<table class="data-table sortable-table"><thead><tr>';
        html += '<th data-sort="occupation" class="sortable-th">Occupation' + arrow("occupation") + '</th>';
        html += '<th data-sort="abs_change" class="sortable-th">YoY Change' + arrow("abs_change") + '</th>';
        html += '<th data-sort="pct_change" class="sortable-th">YoY %' + arrow("pct_change") + '</th>';
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
    }

    function renderMovers(items, container, isGainer) {
        container.setAttribute("aria-busy", "false");
        if (!items || items.length === 0) {
            container.innerHTML = "<p>No data available.</p>";
            container.className = "";
            return;
        }

        if (isGainer) gainersData = items;
        else losersData = items;

        renderTable(items, container, null, true);
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

    // Attach sortable column handlers
    attachSort(gainersContainer, function() { return gainersData; });
    attachSort(losersContainer, function() { return losersData; });

    loadMovers();
})();
