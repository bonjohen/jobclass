# Testing and Deployment

## The Lesson

Separating tests by their infrastructure requirements — fixtures-only, in-memory server, real database — lets CI run fast on every push while reserving expensive real-data validation for local runs. The deployment pipeline then layers lint, format, test, build, and deploy into a strict sequence where each step gates the next.

## Context

The JobClass project has 840+ tests covering parsers, loaders, orchestration, API endpoints, HTML rendering, security headers, and real-data validation. The warehouse database (`warehouse.duckdb`) is too large for CI and contains data that changes with each pipeline run. The testing strategy needed to provide fast CI feedback on every push while still supporting comprehensive local validation against real data.

## What Happened

1. **Tests were organized into three directories by infrastructure requirement.**

   | Directory | What It Tests | Requirements |
   |-----------|--------------|--------------|
   | `tests/unit/` | Parsers, loaders, orchestration, validation, config | Fixtures only — no database, no network |
   | `tests/web/` | API endpoints, HTML pages, security headers, accessibility | In-memory fixtures via TestClient |
   | `tests/warehouse/` | Real data validation against `warehouse.duckdb` | Populated warehouse (auto-skipped if absent) |

2. **Seven categories of verification were established.** Schema contracts (required columns exist), grain uniqueness (no duplicate business keys), referential integrity (fact dimension keys point to existing rows), idempotence (re-running a load produces the same count), validation framework (structural/temporal/drift checks pass), API correctness (expected status codes and response shapes), and security (CSP headers, no PII exposure, CORS configuration).

3. **CI was configured for fast feedback.** GitHub Actions runs lint (`ruff check`) and format checking (`ruff format --check`) as a separate job, then runs the full test suite against Python 3.12 and 3.14 matrices. Only unit and web tests run in CI; warehouse tests auto-skip when the database file is absent.

   ```yaml
   lint:
     python-version: "3.14"
     steps: ruff check + ruff format --check

   test:
     matrix: [3.12, 3.14]
     steps: pip install -e ".[dev]" → pytest --cov
   ```

4. **A strict deployment sequence was established.** Each step gates the next — no skipping:

   ```
   1. ruff check src/ tests/              # Lint passes
   2. ruff format --check src/ tests/     # Formatting matches
   3. pytest tests/unit/ tests/web/ -q    # All tests pass
   4. git push                            # CI passes on GitHub
   5. python scripts/build_static.py \
        --base-path /                     # Rebuild static site
   6. python scripts/deploy_pages.py      # Deploy to GitHub Pages
   ```

5. **Local format checking became a pre-push habit.** CI rejects unformatted code even when it's functionally correct. Running `ruff format --check src/ tests/` locally before pushing avoids CI round-trip delays for formatting-only failures.

## Key Insights

- **Auto-skipping is better than separate CI configurations.** Warehouse tests use `pytest.mark.skipif` to check for the database file. This means the same `pytest` command works everywhere — CI skips warehouse tests automatically, local runs include them when the database exists. No CI-specific test selection is needed.
- **Lint and format are separate gates from tests.** Running `ruff check` and `ruff format --check` as a separate CI job means formatting failures are reported instantly, without waiting for the full test suite. This matches the workflow: format issues are trivial to fix and shouldn't block test feedback.
- **The static build is part of the deployment pipeline, not a separate process.** Building the static site (`build_static.py`) takes several minutes for ~870 occupations. It runs after tests pass but before deploy. Treating it as a pipeline step rather than an ad-hoc script ensures it always runs against tested code.
- **Matrix testing catches version-specific issues cheaply.** Running against Python 3.12 and 3.14 in CI has caught several stdlib changes and deprecation warnings that single-version testing would miss.

## Related Lessons

- [Idempotent Pipeline Design](07-idempotent-pipelines.md) — the idempotence tests that are part of this test suite
- [Static Site Generation](08-static-site-generation.md) — the build step in the deployment pipeline
- [Data Quality Traps in Government Sources](05-data-quality-traps.md) — what the validation tests are designed to catch
