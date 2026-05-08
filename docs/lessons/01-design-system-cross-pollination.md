# Design System Cross-Pollination

## The Lesson

When two projects share an author, the stronger design system should inform the weaker one — but adopting visual feel is a different task than adopting architecture. Port the tokens and typography; don't port the rendering pipeline.

## Context

The JobClass project is a FastAPI + Jinja2 data warehouse with 20 educational lesson pages rendered server-side as HTML templates. The certification project (Atlas) is a pure static site with client-side markdown rendering, a token-based design system (CSS custom properties for every color, spacing, radius, and motion value), Google Fonts (Source Serif 4, Inter Tight, JetBrains Mono), and full dark mode support. JobClass lessons were functional but visually generic — system fonts, cold blue palette, dark code blocks. The goal was to bring the Atlas "feel" (serif typography, warm neutrals, elegant spacing, dark mode) to JobClass without changing its server-rendered architecture.

## What Happened

1. **Started with a structured review.** A full codebase review (`docs/review-2026-05-07.md`) identified 11 findings across security, documentation, and code quality. This established the baseline state and surfaced stale documentation that would need updating alongside any visual changes.
2. **Explored both projects in parallel.** Used multiple exploration agents to document the exact HTML structure, CSS classes, design tokens, and content patterns of both the JobClass lessons (20 Jinja2 templates, ~200 lines of lesson CSS) and the Atlas lessons (token-driven system.css, client-side markdown rendering, 28 lessons from markdown files). The key deliverable was a side-by-side comparison of the two "feels."
3. **Separated visual feel from architecture.** The Atlas lessons use client-side markdown rendering (marked.js from CDN), query-string routing (`lesson.html?lesson=01-slug`), and hardcoded card grids. None of this architecture was appropriate for JobClass, which has server-rendered templates, FastAPI routing, and a test suite expecting specific response structures. The decision was to port only the design tokens, typography, and CSS patterns.
4. **Designed a phased plan.** Six phases: (1) design tokens and font loading, (2) lessons index page with hero and category filters, (3) individual lesson CSS, (4) template nav restructuring, (5) site-wide dark mode polish, (6) static build verification. The plan was reviewed and approved before any code was written.
5. **Chose Google Fonts CDN over self-hosting.** Atlas uses Google Fonts CDN. Self-hosting WOFF2 files would have added 200-400KB to the repo and required manual updates. The CDN approach required only a CSP header update (`style-src` for googleapis.com, `font-src` for gstatic.com).
6. **Committed to site-wide dark mode.** The initial plan considered lessons-only dark mode, but this would create a jarring seam at the nav/footer boundary. Site-wide dark mode required remapping all CSS custom properties under a `[data-theme="dark"]` selector and adding a localStorage-persisted theme toggle to the nav bar.
7. **Executed tokens-first.** The `:root` block was rewritten from 12 variables to 40+ (adding serif/sans/mono font stacks, surface-2, text-2, border-hard, accent-2, radius scale, motion timing, and the full dark-mode override block). This single change propagated to every component that already used `var(--color-*)` references — most of the site updated "for free."
8. **Lesson CSS was a complete rewrite.** The ~200 lines of lesson CSS were replaced with ~300 lines matching Atlas patterns: serif italic h2s, mono eyebrow metadata, light-background code blocks with borders, blockquote-style callouts, category filter pills, animated card arrows, and a hero section with fluid clamp() typography.

## Key Insights

- **Tokens are the highest-leverage change.** Rewriting `:root` custom properties propagated the new palette to every component that already referenced them. Headers, footers, cards, tables, buttons — all shifted from cold blue to warm neutrals without touching their CSS rules. This only works if the existing codebase consistently uses variables instead of hardcoded hex values.
- **Typography carries more "feel" than color.** Switching from system sans-serif to Source Serif 4 for body text and headings was the single change that most transformed the perceived quality. The serif font, combined with lighter weights (400 instead of 700) and negative letter-spacing, immediately evoked the Atlas aesthetic. Color changes were secondary.
- **Dark mode is an all-or-nothing commitment.** Scoping dark mode to a subset of pages (just lessons) was technically possible but created an ugly visual seam at the nav/footer boundaries. Once the dark token block exists, extending it site-wide is incremental — the hard part is the initial token mapping, not the per-component adjustments.
- **Don't port architecture, port aesthetics.** Atlas renders markdown client-side with marked.js; JobClass renders Jinja2 templates server-side. Adopting Atlas's rendering approach would have broken 430 tests, required rewriting 20 templates as markdown files, and eliminated server-side validation. The correct abstraction boundary was the CSS layer: port the design tokens, font choices, and component styles while keeping the existing rendering pipeline untouched.
- **Category filters are cheap interactivity.** Adding `data-cat` attributes to existing card elements and a 15-line vanilla JS filter handler gave the lessons index page a significant UX upgrade (filtering 20 lessons across 5 categories) for minimal complexity. No framework, no state management — just DOM show/hide.
- **A code review makes a natural starting point for a visual refactor.** The review identified stale documentation, missing validation, and CI issues that needed fixing regardless. Addressing these first established a clean baseline and prevented the visual refactor from entangling with unrelated bug fixes.

## Examples

**Before (`:root` tokens — cold blue, system fonts):**
```css
:root {
    --color-primary: #1a365d;
    --color-accent: #3182ce;
    --color-bg: #f7fafc;
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
```

**After (`:root` tokens — warm neutrals, serif + mono, with dark mode):**
```css
:root {
    --color-primary: #1A1D24;
    --color-accent: #2F5DA8;
    --color-bg: #F6F4EF;
    --color-surface-2: #EDEAE0;
    --font-serif: 'Source Serif 4', Georgia, serif;
    --font-mono: 'JetBrains Mono', ui-monospace, monospace;
}
[data-theme="dark"] {
    --color-primary: #F2EEE3;
    --color-accent: #6FA0E8;
    --color-bg: #0F1014;
}
```

**Before (lesson code block — dark background):**
```css
.lesson-code {
    background: #1a202c;
    color: #e2e8f0;
}
```

**After (lesson code block — light surface with border, matching Atlas):**
```css
.lesson-code {
    background: var(--color-surface-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    color: var(--color-text);
}
```

## Applicability

This pattern applies whenever you maintain multiple projects and want visual coherence without architectural coupling. The key constraint is that the source project must use a token-based design system (CSS custom properties or equivalent) — without tokens, there's nothing portable to extract. The pattern does NOT apply when the projects share components at the code level (use a shared component library instead) or when the "feel" is inseparable from interactive behavior (animations, transitions, scroll effects that depend on specific DOM structures).

## Related Lessons

- [Static Site Generation](08-static-site-generation.md) — the static build pipeline that serves the redesigned pages
- [Testing and Deployment](09-testing-deployment.md) — the 430-test suite that constrained the refactor scope
- [Fetch Shim Architecture](21-fetch-shim.md) — the shim that makes the redesigned static site work without a server
