/* Pipeline Explorer — Main Renderer and Interaction Engine
 *
 * Canvas-based visualization of the JobClass pipeline graph.
 * Consumes PIPELINE_GRAPH from pipeline_graph_data.js.
 * No third-party libraries — vanilla Canvas API + vanilla JS.
 */

"use strict";

document.addEventListener("DOMContentLoaded", function () {
    /* --- DOM References --- */
    var container = document.getElementById("pipeline-canvas-container");
    var canvas = document.getElementById("pipeline-canvas");
    if (!canvas || !container) return;
    var ctx = canvas.getContext("2d");

    var minimapCanvas = document.getElementById("pipeline-minimap-canvas");
    var minimapCtx = minimapCanvas ? minimapCanvas.getContext("2d") : null;

    var detailPanel = document.getElementById("pipeline-detail-panel");
    var detailTitle = document.getElementById("pipeline-detail-title");
    var detailType = document.getElementById("pipeline-detail-type");
    var detailBody = document.getElementById("pipeline-detail-body");
    var detailClose = document.getElementById("pipeline-detail-close");

    var searchInput = document.getElementById("pipeline-search");
    var searchDropdown = document.getElementById("pipeline-search-results");
    var resetBtn = document.getElementById("pipeline-reset-btn");
    var zoomIndicator = document.getElementById("pipeline-zoom-level");
    var announcements = document.getElementById("pipeline-announcements");

    var graph = (typeof PIPELINE_GRAPH !== "undefined") ? PIPELINE_GRAPH : null;
    if (!graph || !graph.nodes || graph.nodes.length === 0) return;

    /* --- Node size constants --- */
    var NODE_W = 130;
    var NODE_H = 50;
    var NODE_RADIUS = 8;
    var LANE_PADDING = 20;

    /* --- Color Palettes --- */
    var TYPE_COLORS = {
        source:    { fill: "#dbeafe", stroke: "#3b82f6", text: "#1e40af" },
        process:   { fill: "#fef3c7", stroke: "#f59e0b", text: "#92400e" },
        storage:   { fill: "#d1fae5", stroke: "#10b981", text: "#065f46" },
        gate:      { fill: "#fee2e2", stroke: "#ef4444", text: "#991b1b" },
        "interface": { fill: "#e0e7ff", stroke: "#6366f1", text: "#3730a3" },
        lesson:    { fill: "#fae8ff", stroke: "#a855f7", text: "#6b21a8" }
    };

    var EDGE_STYLES = {
        required:    { color: "#64748b", width: 1.5, dash: [] },
        conditional: { color: "#d97706", width: 1.5, dash: [6, 4] },
        blocked:     { color: "#ef4444", width: 2,   dash: [] },
        optional:    { color: "#94a3b8", width: 1,   dash: [3, 3] },
        educational: { color: "#a855f7", width: 1,   dash: [2, 4] },
        derived:     { color: "#3b82f6", width: 1.5, dash: [8, 3] }
    };

    /* --- Build node index for quick lookup --- */
    var nodeById = {};
    for (var i = 0; i < graph.nodes.length; i++) {
        nodeById[graph.nodes[i].id] = graph.nodes[i];
    }

    /* --- Camera State --- */
    var camera = { x: 0, y: 0, scale: 1, minScale: 0.08, maxScale: 4 };

    /* --- Render State --- */
    var dirty = true;
    var selectedNode = null;
    var hoveredNode = null;
    var highlightedNodes = null; /* Set of node IDs for path highlighting */
    var highlightedEdges = null; /* Set of edge indices */
    var selectedEdge = null;     /* Currently selected edge object */
    var hoveredEdge = null;      /* Currently hovered edge index (PE10-03) */
    var guidedPulseT = 0;        /* 0-1 looping pulse for guided path animation (PE9-08) */
    var flowAnimT = 0;           /* monotonic counter for edge flow animation (PE10-01) */
    var loadStartTime = 0;       /* timestamp for entrance animation (PE10-06) */
    var entranceComplete = false;
    var activeFilters = { type: "all", domains: [] };
    var activeOverlay = null;     /* "validation", "blocked", "lessons", "timeseries" (PE8-06/07) */
    var overlayNodes = null;      /* Set of node IDs in the overlay subgraph */
    var overlayEdges = null;      /* Set of edge indices in the overlay subgraph */
    var prefersReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var canvasW = 0;
    var canvasH = 0;
    var mouseScreenX = 0;
    var mouseScreenY = 0;

    /* --- Overview / Detail View Mode --- */
    var viewMode = "overview"; /* "overview" | "detail" */
    var viewTransition = null; /* { toMode, progress, startTime } or null */
    var overviewHoveredGroup = null; /* index into summaryBlocks */
    var drillGroup = null; /* currently drilled-into group, or null */
    var summaryBlocks = []; /* computed at init from graph.summaryGroups */

    var OVERVIEW_CARD_W = 250;
    var OVERVIEW_CARD_H = 260;
    var OVERVIEW_CARD_R = 10;
    var OVERVIEW_TRANSITION_MS = 400;
    var DETAIL_RETURN_SCALE = 0.12;

    /* --- Canvas Sizing (PE2-01, PE2-12) --- */
    function resizeCanvas() {
        var dpr = window.devicePixelRatio || 1;
        var rect = container.getBoundingClientRect();
        canvasW = rect.width;
        canvasH = rect.height;
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        canvas.style.width = rect.width + "px";
        canvas.style.height = rect.height + "px";
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        dirty = true;
    }

    /* --- Coordinate Transforms (PE2-03) --- */
    function screenToWorld(sx, sy) {
        return {
            x: (sx - camera.x) / camera.scale,
            y: (sy - camera.y) / camera.scale
        };
    }

    /* --- Graph Bounding Box (PE2-11) --- */
    function getGraphBounds() {
        var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (var i = 0; i < graph.lanes.length; i++) {
            var lane = graph.lanes[i];
            if (lane.x < minX) minX = lane.x;
            if (lane.y < minY) minY = lane.y;
            if (lane.x + lane.w > maxX) maxX = lane.x + lane.w;
            if (lane.y + lane.h > maxY) maxY = lane.y + lane.h;
        }
        return { minX: minX, minY: minY, maxX: maxX, maxY: maxY, w: maxX - minX, h: maxY - minY };
    }

    /* --- Camera Animation (PE3-08) --- */
    var animating = false;
    var animStartTime = 0;
    var animDuration = 350;
    var animFrom = { x: 0, y: 0, scale: 1 };
    var animTo = { x: 0, y: 0, scale: 1 };

    function easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    function animateCamera(targetX, targetY, targetScale, duration) {
        /* Skip animation when reduced motion is preferred (PE10-07) */
        if (prefersReducedMotion) {
            camera.x = targetX;
            camera.y = targetY;
            camera.scale = targetScale;
            dirty = true;
            return;
        }
        animFrom.x = camera.x;
        animFrom.y = camera.y;
        animFrom.scale = camera.scale;
        animTo.x = targetX;
        animTo.y = targetY;
        animTo.scale = targetScale;
        animDuration = duration || 350;
        animStartTime = performance.now();
        animating = true;
        dirty = true;
    }

    function tickAnimation() {
        if (!animating) return;
        var elapsed = performance.now() - animStartTime;
        var t = Math.min(elapsed / animDuration, 1);
        var e = easeInOutCubic(t);
        camera.x = animFrom.x + (animTo.x - animFrom.x) * e;
        camera.y = animFrom.y + (animTo.y - animFrom.y) * e;
        camera.scale = animFrom.scale + (animTo.scale - animFrom.scale) * e;
        dirty = true;
        if (t >= 1) animating = false;
    }

    /* --- Fit to Screen (PE2-11) --- */
    function fitToScreen(instant) {
        var bounds = getGraphBounds();
        var pad = 40;
        var scaleX = (canvasW - pad * 2) / bounds.w;
        var scaleY = (canvasH - pad * 2) / bounds.h;
        var targetScale = Math.min(scaleX, scaleY, 1);
        var targetX = (canvasW - bounds.w * targetScale) / 2 - bounds.minX * targetScale;
        var targetY = (canvasH - bounds.h * targetScale) / 2 - bounds.minY * targetScale;
        if (instant) {
            camera.scale = targetScale;
            camera.x = targetX;
            camera.y = targetY;
            dirty = true;
        } else {
            animateCamera(targetX, targetY, targetScale, 400);
        }
    }

    function panToNode(node, scale) {
        var s = scale || 0.8;
        var tx = canvasW / 2 - node.x * s;
        var ty = canvasH / 2 - node.y * s;
        animateCamera(tx, ty, s, 350);
    }

    /* --- Summary Block Computation --- */
    function computeSummaryBlocks() {
        var groups = graph.summaryGroups || [];
        summaryBlocks = [];
        /* Layout: 2 rows x 4 columns for a compact readable flow */
        var cols = 4;
        var gapX = 40;
        var gapY = 40;
        var startX = OVERVIEW_CARD_W / 2 + 20;
        var startY = OVERVIEW_CARD_H / 2 + 30;
        for (var g = 0; g < groups.length; g++) {
            var grp = groups[g];
            var col = g % cols;
            var row = Math.floor(g / cols);
            /* Compute lane bounds for drill-in camera */
            var minLX = Infinity, maxLX = -Infinity;
            for (var l = 0; l < grp.lanes.length; l++) {
                for (var li = 0; li < graph.lanes.length; li++) {
                    if (graph.lanes[li].id === grp.lanes[l]) {
                        var lane = graph.lanes[li];
                        if (lane.x < minLX) minLX = lane.x;
                        if (lane.x + lane.w > maxLX) maxLX = lane.x + lane.w;
                    }
                }
            }
            summaryBlocks.push({
                id: grp.id,
                label: grp.label,
                purpose: grp.purpose,
                accent: grp.accent,
                lanes: grp.lanes,
                items: grp.items || [],
                x: startX + col * (OVERVIEW_CARD_W + gapX),
                y: startY + row * (OVERVIEW_CARD_H + gapY),
                w: OVERVIEW_CARD_W,
                h: OVERVIEW_CARD_H,
                laneMinX: minLX,
                laneMaxX: maxLX
            });
        }
    }

    function getOverviewBounds() {
        if (summaryBlocks.length === 0) return getGraphBounds();
        var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (var i = 0; i < summaryBlocks.length; i++) {
            var b = summaryBlocks[i];
            if (b.x - b.w / 2 < minX) minX = b.x - b.w / 2;
            if (b.x + b.w / 2 > maxX) maxX = b.x + b.w / 2;
            if (b.y - b.h / 2 < minY) minY = b.y - b.h / 2;
            if (b.y + b.h / 2 > maxY) maxY = b.y + b.h / 2;
        }
        return { minX: minX - 10, minY: minY - 10, maxX: maxX + 10, maxY: maxY + 10, w: maxX - minX + 20, h: maxY - minY + 20 };
    }

    function fitOverview(instant) {
        var bounds = getOverviewBounds();
        var pad = 30;
        var scaleX = (canvasW - pad * 2) / bounds.w;
        var scaleY = (canvasH - pad * 2) / bounds.h;
        var targetScale = Math.min(scaleX, scaleY, 1.2);
        var targetX = (canvasW - bounds.w * targetScale) / 2 - bounds.minX * targetScale;
        var targetY = (canvasH - bounds.h * targetScale) / 2 - bounds.minY * targetScale;
        if (instant || prefersReducedMotion) {
            camera.scale = targetScale;
            camera.x = targetX;
            camera.y = targetY;
            dirty = true;
        } else {
            animateCamera(targetX, targetY, targetScale, 400);
        }
    }

    function getGroupCamera(group) {
        var pad = 40;
        var lw = group.laneMaxX - group.laneMinX;
        var lh = 700;
        var scaleX = (canvasW - pad * 2) / lw;
        var scaleY = (canvasH - pad * 2) / lh;
        var s = Math.min(scaleX, scaleY, 1.2);
        var tx = (canvasW - lw * s) / 2 - group.laneMinX * s;
        var ty = (canvasH - lh * s) / 2;
        return { x: tx, y: ty, scale: s };
    }

    function getGroupForNode(nodeId) {
        var node = nodeById[nodeId];
        if (!node) return null;
        for (var i = 0; i < summaryBlocks.length; i++) {
            for (var l = 0; l < summaryBlocks[i].lanes.length; l++) {
                if (node.lane === summaryBlocks[i].lanes[l]) return summaryBlocks[i];
            }
        }
        return null;
    }

    function isNodeInDrillGroup(node) {
        if (!drillGroup) return true; /* no filter active */
        for (var l = 0; l < drillGroup.lanes.length; l++) {
            if (node.lane === drillGroup.lanes[l]) return true;
        }
        return false;
    }

    function drillIntoGroup(group) {
        viewMode = "detail";
        drillGroup = group;
        updateControlsVisibility();
        var cam = getGroupCamera(group);
        if (prefersReducedMotion) {
            camera.x = cam.x; camera.y = cam.y; camera.scale = cam.scale;
            dirty = true;
        } else {
            viewTransition = { toMode: "detail", progress: 0, startTime: performance.now() };
            animateCamera(cam.x, cam.y, cam.scale, OVERVIEW_TRANSITION_MS);
        }
        entranceComplete = true;
        announce("Viewing " + group.label + " detail");
    }

    function showFullDetail() {
        viewMode = "detail";
        drillGroup = null;
        updateControlsVisibility();
        entranceComplete = true;
        fitToScreen();
    }

    function returnToOverview() {
        viewMode = "overview";
        drillGroup = null;
        selectedNode = null;
        selectedEdge = null;
        highlightedNodes = null;
        highlightedEdges = null;
        hoveredNode = null;
        hoveredEdge = null;
        activeOverlay = null;
        overlayNodes = null;
        overlayEdges = null;
        overviewHoveredGroup = null;
        hideDetailPanel();
        updateControlsVisibility();
        if (prefersReducedMotion) {
            fitOverview(true);
        } else {
            viewTransition = { toMode: "overview", progress: 0, startTime: performance.now() };
            fitOverview(false);
        }
        announce("Pipeline overview");
    }

    function tickViewTransition() {
        if (!viewTransition) return;
        var elapsed = performance.now() - viewTransition.startTime;
        viewTransition.progress = Math.min(elapsed / OVERVIEW_TRANSITION_MS, 1);
        dirty = true;
        if (viewTransition.progress >= 1) {
            viewTransition = null;
        }
    }

    function updateControlsVisibility() {
        var page = document.querySelector(".pipeline-page");
        if (page) page.setAttribute("data-view-mode", viewMode);
    }

    /* --- Zoom Level Constants (PE4-01) --- */
    var ZOOM_OVERVIEW = 0.35;
    var ZOOM_DETAIL = 1.0;
    var ZOOM_FADE_RANGE = 0.08; /* scale range over which crossfade occurs (PE4-05) */

    function getZoomLevel() {
        if (camera.scale < ZOOM_OVERVIEW) return "overview";
        if (camera.scale > ZOOM_DETAIL) return "detail";
        return "subsystem";
    }

    /* Returns 0-1 blend factors for crossfade near zoom thresholds (PE4-05).
       overviewFade: 1 = fully overview, 0 = no overview elements visible
       detailFade:   1 = fully detail,   0 = no detail extras visible */
    function getZoomBlend() {
        var s = camera.scale;
        var overviewFade = 0;
        var detailFade = 0;
        if (s < ZOOM_OVERVIEW - ZOOM_FADE_RANGE) {
            overviewFade = 1;
        } else if (s < ZOOM_OVERVIEW + ZOOM_FADE_RANGE) {
            overviewFade = 1 - (s - (ZOOM_OVERVIEW - ZOOM_FADE_RANGE)) / (2 * ZOOM_FADE_RANGE);
        }
        if (s > ZOOM_DETAIL + ZOOM_FADE_RANGE) {
            detailFade = 1;
        } else if (s > ZOOM_DETAIL - ZOOM_FADE_RANGE) {
            detailFade = (s - (ZOOM_DETAIL - ZOOM_FADE_RANGE)) / (2 * ZOOM_FADE_RANGE);
        }
        return { overviewFade: overviewFade, detailFade: detailFade };
    }

    /* --- Entrance Animation (PE10-06) --- */
    var laneOrder = {};
    for (var li = 0; li < graph.lanes.length; li++) laneOrder[graph.lanes[li].id] = li;

    function getEntranceAlpha(laneId) {
        if (entranceComplete || prefersReducedMotion) return 1;
        var elapsed = performance.now() - loadStartTime;
        var idx = laneOrder[laneId] || 0;
        var stagger = idx * 60; /* 60ms per lane */
        var fadeIn = 120;       /* 120ms fade duration */
        var t = Math.min(Math.max((elapsed - stagger) / fadeIn, 0), 1);
        return t;
    }

    /* --- Overlay Subgraph Computation (PE8-06/07) --- */
    function computeOverlay(type) {
        var nodes = {};
        var edges = {};
        if (type === "validation") {
            /* Edges of type conditional or blocked, and their connected nodes */
            for (var i = 0; i < graph.edges.length; i++) {
                if (graph.edges[i].type === "conditional" || graph.edges[i].type === "blocked") {
                    edges[i] = true;
                    nodes[graph.edges[i].from] = true;
                    nodes[graph.edges[i].to] = true;
                }
            }
        } else if (type === "blocked") {
            for (var i = 0; i < graph.edges.length; i++) {
                if (graph.edges[i].type === "blocked") {
                    edges[i] = true;
                    nodes[graph.edges[i].from] = true;
                    nodes[graph.edges[i].to] = true;
                }
            }
            /* Also include gate nodes */
            for (var j = 0; j < graph.nodes.length; j++) {
                if (graph.nodes[j].type === "gate") nodes[graph.nodes[j].id] = true;
            }
        } else if (type === "lessons") {
            /* Edges of type educational, and nodes with lesson anchors */
            for (var i = 0; i < graph.edges.length; i++) {
                if (graph.edges[i].type === "educational") {
                    edges[i] = true;
                    nodes[graph.edges[i].from] = true;
                    nodes[graph.edges[i].to] = true;
                }
            }
            if (graph.lessonAnchors) {
                for (var lk in graph.lessonAnchors) {
                    var ids = graph.lessonAnchors[lk];
                    for (var la = 0; la < ids.length; la++) nodes[ids[la]] = true;
                }
            }
        } else if (type === "timeseries") {
            /* Nodes in timeseries lane, and derived edges */
            for (var j = 0; j < graph.nodes.length; j++) {
                if (graph.nodes[j].lane === "timeseries") nodes[graph.nodes[j].id] = true;
            }
            for (var i = 0; i < graph.edges.length; i++) {
                if (graph.edges[i].type === "derived") {
                    edges[i] = true;
                    nodes[graph.edges[i].from] = true;
                    nodes[graph.edges[i].to] = true;
                }
            }
        }
        return { nodes: nodes, edges: edges };
    }

    /* --- Domain-to-Lane Mapping (PE8-04) --- */
    var DOMAIN_LANES = {
        extraction: ["extraction", "raw", "staging"],
        timeseries: ["timeseries"],
        validation: ["validation"],
        deployment: ["deployment"],
        lessons:    [] /* special: filters by lesson anchor, not lane */
    };

    /* Build set of node IDs with lesson anchors */
    var lessonNodeIds = {};
    if (graph.lessonAnchors) {
        for (var lk in graph.lessonAnchors) {
            var anchors = graph.lessonAnchors[lk];
            for (var la = 0; la < anchors.length; la++) lessonNodeIds[anchors[la]] = true;
        }
    }

    /* --- Node Visibility --- */
    function isNodeVisible(node) {
        /* Drill-group filter: only show nodes in the focused stage */
        if (drillGroup && !isNodeInDrillGroup(node)) return false;
        if (activeFilters.type !== "all" && node.type !== activeFilters.type) return false;
        if (activeFilters.domains.length > 0) {
            var domainMatch = false;
            for (var d = 0; d < activeFilters.domains.length; d++) {
                var dom = activeFilters.domains[d];
                if (dom === "lessons") {
                    if (lessonNodeIds[node.id]) { domainMatch = true; break; }
                } else {
                    var lanes = DOMAIN_LANES[dom];
                    if (lanes) {
                        for (var dl = 0; dl < lanes.length; dl++) {
                            if (node.lane === lanes[dl]) { domainMatch = true; break; }
                        }
                    }
                }
                if (domainMatch) break;
            }
            if (!domainMatch) return false;
        }
        return true;
    }

    /* --- Offscreen Culling (PE10-08) — skip drawing nodes outside viewport --- */
    function isOnScreen(wx, wy, margin) {
        var sx = wx * camera.scale + camera.x;
        var sy = wy * camera.scale + camera.y;
        var m = margin || 80;
        return sx > -m && sx < canvasW + m && sy > -m && sy < canvasH + m;
    }

    /* --- Drawing: Lanes (PE2-04, PE4-02) --- */
    function drawLanes() {
        var zoomLevel = getZoomLevel();
        var fontFamily = getComputedStyle(document.body).fontFamily;

        for (var i = 0; i < graph.lanes.length; i++) {
            var lane = graph.lanes[i];
            /* Only draw lanes in the drill group when focused */
            if (drillGroup) {
                var inGroup = false;
                for (var dg = 0; dg < drillGroup.lanes.length; dg++) {
                    if (lane.id === drillGroup.lanes[dg]) { inGroup = true; break; }
                }
                if (!inGroup) continue;
            }
            var entAlpha = getEntranceAlpha(lane.id);
            ctx.save();
            ctx.globalAlpha = entAlpha;
            ctx.fillStyle = lane.color;
            ctx.fillRect(lane.x, lane.y, lane.w, lane.h);
            ctx.strokeStyle = "#cbd5e1";
            ctx.lineWidth = 1;
            ctx.strokeRect(lane.x, lane.y, lane.w, lane.h);

            /* Lane label at top */
            ctx.fillStyle = "#475569";
            ctx.font = "bold 11px " + fontFamily;
            ctx.textAlign = "center";
            ctx.fillText(lane.label, lane.x + lane.w / 2, lane.y + 16);

            /* At overview zoom, show node counts per lane */
            if (zoomLevel === "overview") {
                var count = 0;
                for (var j = 0; j < graph.nodes.length; j++) {
                    if (graph.nodes[j].lane === lane.id && isNodeVisible(graph.nodes[j])) count++;
                }
                ctx.fillStyle = "#94a3b8";
                ctx.font = "bold 14px " + fontFamily;
                ctx.fillText(count + " node" + (count !== 1 ? "s" : ""), lane.x + lane.w / 2, lane.y + lane.h / 2);
            }

            ctx.restore();
        }
    }

    /* --- Drawing: Rounded Rectangle --- */
    function roundedRect(x, y, w, h, r) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + w - r, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + r);
        ctx.lineTo(x + w, y + h - r);
        ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        ctx.lineTo(x + r, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.closePath();
    }

    /* --- Drawing: Hexagon (sources) (PE2-05) --- */
    function drawHexagon(cx, cy, w, h) {
        var hw = w / 2, hh = h / 2;
        var indent = w * 0.18;
        ctx.beginPath();
        ctx.moveTo(cx - hw + indent, cy - hh);
        ctx.lineTo(cx + hw - indent, cy - hh);
        ctx.lineTo(cx + hw, cy);
        ctx.lineTo(cx + hw - indent, cy + hh);
        ctx.lineTo(cx - hw + indent, cy + hh);
        ctx.lineTo(cx - hw, cy);
        ctx.closePath();
    }

    /* --- Drawing: Diamond (gates) (PE2-05) --- */
    function drawDiamond(cx, cy, w, h) {
        ctx.beginPath();
        ctx.moveTo(cx, cy - h / 2);
        ctx.lineTo(cx + w / 2, cy);
        ctx.lineTo(cx, cy + h / 2);
        ctx.lineTo(cx - w / 2, cy);
        ctx.closePath();
    }

    /* --- Drawing: Cylinder (storage) (PE2-05) --- */
    function drawCylinder(x, y, w, h) {
        var ry = 6;
        ctx.beginPath();
        ctx.ellipse(x + w / 2, y + ry, w / 2, ry, 0, Math.PI, 0);
        ctx.lineTo(x + w, y + h - ry);
        ctx.ellipse(x + w / 2, y + h - ry, w / 2, ry, 0, 0, Math.PI);
        ctx.lineTo(x, y + ry);
        ctx.closePath();
    }

    function drawCylinderTop(x, y, w) {
        var ry = 6;
        ctx.beginPath();
        ctx.ellipse(x + w / 2, y + ry, w / 2, ry, 0, 0, Math.PI * 2);
        ctx.closePath();
    }

    /* --- Drawing: Node Shape (PE2-05) --- */
    function drawNodeShape(node, colors, isHovered, isSelected) {
        var nx = node.x - NODE_W / 2;
        var ny = node.y - NODE_H / 2;
        var cx = node.x;
        var cy = node.y;

        ctx.save();
        if (isSelected) {
            ctx.shadowColor = colors.stroke;
            ctx.shadowBlur = 12;
        } else if (isHovered) {
            ctx.shadowColor = "rgba(0,0,0,0.15)";
            ctx.shadowBlur = 8;
        }

        switch (node.type) {
            case "source":
                drawHexagon(cx, cy, NODE_W, NODE_H);
                break;
            case "gate":
                drawDiamond(cx, cy, NODE_W, NODE_H + 8);
                break;
            case "storage":
                drawCylinder(nx, ny, NODE_W, NODE_H);
                break;
            default:
                roundedRect(nx, ny, NODE_W, NODE_H, NODE_RADIUS);
                break;
        }

        ctx.fillStyle = colors.fill;
        ctx.fill();
        ctx.strokeStyle = isSelected ? colors.stroke : (isHovered ? colors.stroke : colors.stroke);
        ctx.lineWidth = isSelected ? 2.5 : (isHovered ? 2 : 1.2);
        ctx.stroke();

        /* Cylinder top ellipse */
        if (node.type === "storage") {
            drawCylinderTop(nx, ny, NODE_W);
            ctx.fillStyle = colors.fill;
            ctx.fill();
            ctx.stroke();
        }

        ctx.restore();
    }

    /* --- Drawing: Node Label (PE2-06) --- */
    function drawNodeLabel(node, colors) {
        ctx.save();
        ctx.fillStyle = colors.text;
        ctx.font = "10px " + getComputedStyle(document.body).fontFamily;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        var lines = node.label.split("\n");
        var lineHeight = 12;
        var startY = node.y - (lines.length - 1) * lineHeight / 2;
        for (var i = 0; i < lines.length; i++) {
            ctx.fillText(lines[i], node.x, startY + i * lineHeight);
        }
        ctx.restore();
    }

    /* --- Drawing: Status Chip (PE2-10) --- */
    function drawStatusChip(node) {
        /* Lesson-linked chip */
        var hasLesson = false;
        for (var slug in graph.lessonAnchors) {
            if (graph.lessonAnchors[slug].indexOf(node.id) >= 0) {
                hasLesson = true;
                break;
            }
        }
        if (hasLesson) {
            var chipX = node.x + NODE_W / 2 - 8;
            var chipY = node.y - NODE_H / 2 - 4;
            ctx.save();
            ctx.fillStyle = "#a855f7";
            ctx.beginPath();
            ctx.arc(chipX, chipY, 4, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
    }

    /* --- Drawing: Nodes (PE2-05, PE2-06, PE2-10, PE4-02/03/04, PE4-05) --- */
    function drawNodes() {
        var zoomLevel = getZoomLevel();
        var blend = getZoomBlend();

        /* At overview zoom, draw small dots for nodes; crossfade near threshold (PE4-05) */
        if (zoomLevel === "overview" || blend.overviewFade > 0) {
            var dotAlpha = zoomLevel === "overview" ? 1 : blend.overviewFade;
            for (var oi = 0; oi < graph.nodes.length; oi++) {
                var onode = graph.nodes[oi];
                if (!isNodeVisible(onode)) continue;
                if (!isOnScreen(onode.x, onode.y)) continue;
                var dimmedO = (highlightedNodes && !highlightedNodes[onode.id]) || (overlayNodes && !overlayNodes[onode.id]);
                ctx.save();
                ctx.globalAlpha = dotAlpha * (dimmedO ? 0.2 : 1) * getEntranceAlpha(onode.lane);
                var ocolors = TYPE_COLORS[onode.type] || TYPE_COLORS.process;
                ctx.fillStyle = ocolors.stroke;
                ctx.beginPath();
                ctx.arc(onode.x, onode.y, 5, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
            }
            if (zoomLevel === "overview") return;
        }

        /* Subsystem/detail: full node shapes; fade in near overview threshold (PE4-05) */
        var nodeAlpha = blend.overviewFade > 0 ? (1 - blend.overviewFade) : 1;
        var fontFamily = getComputedStyle(document.body).fontFamily;
        for (var i = 0; i < graph.nodes.length; i++) {
            var node = graph.nodes[i];
            if (!isNodeVisible(node)) continue;
            if (!isOnScreen(node.x, node.y, 120)) continue;

            var colors = TYPE_COLORS[node.type] || TYPE_COLORS.process;
            var isHovered = hoveredNode === node;
            var isSelected = selectedNode === node;

            /* Dim if path highlighting is active and this node isn't in the path */
            var dimmed = false;
            if (highlightedNodes && !highlightedNodes[node.id]) dimmed = true;
            if (overlayNodes && !overlayNodes[node.id]) dimmed = true;

            ctx.save();
            ctx.globalAlpha = nodeAlpha * (dimmed ? 0.2 : 1) * getEntranceAlpha(node.lane);

            drawNodeShape(node, colors, isHovered, isSelected);
            drawNodeLabel(node, colors);
            drawStatusChip(node);

            /* At detail zoom, show extra metadata below node with fade-in (PE4-04, PE4-05) */
            if ((zoomLevel === "detail" || blend.detailFade > 0) && !dimmed) {
                var metaText = "";
                if (node.metadata && node.metadata.file) metaText = node.metadata.file;
                else if (node.metadata && node.metadata.route) metaText = node.metadata.route;
                else if (node.metadata && node.metadata.grain) metaText = node.metadata.grain;
                if (metaText) {
                    var metaAlpha = blend.detailFade < 1 ? blend.detailFade : 1;
                    ctx.globalAlpha = nodeAlpha * metaAlpha;
                    ctx.fillStyle = "#94a3b8";
                    ctx.font = "8px " + fontFamily;
                    ctx.textAlign = "center";
                    ctx.textBaseline = "top";
                    ctx.fillText(metaText, node.x, node.y + NODE_H / 2 + 3);
                }
            }

            ctx.restore();
        }
    }

    /* --- Drawing: Edges (PE2-07, PE2-08, PE2-09, PE4-07) --- */
    function drawEdges() {
        var zoomLevel = getZoomLevel();

        /* At overview, draw simplified inter-lane arrows (PE4-07) */
        if (zoomLevel === "overview") {
            var laneEdges = {};
            for (var ei = 0; ei < graph.edges.length; ei++) {
                var edge = graph.edges[ei];
                var fn = nodeById[edge.from];
                var tn = nodeById[edge.to];
                if (!fn || !tn || fn.lane === tn.lane) continue;
                if (!isNodeVisible(fn) || !isNodeVisible(tn)) continue;
                var key = fn.lane + "->" + tn.lane;
                if (!laneEdges[key]) laneEdges[key] = { from: fn.lane, to: tn.lane, count: 0 };
                laneEdges[key].count++;
            }
            var laneById = {};
            for (var li = 0; li < graph.lanes.length; li++) laneById[graph.lanes[li].id] = graph.lanes[li];

            for (var lk in laneEdges) {
                var le = laneEdges[lk];
                var fl = laneById[le.from];
                var tl = laneById[le.to];
                if (!fl || !tl) continue;
                var lx1 = fl.x + fl.w;
                var ly1 = fl.y + fl.h / 2;
                var lx2 = tl.x;
                var ly2 = tl.y + tl.h / 2;
                ctx.save();
                ctx.strokeStyle = "#94a3b8";
                ctx.lineWidth = Math.min(le.count * 0.5, 4);
                ctx.globalAlpha = 0.5;
                ctx.beginPath();
                ctx.moveTo(lx1, ly1);
                ctx.lineTo(lx2, ly2);
                ctx.stroke();
                /* Arrow */
                var a = Math.atan2(ly2 - ly1, lx2 - lx1);
                ctx.beginPath();
                ctx.moveTo(lx2, ly2);
                ctx.lineTo(lx2 - 8 * Math.cos(a - 0.4), ly2 - 8 * Math.sin(a - 0.4));
                ctx.moveTo(lx2, ly2);
                ctx.lineTo(lx2 - 8 * Math.cos(a + 0.4), ly2 - 8 * Math.sin(a + 0.4));
                ctx.stroke();
                ctx.restore();
            }
            return;
        }

        for (var i = 0; i < graph.edges.length; i++) {
            var edge = graph.edges[i];
            var fromNode = nodeById[edge.from];
            var toNode = nodeById[edge.to];
            if (!fromNode || !toNode) continue;
            if (!isNodeVisible(fromNode) || !isNodeVisible(toNode)) continue;

            var style = EDGE_STYLES[edge.type] || EDGE_STYLES.required;

            /* Dim if path/overlay highlighting is active and this edge isn't highlighted */
            var dimmed = false;
            if (highlightedEdges && !highlightedEdges[i]) {
                dimmed = true;
            }
            if (overlayEdges && !overlayEdges[i]) {
                dimmed = true;
            }

            /* Edge hover brightening (PE10-03) */
            var isEdgeHovered = hoveredEdge && hoveredEdge.index === i;

            ctx.save();
            if (dimmed) ctx.globalAlpha = 0.1;
            else if (isEdgeHovered) ctx.globalAlpha = 1;

            ctx.strokeStyle = style.color;
            ctx.lineWidth = isEdgeHovered ? style.width + 1.5 : style.width;
            ctx.setLineDash(style.dash);

            /* Flow animation: animate dash offset for dashed edges (PE10-01) */
            if (!prefersReducedMotion && !dimmed && style.dash.length > 0) {
                ctx.lineDashOffset = -flowAnimT;
            }

            /* Simple straight-line edge from right of source to left of target */
            var x1 = fromNode.x + NODE_W / 2;
            var y1 = fromNode.y;
            var x2 = toNode.x - NODE_W / 2;
            var y2 = toNode.y;

            /* For nodes in same lane, use different connection points */
            if (fromNode.lane === toNode.lane) {
                x1 = fromNode.x;
                y1 = fromNode.y + NODE_H / 2;
                x2 = toNode.x;
                y2 = toNode.y - NODE_H / 2;
            }

            ctx.beginPath();
            ctx.moveTo(x1, y1);

            /* Slight curve for visual appeal */
            var mx = (x1 + x2) / 2;
            var my = (y1 + y2) / 2;
            ctx.quadraticCurveTo(mx, y1, x2, y2);
            ctx.stroke();

            /* Arrowhead */
            var angle = Math.atan2(y2 - my, x2 - mx);
            var arrLen = 6;
            ctx.setLineDash([]);
            ctx.beginPath();
            ctx.moveTo(x2, y2);
            ctx.lineTo(x2 - arrLen * Math.cos(angle - 0.4), y2 - arrLen * Math.sin(angle - 0.4));
            ctx.moveTo(x2, y2);
            ctx.lineTo(x2 - arrLen * Math.cos(angle + 0.4), y2 - arrLen * Math.sin(angle + 0.4));
            ctx.stroke();

            /* Edge condition label (PE2-09) */
            if (edge.condition && camera.scale > 0.35) {
                ctx.fillStyle = style.color;
                ctx.font = "8px " + getComputedStyle(document.body).fontFamily;
                ctx.textAlign = "center";
                ctx.textBaseline = "bottom";
                ctx.fillText(edge.condition, mx, my - 3);
            }

            ctx.restore();
        }
    }

    /* --- Guided Mode Pulse Animation on Edges (PE9-08) --- */
    function drawGuidedPulse() {
        if (!activeMode || activeModeStep < 0 || !highlightedEdges) return;
        for (var i = 0; i < graph.edges.length; i++) {
            if (!highlightedEdges[i]) continue;
            var edge = graph.edges[i];
            var fromNode = nodeById[edge.from];
            var toNode = nodeById[edge.to];
            if (!fromNode || !toNode) continue;
            if (!isNodeVisible(fromNode) || !isNodeVisible(toNode)) continue;

            var x1 = fromNode.x + NODE_W / 2;
            var y1 = fromNode.y;
            var x2 = toNode.x - NODE_W / 2;
            var y2 = toNode.y;
            if (fromNode.lane === toNode.lane) {
                x1 = fromNode.x;
                y1 = fromNode.y + NODE_H / 2;
                x2 = toNode.x;
                y2 = toNode.y - NODE_H / 2;
            }

            /* Compute point along the quadratic curve at parameter t */
            var mx = (x1 + x2) / 2;
            var t = guidedPulseT;
            var u = 1 - t;
            var px = u * u * x1 + 2 * u * t * mx + t * t * x2;
            var py = u * u * y1 + 2 * u * t * y1 + t * t * y2;

            ctx.save();
            ctx.fillStyle = "#3b82f6";
            ctx.globalAlpha = 0.9;
            ctx.beginPath();
            ctx.arc(px, py, 4 / camera.scale, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
    }

    /* --- Minimap Rendering (PE7 stub, basic implementation) --- */
    function drawMinimap() {
        if (!minimapCtx || !minimapCanvas) return;
        var bounds = getGraphBounds();
        var mw = minimapCanvas.width;
        var mh = minimapCanvas.height;
        var scale = Math.min(mw / (bounds.w + 40), mh / (bounds.h + 40));

        minimapCtx.clearRect(0, 0, mw, mh);
        minimapCtx.save();
        minimapCtx.translate(-bounds.minX * scale + 10, -bounds.minY * scale + 5);
        minimapCtx.scale(scale, scale);

        /* Draw lanes as colored rectangles */
        for (var i = 0; i < graph.lanes.length; i++) {
            var lane = graph.lanes[i];
            minimapCtx.fillStyle = lane.color;
            minimapCtx.fillRect(lane.x, lane.y, lane.w, lane.h);
        }

        /* Draw nodes as dots */
        for (var j = 0; j < graph.nodes.length; j++) {
            var node = graph.nodes[j];
            if (!isNodeVisible(node)) continue;
            var colors = TYPE_COLORS[node.type] || TYPE_COLORS.process;
            minimapCtx.fillStyle = colors.stroke;
            minimapCtx.fillRect(node.x - 3, node.y - 2, 6, 4);
        }

        minimapCtx.restore();

        /* Viewport rectangle */
        var vx = (-camera.x / camera.scale - bounds.minX) * scale + 10;
        var vy = (-camera.y / camera.scale - bounds.minY) * scale + 5;
        var vw = (canvasW / camera.scale) * scale;
        var vh = (canvasH / camera.scale) * scale;
        minimapCtx.strokeStyle = "#3b82f6";
        minimapCtx.lineWidth = 1.5;
        minimapCtx.strokeRect(vx, vy, vw, vh);
    }

    /* --- Overview Drawing --- */
    function drawOverview() {
        drawOverviewArrows();
        for (var i = 0; i < summaryBlocks.length; i++) {
            drawOverviewBlock(summaryBlocks[i], i, overviewHoveredGroup === i);
        }
    }

    function overviewRoundRect(bx, by, bw, bh, r) {
        ctx.beginPath();
        ctx.moveTo(bx + r, by);
        ctx.lineTo(bx + bw - r, by);
        ctx.quadraticCurveTo(bx + bw, by, bx + bw, by + r);
        ctx.lineTo(bx + bw, by + bh - r);
        ctx.quadraticCurveTo(bx + bw, by + bh, bx + bw - r, by + bh);
        ctx.lineTo(bx + r, by + bh);
        ctx.quadraticCurveTo(bx, by + bh, bx, by + bh - r);
        ctx.lineTo(bx, by + r);
        ctx.quadraticCurveTo(bx, by, bx + r, by);
        ctx.closePath();
    }

    function drawOverviewBlock(block, idx, isHovered) {
        var bx = block.x - block.w / 2;
        var by = block.y - block.h / 2;
        var r = OVERVIEW_CARD_R;
        var font = "system-ui, sans-serif";

        /* Shadow + fill */
        ctx.save();
        ctx.shadowColor = isHovered ? "rgba(0,0,0,0.18)" : "rgba(0,0,0,0.07)";
        ctx.shadowBlur = isHovered ? 14 : 6;
        ctx.shadowOffsetY = isHovered ? 3 : 1;
        overviewRoundRect(bx, by, block.w, block.h, r);
        ctx.fillStyle = "#ffffff";
        ctx.fill();
        ctx.restore();

        /* Border */
        overviewRoundRect(bx, by, block.w, block.h, r);
        ctx.strokeStyle = isHovered ? block.accent : "#d1d5db";
        ctx.lineWidth = isHovered ? 2 : 1;
        ctx.stroke();

        /* Accent left edge */
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(bx + r, by);
        ctx.quadraticCurveTo(bx, by, bx, by + r);
        ctx.lineTo(bx, by + block.h - r);
        ctx.quadraticCurveTo(bx, by + block.h, bx + r, by + block.h);
        ctx.lineTo(bx + 4, by + block.h);
        ctx.lineTo(bx + 4, by);
        ctx.closePath();
        ctx.fillStyle = block.accent;
        ctx.fill();
        ctx.restore();

        /* Step badge */
        var badgeX = bx + 18;
        var badgeY = by + 16;
        ctx.fillStyle = block.accent;
        ctx.font = "bold 10px " + font;
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillText((idx + 1) + ".", badgeX, badgeY);

        /* Title */
        ctx.fillStyle = "#111827";
        ctx.font = "bold 14px " + font;
        ctx.textAlign = "left";
        ctx.fillText(block.label, badgeX + 18, badgeY);

        /* Purpose line */
        ctx.fillStyle = "#6b7280";
        ctx.font = "11px " + font;
        ctx.textAlign = "left";
        var purposeY = badgeY + 22;
        ctx.fillText(block.purpose, badgeX, purposeY);

        /* Divider */
        ctx.strokeStyle = "#e5e7eb";
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(badgeX, purposeY + 12);
        ctx.lineTo(bx + block.w - 14, purposeY + 12);
        ctx.stroke();

        /* Item list */
        ctx.fillStyle = "#374151";
        ctx.font = "11px " + font;
        var itemStartY = purposeY + 26;
        var itemH = 16;
        for (var j = 0; j < block.items.length; j++) {
            var iy = itemStartY + j * itemH;
            if (iy > by + block.h - 14) break; /* don't overflow */
            /* Bullet dot */
            ctx.fillStyle = block.accent;
            ctx.beginPath();
            ctx.arc(badgeX + 3, iy, 2, 0, Math.PI * 2);
            ctx.fill();
            /* Text */
            ctx.fillStyle = "#374151";
            ctx.fillText(block.items[j], badgeX + 12, iy);
        }
    }

    function drawOverviewArrows() {
        var cols = 4;
        ctx.strokeStyle = "#94a3b8";
        ctx.lineWidth = 1.8;
        ctx.setLineDash([]);

        for (var i = 0; i < summaryBlocks.length - 1; i++) {
            var from = summaryBlocks[i];
            var to = summaryBlocks[i + 1];
            var fromCol = i % cols;
            var toCol = (i + 1) % cols;
            var fromRow = Math.floor(i / cols);
            var toRow = Math.floor((i + 1) / cols);
            var x1, y1, x2, y2;

            if (fromRow === toRow) {
                /* Same row: right side → left side */
                x1 = from.x + from.w / 2;
                y1 = from.y;
                x2 = to.x - to.w / 2;
                y2 = to.y;
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.stroke();
                drawArrowhead(x2, y2, Math.atan2(y2 - y1, x2 - x1));
            } else {
                /* Row transition: bottom of last col → top of first col next row */
                x1 = from.x;
                y1 = from.y + from.h / 2;
                x2 = to.x;
                y2 = to.y - to.h / 2;
                var midY = (y1 + y2) / 2;
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x1, midY);
                ctx.lineTo(x2, midY);
                ctx.lineTo(x2, y2);
                ctx.stroke();
                drawArrowhead(x2, y2, Math.PI / 2); /* pointing down */
            }
        }
    }

    function drawArrowhead(tipX, tipY, angle) {
        var aSize = 7;
        ctx.fillStyle = "#94a3b8";
        ctx.beginPath();
        ctx.moveTo(tipX, tipY);
        ctx.lineTo(tipX - aSize * Math.cos(angle - 0.4), tipY - aSize * Math.sin(angle - 0.4));
        ctx.lineTo(tipX - aSize * Math.cos(angle + 0.4), tipY - aSize * Math.sin(angle + 0.4));
        ctx.closePath();
        ctx.fill();
    }

    function hitTestSummaryBlock(wx, wy) {
        for (var i = 0; i < summaryBlocks.length; i++) {
            var b = summaryBlocks[i];
            if (wx >= b.x - b.w / 2 && wx <= b.x + b.w / 2 &&
                wy >= b.y - b.h / 2 && wy <= b.y + b.h / 2) {
                return i;
            }
        }
        return -1;
    }

    /* --- Main Render Loop (PE2-02) --- */
    function render() {
        tickAnimation();
        tickViewTransition();

        if (viewMode === "detail") {
            /* Keep animating while guided mode pulse is active (PE9-08, PE10-07) */
            if (activeMode && activeModeStep >= 0 && highlightedEdges && !prefersReducedMotion) {
                guidedPulseT = (guidedPulseT + 0.008) % 1;
                dirty = true;
            }
            /* Entrance animation on first load (PE10-06) */
            if (!entranceComplete && !prefersReducedMotion) {
                var entranceElapsed = performance.now() - loadStartTime;
                if (entranceElapsed < graph.lanes.length * 60 + 120) {
                    dirty = true;
                } else {
                    entranceComplete = true;
                }
            }
            /* Flow animation on edges at subsystem+ zoom (PE10-01) */
            if (!prefersReducedMotion && getZoomLevel() !== "overview") {
                flowAnimT = (flowAnimT + 0.3) % 20;
                dirty = true;
            }
        }

        if (!dirty) {
            requestAnimationFrame(render);
            return;
        }
        dirty = false;

        ctx.clearRect(0, 0, canvasW, canvasH);

        if (viewTransition) {
            /* Crossfade: first half fades out old, second half fades in new */
            var t = viewTransition.progress;
            ctx.save();
            ctx.translate(camera.x, camera.y);
            ctx.scale(camera.scale, camera.scale);
            if (t < 0.5) {
                /* Fading out the departing view */
                ctx.globalAlpha = 1 - t * 2;
                if (viewTransition.toMode === "detail") {
                    drawOverview();
                } else {
                    drawLanes(); drawEdges(); drawNodes();
                }
            } else {
                /* Fading in the arriving view */
                ctx.globalAlpha = (t - 0.5) * 2;
                if (viewTransition.toMode === "detail") {
                    drawLanes(); drawEdges(); drawNodes();
                } else {
                    drawOverview();
                }
            }
            ctx.globalAlpha = 1;
            ctx.restore();
        } else if (viewMode === "overview") {
            ctx.save();
            ctx.translate(camera.x, camera.y);
            ctx.scale(camera.scale, camera.scale);
            drawOverview();
            ctx.restore();
        } else {
            ctx.save();
            ctx.translate(camera.x, camera.y);
            ctx.scale(camera.scale, camera.scale);
            drawLanes();
            drawEdges();
            drawGuidedPulse();
            drawNodes();
            ctx.restore();

            drawMinimap();
            drawTooltip();
        }

        /* Zoom indicator */
        if (zoomIndicator) {
            zoomIndicator.textContent = Math.round(camera.scale * 100) + "%";
        }

        requestAnimationFrame(render);
    }

    /* --- Hover Tooltip (PE5-03, PE5-04) --- */
    function drawTooltip() {
        if (!hoveredNode || hoveredNode === selectedNode || isDragging) return;

        var fontFamily = getComputedStyle(document.body).fontFamily;
        var title = hoveredNode.label.replace(/\n/g, " ");
        var purpose = hoveredNode.purpose || "";
        var maxW = 260;
        var pad = 8;
        var lineH = 16;
        var titleH = 14;

        ctx.save();
        ctx.font = "bold 11px " + fontFamily;
        var titleWidth = ctx.measureText(title).width;
        ctx.font = "10px " + fontFamily;

        /* Word-wrap purpose text */
        var purposeLines = [];
        if (purpose) {
            var words = purpose.split(" ");
            var line = "";
            for (var wi = 0; wi < words.length; wi++) {
                var test = line ? line + " " + words[wi] : words[wi];
                if (ctx.measureText(test).width > maxW - pad * 2) {
                    if (line) purposeLines.push(line);
                    line = words[wi];
                } else {
                    line = test;
                }
            }
            if (line) purposeLines.push(line);
            if (purposeLines.length > 3) {
                purposeLines = purposeLines.slice(0, 3);
                purposeLines[2] = purposeLines[2].replace(/\s+\S*$/, "") + "...";
            }
        }

        var boxW = Math.min(maxW, Math.max(titleWidth + pad * 2, maxW));
        var boxH = pad * 2 + titleH + purposeLines.length * lineH;

        /* Position: offset from mouse, clamped to canvas */
        var tx = mouseScreenX + 12;
        var ty = mouseScreenY + 12;
        if (tx + boxW > canvasW - 4) tx = mouseScreenX - boxW - 8;
        if (ty + boxH > canvasH - 4) ty = mouseScreenY - boxH - 8;
        if (tx < 4) tx = 4;
        if (ty < 4) ty = 4;

        /* Draw background */
        ctx.fillStyle = "rgba(15, 23, 42, 0.92)";
        roundedRect(tx, ty, boxW, boxH, 4);
        ctx.fill();

        /* Draw title */
        ctx.fillStyle = "#f8fafc";
        ctx.font = "bold 11px " + fontFamily;
        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.fillText(title, tx + pad, ty + pad);

        /* Draw type badge */
        var badgeText = hoveredNode.type;
        ctx.font = "9px " + fontFamily;
        var badgeW = ctx.measureText(badgeText).width + 6;
        var badgeX = tx + pad + ctx.measureText(title).width + 6;
        if (badgeX + badgeW < tx + boxW - pad) {
            ctx.font = "bold 11px " + fontFamily;
            badgeX = tx + pad + ctx.measureText(title).width + 6;
            ctx.font = "9px " + fontFamily;
            var colors = TYPE_COLORS[hoveredNode.type] || TYPE_COLORS.process;
            ctx.fillStyle = colors.stroke;
            roundedRect(badgeX, ty + pad + 1, badgeW, 13, 2);
            ctx.fill();
            ctx.fillStyle = "#fff";
            ctx.fillText(badgeText, badgeX + 3, ty + pad + 2);
        }

        /* Draw purpose lines */
        ctx.fillStyle = "#cbd5e1";
        ctx.font = "10px " + fontFamily;
        for (var pi = 0; pi < purposeLines.length; pi++) {
            ctx.fillText(purposeLines[pi], tx + pad, ty + pad + titleH + pi * lineH);
        }

        ctx.restore();
    }

    /* --- Hit Testing (PE5-01, PE4-08) --- */
    function hitTestNode(wx, wy) {
        /* Larger hit targets at overview zoom */
        var zoomLevel = getZoomLevel();
        var hitPad = zoomLevel === "overview" ? 12 : 0;
        for (var i = graph.nodes.length - 1; i >= 0; i--) {
            var node = graph.nodes[i];
            if (!isNodeVisible(node)) continue;
            var hw = NODE_W / 2 + hitPad;
            var hh = NODE_H / 2 + hitPad;
            if (wx >= node.x - hw && wx <= node.x + hw && wy >= node.y - hh && wy <= node.y + hh) {
                return node;
            }
        }
        return null;
    }

    /* --- Edge Hit Testing (PE5-10) --- */
    function hitTestEdge(wx, wy) {
        var threshold = 8 / camera.scale;
        for (var i = graph.edges.length - 1; i >= 0; i--) {
            var edge = graph.edges[i];
            var fromNode = nodeById[edge.from];
            var toNode = nodeById[edge.to];
            if (!fromNode || !toNode) continue;
            if (!isNodeVisible(fromNode) || !isNodeVisible(toNode)) continue;

            var x1 = fromNode.x + NODE_W / 2;
            var y1 = fromNode.y;
            var x2 = toNode.x - NODE_W / 2;
            var y2 = toNode.y;
            if (fromNode.lane === toNode.lane) {
                x1 = fromNode.x;
                y1 = fromNode.y + NODE_H / 2;
                x2 = toNode.x;
                y2 = toNode.y - NODE_H / 2;
            }

            /* Point-to-segment distance (simplified for quadratic curve: use midpoint) */
            var mx = (x1 + x2) / 2;
            var my = (y1 + y2) / 2;
            /* Check distance to two line segments: start→mid and mid→end */
            if (pointToSegDist(wx, wy, x1, y1, mx, (y1 + my) / 2) < threshold ||
                pointToSegDist(wx, wy, mx, (y1 + my) / 2, x2, y2) < threshold) {
                return { edge: edge, index: i };
            }
        }
        return null;
    }

    function pointToSegDist(px, py, ax, ay, bx, by) {
        var dx = bx - ax, dy = by - ay;
        var lenSq = dx * dx + dy * dy;
        if (lenSq === 0) return Math.hypot(px - ax, py - ay);
        var t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / lenSq));
        var projX = ax + t * dx, projY = ay + t * dy;
        return Math.hypot(px - projX, py - projY);
    }

    /* --- Path Tracing (PE5-06, PE5-07) --- */
    function traceConnectedNodes(nodeId) {
        var nodeSet = {};
        var edgeSet = {};
        nodeSet[nodeId] = true;

        /* Trace upstream */
        var changed = true;
        while (changed) {
            changed = false;
            for (var i = 0; i < graph.edges.length; i++) {
                var e = graph.edges[i];
                if (nodeSet[e.to] && !nodeSet[e.from]) {
                    nodeSet[e.from] = true;
                    edgeSet[i] = true;
                    changed = true;
                }
                if (nodeSet[e.to] && nodeSet[e.from]) {
                    edgeSet[i] = true;
                }
            }
        }
        /* Trace downstream */
        changed = true;
        while (changed) {
            changed = false;
            for (var j = 0; j < graph.edges.length; j++) {
                var ed = graph.edges[j];
                if (nodeSet[ed.from] && !nodeSet[ed.to]) {
                    nodeSet[ed.to] = true;
                    edgeSet[j] = true;
                    changed = true;
                }
                if (nodeSet[ed.from] && nodeSet[ed.to]) {
                    edgeSet[j] = true;
                }
            }
        }
        return { nodes: nodeSet, edges: edgeSet };
    }

    /* --- Detail Panel (PE6 stub) --- */
    function showDetailPanel(node) {
        if (!detailPanel || !detailTitle || !detailBody) return;
        detailTitle.textContent = node.label.replace(/\n/g, " ");
        if (detailType) {
            detailType.textContent = node.type;
            detailType.className = "pipeline-type-badge pipeline-type-" + node.type;
        }

        var html = "";
        if (node.purpose) {
            html += '<p style="margin-bottom:0.75rem;font-size:0.9rem;">' + escapeHtml(node.purpose) + "</p>";
        }
        if (node.caveats) {
            html += '<p style="margin-bottom:0.5rem;font-size:0.85rem;color:#b45309;"><strong>Caveat:</strong> ' + escapeHtml(node.caveats) + "</p>";
        }
        if (node.metadata) {
            html += '<div style="font-size:0.8rem;color:#64748b;margin-top:0.5rem;">';
            for (var key in node.metadata) {
                var val = node.metadata[key];
                if (Array.isArray(val)) val = val.join(", ");
                html += "<div><strong>" + escapeHtml(key) + ":</strong> " + escapeHtml(String(val)) + "</div>";
            }
            html += "</div>";
        }

        /* Lesson links */
        var lessonLinks = [];
        for (var slug in graph.lessonAnchors) {
            if (graph.lessonAnchors[slug].indexOf(node.id) >= 0) {
                lessonLinks.push(slug);
            }
        }
        if (lessonLinks.length > 0) {
            html += '<div style="margin-top:0.75rem;border-top:1px solid #e2e8f0;padding-top:0.5rem;">';
            html += '<strong style="font-size:0.8rem;">Related Lessons:</strong>';
            for (var li = 0; li < lessonLinks.length; li++) {
                html += ' <a href="/lessons/' + escapeAttr(lessonLinks[li]) + '" style="font-size:0.8rem;color:#6366f1;">' + escapeHtml(lessonLinks[li].replace(/-/g, " ")) + "</a>";
                if (li < lessonLinks.length - 1) html += ",";
            }
            html += "</div>";
        }

        /* Isolate Path and Copy Link buttons (PE8-08, PE11-07) */
        html += '<div style="margin-top:0.75rem;border-top:1px solid #e2e8f0;padding-top:0.5rem;display:flex;gap:6px;">';
        html += '<button class="pipeline-btn pipeline-isolate-btn" data-node-id="' + escapeAttr(node.id) + '" style="font-size:0.78rem;flex:1;">Isolate Path</button>';
        html += '<button class="pipeline-btn pipeline-copy-link-btn" data-node-id="' + escapeAttr(node.id) + '" style="font-size:0.78rem;flex:1;">Copy Link</button>';
        html += '</div>';

        detailBody.innerHTML = html;
        detailPanel.hidden = false;

        /* Bind isolate path button */
        var isolateBtn = detailBody.querySelector(".pipeline-isolate-btn");
        if (isolateBtn) {
            isolateBtn.addEventListener("click", function () {
                var nid = this.getAttribute("data-node-id");
                var traced = traceConnectedNodes(nid);
                overlayNodes = traced.nodes;
                overlayEdges = traced.edges;
                activeOverlay = "isolate";
                for (var ok = 0; ok < overlayBtns.length; ok++) overlayBtns[ok].classList.remove("active");
                announce("Path isolated for " + (nodeById[nid] ? nodeById[nid].label.replace(/\n/g, " ") : nid));
                dirty = true;
            });
        }
        /* Bind copy link button (PE11-07) */
        var copyBtn = detailBody.querySelector(".pipeline-copy-link-btn");
        if (copyBtn) {
            copyBtn.addEventListener("click", function () {
                var nid = this.getAttribute("data-node-id");
                var url = window.location.origin + window.location.pathname + "#node=" + encodeURIComponent(nid);
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(url);
                }
                this.textContent = "Copied!";
                var btn = this;
                setTimeout(function () { btn.textContent = "Copy Link"; }, 1500);
                announce("Link copied to clipboard");
            });
        }
    }

    /* --- Edge Detail Panel (PE6-10) --- */
    function showEdgeDetailPanel(edge) {
        if (!detailPanel || !detailTitle || !detailBody) return;
        var fromNode = nodeById[edge.from];
        var toNode = nodeById[edge.to];
        var fromLabel = fromNode ? fromNode.label.replace(/\n/g, " ") : edge.from;
        var toLabel = toNode ? toNode.label.replace(/\n/g, " ") : edge.to;

        detailTitle.textContent = fromLabel + " \u2192 " + toLabel;
        if (detailType) {
            detailType.textContent = edge.type;
            detailType.className = "pipeline-type-badge";
        }

        var style = EDGE_STYLES[edge.type] || EDGE_STYLES.required;
        var typeDescriptions = {
            required: "This is a required dependency \u2014 the downstream node cannot function without the upstream.",
            conditional: "This dependency applies only when a specific condition is met.",
            blocked: "This path is blocked when the upstream gate fails validation.",
            optional: "This is an optional dependency \u2014 the downstream node works without it but gains features from it.",
            educational: "This is an educational link connecting a lesson to related pipeline components.",
            derived: "This represents a derived data relationship \u2014 the downstream is computed from the upstream."
        };

        var html = '<p style="margin-bottom:0.75rem;font-size:0.9rem;">' + escapeHtml(typeDescriptions[edge.type] || "Data flows from source to target.") + "</p>";

        if (edge.condition) {
            html += '<p style="margin-bottom:0.5rem;font-size:0.85rem;color:#b45309;"><strong>Condition:</strong> ' + escapeHtml(edge.condition) + "</p>";
        }

        html += '<div style="font-size:0.85rem;margin-top:0.75rem;border-top:1px solid #e2e8f0;padding-top:0.5rem;">';
        html += '<div style="margin-bottom:0.25rem;"><strong>From:</strong> ' + escapeHtml(fromLabel) + ' <span style="color:#64748b;">(' + (fromNode ? fromNode.type : "?") + ')</span></div>';
        html += '<div><strong>To:</strong> ' + escapeHtml(toLabel) + ' <span style="color:#64748b;">(' + (toNode ? toNode.type : "?") + ')</span></div>';
        html += "</div>";

        /* Visual style info */
        html += '<div style="font-size:0.8rem;color:#64748b;margin-top:0.5rem;">';
        html += '<div><strong>Line style:</strong> <span style="color:' + style.color + ';">' + (style.dash.length > 0 ? "dashed" : "solid") + " (" + edge.type + ")</span></div>";
        html += "</div>";

        detailBody.innerHTML = html;
        detailPanel.hidden = false;
    }

    function hideDetailPanel() {
        if (detailPanel) detailPanel.hidden = true;
    }

    /* --- Announce for screen readers --- */
    function announce(msg) {
        if (announcements) announcements.textContent = msg;
    }

    /* --- Mouse Events --- */
    var isDragging = false;
    var dragStartX = 0;
    var dragStartY = 0;
    var dragStartCamX = 0;
    var dragStartCamY = 0;

    canvas.addEventListener("mousedown", function (e) {
        isDragging = true;
        dragStartX = e.clientX;
        dragStartY = e.clientY;
        dragStartCamX = camera.x;
        dragStartCamY = camera.y;
        canvas.style.cursor = "grabbing";
    });

    window.addEventListener("mousemove", function (e) {
        if (isDragging) {
            camera.x = dragStartCamX + (e.clientX - dragStartX);
            camera.y = dragStartCamY + (e.clientY - dragStartY);
            dirty = true;
            return;
        }

        /* Hover detection */
        var rect = canvas.getBoundingClientRect();
        var sx = e.clientX - rect.left;
        var sy = e.clientY - rect.top;
        mouseScreenX = sx;
        mouseScreenY = sy;
        var world = screenToWorld(sx, sy);

        /* Overview mode hover: summary blocks */
        if (viewMode === "overview") {
            var groupIdx = hitTestSummaryBlock(world.x, world.y);
            if (groupIdx !== overviewHoveredGroup) {
                overviewHoveredGroup = groupIdx >= 0 ? groupIdx : null;
                dirty = true;
            }
            canvas.style.cursor = groupIdx >= 0 ? "pointer" : "grab";
            return;
        }

        var hit = hitTestNode(world.x, world.y);
        if (hit !== hoveredNode) {
            hoveredNode = hit;
            dirty = true;
        }
        /* Edge hover detection when no node is hovered (PE10-03) */
        var edgeHit = null;
        if (!hit) {
            edgeHit = hitTestEdge(world.x, world.y);
        }
        if (edgeHit !== hoveredEdge) {
            hoveredEdge = edgeHit;
            dirty = true;
        }
        canvas.style.cursor = (hit || edgeHit !== null) ? "pointer" : "grab";
        if (hit) dirty = true; /* Redraw tooltip at new position */
    });

    window.addEventListener("mouseup", function () {
        if (isDragging) {
            isDragging = false;
            canvas.style.cursor = hoveredNode ? "pointer" : "grab";
        }
    });

    canvas.addEventListener("click", function (e) {
        var rect = canvas.getBoundingClientRect();
        var sx = e.clientX - rect.left;
        var sy = e.clientY - rect.top;
        var world = screenToWorld(sx, sy);

        /* Overview mode: click summary blocks to drill in */
        if (viewMode === "overview") {
            var groupIdx = hitTestSummaryBlock(world.x, world.y);
            if (groupIdx >= 0) {
                drillIntoGroup(summaryBlocks[groupIdx]);
            }
            dirty = true;
            return;
        }

        var hit = hitTestNode(world.x, world.y);

        if (hit) {
            selectedNode = hit;
            selectedEdge = null;
            var traced = traceConnectedNodes(hit.id);
            highlightedNodes = traced.nodes;
            highlightedEdges = traced.edges;
            showDetailPanel(hit);
            announce("Selected " + hit.label.replace(/\n/g, " ") + ", " + hit.type);
        } else {
            /* Check edge hit */
            var edgeHit = hitTestEdge(world.x, world.y);
            if (edgeHit) {
                selectedNode = null;
                selectedEdge = edgeHit.edge;
                /* Highlight just this edge and its two endpoints */
                highlightedNodes = {};
                highlightedNodes[edgeHit.edge.from] = true;
                highlightedNodes[edgeHit.edge.to] = true;
                highlightedEdges = {};
                highlightedEdges[edgeHit.index] = true;
                showEdgeDetailPanel(edgeHit.edge);
                var fromNode = nodeById[edgeHit.edge.from];
                var toNode = nodeById[edgeHit.edge.to];
                announce("Selected edge from " + (fromNode ? fromNode.label.replace(/\n/g, " ") : "") + " to " + (toNode ? toNode.label.replace(/\n/g, " ") : ""));
            } else {
                selectedNode = null;
                selectedEdge = null;
                highlightedNodes = null;
                highlightedEdges = null;
                hideDetailPanel();
            }
        }
        dirty = true;
    });

    canvas.addEventListener("dblclick", function (e) {
        var rect = canvas.getBoundingClientRect();
        var sx = e.clientX - rect.left;
        var sy = e.clientY - rect.top;
        var world = screenToWorld(sx, sy);
        var hit = hitTestNode(world.x, world.y);
        if (hit) {
            /* Zoom to node */
            var newScale = Math.min(camera.scale * 2, camera.maxScale);
            panToNode(hit, newScale);
        }
    });

    /* --- Mouse Wheel Zoom (PE3-01) --- */
    canvas.addEventListener("wheel", function (e) {
        e.preventDefault();
        var rect = canvas.getBoundingClientRect();
        var mx = e.clientX - rect.left;
        var my = e.clientY - rect.top;

        var zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
        var newScale = camera.scale * zoomFactor;
        newScale = Math.max(camera.minScale, Math.min(camera.maxScale, newScale));

        /* Zoom anchored to pointer */
        camera.x = mx - (mx - camera.x) * (newScale / camera.scale);
        camera.y = my - (my - camera.y) * (newScale / camera.scale);
        camera.scale = newScale;
        dirty = true;

        /* Auto-return to overview when zoomed out very far in detail mode */
        if (viewMode === "detail" && camera.scale <= DETAIL_RETURN_SCALE) {
            returnToOverview();
        }
    }, { passive: false });

    /* --- Touch Events (PE3-03, PE3-04) --- */
    var lastTouches = null;

    canvas.addEventListener("touchstart", function (e) {
        if (e.touches.length === 1) {
            isDragging = true;
            dragStartX = e.touches[0].clientX;
            dragStartY = e.touches[0].clientY;
            dragStartCamX = camera.x;
            dragStartCamY = camera.y;
        }
        lastTouches = e.touches;
    }, { passive: true });

    canvas.addEventListener("touchmove", function (e) {
        e.preventDefault();
        if (e.touches.length === 1 && isDragging) {
            camera.x = dragStartCamX + (e.touches[0].clientX - dragStartX);
            camera.y = dragStartCamY + (e.touches[0].clientY - dragStartY);
            dirty = true;
        } else if (e.touches.length === 2 && lastTouches && lastTouches.length === 2) {
            /* Pinch zoom */
            var prevDist = Math.hypot(
                lastTouches[0].clientX - lastTouches[1].clientX,
                lastTouches[0].clientY - lastTouches[1].clientY
            );
            var curDist = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            var zf = curDist / prevDist;
            var cx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
            var cy = (e.touches[0].clientY + e.touches[1].clientY) / 2;
            var rect = canvas.getBoundingClientRect();
            cx -= rect.left;
            cy -= rect.top;

            var ns = Math.max(camera.minScale, Math.min(camera.maxScale, camera.scale * zf));
            camera.x = cx - (cx - camera.x) * (ns / camera.scale);
            camera.y = cy - (cy - camera.y) * (ns / camera.scale);
            camera.scale = ns;
            dirty = true;
        }
        lastTouches = e.touches;
    }, { passive: false });

    canvas.addEventListener("touchend", function () {
        isDragging = false;
        lastTouches = null;
    }, { passive: true });

    /* --- Filter Buttons --- */
    var filterBtns = document.querySelectorAll(".pipeline-filter-btn");
    for (var fi = 0; fi < filterBtns.length; fi++) {
        filterBtns[fi].addEventListener("click", function () {
            for (var fj = 0; fj < filterBtns.length; fj++) filterBtns[fj].classList.remove("active");
            this.classList.add("active");
            activeFilters.type = this.getAttribute("data-filter");
            dirty = true;
        });
    }

    /* --- Overlay Toggles (PE8-06/07) --- */
    var overlayBtns = document.querySelectorAll(".pipeline-overlay-btn");
    for (var oi = 0; oi < overlayBtns.length; oi++) {
        overlayBtns[oi].addEventListener("click", function () {
            var otype = this.getAttribute("data-overlay");
            if (activeOverlay === otype) {
                /* Toggle off */
                activeOverlay = null;
                overlayNodes = null;
                overlayEdges = null;
                this.classList.remove("active");
            } else {
                /* Turn off previous overlay button */
                for (var ok = 0; ok < overlayBtns.length; ok++) overlayBtns[ok].classList.remove("active");
                activeOverlay = otype;
                var result = computeOverlay(otype);
                overlayNodes = result.nodes;
                overlayEdges = result.edges;
                this.classList.add("active");
            }
            announce("Overlay: " + (activeOverlay || "none"));
            dirty = true;
        });
    }

    /* --- Domain Filters (PE8-04) --- */
    var domainBtns = document.querySelectorAll(".pipeline-domain-btn");
    for (var di = 0; di < domainBtns.length; di++) {
        domainBtns[di].addEventListener("click", function () {
            var dom = this.getAttribute("data-domain");
            this.classList.toggle("active");
            var idx = activeFilters.domains.indexOf(dom);
            if (idx >= 0) {
                activeFilters.domains.splice(idx, 1);
            } else {
                activeFilters.domains.push(dom);
            }
            announce("Domain filter: " + (activeFilters.domains.length > 0 ? activeFilters.domains.join(", ") : "all"));
            dirty = true;
        });
    }

    /* --- Search --- */
    if (searchInput && searchDropdown) {
        searchInput.addEventListener("input", function () {
            var q = this.value.trim().toLowerCase();
            searchDropdown.innerHTML = "";
            if (q.length < 2) {
                searchDropdown.style.display = "none";
                return;
            }
            var matches = [];
            for (var si = 0; si < graph.nodes.length; si++) {
                var sn = graph.nodes[si];
                var text = (sn.label + " " + sn.id + " " + (sn.purpose || "")).toLowerCase();
                if (text.indexOf(q) >= 0) matches.push(sn);
            }
            if (matches.length === 0) {
                searchDropdown.style.display = "none";
                return;
            }
            searchDropdown.style.display = "block";
            for (var sj = 0; sj < Math.min(matches.length, 8); sj++) {
                var opt = document.createElement("div");
                opt.style.padding = "6px 10px";
                opt.style.cursor = "pointer";
                opt.style.fontSize = "0.85rem";
                opt.style.borderBottom = "1px solid #e2e8f0";
                opt.textContent = matches[sj].label.replace(/\n/g, " ");
                opt.setAttribute("data-node-id", matches[sj].id);
                opt.addEventListener("click", function () {
                    var nid = this.getAttribute("data-node-id");
                    var node = nodeById[nid];
                    if (node) {
                        /* Switch to detail mode if in overview */
                        if (viewMode === "overview") {
                            var grp = getGroupForNode(nid);
                            if (grp) {
                                viewMode = "detail";
                                updateControlsVisibility();
                                entranceComplete = true;
                            }
                        }
                        selectedNode = node;
                        var traced = traceConnectedNodes(node.id);
                        highlightedNodes = traced.nodes;
                        highlightedEdges = traced.edges;
                        showDetailPanel(node);
                        panToNode(node, 0.8);
                    }
                    searchDropdown.style.display = "none";
                    searchInput.value = "";
                });
                opt.addEventListener("mouseenter", function () { this.style.background = "#f1f5f9"; });
                opt.addEventListener("mouseleave", function () { this.style.background = ""; });
                searchDropdown.appendChild(opt);
            }
        });

        document.addEventListener("click", function (e) {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                searchDropdown.style.display = "none";
            }
        });
    }

    /* --- Reset Button (PE3-06) --- */
    if (resetBtn) {
        resetBtn.addEventListener("click", function () {
            returnToOverview();
            /* Also reset filters */
            activeFilters.type = "all";
            activeFilters.domains = [];
            for (var ri = 0; ri < filterBtns.length; ri++) {
                filterBtns[ri].classList.toggle("active", filterBtns[ri].getAttribute("data-filter") === "all");
            }
            for (var rdi = 0; rdi < domainBtns.length; rdi++) domainBtns[rdi].classList.remove("active");
            for (var roi = 0; roi < overlayBtns.length; roi++) overlayBtns[roi].classList.remove("active");
            announce("View reset");
        });
    }

    /* --- Detail Panel Close --- */
    if (detailClose) {
        detailClose.addEventListener("click", function () {
            selectedNode = null;
            selectedEdge = null;
            highlightedNodes = null;
            highlightedEdges = null;
            hideDetailPanel();
            dirty = true;
        });
    }

    /* --- Overview Button --- */
    var overviewBtn = document.getElementById("pipeline-overview-btn");
    if (overviewBtn) {
        overviewBtn.addEventListener("click", function () {
            returnToOverview();
        });
    }

    /* --- Guided Mode --- */
    var guidedOverlay = document.getElementById("pipeline-guided-overlay");
    var guidedText = document.getElementById("pipeline-guided-text");
    var guidedStep = document.getElementById("pipeline-guided-step");
    var guidedPrev = document.getElementById("pipeline-guided-prev");
    var guidedNext = document.getElementById("pipeline-guided-next");
    var guidedExit = document.getElementById("pipeline-guided-exit");
    var activeMode = null;
    var activeModeStep = 0;

    function showModeIntro() {
        if (!activeMode) return;
        selectedNode = null;
        highlightedNodes = null;
        highlightedEdges = null;
        hideDetailPanel();
        fitToScreen();
        if (guidedText) guidedText.textContent = activeMode.description;
        if (guidedStep) guidedStep.textContent = "Intro";
        if (guidedPrev) guidedPrev.disabled = true;
        if (guidedNext) guidedNext.disabled = false;
        if (guidedOverlay) guidedOverlay.hidden = false;
        dirty = true;
    }

    function showGuidedStep() {
        if (!activeMode) return;
        var step = activeMode.steps[activeModeStep];
        var node = nodeById[step.nodeId];
        if (node) {
            selectedNode = node;
            var traced = traceConnectedNodes(node.id);
            highlightedNodes = traced.nodes;
            highlightedEdges = traced.edges;
            showDetailPanel(node);
            panToNode(node, 0.6);
        }
        if (guidedText) guidedText.textContent = step.annotation;
        if (guidedStep) guidedStep.textContent = "Step " + (activeModeStep + 1) + " of " + activeMode.steps.length;
        if (guidedPrev) guidedPrev.disabled = false;
        if (guidedNext) guidedNext.disabled = activeModeStep === activeMode.steps.length - 1;
        if (guidedOverlay) guidedOverlay.hidden = false;
        dirty = true;
    }

    function exitGuidedMode() {
        activeMode = null;
        activeModeStep = 0;
        guidedPulseT = 0;
        if (guidedOverlay) guidedOverlay.hidden = true;
        selectedNode = null;
        highlightedNodes = null;
        highlightedEdges = null;
        hideDetailPanel();
        var modeBtns = document.querySelectorAll(".pipeline-mode-btn");
        for (var mi = 0; mi < modeBtns.length; mi++) modeBtns[mi].classList.remove("active");
        fitToScreen();
    }

    var modeBtns = document.querySelectorAll(".pipeline-mode-btn");
    for (var mi = 0; mi < modeBtns.length; mi++) {
        modeBtns[mi].addEventListener("click", function () {
            var modeId = this.getAttribute("data-mode");
            for (var mj = 0; mj < modeBtns.length; mj++) modeBtns[mj].classList.remove("active");

            /* Toggle off if same mode clicked */
            if (activeMode && activeMode.id === modeId) {
                exitGuidedMode();
                return;
            }

            this.classList.add("active");
            /* Auto-switch to detail mode for guided tours */
            if (viewMode === "overview") {
                viewMode = "detail";
                updateControlsVisibility();
                entranceComplete = true;
                fitToScreen(true);
            }
            for (var mk = 0; mk < graph.guidedModes.length; mk++) {
                if (graph.guidedModes[mk].id === modeId) {
                    activeMode = graph.guidedModes[mk];
                    activeModeStep = -1; /* -1 signals intro step */
                    showModeIntro();
                    announce("Guided mode: " + activeMode.name);
                    break;
                }
            }
        });
    }

    if (guidedPrev) {
        guidedPrev.addEventListener("click", function () {
            if (!activeMode) return;
            if (activeModeStep > 0) {
                activeModeStep--;
                showGuidedStep();
            } else if (activeModeStep === 0) {
                activeModeStep = -1;
                showModeIntro();
            }
        });
    }
    if (guidedNext) {
        guidedNext.addEventListener("click", function () {
            if (!activeMode) return;
            if (activeModeStep === -1) {
                activeModeStep = 0;
                showGuidedStep();
            } else if (activeModeStep < activeMode.steps.length - 1) {
                activeModeStep++;
                showGuidedStep();
            }
        });
    }
    if (guidedExit) {
        guidedExit.addEventListener("click", exitGuidedMode);
    }

    /* --- Minimap Click-to-Navigate & Drag (PE7-04, PE7-05) --- */
    var minimapDragging = false;
    function minimapToWorld(clientX, clientY) {
        var rect = minimapCanvas.getBoundingClientRect();
        var mx = clientX - rect.left;
        var my = clientY - rect.top;
        var bounds = getGraphBounds();
        var mw = minimapCanvas.width;
        var mh = minimapCanvas.height;
        var scale = Math.min(mw / (bounds.w + 40), mh / (bounds.h + 40));
        return {
            x: (mx - 10) / scale + bounds.minX,
            y: (my - 5) / scale + bounds.minY
        };
    }
    function minimapNavigate(clientX, clientY) {
        var world = minimapToWorld(clientX, clientY);
        camera.x = canvasW / 2 - world.x * camera.scale;
        camera.y = canvasH / 2 - world.y * camera.scale;
        dirty = true;
    }
    if (minimapCanvas) {
        minimapCanvas.addEventListener("mousedown", function (e) {
            minimapDragging = true;
            minimapNavigate(e.clientX, e.clientY);
            e.preventDefault();
        });
        window.addEventListener("mousemove", function (e) {
            if (minimapDragging) {
                minimapNavigate(e.clientX, e.clientY);
            }
        });
        window.addEventListener("mouseup", function () {
            minimapDragging = false;
        });
    }

    /* --- URL Hash Deep-Linking (PE11-06) --- */
    function handleHashNavigation() {
        var hash = window.location.hash;
        if (!hash) return;
        var match = hash.match(/node=([^&]+)/);
        if (match) {
            var nid = decodeURIComponent(match[1]);
            var node = nodeById[nid];
            if (node) {
                /* Deep-link goes straight to detail mode */
                viewMode = "detail";
                updateControlsVisibility();
                entranceComplete = true;
                selectedNode = node;
                var traced = traceConnectedNodes(node.id);
                highlightedNodes = traced.nodes;
                highlightedEdges = traced.edges;
                showDetailPanel(node);
                /* Instant on initial load, no animation needed */
                camera.scale = 0.8;
                camera.x = canvasW / 2 - node.x * camera.scale;
                camera.y = canvasH / 2 - node.y * camera.scale;
                dirty = true;
            }
        }
    }

    /* --- Keyboard Navigation (PE12-02 stub) --- */
    document.addEventListener("keydown", function (e) {
        if (e.target.tagName === "INPUT") return;
        if (e.key === "Escape") {
            if (activeMode) {
                exitGuidedMode();
            } else if (viewMode === "detail") {
                returnToOverview();
            } else {
                selectedNode = null;
                selectedEdge = null;
                highlightedNodes = null;
                highlightedEdges = null;
                activeOverlay = null;
                overlayNodes = null;
                overlayEdges = null;
                hideDetailPanel();
                dirty = true;
            }
        }
        /* Overview mode: arrow keys cycle summary blocks, Enter drills in */
        if (viewMode === "overview") {
            if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
                e.preventDefault();
                var cur = overviewHoveredGroup !== null ? overviewHoveredGroup : -1;
                if (e.key === "ArrowRight") cur = Math.min(cur + 1, summaryBlocks.length - 1);
                else cur = Math.max(cur - 1, 0);
                overviewHoveredGroup = cur;
                dirty = true;
            }
            if (e.key === "Enter" && overviewHoveredGroup !== null && overviewHoveredGroup >= 0) {
                drillIntoGroup(summaryBlocks[overviewHoveredGroup]);
            }
            return;
        }
        /* Arrow-key node traversal (PE12-02) */
        if (selectedNode && (e.key === "ArrowRight" || e.key === "ArrowLeft" || e.key === "ArrowUp" || e.key === "ArrowDown")) {
            e.preventDefault();
            var target = null;
            if (e.key === "ArrowRight") {
                /* Follow first outgoing edge */
                for (var ei = 0; ei < graph.edges.length; ei++) {
                    if (graph.edges[ei].from === selectedNode.id) {
                        target = nodeById[graph.edges[ei].to];
                        if (target && isNodeVisible(target)) break;
                        target = null;
                    }
                }
            } else if (e.key === "ArrowLeft") {
                /* Follow first incoming edge */
                for (var ei = 0; ei < graph.edges.length; ei++) {
                    if (graph.edges[ei].to === selectedNode.id) {
                        target = nodeById[graph.edges[ei].from];
                        if (target && isNodeVisible(target)) break;
                        target = null;
                    }
                }
            } else {
                /* Up/Down: cycle within same lane */
                var laneNodes = [];
                for (var ni = 0; ni < graph.nodes.length; ni++) {
                    if (graph.nodes[ni].lane === selectedNode.lane && isNodeVisible(graph.nodes[ni])) {
                        laneNodes.push(graph.nodes[ni]);
                    }
                }
                laneNodes.sort(function (a, b) { return a.y - b.y; });
                var idx = laneNodes.indexOf(selectedNode);
                if (e.key === "ArrowUp" && idx > 0) target = laneNodes[idx - 1];
                if (e.key === "ArrowDown" && idx < laneNodes.length - 1) target = laneNodes[idx + 1];
            }
            if (target) {
                selectedNode = target;
                selectedEdge = null;
                var traced = traceConnectedNodes(target.id);
                highlightedNodes = traced.nodes;
                highlightedEdges = traced.edges;
                showDetailPanel(target);
                panToNode(target, camera.scale);
                announce("Selected " + target.label.replace(/\n/g, " "));
            }
        }
    });

    /* --- Initialization --- */
    var resizeTimer = 0;
    window.addEventListener("resize", function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            resizeCanvas();
            dirty = true;
        }, 100);
    });

    resizeCanvas();
    computeSummaryBlocks();
    updateControlsVisibility();
    fitOverview(true); /* Start with overview fitted */
    handleHashNavigation(); /* May switch to detail mode if #node= present */
    loadStartTime = performance.now();
    requestAnimationFrame(render);
});
