# Choosing the Right Similarity Algorithm

## The Lesson

Before choosing a similarity algorithm, understand whether your data uses binary membership (item has feature or doesn't) or continuous scores (item has every feature at varying levels). Set-based metrics like Jaccard collapse to a constant when every item has every feature — the signal is in the scores, not the membership, and score-based metrics like cosine similarity are required.

## Context

The JobClass warehouse includes an occupation similarity feature that identifies which occupations require similar skills. O*NET rates all 35 skills for every occupation on importance scales from 1 to 5, producing a dense matrix where every occupation has every skill — they differ only in how much each skill matters. The initial implementation used Jaccard similarity and produced a useless result: 100% similarity between every pair of occupations.

## What Happened

1. **Jaccard similarity was implemented as the initial algorithm.** Jaccard computes `|A ∩ B| / |A ∪ B|` — the intersection divided by the union of two sets. It's a standard choice for set-based similarity and works well when items either have a feature or don't (e.g., recipe ingredients, document tags).

2. **Every occupation showed 100% similarity to every other.** Dancers matched Lawyers, Bakers matched Pile Driver Operators. The entire similarity matrix was a constant. The algorithm was correct — the data model assumption was wrong:

   ```python
   # O*NET rates ALL 35 skills for every occupation:
   # Dancer (27-2031): Active Listening IM=3.75, Mathematics IM=1.62, Programming IM=1.12
   # Lawyer (23-1011): Active Listening IM=4.25, Mathematics IM=2.12, Programming IM=1.25
   #
   # Jaccard sees: {35 skills} ∩ {35 skills} / {35 skills} ∪ {35 skills} = 35/35 = 1.0
   ```

3. **Cosine similarity was adopted as the replacement.** Cosine similarity treats each occupation's skill importance scores as a vector in 35-dimensional space, measuring the angle between two vectors. Occupations emphasizing the same skills at similar levels point in the same direction. Values above 0.95 indicate genuinely similar skill profiles; below 0.85 indicates meaningfully different ones.

4. **Switching to cosine similarity revealed a hidden data duplication bug.** Some occupations showed similarity scores greater than 1.0 — theoretically impossible. The cause: "All Other" catch-all occupations (e.g., `17-2199 Engineers, All Other`) had up to 8 duplicate rows per skill in `bridge_occupation_skill`. Each duplicate multiplied the dot product without proportionally increasing the norm:

   ```sql
   -- Duplicates inflate the dot product
   SELECT occupation_key, element_id, COUNT(*) AS n
   FROM bridge_occupation_skill b
   JOIN dim_skill s ON b.skill_key = s.skill_key
   WHERE b.scale_id = 'IM'
   GROUP BY occupation_key, element_id
   HAVING COUNT(*) > 1;
   -- Returns rows with n = 2, 4, 6, 8 for "All Other" occupations
   ```

5. **The fix used AVG + GROUP BY to collapse duplicates before computing similarity.** This produced exactly one importance score per occupation per skill, making the dot product and norm computations correct:

   ```sql
   WITH occ_skill_scores AS (
       SELECT b.occupation_key, s.element_id,
              AVG(b.data_value) AS importance
       FROM bridge_occupation_skill b
       JOIN dim_skill s ON b.skill_key = s.skill_key
       WHERE b.scale_id = 'IM'
       GROUP BY b.occupation_key, s.element_id
   )
   ```

6. **The final implementation used three CTEs.** `occ_skill_scores` produces one importance score per occupation-skill pair (AVG deduplicates catch-all rows). `norms` computes the L2 norm per occupation. `dot_products` computes pairwise dot products via self-join on `element_id`. The final SELECT divides dot product by the product of norms.

## Key Insights

- **When your metric exceeds its theoretical bounds, look for data duplication before doubting the formula.** Cosine similarity is bounded by [0, 1] for non-negative inputs. Scores above 1.0 meant the inputs were wrong (duplicated rows inflating the dot product), not that the math was wrong.
- **Set-based metrics are useless when every item has every feature.** Jaccard, Dice, and other set-overlap metrics require variation in feature membership to produce meaningful scores. When all items share all features, the intersection always equals the union.
- **The right algorithm depends on data structure, not problem domain.** This is not a "skills are special" issue — it's a general principle. Any dataset with continuous scores on a fixed feature set needs a score-based metric (cosine, correlation, Euclidean), not a set-based one.
- **Legacy column names can be left in place when the cost of renaming is high.** The SQL view column is still named `jaccard_similarity` to avoid a cascading rename across the codebase. The API exposes it as `similarity_score`. This is a pragmatic trade-off, not a best practice.

### Algorithm Decision Guide

| Data Structure | Algorithm | Example |
|---------------|-----------|---------|
| Binary presence/absence | Jaccard similarity | Recipe ingredients, tag sets |
| Continuous scores, same features | Cosine similarity | Skill ratings, TF-IDF vectors |
| Continuous scores, magnitude matters | Euclidean distance | Salary comparisons, physical measurements |
| Rankings or ordinal data | Spearman correlation | Preference rankings, survey responses |

## Related Lessons

- [Dimensional Modeling for Labor Data](03-dimensional-modeling.md) — the bridge table structure that stores skill scores
- [Data Quality Traps in Government Sources](05-data-quality-traps.md) — another case where source data artifacts caused incorrect results
- [Derived Metrics from Base Observations](18-derived-metrics.md) — other computed analytical values in the warehouse
