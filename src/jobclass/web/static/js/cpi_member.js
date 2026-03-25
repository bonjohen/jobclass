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

            // Breadcrumb
            buildBreadcrumb(m.ancestors, m.member_code, m.title);

            // Load children, siblings, relations, variants in parallel
            loadChildren(m.member_code);
            loadSiblings(m.member_code);
            loadRelations(m.member_code);
            loadVariants(m.member_code);
            loadSeries(m.member_code);
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
                    html += '<li class="cpi-relation-item">';
                    html += '<span class="cpi-relation-type">' + escapeHtml(rel.relation_type) + '</span> ';
                    html += '<a href="/cpi/member/' + escapeAttr(rel.member_code) + '">';
                    html += '<span class="cpi-code">' + escapeHtml(rel.member_code) + '</span> ';
                    html += escapeHtml(rel.title);
                    html += '</a>';
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
