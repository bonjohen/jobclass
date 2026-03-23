# JobClass — Labor Market Occupation Pipeline

A data pipeline that ingests federal labor market data products into a layered analytical warehouse, with occupation as the stable external key.

## What It Does

Ingests, validates, and models data from four federal sources into a queryable warehouse:

- **SOC** — Occupation taxonomy and hierarchy
- **OEWS** — Employment counts and wage distributions by occupation and geography
- **O\*NET** — Semantic descriptors (skills, knowledge, abilities, tasks) tied to occupations
- **Employment Projections** — Forward-looking employment outlook by occupation

## Questions It Answers

- How many people work in a given occupation, nationally and by state?
- What are the wage distributions across geographies?
- What skills, tasks, knowledge, and abilities define an occupation?
- Which occupations are similar based on shared descriptors?
- What is the projected employment outlook for an occupation?
- What source version and release lineage produced a given result?

## Architecture

Four-layer warehouse: **Raw** (immutable source capture) → **Staging** (parsed, typed, standardized) → **Core** (conformed dimensions, facts, bridges) → **Marts** (analyst-ready denormalized views).

Key properties: idempotent loading, version-aware modeling, immutable raw storage, fail-fast on schema drift, explicit source lineage on every record.

  ## Phase Commit Log                

    Status of each phase's commit upon completion.   
    
    | Phase | Description | Commit Message | Status | 
    |-------|-------------|----------------|--------| 
    | 1 | Project Foundation | Phase 1: Project foundation — structure, config, database, logging, tests | Complete |
    | 2 | Extraction Framework & Run Manifest | | In Progress |
    | 3 | SOC Taxonomy Pipeline | | Pending |  
    | 4 | OEWS Employment & Wages Pipeline | | Pending |       
    | 5 | O*NET Semantic Pipeline | | Pending |      
    | 6 | Validation Framework & Failure Handling | | Pending |
    | 7 | Observability & Run Reporting | | Pending |
    | 8 | Orchestration | | Pending |
    | 9 | Analyst Marts | | Pending |
    | 10 | Employment Projections (Optional R1) | | Pending |
    | 11 | End-to-End Integration & Deliverables | | Pending | 


## Project Structure

```
docs/
  specs/
    design_document_v1.md       # Full design specification
    project_detail_design.md    # Requirements and downstream user needs
```

## Documentation

| Document | Purpose |
|----------|---------|
| [Design Document](docs/specs/design_document_v1.md) | Full architectural specification, data model, pipeline flow, and design tradeoffs |
| [Project Detail Design](docs/specs/project_detail_design.md) | Requirements from the perspective of downstream users; input for release and test planning |

## Status

Pre-implementation. Design phase complete. Next steps: phased release plan and test plan.
