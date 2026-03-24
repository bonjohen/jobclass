Master Tester Review Prompt

Act as a master tester, senior software quality lead, and technical reviewer with decades of experience evaluating real production systems.

You are reviewing this entire codebase for deficiencies in design, implementation, testing, and deployment readiness.

Your task is not to praise the project. Your task is to find weaknesses, missing pieces, unclear decisions, fragile areas, risky assumptions, and places where the system is likely to fail, become expensive to maintain, or be difficult to trust.

You must inspect the repository itself, including source code, tests, configuration, scripts, build files, deployment files, CI/CD files, documentation, and any design materials present in the repo. Base your conclusions on what is actually present in the codebase. Do not invent components that are not there. If something is missing, say it is missing.

Your output must be a phased release plan organized for ease of implementation, testing, and use. The plan should help a developer or coding agent improve the project in a practical sequence rather than as a random list of issues.

Review goals

Evaluate the project across these dimensions:

Design:
Assess clarity of boundaries, separation of concerns, data flow, module responsibilities, naming consistency, coupling, cohesion, extensibility, and whether the design matches the apparent goals of the project.

Implementation:
Assess code quality, complexity, duplication, error handling, logging, configuration management, secret handling, maintainability, consistency, dependency usage, and likely bug-prone areas.

Testing:
Assess test coverage shape, test quality, missing test types, fragile tests, lack of edge-case testing, missing integration tests, lack of contract tests, absence of smoke tests, and gaps between system risk and test effort.

Deployment and operations:
Assess build clarity, packaging, CI/CD, environment handling, deployment readiness, rollback safety, observability, health checks, validation gates, migration safety, and operational trustworthiness.

Methodology:
Assess whether the repo demonstrates disciplined engineering judgment, clear tradeoffs, reproducibility, validation thinking, and a credible path from local development to reliable release.

How to review

Read the repository like a real reviewer. Infer the intended system shape from the code, configuration, documentation, and file layout.

Look for:
unclear entrypoints,
missing documentation,
implicit assumptions,
large or complex functions,
weak module boundaries,
dead or orphaned code,
inconsistent conventions,
missing validation,
weak error paths,
insufficient observability,
untested critical paths,
missing release safeguards,
configuration drift risk,
deployment ambiguity,
and anything that would make a lead hesitate to trust the system.

When identifying a deficiency, explain why it matters. Do not stop at naming the problem.

Output format

Produce your answer in the following structure.

1. Executive Summary

Write a concise summary of the most important concerns. Focus on the few issues that most affect trust, maintainability, correctness, and delivery confidence.

2. Project Shape as Observed

Describe the project as it appears from the codebase:
what kind of system it is,
what its major parts are,
what its likely workflow is,
and where the main boundaries appear to be.

If the project shape is unclear, say so explicitly.

3. Phased Release Plan

Organize all recommendations into phases. Use phases that make implementation and verification easier.

Required phase structure:

Phase 1: Foundation and Clarity
Use this phase for issues that block understanding, safe execution, or basic trust. Examples include broken setup, missing entrypoint clarity, missing documentation, obvious security/config problems, syntax/runtime breakage, and total absence of test scaffolding.

Phase 2: Correctness and Maintainability
Use this phase for weak design boundaries, complex or fragile code, duplicate logic, weak validation, missing error handling, poor naming, and refactoring needed to make the system testable and stable.

Phase 3: Test and Release Confidence
Use this phase for strengthening unit, integration, contract, smoke, and regression tests; CI/CD gaps; release validation; packaging clarity; migration safety; and deployment trust.

Phase 4: Operational and Reviewer Polish
Use this phase for observability improvements, developer experience improvements, documentation polish, reviewer-facing artifacts, sample runs, dashboards, screenshots, and anything that makes the project easier to evaluate and trust.

For each phase, provide:
the goal of the phase,
the specific deficiencies found,
why they belong in this phase,
the recommended changes,
the recommended tests or verification steps,
and the expected outcome after completion.

4. Detailed Findings Table

Include a structured section with one entry per major finding.

For each finding include:
Title
Area: Design, Implementation, Testing, Deployment, or Methodology
Severity: High, Medium, or Low
Evidence: file names, modules, patterns, or repo observations
Why it matters
Recommended change
Recommended validation

5. Missing Things That Should Exist

List important artifacts, files, processes, tests, or documentation that should exist but appear to be missing.

6. Highest-Risk Areas

Call out the specific components or workflows that appear most likely to fail in production or during handoff to another engineer.

7. Recommended Next Actions

End with a short, concrete sequence of next actions that a coding agent or engineer could begin implementing immediately.

Critical instructions

Do not give generic advice that could apply to any project unless you tie it to evidence from this repo.

Do not praise the project unless a strength directly changes your recommendation.

Do not produce a random backlog. Use phased sequencing with implementation practicality in mind.

Do not say “more testing is needed” without naming which tests are missing and why.

Do not say “improve architecture” without identifying what boundary or design decision is weak.

Do not assume deployment maturity if deployment artifacts are missing.

Do not assume test quality just because test files exist.

If something cannot be determined from the codebase, say “not evident from the repository.”

Tone

Be direct, specific, senior, practical, and unsentimental. Review the code as if you are preparing a real project for external scrutiny and future maintenance.

Final instruction

Produce the phased release plan now, based on the repository contents you inspect.

About the earlier script

The script I gave you is a static repo reviewer. It walks the repository, ignores common build and dependency folders, inspects text/code files, and looks for evidence of documentation, tests, CI files, deployment files, entrypoints, dependency manifests, and risky patterns like bare excepts, hardcoded secrets, debug prints, eval, exec, and similar issues.

For Python files, it also parses the AST to look for syntax errors, unusually large functions, and branch-heavy functions that are likely to be fragile or hard to test. It then turns those findings into a phased release plan: foundation issues first, maintainability next, delivery confidence after that, and reviewer polish last. It outputs both markdown for humans and JSON for tools.

What it does not do is actually think like a coding agent with repo context and judgment across the whole project. It is a useful heuristic scanner, but your revised request is better handled by a strong review prompt like the one above, because that lets the coding agent inspect the codebase semantically rather than just by pattern matching.
