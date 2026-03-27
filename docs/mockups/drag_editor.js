/**
 * Mockup Drag Editor v3
 *
 * Features:
 *   - Drag nodes; connected edges + labels follow automatically
 *   - Click an edge to select it; drag endpoint handles to re-anchor
 *   - Drag segment handles to slide intermediate path segments
 *   - Hold Shift while dragging a node to lock H/V axis
 *   - Snap to configurable grid (default 5 px)
 *   - Export node + edge changes as JSON for Claude to apply
 */
(function () {
  'use strict';
  var svg = document.querySelector('svg');
  if (!svg) return;

  var NS = 'http://www.w3.org/2000/svg';

  /* ── Persisted state ────────────────────────────────────── */

  var FILE_KEY = 'drag_editor__' + (location.pathname.split('/').pop() || 'unknown');
  var stored = JSON.parse(localStorage.getItem(FILE_KEY) || '{}');
  var savedNodes = {};
  var savedEdgeMods = {};
  if (stored._v === 3) {
    savedNodes = stored.nodes || {};
    savedEdgeMods = stored.edgeMods || {};
  } else if (stored._v === 2) {
    savedNodes = stored.nodes || {};
  } else {
    Object.keys(stored).forEach(function (k) {
      if (stored[k] && stored[k].original && stored[k].current) savedNodes[k] = stored[k];
    });
  }

  /* ── Runtime state ──────────────────────────────────────── */

  var MATCH_TOL = 30;       // edge-endpoint to node boundary matching
  var HIT_TOL = 10;         // click distance to select an edge
  var SNAP_TOL = 15;        // re-anchor snap radius
  var snapGrid = 5;
  var snapEnabled = true;

  var draggables = [];       // node entries
  var connections = [];      // edge descriptors
  var edgeLabels = [];       // { rectEl, textEl, conn, offX, offY }
  var active = null;         // node drag  { entry, startMouse, startPos }
  var selConn = null;        // selected edge connection
  var epDrag = null;         // endpoint drag  { conn, isStart, startMouse }
  var segDrag = null;        // segment drag   { conn, segIdx, isVert, startMouse, startVal }

  var overlay = document.createElementNS(NS, 'g');
  overlay.setAttribute('id', 'de-overlay');
  svg.appendChild(overlay);

  /* ── SVG helpers ────────────────────────────────────────── */

  function svgPt(e) {
    var p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY;
    return p.matrixTransform(svg.getScreenCTM().inverse());
  }
  function parseTr(g) {
    var a = g.getAttribute('transform');
    if (!a) return null;
    var m = a.match(/translate\(\s*([-\d.]+)\s*[,\s]\s*([-\d.]+)\s*\)/);
    return m ? { x: +m[1], y: +m[2] } : null;
  }
  function setTr(g, x, y) { g.setAttribute('transform', 'translate(' + x + ', ' + y + ')'); }
  function labelOf(g) {
    var t = g.querySelectorAll('text');
    for (var i = 0; i < t.length; i++) { var s = t[i].textContent.trim(); if (s) return s; }
    return null;
  }
  function snap(v) { return snapEnabled ? Math.round(v / snapGrid) * snapGrid : Math.round(v); }
  function rd(v) { return Math.round(v); }

  /* ── Geometry ───────────────────────────────────────────── */

  function d2(a, b) { return (a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y); }
  /** Distance from point (px,py) to line segment (ax,ay)-(bx,by). */
  function dSeg(px, py, ax, ay, bx, by) {
    var dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy;
    if (l2 === 0) return Math.hypot(px - ax, py - ay);
    var t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / l2));
    return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
  }

  /* ── Node edge / anchor points ──────────────────────────── */

  /** Return the 4 discrete anchor points for re-anchor snapping. */
  function nodeAnchors(g, pos) {
    var poly = g.querySelector('polygon');
    if (poly) {
      var pts = poly.getAttribute('points').trim().split(/\s+/).map(function (p) {
        var c = p.split(','); return { x: +c[0], y: +c[1] };
      });
      if (pts.length >= 4) return [
        { x: pos.x + pts[0].x, y: pos.y + pts[0].y, side: 'top' },
        { x: pos.x + pts[1].x, y: pos.y + pts[1].y, side: 'right' },
        { x: pos.x + pts[2].x, y: pos.y + pts[2].y, side: 'bottom' },
        { x: pos.x + pts[3].x, y: pos.y + pts[3].y, side: 'left' }
      ];
    }
    var ell = g.querySelector('ellipse');
    if (ell) {
      var rx = +(ell.getAttribute('rx') || 0), h = 60;
      return [
        { x: pos.x, y: pos.y + h / 2, side: 'left' },
        { x: pos.x + rx * 2, y: pos.y + h / 2, side: 'right' },
        { x: pos.x + rx, y: pos.y, side: 'top' },
        { x: pos.x + rx, y: pos.y + h, side: 'bottom' }
      ];
    }
    var r = g.querySelector('rect');
    if (r) {
      var w = +(r.getAttribute('width') || 0), rh = +(r.getAttribute('height') || 0);
      return [
        { x: pos.x, y: pos.y + rh / 2, side: 'left' },
        { x: pos.x + w, y: pos.y + rh / 2, side: 'right' },
        { x: pos.x + w / 2, y: pos.y, side: 'top' },
        { x: pos.x + w / 2, y: pos.y + rh, side: 'bottom' }
      ];
    }
    return [];
  }

  /** Return boundary segments for better endpoint matching. */
  function nodeBoundary(g, pos) {
    var poly = g.querySelector('polygon');
    if (poly) {
      // For diamonds, use tip-points (same as anchors) — matching by point distance
      return { type: 'points', pts: nodeAnchors(g, pos) };
    }
    var ell = g.querySelector('ellipse');
    var r = g.querySelector('rect');
    var w, h;
    if (ell) { w = +(ell.getAttribute('rx') || 0) * 2; h = 60; }
    else if (r) { w = +(r.getAttribute('width') || 0); h = +(r.getAttribute('height') || 0); }
    else return { type: 'points', pts: [] };
    return {
      type: 'segs',
      segs: [
        { x1: pos.x, y1: pos.y, x2: pos.x, y2: pos.y + h, side: 'left' },
        { x1: pos.x + w, y1: pos.y, x2: pos.x + w, y2: pos.y + h, side: 'right' },
        { x1: pos.x, y1: pos.y, x2: pos.x + w, y2: pos.y, side: 'top' },
        { x1: pos.x, y1: pos.y + h, x2: pos.x + w, y2: pos.y + h, side: 'bottom' }
      ]
    };
  }

  /** Find closest node + side for an edge endpoint. Uses boundary matching. */
  function matchEndpoint(pt) {
    var bestD = MATCH_TOL, bestN = null, bestS = null;
    draggables.forEach(function (entry) {
      var b = nodeBoundary(entry.el, entry.original);
      if (b.type === 'points') {
        b.pts.forEach(function (p) {
          var d = Math.hypot(pt.x - p.x, pt.y - p.y);
          if (d < bestD) { bestD = d; bestN = entry; bestS = p.side; }
        });
      } else {
        b.segs.forEach(function (s) {
          var d = dSeg(pt.x, pt.y, s.x1, s.y1, s.x2, s.y2);
          if (d < bestD) { bestD = d; bestN = entry; bestS = s.side; }
        });
      }
    });
    return bestN ? { node: bestN, side: bestS } : null;
  }

  /* ── Path parsing ───────────────────────────────────────── */

  function parsePath(d) {
    var cmds = [], re = /([MLQCSTAZHVmlqcstahvz])\s*((?:[-+]?[\d.]+[\s,]*)*)/g, m;
    while ((m = re.exec(d)) !== null) {
      var ns = m[2].trim();
      cmds.push({ cmd: m[1], nums: ns ? ns.split(/[\s,]+/).filter(Boolean).map(Number) : [] });
    }
    return cmds;
  }
  function cmdsToD(cmds) {
    return cmds.map(function (c) {
      if (!c.nums.length) return c.cmd;
      var p = [];
      for (var i = 0; i < c.nums.length; i += 2)
        p.push(i + 1 < c.nums.length ? rd(c.nums[i]) + ',' + rd(c.nums[i + 1]) : String(rd(c.nums[i])));
      return c.cmd + ' ' + p.join(' ');
    }).join(' ');
  }
  function cpCmds(c) { return c.map(function (x) { return { cmd: x.cmd, nums: x.nums.slice() }; }); }
  function pathEndpoints(cmds) {
    var first = null, last = null;
    if (cmds.length && cmds[0].cmd === 'M') first = { x: cmds[0].nums[0], y: cmds[0].nums[1] };
    for (var i = cmds.length - 1; i >= 0; i--) {
      var c = cmds[i];
      if (c.cmd === 'L') { last = { x: c.nums[0], y: c.nums[1] }; break; }
      if (c.cmd === 'Q') { last = { x: c.nums[2], y: c.nums[3] }; break; }
      if (c.cmd === 'C') { last = { x: c.nums[4], y: c.nums[5] }; break; }
      if (c.cmd === 'M' && i > 0) { last = { x: c.nums[0], y: c.nums[1] }; break; }
    }
    return { start: first, end: last || first };
  }

  /** Get current line segments of a connection (from live DOM). */
  function connSegments(conn) {
    if (conn.type === 'line') {
      return [{ x1: +conn.el.getAttribute('x1'), y1: +conn.el.getAttribute('y1'),
                x2: +conn.el.getAttribute('x2'), y2: +conn.el.getAttribute('y2') }];
    }
    var cmds = parsePath(conn.el.getAttribute('d'));
    var segs = [], cx = 0, cy = 0;
    cmds.forEach(function (c) {
      if (c.cmd === 'M') { cx = c.nums[0]; cy = c.nums[1]; }
      else if (c.cmd === 'L') { segs.push({ x1: cx, y1: cy, x2: c.nums[0], y2: c.nums[1] }); cx = c.nums[0]; cy = c.nums[1]; }
      else if (c.cmd === 'Q') { segs.push({ x1: cx, y1: cy, x2: c.nums[2], y2: c.nums[3] }); cx = c.nums[2]; cy = c.nums[3]; }
    });
    return segs;
  }

  /* ══════════════════════════════════════════════════════════
     Phase 1 — Discover draggable nodes
     ══════════════════════════════════════════════════════════ */

  svg.querySelectorAll('g[transform]').forEach(function (g) {
    var pos = parseTr(g);
    if (!pos) return;
    var lbl = labelOf(g);
    if (!lbl) return;
    draggables.push({ el: g, label: lbl, original: { x: pos.x, y: pos.y } });
    g.style.cursor = 'grab';
  });

  /* ══════════════════════════════════════════════════════════
     Phase 2 — Discover edges & match endpoints to nodes
     ══════════════════════════════════════════════════════════ */

  function isExcluded(el) {
    var p = el.parentElement;
    while (p && p !== svg) {
      var t = p.tagName.toLowerCase();
      if (t === 'defs' || t === 'pattern') return true;
      if (draggables.some(function (d) { return d.el === p; })) return true;
      p = p.parentElement;
    }
    return false;
  }

  function edgeKey(conn) {
    if (conn.type === 'line') {
      var o = conn.orig;
      return 'L:' + o.x1 + ',' + o.y1 + ':' + o.x2 + ',' + o.y2;
    }
    return 'P:' + conn.origD.substring(0, 120);
  }

  svg.querySelectorAll('line').forEach(function (el) {
    if (isExcluded(el)) return;
    var x1 = +el.getAttribute('x1'), y1 = +el.getAttribute('y1');
    var x2 = +el.getAttribute('x2'), y2 = +el.getAttribute('y2');
    var sm = matchEndpoint({ x: x1, y: y1 }), em = matchEndpoint({ x: x2, y: y2 });
    if (sm || em) connections.push({
      el: el, type: 'line',
      startNode: sm ? sm.node : null, startSide: sm ? sm.side : null,
      endNode: em ? em.node : null, endSide: em ? em.side : null,
      orig: { x1: x1, y1: y1, x2: x2, y2: y2 }, overrides: {}
    });
  });

  svg.querySelectorAll('path').forEach(function (el) {
    if (isExcluded(el)) return;
    var fill = el.getAttribute('fill');
    if (fill && fill !== 'none') return;
    var d = el.getAttribute('d');
    if (!d) return;
    var cmds = parsePath(d), ep = pathEndpoints(cmds);
    if (!ep.start) return;
    var sm = matchEndpoint(ep.start), em = ep.end ? matchEndpoint(ep.end) : null;
    if (sm || em) connections.push({
      el: el, type: 'path',
      startNode: sm ? sm.node : null, startSide: sm ? sm.side : null,
      endNode: em ? em.node : null, endSide: em ? em.side : null,
      origD: d, origCmds: cmds, overrides: {}
    });
  });

  /* ══════════════════════════════════════════════════════════
     Phase 3 — Discover edge labels (small rect+text pills)
     ══════════════════════════════════════════════════════════ */

  svg.querySelectorAll('rect').forEach(function (rect) {
    if (isExcluded(rect)) return;
    var h = +(rect.getAttribute('height') || 999);
    if (h > 22) return;                   // not a label pill
    var rx = +(rect.getAttribute('rx') || 0);
    if (rx < 2) return;                   // not rounded = not a pill
    // Find adjacent <text> sibling
    var next = rect.nextElementSibling;
    if (!next || next.tagName !== 'text') return;
    // Compute pill center
    var cx = +(rect.getAttribute('x') || 0) + +(rect.getAttribute('width') || 0) / 2;
    var cy = +(rect.getAttribute('y') || 0) + h / 2;
    // Match to closest edge within 30px
    var bestD = 30, bestC = null;
    connections.forEach(function (conn) {
      var segs = connSegments(conn);
      segs.forEach(function (s) {
        var d = dSeg(cx, cy, s.x1, s.y1, s.x2, s.y2);
        if (d < bestD) { bestD = d; bestC = conn; }
      });
    });
    if (bestC) edgeLabels.push({ rectEl: rect, textEl: next, conn: bestC, origRX: +rect.getAttribute('x'), origRY: +rect.getAttribute('y'), origTX: +next.getAttribute('x'), origTY: +next.getAttribute('y') });
  });

  /* ══════════════════════════════════════════════════════════
     Edge computation — position edges based on node + overrides
     ══════════════════════════════════════════════════════════ */

  function nDelta(entry) {
    if (!entry) return { x: 0, y: 0 };
    var c = parseTr(entry.el);
    return { x: c.x - entry.original.x, y: c.y - entry.original.y };
  }

  /** Get the anchor point for a given side on a node at its current position. */
  function anchorPt(entry, side) {
    var pos = parseTr(entry.el);
    var pts = nodeAnchors(entry.el, pos);
    var a = pts.find(function (p) { return p.side === side; });
    return a || pos;
  }

  function computeLineUpdate(conn) {
    var o = conn.orig, ov = conn.overrides || {};
    var r = { x1: o.x1, y1: o.y1, x2: o.x2, y2: o.y2 };
    // Start
    if (ov.startSide && conn.startNode) {
      var a = anchorPt(conn.startNode, ov.startSide);
      r.x1 = a.x; r.y1 = a.y;
    } else if (conn.startNode) {
      var d = nDelta(conn.startNode); r.x1 += d.x; r.y1 += d.y;
    }
    // End
    if (ov.endSide && conn.endNode) {
      var a2 = anchorPt(conn.endNode, ov.endSide);
      r.x2 = a2.x; r.y2 = a2.y;
    } else if (conn.endNode) {
      var d2 = nDelta(conn.endNode); r.x2 += d2.x; r.y2 += d2.y;
    }
    return { x1: rd(r.x1), y1: rd(r.y1), x2: rd(r.x2), y2: rd(r.y2) };
  }

  function computePathUpdate(conn) {
    var cmds = cpCmds(conn.origCmds), len = cmds.length;
    var ov = conn.overrides || {};
    var segOffs = ov.segOffsets || {};

    // Start endpoint
    if (ov.startSide && conn.startNode) {
      var a = anchorPt(conn.startNode, ov.startSide);
      cmds[0].nums[0] = a.x; cmds[0].nums[1] = a.y;
    } else if (conn.startNode) {
      var sd = nDelta(conn.startNode);
      cmds[0].nums[0] += sd.x; cmds[0].nums[1] += sd.y;
      if (len > 2 && cmds[1].cmd === 'L') {
        var oMx = conn.origCmds[0].nums[0], oMy = conn.origCmds[0].nums[1];
        var oLx = conn.origCmds[1].nums[0], oLy = conn.origCmds[1].nums[1];
        if (Math.abs(oMy - oLy) < 2) cmds[1].nums[1] += sd.y;
        if (Math.abs(oMx - oLx) < 2) cmds[1].nums[0] += sd.x;
      }
    }

    // End endpoint
    var li = len - 1;
    if (ov.endSide && conn.endNode) {
      var a2 = anchorPt(conn.endNode, ov.endSide);
      if (cmds[li].cmd === 'L') { cmds[li].nums[0] = a2.x; cmds[li].nums[1] = a2.y; }
      else if (cmds[li].cmd === 'Q') { cmds[li].nums[2] = a2.x; cmds[li].nums[3] = a2.y; }
    } else if (conn.endNode) {
      var ed = nDelta(conn.endNode);
      if (cmds[li].cmd === 'L') {
        cmds[li].nums[0] += ed.x; cmds[li].nums[1] += ed.y;
        if (len > 2) {
          var pi = li - 1;
          if (cmds[pi].cmd === 'L' || cmds[pi].cmd === 'M') {
            var oEx = conn.origCmds[li].nums[0], oEy = conn.origCmds[li].nums[1];
            var oPx = conn.origCmds[pi].nums[0], oPy = conn.origCmds[pi].nums[1];
            if (Math.abs(oEy - oPy) < 2) cmds[pi].nums[1] += ed.y;
            if (Math.abs(oEx - oPx) < 2) cmds[pi].nums[0] += ed.x;
          }
        }
      } else if (cmds[li].cmd === 'Q') {
        cmds[li].nums[0] += ed.x; cmds[li].nums[1] += ed.y;
        cmds[li].nums[2] += ed.x; cmds[li].nums[3] += ed.y;
      }
    }

    // Segment offsets (intermediate segments only)
    for (var si in segOffs) {
      var idx = +si, off = segOffs[si];
      if (idx < 0 || idx + 1 >= len) continue;
      var isV = Math.abs(conn.origCmds[idx].nums[0] - conn.origCmds[idx + 1].nums[0]) < 2;
      if (isV) { cmds[idx].nums[0] += off; cmds[idx + 1].nums[0] += off; }
      else     { cmds[idx].nums[1] += off; cmds[idx + 1].nums[1] += off; }
    }

    return { d: cmdsToD(cmds) };
  }

  function computeEdge(conn) {
    return conn.type === 'line' ? computeLineUpdate(conn) : computePathUpdate(conn);
  }

  function applyEdge(conn, upd) {
    if (!upd) return;
    if (conn.type === 'line') {
      conn.el.setAttribute('x1', upd.x1); conn.el.setAttribute('y1', upd.y1);
      conn.el.setAttribute('x2', upd.x2); conn.el.setAttribute('y2', upd.y2);
    } else if (upd.d) {
      conn.el.setAttribute('d', upd.d);
    }
  }

  function updateAllEdges() {
    connections.forEach(function (c) { applyEdge(c, computeEdge(c)); });
  }

  /* ── Label repositioning ────────────────────────────────── */

  /** Compute the midpoint of a connection's current geometry. */
  function edgeMidpoint(conn) {
    if (conn.type === 'path') {
      try {
        var len = conn.el.getTotalLength();
        var pt = conn.el.getPointAtLength(len / 2);
        return { x: pt.x, y: pt.y };
      } catch (e) { /* fallthrough */ }
    }
    var segs = connSegments(conn);
    if (!segs.length) return { x: 0, y: 0 };
    // Use midpoint of the middle segment
    var mid = segs[Math.floor(segs.length / 2)];
    return { x: (mid.x1 + mid.x2) / 2, y: (mid.y1 + mid.y2) / 2 };
  }

  /** Cache original midpoints for offset computation. */
  edgeLabels.forEach(function (lbl) {
    var mp = edgeMidpoint(lbl.conn);
    var rcx = lbl.origRX + +(lbl.rectEl.getAttribute('width') || 0) / 2;
    var rcy = lbl.origRY + +(lbl.rectEl.getAttribute('height') || 0) / 2;
    lbl.offX = rcx - mp.x;
    lbl.offY = rcy - mp.y;
  });

  function updateAllLabels() {
    edgeLabels.forEach(function (lbl) {
      var mp = edgeMidpoint(lbl.conn);
      var ncx = mp.x + lbl.offX, ncy = mp.y + lbl.offY;
      var rw = +(lbl.rectEl.getAttribute('width') || 0);
      var rh = +(lbl.rectEl.getAttribute('height') || 0);
      lbl.rectEl.setAttribute('x', rd(ncx - rw / 2));
      lbl.rectEl.setAttribute('y', rd(ncy - rh / 2));
      lbl.textEl.setAttribute('x', rd(ncx));
      lbl.textEl.setAttribute('y', rd(ncy + rh / 2 - 2));
    });
  }

  /* ══════════════════════════════════════════════════════════
     Phase 4 — Apply saved state
     ══════════════════════════════════════════════════════════ */

  draggables.forEach(function (e) {
    var s = savedNodes[e.label];
    if (s) { e.original = s.original; setTr(e.el, s.current.x, s.current.y); }
  });
  connections.forEach(function (c) {
    var k = edgeKey(c);
    if (savedEdgeMods[k]) c.overrides = savedEdgeMods[k];
  });
  updateAllEdges();
  updateAllLabels();

  /* ══════════════════════════════════════════════════════════
     Handle & anchor rendering
     ══════════════════════════════════════════════════════════ */

  var handles = [];
  var anchorDots = [];

  function clearOverlay() {
    while (overlay.firstChild) overlay.removeChild(overlay.firstChild);
    handles = []; anchorDots = [];
  }

  function mkCircle(cx, cy, r, fill, cls, data) {
    var c = document.createElementNS(NS, 'circle');
    c.setAttribute('cx', rd(cx)); c.setAttribute('cy', rd(cy));
    c.setAttribute('r', r); c.setAttribute('fill', fill);
    c.setAttribute('stroke', '#0f172a'); c.setAttribute('stroke-width', '1.5');
    c.setAttribute('cursor', 'pointer');
    c.classList.add(cls);
    if (data) Object.keys(data).forEach(function (k) { c.dataset[k] = data[k]; });
    overlay.appendChild(c);
    return c;
  }

  function mkRect(cx, cy, sz, fill, cls, data) {
    var r = document.createElementNS(NS, 'rect');
    r.setAttribute('x', rd(cx - sz / 2)); r.setAttribute('y', rd(cy - sz / 2));
    r.setAttribute('width', sz); r.setAttribute('height', sz);
    r.setAttribute('fill', fill); r.setAttribute('stroke', '#0f172a');
    r.setAttribute('stroke-width', '1.5'); r.setAttribute('cursor', 'pointer');
    r.classList.add(cls);
    if (data) Object.keys(data).forEach(function (k) { r.dataset[k] = data[k]; });
    overlay.appendChild(r);
    return r;
  }

  function showEdgeHandles(conn) {
    clearOverlay();
    var segs = connSegments(conn);
    if (!segs.length) return;

    // Endpoint handles (circles)
    var first = segs[0], last = segs[segs.length - 1];
    var epH1 = mkCircle(first.x1, first.y1, 6, '#38bdf8', 'de-ep', { end: 'start' });
    var epH2 = mkCircle(last.x2, last.y2, 6, '#38bdf8', 'de-ep', { end: 'end' });
    handles.push(epH1, epH2);

    // Segment midpoint handles (squares) — skip first/last if connected to a node
    var startSeg = conn.startNode ? 0 : -1;
    var endSeg = conn.endNode ? segs.length - 1 : -1;
    segs.forEach(function (s, i) {
      if (i === startSeg || i === endSeg) return;
      // Only show on clearly H or V segments
      var isV = Math.abs(s.x1 - s.x2) < 3;
      var isH = Math.abs(s.y1 - s.y2) < 3;
      if (!isV && !isH) return;
      var mx = (s.x1 + s.x2) / 2, my = (s.y1 + s.y2) / 2;
      var h = mkRect(mx, my, 8, '#a78bfa', 'de-seg', { idx: String(i), vert: isV ? '1' : '0' });
      h.setAttribute('cursor', isV ? 'ew-resize' : 'ns-resize');
      handles.push(h);
    });

    // Show anchor dots on connected nodes
    [conn.startNode, conn.endNode].forEach(function (n) {
      if (!n) return;
      var pos = parseTr(n.el);
      nodeAnchors(n.el, pos).forEach(function (a) {
        var dot = mkCircle(a.x, a.y, 4, '#22c55e', 'de-anchor', { side: a.side });
        dot.setAttribute('opacity', '0.5');
        anchorDots.push(dot);
      });
    });
  }

  function highlightConn(conn, on) {
    if (on) {
      conn._os = conn.el.getAttribute('stroke');
      conn.el.setAttribute('stroke', '#38bdf8');
      conn.el.style.filter = 'drop-shadow(0 0 3px #38bdf8)';
    } else {
      if (conn._os) conn.el.setAttribute('stroke', conn._os);
      conn.el.style.filter = '';
    }
  }

  /* ══════════════════════════════════════════════════════════
     Hit-testing — find edge nearest to a click
     ══════════════════════════════════════════════════════════ */

  function hitTestEdge(pt) {
    var bestD = HIT_TOL, bestC = null, bestSeg = -1;
    connections.forEach(function (conn) {
      connSegments(conn).forEach(function (s, i) {
        var d = dSeg(pt.x, pt.y, s.x1, s.y1, s.x2, s.y2);
        if (d < bestD) { bestD = d; bestC = conn; bestSeg = i; }
      });
    });
    return bestC ? { conn: bestC, segIdx: bestSeg } : null;
  }

  /* ══════════════════════════════════════════════════════════
     Interaction — unified mouse handlers
     ══════════════════════════════════════════════════════════ */

  function deselectEdge() {
    if (selConn) { highlightConn(selConn, false); selConn = null; }
    clearOverlay();
  }

  svg.addEventListener('mousedown', function (e) {
    var pt = svgPt(e);
    var tgt = e.target;

    // ── Priority 1: overlay handle clicked ──
    if (tgt.classList.contains('de-ep')) {
      e.preventDefault(); e.stopPropagation();
      epDrag = { conn: selConn, isStart: tgt.dataset.end === 'start', startMouse: pt };
      return;
    }
    if (tgt.classList.contains('de-seg')) {
      e.preventDefault(); e.stopPropagation();
      var isV = tgt.dataset.vert === '1';
      segDrag = { conn: selConn, segIdx: +tgt.dataset.idx, isVert: isV, startMouse: pt, startVal: 0 };
      // Compute current offset value for this segment from overrides
      var so = (selConn.overrides || {}).segOffsets || {};
      segDrag.startVal = so[segDrag.segIdx] || 0;
      return;
    }

    // ── Priority 2: node drag ──
    var node = tgt;
    while (node && node !== svg) {
      var entry = draggables.find(function (d) { return d.el === node; });
      if (entry) {
        e.preventDefault(); e.stopPropagation();
        deselectEdge();
        var cur = parseTr(entry.el);
        active = { entry: entry, startMouse: pt, startPos: cur };
        entry.el.style.cursor = 'grabbing';
        highlightNodeEdges(entry, true);
        updateInfo(entry.label, cur.x, cur.y, countEdges(entry));
        return;
      }
      node = node.parentElement;
    }

    // ── Priority 3: edge select ──
    var hit = hitTestEdge(pt);
    if (hit) {
      e.preventDefault();
      deselectEdge();
      selConn = hit.conn;
      highlightConn(selConn, true);
      showEdgeHandles(selConn);
      var sl = (selConn.startNode ? selConn.startNode.label : '?');
      var el = (selConn.endNode ? selConn.endNode.label : '?');
      infoEl().innerHTML = '<span style="color:#38bdf8">Edge selected</span><br>' +
        '<span style="font-size:11px;color:#94a3b8">' + sl + ' \u2192 ' + el + '</span>';
      return;
    }

    // ── Priority 4: deselect ──
    deselectEdge();
  });

  svg.addEventListener('mousemove', function (e) {
    var pt = svgPt(e);

    // ── Node drag ──
    if (active) {
      var rx = pt.x - active.startMouse.x, ry = pt.y - active.startMouse.y;
      if (e.shiftKey) { if (Math.abs(rx) >= Math.abs(ry)) ry = 0; else rx = 0; }
      var nx = snap(active.startPos.x + rx), ny = snap(active.startPos.y + ry);
      setTr(active.entry.el, nx, ny);
      updateAllEdges(); updateAllLabels();
      updateInfo(active.entry.label, nx, ny, countEdges(active.entry));
      return;
    }

    // ── Endpoint re-anchor drag ──
    if (epDrag) {
      // Find closest anchor on any node
      var bestD2 = SNAP_TOL * SNAP_TOL, bestA = null, bestN = null;
      draggables.forEach(function (entry) {
        var pos = parseTr(entry.el);
        nodeAnchors(entry.el, pos).forEach(function (a) {
          var dist = d2(pt, a);
          if (dist < bestD2) { bestD2 = dist; bestA = a; bestN = entry; }
        });
      });

      var conn = epDrag.conn;
      if (!conn.overrides) conn.overrides = {};
      if (bestA) {
        if (epDrag.isStart) {
          conn.overrides.startSide = bestA.side;
          conn.startNode = bestN;
        } else {
          conn.overrides.endSide = bestA.side;
          conn.endNode = bestN;
        }
      }
      updateAllEdges(); updateAllLabels();
      showEdgeHandles(conn);
      return;
    }

    // ── Segment slide drag ──
    if (segDrag) {
      var conn2 = segDrag.conn;
      if (!conn2.overrides) conn2.overrides = {};
      if (!conn2.overrides.segOffsets) conn2.overrides.segOffsets = {};
      var delta;
      if (segDrag.isVert) {
        delta = pt.x - segDrag.startMouse.x;
      } else {
        delta = pt.y - segDrag.startMouse.y;
      }
      conn2.overrides.segOffsets[segDrag.segIdx] = snap(segDrag.startVal + delta) - segDrag.startVal + segDrag.startVal;
      // Simplify: just snap the total
      conn2.overrides.segOffsets[segDrag.segIdx] = snap(segDrag.startVal + delta);
      updateAllEdges(); updateAllLabels();
      showEdgeHandles(conn2);
      return;
    }
  });

  window.addEventListener('mouseup', function () {
    // ── Finish node drag ──
    if (active) {
      var entry = active.entry;
      entry.el.style.cursor = 'grab';
      highlightNodeEdges(entry, false);
      var cur = parseTr(entry.el);
      savedNodes[entry.label] = { original: entry.original, current: { x: cur.x, y: cur.y } };
      entry.el.dataset.moved = (cur.x !== entry.original.x || cur.y !== entry.original.y) ? 'true' : '';
      if (!entry.el.dataset.moved) delete entry.el.dataset.moved;
      persist(); updateBadges(); updateBadgeCount();
      active = null;
      return;
    }

    // ── Finish endpoint drag ──
    if (epDrag) {
      var conn = epDrag.conn;
      savedEdgeMods[edgeKey(conn)] = conn.overrides;
      persist();
      epDrag = null;
      if (conn === selConn) showEdgeHandles(conn);
      return;
    }

    // ── Finish segment drag ──
    if (segDrag) {
      var conn2 = segDrag.conn;
      savedEdgeMods[edgeKey(conn2)] = conn2.overrides;
      persist();
      segDrag = null;
      if (conn2 === selConn) showEdgeHandles(conn2);
      return;
    }
  });

  window.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') deselectEdge();
  });

  /* ── Node edge highlighting ─────────────────────────────── */

  function highlightNodeEdges(entry, on) {
    connections.forEach(function (c) {
      if (c.startNode === entry || c.endNode === entry) {
        if (on) { c._ns = c.el.getAttribute('stroke'); c.el.setAttribute('stroke', '#38bdf8'); c.el.style.filter = 'drop-shadow(0 0 2px #38bdf8)'; }
        else { if (c._ns) c.el.setAttribute('stroke', c._ns); c.el.style.filter = ''; }
      }
    });
  }
  function countEdges(entry) {
    var n = 0;
    connections.forEach(function (c) { if (c.startNode === entry || c.endNode === entry) n++; });
    return n;
  }

  /* ── Persistence ────────────────────────────────────────── */

  function persist() {
    localStorage.setItem(FILE_KEY, JSON.stringify({ _v: 3, nodes: savedNodes, edgeMods: savedEdgeMods }));
  }

  /* ── Visual badges ──────────────────────────────────────── */

  var badges = [];
  function updateBadges() {
    badges.forEach(function (b) { b.remove(); }); badges.length = 0;
    draggables.forEach(function (d) {
      if (!d.el.dataset.moved) return;
      var shape = d.el.querySelector('rect, polygon');
      if (!shape) return;
      var dot = document.createElementNS(NS, 'circle');
      var cx = 0, cy = 0;
      if (shape.tagName === 'rect') { cx = +(shape.getAttribute('width') || 0) - 4; cy = 4; }
      else { cx = 8; cy = 4; }
      dot.setAttribute('cx', cx); dot.setAttribute('cy', cy); dot.setAttribute('r', '4');
      dot.setAttribute('fill', '#f59e0b'); dot.setAttribute('stroke', '#0f172a'); dot.setAttribute('stroke-width', '1');
      d.el.appendChild(dot); badges.push(dot);
    });
  }

  /* ── UI Panel ───────────────────────────────────────────── */

  var panel = document.createElement('div');
  panel.id = 'drag-editor-panel';
  panel.innerHTML = [
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">',
    '  <strong style="font-size:13px">Drag Editor v3</strong>',
    '  <span id="de-badge" style="background:#334155;padding:1px 7px;border-radius:9px;font-size:11px">0 moved</span>',
    '</div>',
    '<div id="de-info" style="font-size:12px;font-family:monospace;color:#94a3b8;min-height:52px;margin-bottom:8px">',
    '  Drag nodes. Click edges to select.<br>',
    '  <span style="color:#64748b;font-size:11px">',
    '    <kbd style="background:#334155;padding:1px 4px;border-radius:3px;font-size:10px">Shift</kbd> lock H/V &middot; ',
    '    <kbd style="background:#334155;padding:1px 4px;border-radius:3px;font-size:10px">Esc</kbd> deselect',
    '  </span>',
    '</div>',
    '<div id="de-stats" style="font-size:11px;color:#64748b;margin-bottom:8px"></div>',
    '<label style="font-size:12px;display:flex;align-items:center;gap:6px;margin-bottom:10px;cursor:pointer">',
    '  <input type="checkbox" id="de-snap" checked style="cursor:pointer"> Snap',
    '  <input type="number" id="de-grid" value="5" min="1" max="50" style="width:36px;background:#1e293b;border:1px solid #334155;color:#e2e8f0;border-radius:4px;padding:2px 4px;font-size:11px"> px',
    '</label>',
    '<div style="display:flex;gap:6px">',
    '  <button id="de-export" style="flex:1">Export Changes</button>',
    '  <button id="de-reset" style="flex:1;background:#334155">Reset All</button>',
    '</div>',
    '<pre id="de-output" style="display:none;margin-top:8px;max-height:300px;overflow:auto;',
    '  background:#0f172a;border:1px solid #334155;border-radius:4px;padding:8px;font-size:11px;',
    '  white-space:pre-wrap;word-break:break-all;color:#e2e8f0;cursor:text;user-select:all"></pre>'
  ].join('\n');
  Object.assign(panel.style, {
    position: 'fixed', bottom: '16px', right: '16px', width: '300px',
    background: '#1e293b', border: '1px solid #334155', borderRadius: '8px',
    padding: '12px', color: '#e2e8f0', fontFamily: 'system-ui, sans-serif',
    zIndex: '99999', boxShadow: '0 4px 24px rgba(0,0,0,0.5)'
  });
  document.body.appendChild(panel);
  panel.querySelectorAll('button').forEach(function (b) {
    Object.assign(b.style, { background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '4px', padding: '6px 10px', fontSize: '12px', cursor: 'pointer', fontWeight: '600' });
  });
  document.getElementById('de-reset').style.background = '#334155';

  function infoEl() { return document.getElementById('de-info'); }
  document.getElementById('de-stats').textContent = draggables.length + ' nodes \u00b7 ' + connections.length + ' edges \u00b7 ' + edgeLabels.length + ' labels';

  function updateInfo(label, x, y, ec) {
    infoEl().innerHTML = '<span style="color:#e2e8f0">' + label + '</span>  \u2192  (' + x + ', ' + y + ')' +
      (ec ? '<br><span style="color:#64748b;font-size:11px">' + ec + ' edge' + (ec !== 1 ? 's' : '') + '</span>' : '');
  }

  function updateBadgeCount() {
    var count = 0;
    Object.keys(savedNodes).forEach(function (k) { var s = savedNodes[k]; if (s.current.x !== s.original.x || s.current.y !== s.original.y) count++; });
    // Also count edge modifications
    var edgeMods = Object.keys(savedEdgeMods).length;
    var badge = document.getElementById('de-badge');
    var total = count + edgeMods;
    badge.textContent = count + ' node' + (count !== 1 ? 's' : '') + (edgeMods ? ' + ' + edgeMods + ' edge' + (edgeMods !== 1 ? 's' : '') : '');
    badge.style.background = total > 0 ? '#f59e0b' : '#334155';
    badge.style.color = total > 0 ? '#0f172a' : '#94a3b8';
  }
  updateBadgeCount();

  document.getElementById('de-snap').addEventListener('change', function () { snapEnabled = this.checked; });
  document.getElementById('de-grid').addEventListener('input', function () { snapGrid = parseInt(this.value) || 5; });

  /* ── Export ──────────────────────────────────────────────── */

  document.getElementById('de-export').addEventListener('click', function () {
    var out = document.getElementById('de-output');
    var nodeChg = [], edgeChg = [];

    Object.keys(savedNodes).forEach(function (label) {
      var s = savedNodes[label];
      if (s.current.x !== s.original.x || s.current.y !== s.original.y)
        nodeChg.push({ label: label, original: s.original, 'new': s.current });
    });

    connections.forEach(function (conn) {
      var moved = false;
      if (conn.startNode) { var d = nDelta(conn.startNode); if (d.x || d.y) moved = true; }
      if (conn.endNode) { var d2a = nDelta(conn.endNode); if (d2a.x || d2a.y) moved = true; }
      var ov = conn.overrides || {};
      if (ov.startSide || ov.endSide || (ov.segOffsets && Object.keys(ov.segOffsets).length)) moved = true;
      if (!moved) return;

      var upd = computeEdge(conn);
      if (conn.type === 'line') {
        edgeChg.push({ type: 'line', original: conn.orig, 'new': upd });
      } else {
        edgeChg.push({ type: 'path', original_d: conn.origD, new_d: upd.d });
      }
    });

    if (!nodeChg.length && !edgeChg.length) { out.textContent = 'No changes.'; out.style.display = 'block'; return; }

    var result = { file: location.pathname.split('/').pop(), nodes: nodeChg, edges: edgeChg };
    var json = JSON.stringify(result, null, 2);
    out.textContent = json; out.style.display = 'block';
    if (navigator.clipboard) navigator.clipboard.writeText(json).then(function () {
      var b = document.getElementById('de-export'), orig = b.textContent;
      b.textContent = 'Copied!'; setTimeout(function () { b.textContent = orig; }, 1500);
    });
  });

  /* ── Reset ──────────────────────────────────────────────── */

  document.getElementById('de-reset').addEventListener('click', function () {
    deselectEdge();
    draggables.forEach(function (d) { setTr(d.el, d.original.x, d.original.y); delete d.el.dataset.moved; });
    connections.forEach(function (c) { c.overrides = {}; });
    Object.keys(savedNodes).forEach(function (k) { delete savedNodes[k]; });
    Object.keys(savedEdgeMods).forEach(function (k) { delete savedEdgeMods[k]; });
    persist(); updateAllEdges(); updateAllLabels(); updateBadges(); updateBadgeCount();
    infoEl().innerHTML = 'All positions reset.';
    document.getElementById('de-output').style.display = 'none';
  });

  /* ── Init ───────────────────────────────────────────────── */

  draggables.forEach(function (d) {
    var s = savedNodes[d.label];
    if (s && (s.current.x !== s.original.x || s.current.y !== s.original.y)) d.el.dataset.moved = 'true';
  });
  updateBadges();
  window.addEventListener('mouseup', function () { setTimeout(updateBadgeCount, 0); });

  console.log('[Drag Editor v3] ' + draggables.length + ' nodes, ' + connections.length + ' edges, ' + edgeLabels.length + ' labels.');
})();
