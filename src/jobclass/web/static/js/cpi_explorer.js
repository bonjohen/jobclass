/* JobClass — CPI Weighted Hierarchy Explorer (icicle chart) */
"use strict";

(function() {
    var page = document.getElementById("cpi-explorer-page");
    if (!page) return;

    var vizEl = document.getElementById("explorer-viz");
    var lensEl = document.getElementById("explorer-lens");
    var pathEl = document.getElementById("explorer-path");
    var legendEl = document.getElementById("explorer-legend");
    var colorSelect = document.getElementById("explorer-color-mode");
    var depthSelect = document.getElementById("explorer-depth");
    var resetBtn = document.getElementById("explorer-reset");

    var ROOT_CODE = "SA0";
    var currentRoot = ROOT_CODE;
    var drillStack = [];  // stack of parent codes for back-navigation
    var treeCache = {};   // code → tree data
    var selectedNode = null;

    // --- Color scales ---
    var COLORS = {
        importance: function(val, max) {
            if (val == null || max === 0) return "#e2e8f0";
            var t = Math.min(val / (max || 1), 1);
            // Light blue → dark blue
            var r = Math.round(190 - t * 147);
            var g = Math.round(227 - t * 119);
            var b = Math.round(248 - t * 72);
            return "rgb(" + r + "," + g + "," + b + ")";
        },
        change: function(pct) {
            if (pct == null) return "#e2e8f0";
            // Green for positive, red for negative, gray for zero
            if (pct > 0) {
                var t = Math.min(pct / 10, 1);
                return "rgb(" + Math.round(198 - t * 148) + "," + Math.round(246 - t * 50) + "," + Math.round(213 - t * 100) + ")";
            }
            if (pct < 0) {
                var t2 = Math.min(Math.abs(pct) / 10, 1);
                return "rgb(" + Math.round(254 - t2 * 25) + "," + Math.round(215 - t2 * 153) + "," + Math.round(215 - t2 * 153) + ")";
            }
            return "#e2e8f0";
        }
    };

    // --- Fetch tree data ---
    function loadTree(rootCode, depth, callback) {
        var cacheKey = rootCode + ":" + depth;
        if (treeCache[cacheKey]) {
            callback(treeCache[cacheKey]);
            return;
        }
        var url = "/api/cpi/explorer/tree?root=" + encodeURIComponent(rootCode)
            + "&max_depth=" + depth;
        fetchWithTimeout(url)
            .then(function(r) {
                if (!r.ok) throw new Error("failed");
                return r.json();
            })
            .then(function(data) {
                treeCache[cacheKey] = data;
                callback(data);
            })
            .catch(function() {
                vizEl.innerHTML = '<p class="no-data-message">Could not load CPI hierarchy data.</p>';
            });
    }

    // --- Render icicle chart as SVG ---
    function renderIcicle(tree) {
        var colorMode = colorSelect.value;
        var W = 900, H = 420;
        var BAND_H = H / (parseInt(depthSelect.value, 10) + 1);

        // Flatten tree into rows by depth level
        var levels = [];
        function flatten(node, depth, x0, x1) {
            if (!levels[depth]) levels[depth] = [];
            var entry = {
                code: node.member_code,
                title: node.title,
                level: node.hierarchy_level,
                ri: node.relative_importance,
                x0: x0,
                x1: x1,
                depth: depth,
                children: node.children || [],
                node: node
            };
            levels[depth].push(entry);

            // Distribute children proportionally by importance
            var children = node.children || [];
            if (children.length === 0) return;

            var totalRI = 0;
            children.forEach(function(c) { totalRI += (c.relative_importance || 0.01); });
            if (totalRI === 0) totalRI = children.length * 0.01;

            var cx = x0;
            children.forEach(function(c) {
                var share = (c.relative_importance || 0.01) / totalRI;
                var cw = (x1 - x0) * share;
                flatten(c, depth + 1, cx, cx + cw);
                cx += cw;
            });
        }
        flatten(tree, 0, 0, W);

        // Find max importance for color scaling
        var maxRI = 0;
        levels.forEach(function(lv) {
            lv.forEach(function(e) {
                if (e.ri != null && e.ri > maxRI) maxRI = e.ri;
            });
        });

        // Build SVG
        var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" class="cpi-icicle-svg" role="img" aria-label="CPI weighted hierarchy">';

        levels.forEach(function(lv, depth) {
            var y = depth * BAND_H;
            lv.forEach(function(e) {
                var bw = e.x1 - e.x0;
                if (bw < 0.5) return; // skip tiny slivers

                var fill;
                if (colorMode === "importance") {
                    fill = COLORS.importance(e.ri, maxRI);
                } else {
                    fill = COLORS.change(null); // placeholder for change modes
                }

                var strokeW = (selectedNode && selectedNode.code === e.code) ? 2 : 0.5;
                var strokeColor = (selectedNode && selectedNode.code === e.code) ? "#2d3748" : "#fff";

                svg += '<rect x="' + e.x0 + '" y="' + y + '" width="' + bw + '" height="' + (BAND_H - 1)
                    + '" fill="' + fill + '" stroke="' + strokeColor + '" stroke-width="' + strokeW
                    + '" data-code="' + escapeAttr(e.code) + '" class="icicle-band" style="cursor:pointer">';
                svg += '<title>' + escapeHtml(e.code) + ' — ' + escapeHtml(e.title);
                if (e.ri != null) svg += ' (RI: ' + e.ri.toFixed(3) + ')';
                svg += '</title>';
                svg += '</rect>';

                // Label if band is wide enough
                if (bw > 50) {
                    var fontSize = bw > 120 ? 11 : 9;
                    var maxChars = Math.floor(bw / (fontSize * 0.6));
                    var label = e.title.length > maxChars ? e.title.substring(0, maxChars - 1) + "\u2026" : e.title;
                    svg += '<text x="' + (e.x0 + 4) + '" y="' + (y + BAND_H / 2 + 3)
                        + '" class="icicle-label" font-size="' + fontSize + '" data-code="' + escapeAttr(e.code)
                        + '" style="cursor:pointer;pointer-events:none">'
                        + escapeHtml(label) + '</text>';
                }
            });
        });

        svg += '</svg>';
        vizEl.innerHTML = svg;

        // Attach click handlers
        var bands = vizEl.querySelectorAll(".icicle-band");
        for (var i = 0; i < bands.length; i++) {
            bands[i].addEventListener("click", function() {
                var code = this.getAttribute("data-code");
                onBandClick(code, levels);
            });
        }
    }

    // --- Band click handler ---
    function onBandClick(code, levels) {
        // Find the node data
        var entry = null;
        for (var d = 0; d < levels.length; d++) {
            for (var j = 0; j < levels[d].length; j++) {
                if (levels[d][j].code === code) {
                    entry = levels[d][j];
                    break;
                }
            }
            if (entry) break;
        }
        if (!entry) return;

        selectedNode = entry;
        showLens(entry);

        // Re-render to update selection highlight
        var depth = parseInt(depthSelect.value, 10);
        loadTree(currentRoot, depth, renderIcicle);
    }

    // --- Member lens side panel ---
    function showLens(entry) {
        lensEl.style.display = "block";
        document.getElementById("lens-title").textContent = entry.title;
        document.getElementById("lens-code").textContent = entry.code;
        document.getElementById("lens-level").textContent = entry.level || "—";
        document.getElementById("lens-importance").textContent =
            entry.ri != null ? entry.ri.toFixed(3) : "—";
        document.getElementById("lens-children").textContent =
            entry.children ? entry.children.length : 0;
        document.getElementById("lens-link").href = "/cpi/member/" + encodeURIComponent(entry.code);

        var drillBtn = document.getElementById("lens-drill");
        drillBtn.style.display = (entry.children && entry.children.length > 0) ? "inline-block" : "none";
        // Remove old listener
        var newBtn = drillBtn.cloneNode(true);
        drillBtn.parentNode.replaceChild(newBtn, drillBtn);
        newBtn.addEventListener("click", function() {
            drillInto(entry.code);
        });
    }

    function hideLens() {
        lensEl.style.display = "none";
        selectedNode = null;
    }

    document.getElementById("lens-close").addEventListener("click", hideLens);

    // --- Drill into a member (click-to-expand) ---
    function drillInto(code) {
        drillStack.push(currentRoot);
        currentRoot = code;
        selectedNode = null;
        hideLens();
        refresh();
    }

    // --- Update drill path display ---
    function updatePath() {
        var parts = [];
        for (var i = 0; i < drillStack.length; i++) {
            var c = drillStack[i];
            parts.push('<a href="#" class="cpi-explorer-path-link" data-idx="' + i + '">' + escapeHtml(c) + '</a>');
        }
        parts.push('<span class="breadcrumb-current">' + escapeHtml(currentRoot) + '</span>');
        pathEl.innerHTML = parts.join(' <span class="breadcrumb-sep">&#8250;</span> ');

        // Attach click handlers for path links
        var links = pathEl.querySelectorAll(".cpi-explorer-path-link");
        for (var j = 0; j < links.length; j++) {
            links[j].addEventListener("click", function(e) {
                e.preventDefault();
                var idx = parseInt(this.getAttribute("data-idx"), 10);
                currentRoot = drillStack[idx];
                drillStack = drillStack.slice(0, idx);
                selectedNode = null;
                hideLens();
                refresh();
            });
        }
    }

    // --- Update legend for color mode ---
    function updateLegend() {
        var mode = colorSelect.value;
        if (mode === "importance") {
            legendEl.innerHTML =
                '<span class="legend-item"><span class="legend-swatch" style="background:#2b6cb0;"></span> Higher weight</span>' +
                '<span class="legend-item"><span class="legend-swatch" style="background:#bee3f8;"></span> Lower weight</span>';
        } else {
            legendEl.innerHTML =
                '<span class="legend-item"><span class="legend-swatch" style="background:#38a169;"></span> Price increase</span>' +
                '<span class="legend-item"><span class="legend-swatch" style="background:#e2e8f0;"></span> No change</span>' +
                '<span class="legend-item"><span class="legend-swatch" style="background:#e53e3e;"></span> Price decrease</span>';
        }
    }

    // --- Main refresh ---
    function refresh() {
        var depth = parseInt(depthSelect.value, 10);
        vizEl.innerHTML = '<p class="loading">Loading&hellip;</p>';
        updatePath();
        updateLegend();
        loadTree(currentRoot, depth, renderIcicle);
    }

    // --- Event listeners ---
    colorSelect.addEventListener("change", function() {
        var depth = parseInt(depthSelect.value, 10);
        updateLegend();
        loadTree(currentRoot, depth, renderIcicle);
    });

    depthSelect.addEventListener("change", function() {
        treeCache = {}; // depth change invalidates cache
        refresh();
    });

    resetBtn.addEventListener("click", function() {
        currentRoot = ROOT_CODE;
        drillStack = [];
        selectedNode = null;
        hideLens();
        refresh();
    });

    // --- Initial load ---
    refresh();
})();
