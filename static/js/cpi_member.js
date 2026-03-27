/* JobClass — CPI member detail page */
"use strict";

(function() {
    var page = document.getElementById("cpi-member-page");
    if (!page) return;
    var code = page.getAttribute("data-member-code");
    if (!code) return;

    var loadingEl = document.getElementById("member-loading");
    var contentEl = document.getElementById("member-content");

    // Fetch member detail
    fetchWithTimeout("/api/cpi/members/" + encodeURIComponent(code))
        .then(function(r) {
            if (!r.ok) throw new Error("not found");
            return r.json();
        })
        .then(function(m) {
            loadingEl.style.display = "none";
            contentEl.style.display = "block";

            // Header
            document.getElementById("member-title").textContent = m.title;
            document.getElementById("member-code-badge").textContent = m.member_code;
            document.getElementById("member-level-badge").textContent = m.hierarchy_level || "—";
            document.getElementById("member-role-badge").textContent = m.semantic_role;
            if (m.semantic_role === "external_overlay") {
                var badge = document.createElement("span");
                badge.className = "cpi-overlay-badge";
                badge.textContent = "External Overlay";
                document.querySelector(".cpi-member-meta").appendChild(badge);
            }

            // Breadcrumb
            buildBreadcrumb(m.ancestors, m.member_code, m.title);

            // Load children, siblings, relations, variants, importance, avg prices in parallel
            loadChildren(m.member_code);
            loadSiblings(m.member_code);
            loadRelations(m.member_code);
            loadVariants(m.member_code);
            loadSeries(m.member_code);
            loadImportance(m.member_code);
            if (m.has_average_price) loadAveragePrices(m.member_code);
            loadRevisions(m.member_code);
            showLaborContext(m.member_code);
        })
        .catch(function() {
            loadingEl.textContent = "CPI member not found.";
        });

    // --- Breadcrumb ---
    function buildBreadcrumb(ancestors, currentCode, currentTitle) {
        var nav = document.getElementById("cpi-breadcrumb");
        if (!nav) return;
        var html = '<a href="/cpi">CPI</a>';
        if (ancestors && ancestors.length > 0) {
            ancestors.forEach(function(a) {
                html += ' <span class="breadcrumb-sep">\u203A</span> ';
                html += '<a href="/cpi/member/' + escapeAttr(a.member_code) + '">';
                html += escapeHtml(a.title) + '</a>';
            });
        }
        html += ' <span class="breadcrumb-sep">\u203A</span> ';
        html += '<span class="breadcrumb-current">' + escapeHtml(currentTitle) + '</span>';
        nav.innerHTML = html;
    }

    // --- Children ---
    function loadChildren(memberCode) {
        fetchWithTimeout("/api/cpi/members/" + encodeURIComponent(memberCode) + "/children")
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.children || data.children.length === 0) return;
                var section = document.getElementById("children-section");
                section.style.display = "block";
                var list = document.getElementById("children-list");
                var html = "";
                data.children.forEach(function(c) {
                    html += '<li class="cpi-member-item">';
                    html += '<a href="/cpi/member/' + escapeAttr(c.member_code) + '">';
                    html += '<span class="cpi-code">' + escapeHtml(c.member_code) + '</span> ';
                    html += escapeHtml(c.title);
                    html += '</a>';
                    if (c.semantic_role && c.semantic_role !== "hierarchy_node") {
                        html += ' <span class="cpi-role-badge">' + escapeHtml(c.semantic_role) + '</span>';
                    }
                    html += '</li>';
                });
                list.innerHTML = html;
            })
            .catch(function() {});
    }

    // --- Siblings ---
    function loadSiblings(memberCode) {
        fetchWithTimeout("/api/cpi/members/" + encodeURIComponent(memberCode) + "/siblings")
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.siblings || data.siblings.length === 0) return;
                var section = document.getElementById("siblings-section");
                section.style.display = "block";
                var list = document.getElementById("siblings-list");
                var html = "";
                data.siblings.forEach(function(s) {
                    html += '<li class="cpi-member-item">';
                    html += '<a href="/cpi/member/' + escapeAttr(s.member_code) + '">';
                    html += '<span class="cpi-code">' + escapeHtml(s.member_code) + '</span> ';
                    html += escapeHtml(s.title);
                    html += '</a>';
                    html += '</li>';
                });
                list.innerHTML = html;
            })
            .catch(function() {});
    }

    // --- Relations ---
    function loadRelations(memberCode) {
        fetchWithTimeout("/api/cpi/members/" + encodeURIComponent(memberCode) + "/relations")
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.relations || data.relations.length === 0) return;
                var section = document.getElementById("relations-section");
                section.style.display = "block";
                var container = document.getElementById("relations-list");
                var html = '<ul class="cpi-relations-list">';
                data.relations.forEach(function(rel) {
                    var isOverlay = rel.relation_type === "cleveland_fed" || rel.relation_type === "fred_mirror";
                    html += '<li class="cpi-relation-item' + (isOverlay ? ' cpi-overlay-row' : '') + '">';
                    html += '<span class="cpi-relation-type">' + escapeHtml(rel.relation_type) + '</span> ';
                    html += '<a href="/cpi/member/' + escapeAttr(rel.member_code) + '">';
                    html += '<span class="cpi-code">' + escapeHtml(rel.member_code) + '</span> ';
                    html += escapeHtml(rel.title);
                    html += '</a>';
                    if (isOverlay) {
                        html += ' <span class="cpi-overlay-badge">External</span>';
                    }
                    if (rel.description) {
                        html += ' <span class="cpi-relation-desc">— ' + escapeHtml(rel.description) + '</span>';
                    }
                    html += '</li>';
                });
                html += '</ul>';
                container.innerHTML = html;
            })
            .catch(function() {});
    }

    // --- Area variants ---
    function loadVariants(memberCode) {
        fetchWithTimeout("/api/cpi/members/" + encodeURIComponent(memberCode) + "/variants")
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.variants || data.variants.length === 0) return;
                var section = document.getElementById("areas-section");
                section.style.display = "block";
                var tbody = document.getElementById("areas-tbody");
                var html = "";
                data.variants.forEach(function(v) {
                    html += '<tr>';
                    html += '<td class="cpi-code">' + escapeHtml(v.area_code) + '</td>';
                    html += '<td>' + escapeHtml(v.area_title) + '</td>';
                    html += '<td>' + escapeHtml(v.index_family) + '</td>';
                    html += '<td>' + (v.seasonal_adjustment === 'S' ? 'Seasonally adjusted' : 'Not adjusted') + '</td>';
                    html += '<td>' + escapeHtml(v.publication_frequency) + '</td>';
                    html += '</tr>';
                });
                tbody.innerHTML = html;
            })
            .catch(function() {});
    }

    // --- Time-series chart ---
    function loadSeries(memberCode) {
        var family = document.getElementById("variant-family").value;
        var sa = document.getElementById("variant-sa").value;
        var chartContainer = document.getElementById("series-chart");
        chartContainer.innerHTML = '<p class="loading">Loading series data&hellip;</p>';

        var url = "/api/cpi/members/" + encodeURIComponent(memberCode)
            + "/series?area_code=0000&index_family=" + encodeURIComponent(family)
            + "&seasonal_adjustment=" + encodeURIComponent(sa);

        fetchWithTimeout(url)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.series || data.series.length === 0) {
                    chartContainer.innerHTML = '<p class="no-data-message">No series data available for this variant.</p>';
                    return;
                }
                renderSeriesChart(data.series, chartContainer);
            })
            .catch(function() {
                chartContainer.innerHTML = '<p class="no-data-message">Could not load series data.</p>';
            });
    }

    // --- Relative importance ---
    function loadImportance(memberCode) {
        fetchWithTimeout("/api/cpi/members/" + encodeURIComponent(memberCode) + "/importance?area_code=0000")
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.entries || data.entries.length === 0) return;
                var section = document.getElementById("importance-section");
                section.style.display = "block";

                // Build chart
                var chartContainer = document.getElementById("importance-chart");
                renderImportanceChart(data.entries, chartContainer);

                // Build table
                var table = document.getElementById("importance-table");
                table.style.display = "table";
                var tbody = document.getElementById("importance-tbody");
                var html = "";
                data.entries.forEach(function(e) {
                    html += '<tr><td>' + escapeHtml(e.reference_period) + '</td>';
                    html += '<td>' + e.relative_importance.toFixed(3) + '</td></tr>';
                });
                tbody.innerHTML = html;
            })
            .catch(function() {});
    }

    function renderImportanceChart(entries, container) {
        if (entries.length < 2) {
            container.innerHTML = '<p>Relative importance: <strong>' + entries[0].relative_importance.toFixed(3) + '</strong> (' + escapeHtml(entries[0].reference_period) + ')</p>';
            return;
        }
        var W = 700, H = 200, PAD_L = 60, PAD_R = 20, PAD_T = 15, PAD_B = 35;
        var plotW = W - PAD_L - PAD_R;
        var plotH = H - PAD_T - PAD_B;

        var vals = entries.map(function(e) { return e.relative_importance; });
        var minV = Math.min.apply(null, vals);
        var maxV = Math.max.apply(null, vals);
        var range = maxV - minV || 1;
        minV -= range * 0.1;
        maxV += range * 0.1;
        range = maxV - minV;

        function xPos(i) { return PAD_L + (i / (entries.length - 1)) * plotW; }
        function yPos(v) { return PAD_T + plotH - ((v - minV) / range) * plotH; }

        var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" class="cpi-series-svg" role="img" aria-label="Relative importance history">';

        // Gridlines
        for (var t = 0; t <= 4; t++) {
            var v = minV + (range * t / 4);
            var y = yPos(v);
            svg += '<line x1="' + PAD_L + '" y1="' + y + '" x2="' + (W - PAD_R) + '" y2="' + y + '" class="chart-grid"/>';
            svg += '<text x="' + (PAD_L - 8) + '" y="' + (y + 4) + '" class="chart-label" text-anchor="end">' + v.toFixed(2) + '</text>';
        }

        // X labels
        var step = Math.max(1, Math.floor(entries.length / 6));
        for (var i = 0; i < entries.length; i += step) {
            svg += '<text x="' + xPos(i) + '" y="' + (H - 6) + '" class="chart-label" text-anchor="middle">' + escapeHtml(entries[i].reference_period) + '</text>';
        }

        // Line
        var pts = entries.map(function(e, idx) { return xPos(idx) + ',' + yPos(e.relative_importance); });
        svg += '<polyline points="' + pts.join(' ') + '" fill="none" stroke="#805ad5" stroke-width="2"/>';

        // Dots
        entries.forEach(function(e, idx) {
            svg += '<circle cx="' + xPos(idx) + '" cy="' + yPos(e.relative_importance) + '" r="3" fill="#805ad5">';
            svg += '<title>' + escapeHtml(e.reference_period) + ': ' + e.relative_importance.toFixed(3) + '</title>';
            svg += '</circle>';
        });

        svg += '</svg>';
        container.innerHTML = svg;
    }

    // --- Average prices ---
    function loadAveragePrices(memberCode) {
        fetchWithTimeout("/api/cpi/members/" + encodeURIComponent(memberCode) + "/average-prices?area_code=0000")
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.entries || data.entries.length === 0) return;
                var section = document.getElementById("avg-price-section");
                section.style.display = "block";

                var chartContainer = document.getElementById("avg-price-chart");
                renderAvgPriceChart(data.entries, chartContainer);

                var table = document.getElementById("avg-price-table");
                table.style.display = "table";
                var tbody = document.getElementById("avg-price-tbody");
                var html = "";
                data.entries.forEach(function(e) {
                    html += '<tr><td>' + e.year + '</td>';
                    html += '<td>$' + e.average_price.toFixed(3) + '</td></tr>';
                });
                tbody.innerHTML = html;
            })
            .catch(function() {});
    }

    function renderAvgPriceChart(entries, container) {
        if (entries.length < 2) {
            container.innerHTML = '<p>Average price: <strong>$' + entries[0].average_price.toFixed(3) + '</strong> (' + entries[0].year + ')</p>';
            return;
        }
        var W = 700, H = 200, PAD_L = 60, PAD_R = 20, PAD_T = 15, PAD_B = 35;
        var plotW = W - PAD_L - PAD_R, plotH = H - PAD_T - PAD_B;
        var vals = entries.map(function(e) { return e.average_price; });
        var minV = Math.min.apply(null, vals), maxV = Math.max.apply(null, vals);
        var range = maxV - minV || 1;
        minV -= range * 0.1; maxV += range * 0.1; range = maxV - minV;
        var years = entries.map(function(e) { return e.year; });
        var minY = Math.min.apply(null, years), maxY = Math.max.apply(null, years);
        var yearRange = maxY - minY || 1;

        function xPos(yr) { return PAD_L + ((yr - minY) / yearRange) * plotW; }
        function yPos(v) { return PAD_T + plotH - ((v - minV) / range) * plotH; }

        var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" class="cpi-series-svg" role="img" aria-label="Average price history">';
        for (var t = 0; t <= 4; t++) {
            var v = minV + (range * t / 4);
            var y = yPos(v);
            svg += '<line x1="' + PAD_L + '" y1="' + y + '" x2="' + (W - PAD_R) + '" y2="' + y + '" class="chart-grid"/>';
            svg += '<text x="' + (PAD_L - 8) + '" y="' + (y + 4) + '" class="chart-label" text-anchor="end">$' + v.toFixed(2) + '</text>';
        }
        var xStep = Math.max(1, Math.floor(yearRange / 8));
        for (var yr = minY; yr <= maxY; yr += xStep) {
            svg += '<text x="' + xPos(yr) + '" y="' + (H - 6) + '" class="chart-label" text-anchor="middle">' + yr + '</text>';
        }
        var pts = entries.map(function(e) { return xPos(e.year) + ',' + yPos(e.average_price); });
        svg += '<polyline points="' + pts.join(' ') + '" fill="none" stroke="#38a169" stroke-width="2"/>';
        entries.forEach(function(e) {
            svg += '<circle cx="' + xPos(e.year) + '" cy="' + yPos(e.average_price) + '" r="3" fill="#38a169">';
            svg += '<title>' + e.year + ': $' + e.average_price.toFixed(3) + '</title>';
            svg += '</circle>';
        });
        svg += '</svg>';
        container.innerHTML = svg;
    }

    // --- Labor domain context ---
    function showLaborContext(memberCode) {
        // SA0 (All Items CPI-U) is the deflator for real-wage metrics
        if (memberCode !== "SA0") return;
        var section = document.getElementById("labor-context-section");
        if (!section) return;
        section.style.display = "block";
        var content = document.getElementById("labor-context-content");
        content.innerHTML =
            '<p><strong>CPI-U All Items</strong> is the deflator for real-wage metrics in the labor domain.</p>' +
            '<p>Base year: <strong>2023</strong>. Formula: <code>real_wage = nominal &times; CPI<sub>2023</sub> / CPI<sub>year</sub></code></p>' +
            '<p>Affected metrics: Real Mean Annual Wage, Real Median Annual Wage.</p>' +
            '<p>Browse <a href="/trends">occupation trends</a> to see real-wage time series using this deflator.</p>';
    }

    // --- Revision vintages ---
    function loadRevisions(memberCode) {
        fetchWithTimeout("/api/cpi/members/" + encodeURIComponent(memberCode) + "/revisions?area_code=0000")
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.entries || data.entries.length === 0) return;
                var section = document.getElementById("revisions-section");
                section.style.display = "block";

                var chartContainer = document.getElementById("revisions-chart");
                renderRevisionsChart(data.entries, chartContainer);

                var table = document.getElementById("revisions-table");
                table.style.display = "table";
                var tbody = document.getElementById("revisions-tbody");
                var html = "";
                data.entries.forEach(function(e) {
                    var cls = e.is_preliminary ? "cpi-preliminary-row" : "cpi-final-row";
                    html += '<tr class="' + cls + '">';
                    html += '<td>' + e.year + '</td>';
                    html += '<td>' + escapeHtml(e.vintage_label) + '</td>';
                    html += '<td>' + e.index_value.toFixed(1) + '</td>';
                    html += '<td>' + (e.is_preliminary ? '<span class="cpi-preliminary-label">Preliminary</span>' : '<span class="cpi-final-label">Final</span>') + '</td>';
                    html += '</tr>';
                });
                tbody.innerHTML = html;
            })
            .catch(function() {});
    }

    function renderRevisionsChart(entries, container) {
        // Group by year, show preliminary vs final side-by-side
        var byYear = {};
        entries.forEach(function(e) {
            if (!byYear[e.year]) byYear[e.year] = [];
            byYear[e.year].push(e);
        });
        var years = Object.keys(byYear).sort();
        if (years.length === 0) { container.innerHTML = ""; return; }

        var W = 700, H = 220, PAD_L = 60, PAD_R = 20, PAD_T = 15, PAD_B = 35;
        var plotW = W - PAD_L - PAD_R, plotH = H - PAD_T - PAD_B;

        var allVals = entries.map(function(e) { return e.index_value; });
        var minV = Math.min.apply(null, allVals), maxV = Math.max.apply(null, allVals);
        var range = maxV - minV || 1;
        minV -= range * 0.1; maxV += range * 0.1; range = maxV - minV;

        var barW = Math.min(30, plotW / (years.length * 3));
        function xCenter(i) { return PAD_L + (i + 0.5) / years.length * plotW; }
        function yPos(v) { return PAD_T + plotH - ((v - minV) / range) * plotH; }

        var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" class="cpi-series-svg" role="img" aria-label="Revision vintage comparison">';

        // Gridlines
        for (var t = 0; t <= 4; t++) {
            var v = minV + (range * t / 4);
            var y = yPos(v);
            svg += '<line x1="' + PAD_L + '" y1="' + y + '" x2="' + (W - PAD_R) + '" y2="' + y + '" class="chart-grid"/>';
            svg += '<text x="' + (PAD_L - 8) + '" y="' + (y + 4) + '" class="chart-label" text-anchor="end">' + v.toFixed(1) + '</text>';
        }

        years.forEach(function(yr, i) {
            var x = xCenter(i);
            svg += '<text x="' + x + '" y="' + (H - 6) + '" class="chart-label" text-anchor="middle">' + yr + '</text>';
            var vintages = byYear[yr];
            vintages.forEach(function(e, j) {
                var bx = x + (j - vintages.length / 2) * (barW + 2);
                var by = yPos(e.index_value);
                var bh = PAD_T + plotH - by;
                var color = e.is_preliminary ? "#e2a832" : "#2b6cb0";
                svg += '<rect x="' + (bx - barW / 2) + '" y="' + by + '" width="' + barW + '" height="' + bh + '" fill="' + color + '" opacity="0.8">';
                svg += '<title>' + yr + ' ' + escapeHtml(e.vintage_label) + ': ' + e.index_value.toFixed(1) + (e.is_preliminary ? ' (preliminary)' : ' (final)') + '</title>';
                svg += '</rect>';
            });
        });

        svg += '</svg>';
        var legend = '<div class="cpi-chart-legend">';
        legend += '<span class="legend-item"><span class="legend-swatch" style="background:#e2a832"></span> Preliminary</span>';
        legend += '<span class="legend-item"><span class="legend-swatch" style="background:#2b6cb0"></span> Final</span>';
        legend += '</div>';
        container.innerHTML = svg + legend;
    }

    // Variant selector change handlers
    document.getElementById("variant-family").addEventListener("change", function() { loadSeries(code); });
    document.getElementById("variant-sa").addEventListener("change", function() { loadSeries(code); });

    // --- Simple SVG line chart ---
    function renderSeriesChart(series, container) {
        var W = 700, H = 280, PAD_L = 60, PAD_R = 20, PAD_T = 20, PAD_B = 40;
        var plotW = W - PAD_L - PAD_R;
        var plotH = H - PAD_T - PAD_B;

        var vals = series.map(function(s) { return s.value; });
        var minV = Math.min.apply(null, vals);
        var maxV = Math.max.apply(null, vals);
        var range = maxV - minV || 1;
        // Add 5% padding
        minV -= range * 0.05;
        maxV += range * 0.05;
        range = maxV - minV;

        var years = series.map(function(s) { return s.year; });
        var minY = Math.min.apply(null, years);
        var maxY = Math.max.apply(null, years);
        var yearRange = maxY - minY || 1;

        function xPos(year) { return PAD_L + ((year - minY) / yearRange) * plotW; }
        function yPos(val) { return PAD_T + plotH - ((val - minV) / range) * plotH; }

        var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" class="cpi-series-svg" role="img" aria-label="CPI index time series">';

        // Y-axis gridlines and labels
        var yTicks = 5;
        for (var i = 0; i <= yTicks; i++) {
            var v = minV + (range * i / yTicks);
            var y = yPos(v);
            svg += '<line x1="' + PAD_L + '" y1="' + y + '" x2="' + (W - PAD_R) + '" y2="' + y + '" class="chart-grid"/>';
            svg += '<text x="' + (PAD_L - 8) + '" y="' + (y + 4) + '" class="chart-label" text-anchor="end">' + v.toFixed(1) + '</text>';
        }

        // X-axis labels
        var xStep = Math.max(1, Math.floor(yearRange / 8));
        for (var yr = minY; yr <= maxY; yr += xStep) {
            svg += '<text x="' + xPos(yr) + '" y="' + (H - 8) + '" class="chart-label" text-anchor="middle">' + yr + '</text>';
        }

        // Data line
        var points = series.map(function(s) { return xPos(s.year) + ',' + yPos(s.value); });
        svg += '<polyline points="' + points.join(' ') + '" class="chart-line" fill="none"/>';

        // Data dots
        series.forEach(function(s) {
            svg += '<circle cx="' + xPos(s.year) + '" cy="' + yPos(s.value) + '" r="3" class="chart-dot">';
            svg += '<title>' + s.year + ': ' + s.value.toFixed(1) + '</title>';
            svg += '</circle>';
        });

        // YoY change overlay
        if (series.length >= 2) {
            var yoyPoints = [];
            for (var j = 1; j < series.length; j++) {
                var pct = ((series[j].value - series[j-1].value) / series[j-1].value) * 100;
                yoyPoints.push({ year: series[j].year, pct: pct });
            }
            // Scale YoY to same plot area
            var yoyVals = yoyPoints.map(function(p) { return p.pct; });
            var yoyMin = Math.min.apply(null, yoyVals) - 0.5;
            var yoyMax = Math.max.apply(null, yoyVals) + 0.5;
            var yoyRange = yoyMax - yoyMin || 1;

            var yoyLine = yoyPoints.map(function(p) {
                var x = xPos(p.year);
                var y2 = PAD_T + plotH - ((p.pct - yoyMin) / yoyRange) * plotH;
                return x + ',' + y2;
            });
            svg += '<polyline points="' + yoyLine.join(' ') + '" class="chart-line-yoy" fill="none"/>';

            // YoY right-axis labels
            for (var k = 0; k <= 4; k++) {
                var yv = yoyMin + (yoyRange * k / 4);
                var yy = PAD_T + plotH - ((yv - yoyMin) / yoyRange) * plotH;
                svg += '<text x="' + (W - PAD_R + 4) + '" y="' + (yy + 4) + '" class="chart-label-yoy" text-anchor="start">'
                    + yv.toFixed(1) + '%</text>';
            }
        }

        svg += '</svg>';

        var legend = '<div class="cpi-chart-legend">';
        legend += '<span class="legend-item"><span class="legend-swatch legend-index"></span> Index value</span>';
        legend += '<span class="legend-item"><span class="legend-swatch legend-yoy"></span> YoY % change</span>';
        legend += '</div>';

        container.innerHTML = svg + legend;
    }
})();
