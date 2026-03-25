  Working Process Summary                                                                                                                                                                                             
  1. Design Phase                                                                                                                                                                                                       You provide a design document created externally. I construct a detailed requirements/design spec from it
   (e.g., base_design_document.md → project_detail_design.md). You edit and refine this.

  2. Release Planning

  I produce a phased release plan following a checkbox convention:
  - [ ] — not started
  - [>] — in progress
  - [#] — complete
  - [!] — blocked / on hold

  3. Phase-by-Phase Execution

  I work through each phase sequentially:
  - Mark tasks [>] as work begins
  - Implement code, tests, and infrastructure
  - Mark tasks [#] as each completes
  - Commit at phase completion with a descriptive message (e.g., Phase 5: O*NET pipeline — parsers,        
  staging, bridges, validations)

  4. Review & Push

  At the end of a release (or at key milestones), you review results before we push to remote.

  5. Iteration & Maintenance

  After initial releases, we iterate through additional work streams:

  - Code Review Agent Process — I generate a review prompt (code_review_agent_v2.md), produce findings and 
  a remediation plan (code_review_plan_v2.md), then a phased release plan for fixes
  (phased_code_review_release_plan_v2.md). This ran twice: CR1–CR4 (95 tasks) and CR2 integrated into later
   work.
  - New Feature Releases — Same design→plan→execute cycle for major additions: Time-Series Intelligence    
  (TS1–TS10, 101 tasks), Lessons section (36 tasks), New Data Sources (NDS0–NDS8, 102 tasks).
  - Real Data Validation — Separate phases (RD1–RD6) to verify the pipeline against live BLS/O*NET sources,
   not just fixtures.
  - Static Site & Deployment — Build system for GitHub Pages, fetch shim for client-side API, CI
  auto-deploy.
  - Bug Fixes & Polish — Targeted commits for issues discovered in production (empty data messaging,       
  similarity algorithm fixes, thread safety, etc.).

  Across 39 commits, the project grew from foundation to 653+ tests, 7 data sources, a full web UI, static 
  site deployment, and CI/CD — all following this disciplined phase-commit-review cadence.