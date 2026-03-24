# Code Review Agent V2 — Review Prompt

## Context

This is the second code review of the JobClass project. The first review (archived at `docs/specs/archive/code_review_plan.md`) identified 26 findings across 4 phases. The majority of those findings have been remediated. This V2 review focuses on the **current codebase state** to identify:

1. Remaining gaps from V1 findings that were partially addressed.
2. New issues introduced by features added after V1 (time-series pipeline, trends UI, static site generation, lessons section, ranked movers, geography comparison).
3. Architectural debt that has accumulated as the project has grown from its initial scope.

## Review Scope

The codebase now includes:

- **Pipeline layer**: Extract, parse, load, validate, orchestrate, observe, marts, config.
- **Web layer**: FastAPI app with 10+ API routers, 15+ HTML page routes, Jinja2 templates, external JS files, static CSS.
- **Static site**: `scripts/build_static.py` pre-renders all pages and generates static JSON API files. A JavaScript fetch shim intercepts API calls on the static site and routes them to local JSON.
- **Lessons section**: 12 educational lesson pages with navigation chain.
- **Trends subsystem**: Time-series pipeline (multi-vintage OEWS), trend explorer, occupation comparison, geography comparison, ranked movers.
- **CI/CD**: GitHub Actions workflow, Dockerfile, deploy scripts.
- **Tests**: 585+ tests across unit, web, warehouse, and integration directories.

## Review Dimensions

Evaluate the project across these dimensions:

### 1. Design
Assess separation of concerns, data flow clarity, module responsibilities, naming consistency, coupling, cohesion, extensibility, and whether the design matches the stated goals. Pay particular attention to:
- The boundary between pipeline and web layers.
- The growing complexity of the static site shim (client-side API composition).
- Route/template organization as page count increases.
- The valid_slugs dictionary pattern in app.py for lessons.

### 2. Implementation
Assess code quality, complexity, duplication, error handling, logging, configuration management, maintainability, consistency, and likely bug-prone areas. Pay particular attention to:
- JavaScript code quality across 15+ separate .js files.
- The fetch shim in `build_static.py` — a large raw string of JavaScript embedded in Python.
- SQL query construction patterns (f-strings vs parameterized queries).
- Exception handling specificity (broad catches vs specific).
- Consistency of API response shapes across endpoints.

### 3. Testing
Assess test coverage, test quality, missing test types, fragile tests, edge-case coverage, and gaps between system risk and test effort. Pay particular attention to:
- Whether new features (trends, lessons, static site) have proportional test coverage.
- Whether tests validate behavior rather than just non-emptiness.
- Test isolation — whether test failures cascade unnecessarily.
- Missing end-to-end test scenarios for the static site.

### 4. Deployment and Operations
Assess build clarity, packaging, CI/CD completeness, environment handling, deployment readiness, rollback safety, observability, health checks, and operational trustworthiness. Pay particular attention to:
- Static site build/deploy pipeline reliability.
- Whether CI tests the static site build.
- Monitoring coverage for the trends pipeline (multi-vintage extraction).
- Database migration safety for schema changes.

### 5. Security
Assess input validation, output encoding, header security, dependency safety, and attack surface. Pay particular attention to:
- Whether all new API endpoints have input validation matching existing patterns.
- Whether the static site shim introduces any client-side vulnerabilities.
- Whether CSP headers accommodate the static site's needs.

## How to Review

Read the repository like a real reviewer. Infer the intended system shape from the code, configuration, documentation, and file layout.

Look for:
- Inconsistencies between old and new code patterns.
- Features that work on the live server but break on the static site (or vice versa).
- API endpoints without corresponding tests.
- JavaScript files without error handling.
- SQL queries with hardcoded values that should be parameterized.
- Configuration that assumes a specific environment.
- Dead code, orphaned files, or unused imports.
- Test files that don't test what their name suggests.
- Documentation that contradicts the current implementation.

When identifying a deficiency, explain **why it matters** with evidence from this specific codebase.

## Output Format

### 1. Executive Summary
Concise summary of the most important concerns. Focus on issues that affect trust, maintainability, correctness, and delivery confidence.

### 2. V1 Remediation Status
Brief table showing each V1 finding and its current status (Fixed, Partially Fixed, Not Addressed, or New Issue Introduced).

### 3. Phased Release Plan

Organize all **new** recommendations into phases:

**Phase 1: Foundation and Clarity**
Issues that block safe execution, clear understanding, or basic trust. Security vulnerabilities, broken functionality, missing critical validation.

**Phase 2: Correctness and Maintainability**
Code quality issues, duplication, inconsistent patterns, missing error handling, architectural debt that makes the system harder to extend.

**Phase 3: Test and Release Confidence**
Test gaps, CI/CD improvements, release validation, coverage for new features, static site verification.

**Phase 4: Operational and Reviewer Polish**
Observability, developer experience, documentation accuracy, performance, accessibility improvements.

For each finding within a phase, provide:
- **Title** — concise name
- **Area** — Design, Implementation, Testing, Deployment, Security, or Methodology
- **Severity** — Critical, High, Medium, or Low
- **Evidence** — file names, line numbers, specific patterns observed
- **Why it matters** — tied to this codebase, not generic advice
- **Recommended change** — specific, actionable
- **Recommended validation** — how to verify the fix

### 4. Highest-Risk Areas
The specific components or workflows most likely to fail in production or during handoff.

### 5. Recommended Next Actions
Short, concrete sequence of next actions for a coding agent or engineer.

## Critical Instructions

- Do not give generic advice. Tie every finding to evidence from this repository.
- Do not re-litigate V1 findings that are fully fixed. Acknowledge them in the status table and move on.
- Do not praise the project unless a strength changes your recommendation.
- Do not say "more testing is needed" without naming which tests are missing and why.
- Do not assume deployment maturity just because a Dockerfile exists.
- If something cannot be determined from the codebase, say "not evident from the repository."
- Focus on findings that a V1 review would NOT have caught because the affected code did not exist at V1 time.

## Tone

Be direct, specific, senior, practical, and unsentimental. Review the code as if preparing a real project for external scrutiny.
