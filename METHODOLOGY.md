# CHQ maps: methods and results

Data processed: 21 October 2026. The maps use `chq_equal`, the equal-weight
index of 41 current-state variables. No PCA, variable selection or aggregation
into six domains has been applied.

## Calculation

For each transaction, available variable scores are averaged after coding and
aligning their direction so that higher values indicate better quality:

\[
CHQ_i=\frac{100}{m_i}\sum_{j\in O_i}s_{ij},\qquad
s_{ij}\in[0,1],\quad m_i=|O_i|\leq41.
\]

The coding follows `build_chq_equal.py` in the separate analysis project.
Missing or inapplicable variables are excluded from that transaction’s
denominator, so effective weights can differ between transactions. Each local
authority’s score is the arithmetic mean of its valid transaction CHQ scores,
giving each transaction equal weight. No housing-stock weights are applied.
The separate analysis also contains an extended 49-variable score, including
eight potential-performance variables. The website displays the 41-variable
baseline only.

Geographic matching uses `onspd_lad_code` and ONS December 2024 Local Authority
Districts (BGC) boundaries. The same boundaries are used for every year from
2012 to 2024. In total, 4,368,473 transactions match to 318 authorities; 14
records have no mapped authority. On CHQ maps, authorities with fewer than 100
valid transactions are grey by default. For the pooled period, only the Isles
of Scilly (two transactions) falls below this threshold.

The source includes England and Wales; an earlier England-only description
was incorrect. ONSPD geography assigns 4,217,705 transactions to England and
150,768 to Wales. The source `country` field and postcode geography disagree
on 97 records; the map consistently uses postcode geography.

## Main findings

- The mean CHQ across all mapped transactions is 62.5152.
- Regional means: East Midlands 64.12; South West 63.35; North East 63.11;
  South East 63.00; East of England 62.90; West Midlands 62.18; London 62.02;
  North West 61.93; Yorkshire and The Humber 61.50; Wales 60.43.
- Variation within regions is substantial. In London, Tower Hamlets has a
  mean of 75.88 (28,626 transactions), compared with 55.67 in Kensington and
  Chelsea (11,139 transactions). These results do not suggest a simple
  north–south gradient.
- The median authority mean is 62.75; the 10th and 90th percentiles are about
  58.93 and 68.04.
- Authority-level variable completeness ranges from 78.4% to 90.2%. It is the
  mean available variable count divided by 41, not geographic coverage.

These are sales-sample averages. They are not adjusted for sale year, dwelling
mix or missing-variable mix, and are not weighted by housing stock or population.
A high CHQ score does not establish validated climate resilience. Giving each
unique EPC equal weight produces authority means correlated at 0.99951 with the
transaction-weighted means, with a maximum absolute difference of 0.626 points.
This sensitivity check addresses repeated-sales weighting only.

## Published files

- `downloads/chq_41_variables.csv`: all 41 baseline variables, definitions, source
  fields, scoring rules and missing rates. This is also shown in the website table.

- `downloads/lad_chq_summary.csv`: pooled local authority summaries.
- `downloads/lad_chq_by_year.csv`: annual local authority summaries.
- `downloads/region_chq_summary.csv`: pooled regional summaries.
- `downloads/chq_equal_lad_map.png` and `.pdf`: authority means, a London inset
  and regional comparisons. The colour scale is 50–90; the index remains 0–100.
- `downloads/chq_map_coverage.png`: transaction counts and variable completeness.

The website contains only aggregate records. Transaction identifiers, addresses
and row-level certificates are not published. Neither house prices nor climate
observations enter the CHQ scores or geographic aggregation.

## Reproduction and validation

The separate analysis project contains `aggregate_chq_maps.py` and
`plot_chq_maps.py`. In the original server environment, the maps were produced
with:

```bash
cd /workplace/UKClimate
/workplace/.venv-urban-dinov3/bin/python aggregate_chq_maps.py
/usr/bin/python3 plot_chq_maps.py
```

The analysis outputs are in `data/analysis/chq_maps_v1/` in that project.
They include country summaries, unique-EPC sensitivity results and audit files
in addition to the public downloads above. Source data and analysis caches are
not part of this website repository.

Aggregation checks confirmed source-row order and transaction/EPC identifiers,
geometry matches, consistent counts across geographic levels, and reconciliation
of annual and pooled means. Website checks cover all 318 map polygons, search,
keyboard selection, year controls, the 41-row variable table, zoom, downloads and
mobile layout. See [README.md](README.md) for running the website checks.

## Boundary attribution

[ONS Local Authority Districts, December 2024 (BGC)](https://www.arcgis.com/home/item.html?id=6a05f93297cf4a438d08e972099f54b9).
Contains public sector information licensed under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

## 41-variable PCA result

The website now includes `41-variable PCA CHQ · 4 PCs` as an exploratory
alternative to the baseline. It uses the same 41 current-state, higher-is-better
0–1 encodings. Each variable is median-imputed, all 41 columns are z-score
standardised, and an ordinary PCA is fitted to the full score file. The first
four PCs are retained; they explain 43.43% of the standardised variance. The
composite is the explained-variance-weighted sum of the four oriented PC scores,
with its sign chosen to agree positively with the equal-weight baseline. The
result is clipped at the source 1st and 99th percentiles and linearly mapped to
0–100. The map reports the mean composite for each local authority and year;
the coverage view reports mean input completeness across the 41 variables.

This PCA score is a data-reduction result, not a validated health, thermal
comfort or climate-resilience outcome. PCA signs/loadings are sample-dependent,
and median imputation means a score can be produced when some inputs are
missing; input coverage should therefore be examined alongside the score. The
model does not add outdoor weather, hazard exposure or household vulnerability.
The model specification, loadings and area summaries are available in the
three PCA downloads below.

PCA files:

- `downloads/chq_pca41_model_specification.json`
- `downloads/chq_pca41_loadings.csv`
- `downloads/chq_pca41_lad_summary.csv`

## Building-only attribute patterns

An exploratory clustering alternative uses the six observed building-only EPC
ratings as separate inputs: walls, windows, heating, controls, hot water and
lighting. One latest record per previously connected entity is used, excluding
252 homes with any missing core attribute. The complete fitting cohort contains
3,978,388 sampled homes (3,978,374 with mapped LAD geography).

K-means uses original 0–1 ordinal scales with equal explicit dimension weights.
Distinct rating profiles are frequency-weighted, exactly preserving the full
cohort objective. Comparison of k = 2–10, cluster sizes and 20 whole-LAD bootstrap
refits selects a coarse four-pattern solution using an exploratory silhouette
tolerance of 0.02. Silhouette is 0.3318; median bootstrap ARI is 0.9915. Seven to
nine clusters give a higher silhouette (about 0.351); four is an interpretable
resolution choice rather than a uniquely established cluster count.

The four patterns are stronger envelope/services (34.4%), weak walls with
stronger services (32.8%), lighting shortfall (23.3%), and heating/hot-water
shortfall (9.5%). Mean original building-only CHQ is respectively 81.6, 60.5,
52.3 and 50.4. This total is reported after clustering and is not a fit input.
Z-score refitting yields ARI 0.5725: classification depends on the metric.
Pattern proportions also differ markedly by EPC report type; subgroup shares
and within-report-type refits are provided. None validates indoor climate or
health outcomes.

The map's pattern option displays area pluralities or individual pattern shares.
Every area contains a mixture. Its year controls select latest-transaction-year
cohorts, not the same homes repeatedly; no housing-stock weighting is used.
Complete-home coverage, small-area masking and tied pluralities are explicit.
The existing transaction-mean CHQ and PCA maps retain their prior definitions.

See [the full clustering report](downloads/chq_building_cluster_report.md),
[model and sensitivity](downloads/chq_building_cluster_model.json), and
[reproducible analysis](analysis/build_building_clusters.py). Row-level labels
remain on the research server; only summaries and figures are published.

## Agreement of the six published numeric scores

The Agreement section compares the original 41-variable baseline, 5/10/18-variable
candidates, building-only six-attribute score and published four-PC score. It
joins the unchanged scores by exact source row. Primary results use 2,694,335
latest sampled homes with all six scores; secondary matrices use pairwise
available latest homes or 314 authority means of the same common homes
(minimum 100 per authority, equal authority weights). No scores are refitted or
imputed for this comparison. Full transaction-weighted results are also in the
downloaded pair metrics as a repeated-sales sensitivity check.

This common cohort retains 67.7% of latest sampled homes, all report type 2,
including only 1.35% of flats and 6.26% of maisonettes. It is a selected comparison
sample. Pairwise samples have different denominators and are presented alongside
it; score coverage and common-cohort retention by dwelling/report/year are
explicit. The pooled comparison does not follow the map's year or area controls.

Spearman and Pearson describe association. Lin CCC describes numerical
concordance on the published scales. Quadratic-weighted rank-quintile kappa,
threshold-inclusive bottom/top decile Jaccard, mean bias, MAE, RMSE and mean
absolute rank-percentile gaps add complementary agreement measures. Average
ranks preserve score ties; tied scores stay together in empirical quintiles.
Decile cutoffs include ties and can yield groups larger than 10%; actual fractions
are displayed. Global rank concordance uses tie-corrected Kendall W.

Shared EPC inputs and the PCA's baseline-oriented sign create dependence;
agreement is not independent outcome validation. Different coding/calibration
is retained: candidates use discovery-frozen encoding, while the original
baseline uses earlier full-sample coding and PCA uses percentile-rescaled,
imputed inputs. High rank correlation can coexist with lower numerical CCC.
Area agreement does not establish agreement among individual homes.

The four building patterns are nominal categories. Their IDs are never
correlated with numeric scores. Mean/quantile score distributions, eta-squared
and normalized mutual information describe their association with each score
on the common cohort. Pattern shares consequently differ from the full
clustering sample. These analyses do not establish validity or causality.

See [the agreement report](downloads/chq_agreement_report.md),
[methods and denominators](downloads/chq_agreement_methods.json),
[pair metrics](downloads/chq_agreement_pairs.csv), and
[reproduction script](analysis/compare_chq_agreement.py). Only aggregates and
exportable figures are published; no source-level records are uploaded.

## Building-only PCA distribution in two dimensions

The PCA-space section projects the same six original 0–1 EPC attributes used
for clustering. It uses the identical 3,978,388 complete latest sampled homes,
mean-centred without z-score scaling, and keeps the existing six-dimensional
cluster labels. No new cluster fit or CHQ composite is created.

PCA is computed from the exact frequency-weighted sample covariance of all
7,507 distinct six-rating profiles. This equals the covariance of the full
complete-home cohort, rather than an unweighted PCA of unique combinations.
PC1 explains 44.2308% and PC2 22.6479% of variance, cumulatively 66.8788%.
The remaining four components retain 33.1212%; overlap in the two displayed
axes does not establish separation or lack of separation in six dimensions.
PC1 is associated mainly with walls, windows and lighting; PC2 contrasts
lighting with wall ratings. Neither axis represents measured climate or a new
quality standard. For reproducible sign choice, each component's coefficient
with greatest absolute magnitude is positive.

The interactive plot includes every distinct profile, without jitter or random
sampling. Marker size increases with log home frequency; each point can
represent multiple homes. The optional density view uses exact household
counts within a fixed 90-by-70 grid, with colour indicating the cell's plurality
cluster and intensity scaled by log counts. Filtering retains fixed coordinate
axes and rescales density intensity. Cell compositions and profile frequencies
are available on hover/tap; projected cluster means are marked with crosses.
The pooled plot is independent of the map's year/authority controls.

[Profile coordinates and frequencies](downloads/chq_building_pca2_profiles.csv),
[coefficients and correlation loadings](downloads/chq_building_pca2_loadings.csv),
[all explained variance shares](downloads/chq_building_pca2_variance.csv), and
[the projection model](downloads/chq_building_pca2_model.json) are public aggregate
outputs. Per-home coordinates and identifiers remain local. Standalone
[PNG](downloads/chq_building_pca2.png) and [PDF](downloads/chq_building_pca2.pdf)
figures are included. Reproduce using
[analysis/project_building_pca.py](analysis/project_building_pca.py).

Validation checks confirm aligned original labels, entity uniqueness, exact
cohort and frequency totals, equality of weighted and full-home covariance,
orthonormal component vectors, diagonal PC covariance, zero weighted PC means,
projection of original cluster centroids, and independent row transformations.

## Consolidated research report

The [Chinese research report](reports/CHQ_research_report_zh.md) summarizes all
current published results and distinguishes transactions, latest homes and
common-score cohorts. [HTML](reports/CHQ_research_report_zh.html) and
[PDF](reports/CHQ_research_report_zh.pdf) include four published figures.
It adds a descriptive [six-score distribution table](downloads/chq_report_score_distributions.csv)
from unchanged source scores; it does not fit or revise any model.
The [manifest](reports/report_manifest.json) records source and output checksums.
