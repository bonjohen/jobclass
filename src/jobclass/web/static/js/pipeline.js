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
        conditional: { color: "#f59e0b", width: 1.5, dash: [6, 4] },
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
    var activeFilters = { type: "all" };
    var canvasW = 0;
    var canvasH = 0;

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

    /* --- Fit to Screen (PE2-11) --- */
    function fitToScreen() {
        var bounds = getGraphBounds();
        var pad = 40;
        var scaleX = (canvasW - pad * 2) / bounds.w;
        var scaleY = (canvasH - pad * 2) / bounds.h;
        camera.scale = Math.min(scaleX, scaleY, 1);
        camera.x = (canvasW - bounds.w * camera.scale) / 2 - bounds.minX * camera.scale;
        camera.y = (canvasH - bounds.h * camera.scale) / 2 - bounds.minY * camera.scale;
        dirty = true;
    }

    /* --- Node Visibility --- */
    function isNodeVisible(node) {
        if (activeFilters.type !== "all" && node.type !== activeFilters.type) return false;
        return true;
    }

    /* --- Drawing: Lanes (PE2-04) --- */
    function drawLanes() {
        for (var i = 0; i < graph.lanes.length; i++) {
            var lane = graph.lanes[i];
            ctx.fillStyle = lane.color;
            ctx.fillRect(lane.x, lane.y, lane.w, lane.h);
            ctx.strokeStyle = "#cbd5e1";
            ctx.lineWidth = 1;
            ctx.strokeRect(lane.x, lane.y, lane.w, lane.h);

            /* Lane label at top */
            ctx.save();
            ctx.fillStyle = "#475569";
            ctx.font = "bold 11px " + getComputedStyle(document.body).fontFamily;
            ctx.textAlign = "center";
            ctx.fillText(lane.label, lane.x + lane.w / 2, lane.y + 16);
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

    /* --- Drawing: Nodes (PE2-05, PE2-06, PE2-10) --- */
    function drawNodes() {
        for (var i = 0; i < graph.nodes.length; i++) {
            var node = graph.nodes[i];
            if (!isNodeVisible(node)) continue;

            var colors = TYPE_COLORS[node.type] || TYPE_COLORS.process;
            var isHovered = hoveredNode === node;
            var isSelected = selectedNode === node;

            /* Dim if path highlighting is active and this node isn't in the path */
            var dimmed = false;
            if (highlightedNodes && !highlightedNodes[node.id]) {
                dimmed = true;
            }

            ctx.save();
            if (dimmed) ctx.globalAlpha = 0.2;

            drawNodeShape(node, colors, isHovered, isSelected);
            drawNodeLabel(node, colors);
            drawStatusChip(node);

            ctx.restore();
        }
    }

    /* --- Drawing: Edges (PE2-07, PE2-08, PE2-09) --- */
    function drawEdges() {
        for (var i = 0; i < graph.edges.length; i++) {
            var edge = graph.edges[i];
            var fromNode = nodeById[edge.from];
            var toNode = nodeById[edge.to];
            if (!fromNode || !toNode) continue;
            if (!isNodeVisible(fromNode) || !isNodeVisible(toNode)) continue;

            var style = EDGE_STYLES[edge.type] || EDGE_STYLES.required;

            /* Dim if path highlighting is active and this edge isn't highlighted */
            var dimmed = false;
            if (highlightedEdges && !highlightedEdges[i]) {
                dimmed = true;
            }

            ctx.save();
            if (dimmed) ctx.globalAlpha = 0.1;

            ctx.strokeStyle = style.color;
            ctx.lineWidth = style.width;
            ctx.setLineDash(style.dash);

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

    /* --- Main Render Loop (PE2-02) --- */
    function render() {
        if (!dirty) {
            requestAnimationFrame(render);
            return;
        }
        dirty = false;

        ctx.clearRect(0, 0, canvasW, canvasH);
        ctx.save();
        ctx.translate(camera.x, camera.y);
        ctx.scale(camera.scale, camera.scale);

        drawLanes();
        drawEdges();
        drawNodes();

        ctx.restore();

        /* Zoom indicator */
        if (zoomIndicator) {
            zoomIndicator.textContent = Math.round(camera.scale * 100) + "%";
        }

        drawMinimap();

        requestAnimationFrame(render);
    }

    /* --- Hit Testing (PE5-01, needed for hover/select) --- */
    function hitTestNode(wx, wy) {
        for (var i = graph.nodes.length - 1; i >= 0; i--) {
            var node = graph.nodes[i];
            if (!isNodeVisible(node)) continue;
            var hw = NODE_W / 2;
            var hh = NODE_H / 2;
            if (wx >= node.x - hw && wx <= node.x + hw && wy >= node.y - hh && wy <= node.y + hh) {
                return node;
            }
        }
        return null;
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
        var world = screenToWorld(sx, sy);
        var hit = hitTestNode(world.x, world.y);
        if (hit !== hoveredNode) {
            hoveredNode = hit;
            canvas.style.cursor = hit ? "pointer" : "grab";
            dirty = true;
        }
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
        var hit = hitTestNode(world.x, world.y);

        if (hit) {
            selectedNode = hit;
            var traced = traceConnectedNodes(hit.id);
            highlightedNodes = traced.nodes;
            highlightedEdges = traced.edges;
            showDetailPanel(hit);
            announce("Selected " + hit.label.replace(/\n/g, " ") + ", " + hit.type);
        } else {
            selectedNode = null;
            highlightedNodes = null;
            highlightedEdges = null;
            hideDetailPanel();
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
            camera.scale = Math.min(camera.scale * 2, camera.maxScale);
            camera.x = canvasW / 2 - hit.x * camera.scale;
            camera.y = canvasH / 2 - hit.y * camera.scale;
            dirty = true;
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
                        camera.scale = 0.8;
                        camera.x = canvasW / 2 - node.x * camera.scale;
                        camera.y = canvasH / 2 - node.y * camera.scale;
                        selectedNode = node;
                        var traced = traceConnectedNodes(node.id);
                        highlightedNodes = traced.nodes;
                        highlightedEdges = traced.edges;
                        showDetailPanel(node);
                        dirty = true;
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
            selectedNode = null;
            hoveredNode = null;
            highlightedNodes = null;
            highlightedEdges = null;
            hideDetailPanel();
            /* Reset filters */
            activeFilters.type = "all";
            for (var ri = 0; ri < filterBtns.length; ri++) {
                filterBtns[ri].classList.toggle("active", filterBtns[ri].getAttribute("data-filter") === "all");
            }
            fitToScreen();
            announce("View reset");
        });
    }

    /* --- Detail Panel Close --- */
    if (detailClose) {
        detailClose.addEventListener("click", function () {
            selectedNode = null;
            highlightedNodes = null;
            highlightedEdges = null;
            hideDetailPanel();
            dirty = true;
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

    function showGuidedStep() {
        if (!activeMode) return;
        var step = activeMode.steps[activeModeStep];
        var node = nodeById[step.nodeId];
        if (node) {
            camera.scale = 0.6;
            camera.x = canvasW / 2 - node.x * camera.scale;
            camera.y = canvasH / 2 - node.y * camera.scale;
            selectedNode = node;
            var traced = traceConnectedNodes(node.id);
            highlightedNodes = traced.nodes;
            highlightedEdges = traced.edges;
            showDetailPanel(node);
        }
        if (guidedText) guidedText.textContent = step.annotation;
        if (guidedStep) guidedStep.textContent = "Step " + (activeModeStep + 1) + " of " + activeMode.steps.length;
        if (guidedPrev) guidedPrev.disabled = activeModeStep === 0;
        if (guidedNext) guidedNext.disabled = activeModeStep === activeMode.steps.length - 1;
        if (guidedOverlay) guidedOverlay.hidden = false;
        dirty = true;
    }

    function exitGuidedMode() {
        activeMode = null;
        activeModeStep = 0;
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
            for (var mk = 0; mk < graph.guidedModes.length; mk++) {
                if (graph.guidedModes[mk].id === modeId) {
                    activeMode = graph.guidedModes[mk];
                    activeModeStep = 0;
                    showGuidedStep();
                    announce("Guided mode: " + activeMode.name);
                    break;
                }
            }
        });
    }

    if (guidedPrev) {
        guidedPrev.addEventListener("click", function () {
            if (activeMode && activeModeStep > 0) {
                activeModeStep--;
                showGuidedStep();
            }
        });
    }
    if (guidedNext) {
        guidedNext.addEventListener("click", function () {
            if (activeMode && activeModeStep < activeMode.steps.length - 1) {
                activeModeStep++;
                showGuidedStep();
            }
        });
    }
    if (guidedExit) {
        guidedExit.addEventListener("click", exitGuidedMode);
    }

    /* --- Minimap Click-to-Navigate (PE7-04) --- */
    if (minimapCanvas) {
        minimapCanvas.addEventListener("click", function (e) {
            var rect = minimapCanvas.getBoundingClientRect();
            var mx = e.clientX - rect.left;
            var my = e.clientY - rect.top;
            var bounds = getGraphBounds();
            var mw = minimapCanvas.width;
            var mh = minimapCanvas.height;
            var scale = Math.min(mw / (bounds.w + 40), mh / (bounds.h + 40));

            var worldX = (mx - 10) / scale + bounds.minX;
            var worldY = (my - 5) / scale + bounds.minY;
            camera.x = canvasW / 2 - worldX * camera.scale;
            camera.y = canvasH / 2 - worldY * camera.scale;
            dirty = true;
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
                camera.scale = 0.8;
                camera.x = canvasW / 2 - node.x * camera.scale;
                camera.y = canvasH / 2 - node.y * camera.scale;
                selectedNode = node;
                var traced = traceConnectedNodes(node.id);
                highlightedNodes = traced.nodes;
                highlightedEdges = traced.edges;
                showDetailPanel(node);
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
            } else {
                selectedNode = null;
                highlightedNodes = null;
                highlightedEdges = null;
                hideDetailPanel();
                dirty = true;
            }
        }
    });

    /* --- Initialization --- */
    window.addEventListener("resize", function () {
        resizeCanvas();
        dirty = true;
    });

    resizeCanvas();
    fitToScreen();
    handleHashNavigation();
    requestAnimationFrame(render);
});
