# Mockup Editing Guide

How to manually reposition objects in the pipeline mockup HTML files.

## Quick Reference

| What you want to move | What to change |
|----------------------|----------------|
| A rectangular node | `transform="translate(X, Y)"` on its `<g>` |
| A diamond node | `transform="translate(X, Y)"` on its `<g>` |
| An edge/line | `x1,y1` (start) and `x2,y2` (end) attributes |
| A routed path | `d="M x,y L x,y L x,y ..."` attribute |
| A text label | `x` and `y` attributes on `<text>` |
| A label pill (rect+text) | `x,y` on `<rect>` and `x,y` on `<text>` |

---

## Coordinate System

- Origin `(0,0)` is the **top-left** corner of the SVG.
- **X increases rightward**, Y increases downward.
- The `viewBox` attribute on `<svg>` defines the coordinate space (e.g., `viewBox="0 0 900 500"` means 900 units wide, 500 tall).
- All coordinates inside the SVG use this coordinate space regardless of the rendered pixel size.

## Moving Rectangular Nodes

Rectangular nodes are wrapped in a `<g>` (group) element with a `translate` transform:

```html
<g class="node" transform="translate(100, 80)">
  <rect width="230" height="50" rx="8" .../>
  <text x="16" y="20" ...>dim_occupation</text>
</g>
```

- **`translate(X, Y)`** sets the top-left corner of the group.
- Everything inside the group (rect, text) is positioned relative to this origin.
- To move the node, change only the translate values. Do NOT change the internal rect/text coordinates.

**Example:** Move `dim_occupation` 50px right and 20px down:
```
Before: transform="translate(100, 80)"
After:  transform="translate(150, 100)"
```

### Node edge coordinates (for connecting edges)

After moving a node, you need to know where its edges are to fix connected lines:

```
Node at translate(X, Y) with width W and height H:

  Left center:   (X,       Y + H/2)
  Right center:  (X + W,   Y + H/2)
  Top center:    (X + W/2, Y)
  Bottom center: (X + W/2, Y + H)
```

**Example:** A node at `translate(100, 80)` with `width="230" height="50"`:
- Left center: `(100, 105)`
- Right center: `(330, 105)`
- Top center: `(215, 80)`
- Bottom center: `(215, 130)`

## Moving Diamond Nodes

Diamond nodes use the same `translate` pattern but contain a `<polygon>`:

```html
<g class="node" transform="translate(130, 90)">
  <polygon points="60,0 120,65 60,130 0,65" .../>
  <text x="60" y="58" text-anchor="middle" ...>Schema Drift</text>
</g>
```

The polygon `points` define the diamond shape relative to the group origin:
```
points="60,0  120,65  60,130  0,65"
        Top    Right   Bottom  Left
```

This diamond is 120 units wide and 130 units tall, centered at local `(60, 65)`.

### Diamond tip coordinates

```
Diamond at translate(X, Y) with points="60,0 120,65 60,130 0,65":

  Top tip:    (X + 60,  Y)        — connect edges entering from above
  Right tip:  (X + 120, Y + 65)   — connect edges entering from the right
  Bottom tip: (X + 60,  Y + 130)  — connect edges entering from below
  Left tip:   (X + 0,   Y + 65)   — connect edges entering from the left
```

**Example:** Diamond at `translate(340, 90)`:
- Left tip: `(340, 155)`
- Right tip: `(460, 155)`
- Top tip: `(400, 90)`
- Bottom tip: `(400, 220)`

## Moving Edges

### Simple lines

```html
<line x1="250" y1="155" x2="340" y2="155" stroke="..." marker-end="url(#arrow)"/>
```

- `x1,y1` = start point (should be at a node edge)
- `x2,y2` = end point (should be at a node edge)
- The arrowhead renders at the `x2,y2` end (via `marker-end`)

### Multi-segment paths

Routed edges use `<path>` with move (M) and line-to (L) commands:

```html
<path d="M 100,105 L 85,105 L 85,375 L 215,375 L 215,435" .../>
```

Reading this path:
```
M 100,105   — start at (100, 105)
L 85,105    — line to (85, 105)     ← horizontal left
L 85,375    — line to (85, 375)     ← vertical down
L 215,375   — line to (215, 375)    ← horizontal right
L 215,435   — line to (215, 435)    ← vertical down to target
```

- The **first** coordinate (after M) should match a source node edge.
- The **last** coordinate (final L) should match a target node edge.
- Intermediate coordinates are routing waypoints.

### Curved paths

Some edges use quadratic Bézier curves:

```html
<path d="M 370,640 Q 435,607 500,575" .../>
```

- `M x,y` = start point
- `Q cx,cy x,y` = curve through control point `(cx,cy)` to endpoint `(x,y)`
- Moving the control point changes the curve's bend.

## Moving Label Pills

Label pills are a rect + text pair:

```html
<rect x="248" y="143" width="90" height="16" rx="8" fill="#0f172a" stroke="#f59e0b" .../>
<text x="293" y="154" text-anchor="middle" font-size="8" fill="#f59e0b">schema valid</text>
```

To move a pill, update both elements together:
- **rect:** change `x` and `y` (top-left corner of the background box)
- **text:** change `x` and `y` (text baseline position, usually centered in the rect)

The text position relative to the rect:
```
text.x = rect.x + rect.width / 2     (when text-anchor="middle")
text.y = rect.y + rect.height - 2    (approximate baseline)
```

**Example:** Move a pill 30px right:
```
Before: <rect x="248" y="143" width="90" height="16" .../>
        <text x="293" y="154" ...>
After:  <rect x="278" y="143" width="90" height="16" .../>
        <text x="323" y="154" ...>
```

## The Lane Background

The lane is a large rounded rectangle behind all nodes:

```html
<rect x="55" y="40" width="790" height="410" rx="8" fill="#ef444408" stroke="#ef444425" .../>
```

If you move nodes outside the lane bounds, expand the lane by adjusting its `x`, `y`, `width`, or `height`. The SVG `viewBox` may also need to grow.

## Resizing the Canvas

If you need more room, change both the SVG dimensions and viewBox:

```html
<svg width="900" height="500" viewBox="0 0 900 500">
```

- `width/height` = rendered size in the browser
- `viewBox` = coordinate space (keep these matching for 1:1 mapping)
- After resizing, also update the background grid rect and lane rect.

## Workflow: Moving a Node and Its Edges

1. **Find the node's `<g>` element** and note its current translate values.
2. **Calculate current edge points** from the translate + width/height.
3. **Change the translate** to the new position.
4. **Recalculate edge points** with the new translate values.
5. **Find all connected edges** (search for the old coordinates in `<line>` and `<path>` elements).
6. **Update the edge endpoints** to match the new node edge coordinates.
7. **Move any associated labels** that sit on or near the moved edges.

### Tip: Use the HTML comment block

The cleaned-up mockups include a comment block listing every node's position and edge coordinates. Use this as a reference and update it when you move things:

```html
<!--
  dim_occupation (100, 80, 230, 50)  L(100,105) R(330,105) T(215,80) B(215,130)
-->
```

## Common Patterns

### Increase spacing between two nodes
Move the lower node down (increase its Y), then update connecting edges.

### Widen a gap for edge labels
Move the right-side nodes rightward (increase X), update horizontal edges, and expand the lane/viewBox width.

### Add a new edge between existing nodes
1. Look up source and target node edge coordinates from the comment block.
2. Add a `<line>` or `<path>` element **before** the node `<g>` elements (edges render behind nodes).
3. Set start/end coordinates to the node edges.
4. Add a marker-end for the arrowhead (pick from the defined markers in `<defs>`).

### Avoid edges crossing through nodes
Route the edge through the margins (left of x=100 or right of the rightmost node) using a multi-segment `<path>` with L-shaped turns.
