# Building-only CHQ patterns

Exploratory analysis, 28 October 2026.

Four broad patterns were identified from the **six observed building-only EPC attributes**. Clustering uses each attribute separately, not the total CHQ score.

## Cohort and inputs

- Source: 4,368,487 transactions. One latest observation per connected UPRN/EPC entity prevents repeated sales from overweighting a home.
- Latest-observation cohort: 3,978,640 sampled homes. All six ratings observed: **3,978,388**; 252 incomplete homes remain unassigned. A further 14 classified homes lack mapped LAD geography.
- Inputs: walls, windows, main heating, heating controls, hot water, lighting. Existing ordinal scores 0, .25, .5, .75, 1 are retained.
- Primary distance: squared Euclidean on the six original 0–1 scales; each dimension has equal explicit weight. Actual dimension variance still affects distance.
- No PCA, imputation, house prices, outdoor climate, year, geography or total CHQ enters the clustering.
- This is a descriptive pooled fit. Later periods have been used; none is claimed as an untouched test set.

## Main profiles

| Pattern | Homes | Share | Mean CHQ | Walls | Windows | Heating | Controls | Hot water | Lighting |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Stronger envelope and services | 1,368,930 | 34.4% | 81.6 | 85.2 | 80.1 | 75.7 | 79.3 | 75.7 | 93.8 |
| Weak walls, stronger services | 1,305,210 | 32.8% | 60.5 | 16.7 | 50.4 | 74.4 | 62.0 | 71.1 | 88.2 |
| Lighting shortfall | 926,567 | 23.3% | 52.3 | 43.4 | 51.3 | 72.8 | 58.0 | 66.5 | 22.0 |
| Heating and hot-water shortfall | 377,681 | 9.5% | 50.4 | 62.2 | 61.6 | 29.5 | 49.4 | 17.5 | 81.8 |

All component means are on a 0–100 rating scale, not physical efficiency percentages. The names describe relative EPC attribute combinations, not measured indoor comfort or resilience.

Pattern 1 combines strong wall/window ratings with stronger service ratings. Pattern 2 has a marked wall shortfall despite relatively strong heating, hot water and lighting. Pattern 3 is separated mainly by lighting ratings. Pattern 4 has particularly weak heating and hot-water ratings despite stronger walls and windows. Patterns 3 and 4 have similar total CHQ but very different shortfalls: this is why clustering six attributes adds information beyond ranking total scores.

## Choosing the number of clusters

Frequency-weighted ordinary K-means is fitted to the 7,507 distinct six-rating profiles. Weights are the number of fitting homes with each profile. This exactly preserves the full-home within-cluster sum-of-squares objective while avoiding fitting millions of duplicate rows.

Compare k = 2–10 with 30 starts per fit. A fixed random sample of 5,000 complete latest homes is used for silhouette, Calinski–Harabasz and Davies–Bouldin. Twenty whole-LAD bootstrap reweightings per k test stability; each bootstrap is refitted with 10 starts. These are internal diagnostics, not independent outcome validation.

The exploratory selection rule chooses the smallest k within 0.02 of the best eligible silhouette, requiring every cluster to contain at least 2% of homes and median bootstrap adjusted Rand index (ARI) >= 0.80. These tolerances are researcher choices, not preregistered or established quality standards.

- Selected k = 4: silhouette **0.3318**, median LAD-bootstrap ARI **0.9915**, empirical bootstrap 10th percentile **0.9835**.
- Best silhouette among k = 2–10 is k = 9 (**0.3515**); k = 7 is almost identical (**0.3513**). These support finer partitions, rather than establishing four as the only true cluster count.
- The silhouette gain from k = 4 to the best candidate is 0.0197. The selected solution is a coarse descriptive typology; a tighter tolerance would choose more clusters.

## Sensitivity and reporting artefacts

Repeating four-cluster fitting after z-scoring the dimensions gives ARI **0.5725** on the evaluation sample, with **81.24%** of fitting homes retaining the same matched type. Thus global cluster boundaries are sensitive to scaling, even though LAD-bootstrap stability within the chosen metric is high.

**EPC report type is strongly associated with the patterns.** Under the pooled fitted labels, the stronger-envelope/services pattern accounts for **21.7% of report-type-2 homes** and **89.9% of report-type-3 homes**. The association may reflect both dwelling composition and assessment methods; it must not be treated as a causal type effect. Download subgroup shares and within-report-type refit diagnostics in the model JSON. Any later outcome analysis should stratify or adjust for report type, dwelling type and year. Refitting four clusters separately within report types gives ARI 0.639 (type 2) and 0.258 (type 3) against pooled labels on within-type evaluation samples: the pooled typology does not transfer equally to both report strata.

Lighting-pattern share falls from around 37.9% in the 2012 latest-record cohort to 6.6% in 2024. These are different sampled homes and certificate/transaction mixtures; the contrast does not measure within-home improvement or a causal time trend.

## Maps and interpretation

One latest record per home is used for both the pooled and yearly maps. The year is the latest transaction-year cohort, not the EPC inspection year. Pooled counts reconcile with the sum across years. All maps use the same fixed fitted centroids.

Categorical colour shows the plurality pattern among classified sampled homes in a local authority. The area still contains several patterns: use the selected-area composition bars or the individual pattern-share views. Equal pluralities are flagged and resolved by lower cluster ID for display. Grey areas have fewer than 100 classified homes. Shares use classified homes as the denominator; classification coverage uses all latest sampled homes. There are no housing-stock or population weights.

## Reproduction and files

```bash
python3 analysis/build_building_clusters.py --scores /path/to/chq_building_only_scores.parquet --out /path/to/local/outputs
```

Requires Python, numpy, pandas, pyarrow, scipy, scikit-learn 1.3.2, threadpoolctl and matplotlib. Source parquet data remain on the research server. Source-level labels (including unassigned records) are kept locally in `cluster_assignments.parquet`; only aggregates are published.

- `chq_building_cluster_profiles.csv`: national profile means, sizes, shares, CHQ and score dispersion.
- `chq_building_cluster_diagnostics.csv`: k-selection diagnostics.
- `chq_building_cluster_stability.csv`: all 180 bootstrap ARI results.
- `chq_building_cluster_subgroups.csv`: fixed-label shares by report type, dwelling type and latest year.
- `chq_building_cluster_lad_shares.csv`: pooled and annual LAD shares and classified denominators.
- `chq_building_cluster_model.json`: full protocol, frozen centroids, source checksum, results and sensitivity.
- `chq_building_cluster_profiles.png` / `.pdf` and `chq_building_cluster_diagnostics.png`: exportable figures.

Validation checks confirm entity uniqueness, exact ordinal values, agreement with the unchanged building-only score, incomplete-record exclusions, nearest-centroid assignments, profile means, geography totals and annual/pooled count reconciliation.

These are exploratory EPC building-attribute patterns. They do not establish health outcomes, actual indoor temperature, climate exposure, or validated climate resilience.
