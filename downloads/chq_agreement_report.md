# Agreement of published CHQ scores

Analysis date: 28 October 2026.

## Cohort and fair comparison

The primary comparison uses **2,694,335 latest sampled homes** with all six published scores available, out of 3,978,640 latest homes (67.7%). Each connected UPRN/EPC entity contributes its latest transaction-year record, breaking ties by source_row. Published scores are joined by exact source-row alignment and are not refitted or imputed for this analysis.

Scores: original 41-variable available-score baseline; discovery-frozen complete 5-, 10- and 18-variable candidates; complete six-attribute building-only score; and the published 41-variable / four-PC composite. Candidate text/scaling coding differs from the original baseline. The PCA has different percentile-based calibration and imputation. Agreement describes these published definitions, not harmonized reimplementations.

Secondary results include pairwise-available latest homes, all-six-complete transactions (n = 2,978,391), and **314 authority means** based on identical complete homes with at least 100 such homes per authority. Every authority has equal weight. Aggregation may raise correlations; area results cannot substitute for household agreement.

## Main household results against the 41-variable baseline

| Other score | Spearman rho | Pearson r | Lin CCC | Weighted quintile kappa | Bottom-decile Jaccard | Top-decile Jaccard | Mean B - baseline | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5-variable candidate | 0.812 | 0.829 | 0.325 | 0.776 | 0.424 | 0.409 | 17.879 | 17.944 |
| 10-variable candidate | 0.930 | 0.942 | 0.510 | 0.895 | 0.684 | 0.477 | 12.078 | 12.089 |
| 18-variable candidate | 0.963 | 0.964 | 0.785 | 0.930 | 0.682 | 0.693 | 6.125 | 6.161 |
| Building-only · 6 attributes | 0.904 | 0.919 | 0.869 | 0.867 | 0.567 | 0.516 | 2.483 | 4.452 |
| 41-variable PCA · 4 PCs | 0.965 | 0.942 | 0.535 | 0.936 | 0.620 | 0.770 | -13.395 | 13.636 |

## The common cohort is selective

**All 2,694,335 common homes are report type 2; no report-type-3 homes satisfy all six score definitions.** Only 1.35% of flats and 6.26% of maisonettes remain in the common cohort, versus 83.21% of houses and 96.38% of bungalows. This primary matrix is internally comparable but is not representative of all housing or all EPC report types. Pairwise results are essential sensitivity checks.

| Other score versus 41 baseline | Pairwise latest homes | Spearman rho | Lin CCC |
|---|---:|---:|---:|
| 5-variable candidate | 3,235,889 | 0.810 | 0.327 |
| 10-variable candidate | 2,900,840 | 0.932 | 0.528 |
| 18-variable candidate | 2,694,335 | 0.963 | 0.785 |
| Building-only · 6 attributes | 3,978,388 | 0.936 | 0.939 |
| 41-variable PCA · 4 PCs | 3,978,640 | 0.944 | 0.748 |

Tie-corrected Kendall concordance W across all six rank systems is **0.8882** for common homes and **0.9061** for eligible common-cohort authorities. These summarize concordance, not validity.

## Interpreting the metrics

- Spearman rho: alignment of average ranks. Pearson r: linear association. Neither establishes identical numerical scores.
- Lin CCC: `2 cov(A,B)/(var(A)+var(B)+(mean(A)-mean(B))²)` using population moments. It penalizes scale and location differences. Reported on published 0–100 scales; PCA rescaling changes the interpretation.
- Quadratic-weighted Cohen kappa: agreement of within-cohort rank quintiles. Average ranks keep ties intact; quintile = `min(4,floor(5*(average_rank-.5)/n))`. Equal-score homes are never split arbitrarily, so group sizes can differ.
- Bottom/top decile Jaccard: intersection divided by union for `score <= empirical P10` and `score >= empirical P90`. Threshold ties are included; effective tail fractions can exceed 10%. Cutoffs and actual fractions are in pair downloads and the website details.
- Mean difference is B minus A in published score points. MAE and RMSE describe paired numerical differences; average absolute percentile gaps describe ranking shifts.
- No confidence intervals, p-values or causal claims are reported; this is a descriptive comparison of the linked dataset.

## Patterns are nominal

The four building patterns are not seventh numeric scores. They are compared using score distributions within each pattern, eta-squared (between-pattern / total score variation), and normalized mutual information with score-rank quintiles. These are associations, not agreement, ranking of type IDs or validation. All such comparisons use the same six-score-complete home cohort.

## Coverage and subgroup sensitivity

Use `chq_agreement_coverage.csv` for per-model availability, `chq_agreement_common_coverage.csv` for common-cohort retention by report type, dwelling type and latest transaction year, and `chq_agreement_subgroups.csv` for same-common-cohort pairwise rank correlations within those groups. Pairwise sample results in `chq_agreement_pairs.csv` use different denominators per score pair; compare them with the fixed common-cohort primary results. The website displays both.

## Limits

- Shared EPC inputs create structural dependence; high agreement is not independent climate or health validation.
- 41 baseline uses original full-sample coding; 5/10/18 candidates use discovery-frozen coding. Comparisons use published scores as-is, not harmonized refits.
- PCA uses its published percentile rescaling and median-imputed inputs; its score units have different calibration. Low CCC can coexist with high rank correlation.
- All-six complete-case restriction selects a subset; compare pairwise coverage and dwelling/report/year diagnostics.
- The PCA composite sign was aligned to the equal-weight baseline during its construction; positive association was partly built in.
- Quintiles and tails are empirical relative groups, not clinical thresholds. Ties are retained, without arbitrary equal-size splitting.
- Cluster IDs are nominal. Pattern-score eta-squared and NMI describe association and reuse six core inputs, not causal effects or independent validation.
- No confidence intervals or causal claims; results describe this dataset. The pooled latest-year cohorts are not a longitudinal panel.

## Reproduction and verification

```bash
python3 analysis/compare_chq_agreement.py --root /path/to/analysis --out /path/to/local/agreement
```

Dependencies: numpy, pandas, pyarrow, scipy, scikit-learn and matplotlib. Only aggregate CSV/JSON/figures are published. No dwelling identifiers or source-level scores are uploaded. The methods JSON records metric definitions, source paths and SHA256 checksums. Validation checks aligned rows, entity uniqueness, counts, metric ranges, pattern totals, source-geography reconciliation and independent Spearman/bias calculations.
