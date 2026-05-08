# Crosswalk and Taxonomy Evolution

## The Lesson

Occupation codes are not stable identifiers across taxonomy revisions. The same SOC code can refer to different occupations in different versions, and naively comparing values across revisions produces misleading results. A crosswalk — an explicit mapping from old codes to new codes with cardinality metadata — is required for any cross-version analysis, and only 1:1 mappings are safe for direct metric comparison.

## Context

A labor market data warehouse needed to support time-series analysis across SOC 2010 and SOC 2018 vintages. SOC code `15-1131` meant "Computer Programmers" in 2010 but was renumbered to `15-1251` ("Software Developers") in 2018, with a definition change. The SOC 2010-to-2018 revision restructured entire occupation groups — some codes were split into multiple new codes, others were merged, and a few shifted to different major groups entirely. The BLS publishes a crosswalk CSV mapping every old code to every new code, which the pipeline needed to parse, classify, and store.

## What Happened

1. **The crosswalk CSV was parsed into structured rows.** Each `CrosswalkRow` captures both the old and new code plus metadata about the mapping relationship:

   ```python
   @dataclass
   class CrosswalkRow:
       source_soc_code: str        # SOC 2010 code
       source_soc_title: str
       source_soc_version: str     # "2010"
       target_soc_code: str        # SOC 2018 code
       target_soc_title: str
       target_soc_version: str     # "2018"
       mapping_type: str           # "1:1", "split", "merge", "complex"
       source_release_id: str
       parser_version: str
   ```

2. **A two-pass algorithm classified each pair by cardinality.** The `mapping_type` is not present in the source data — it is computed by analyzing fan-out (how many targets each source maps to) and fan-in (how many sources each target receives) across all pairs:

   ```python
   # Pass 1: build cardinality maps
   source_targets = defaultdict(set)  # 2010 code -> set of 2018 codes
   target_sources = defaultdict(set)  # 2018 code -> set of 2010 codes
   for pair in all_pairs:
       source_targets[pair.source].add(pair.target)
       target_sources[pair.target].add(pair.source)

   # Pass 2: classify each pair
   for pair in all_pairs:
       src_fan = len(source_targets[pair.source])
       tgt_fan = len(target_sources[pair.target])
       if src_fan == 1 and tgt_fan == 1:   pair.mapping_type = "1:1"
       elif src_fan > 1 and tgt_fan == 1:  pair.mapping_type = "split"
       elif src_fan == 1 and tgt_fan > 1:  pair.mapping_type = "merge"
       else:                                pair.mapping_type = "complex"
   ```

   | Type | Fan-out | Fan-in | Safe for wage comparison? |
   |---|---|---|---|
   | 1:1 | 1 | 1 | Yes — same occupation, different code |
   | split | >1 | 1 | No — wages cannot be disaggregated |
   | merge | 1 | >1 | No — wages cannot be averaged meaningfully |
   | complex | >1 | >1 | No — requires manual analysis |

3. **The comparable history pipeline was restricted to 1:1 mappings.** Splits cannot disaggregate a mean wage into parts because the component occupations have different wage distributions. Merges lose granularity — an unweighted average misrepresents the combined group, and a weighted average introduces circular dependencies. The pipeline sacrifices coverage (some occupations cannot be tracked across versions) in exchange for correctness (every comparison that is made is statistically valid).

4. **Column alias handling was added for format variation.** The BLS CSV uses different header formats across releases (`"2010 SOC Code"` vs. `"Old SOC Code"`). The parser tries each alias in order and uses the first match. Regex validation ensures all codes match the `XX-XXXX` pattern before processing.

## Key Insights

- **Same code does not mean same occupation.** SOC codes are identifiers within a specific taxonomy version. Cross-version comparison without a crosswalk will silently produce wrong results for every code that was renumbered, split, or merged.
- **The two-pass design is necessary because classification requires global knowledge.** You cannot determine whether a pair is 1:1 or part of a split until you have seen every pair involving that source code. Single-pass streaming would require deferred classification with a flush step — more complex for no benefit given the small file size (under 2,000 rows).
- **Only 1:1 mappings are safe for direct value comparison.** Splits can aggregate employment counts (addition is safe) but not wages (you cannot split a mean). Merges have the opposite problem. Restricting comparable history to 1:1 pairs is the only way to guarantee statistical validity.
- **Storing all mapping types enables future analysis.** The bridge table stores splits, merges, and complex mappings even though the comparable-history pipeline does not use them. Future analysis (e.g., employment aggregation across split codes) can leverage these without re-parsing.

## Related Lessons

- [Multi-Vintage Challenge](04-multi-vintage-challenge.md)
- [Multi-Vintage Query Pitfalls](12-multi-vintage-queries.md)
- [Federal Data Landscape](02-federal-data-landscape.md)
