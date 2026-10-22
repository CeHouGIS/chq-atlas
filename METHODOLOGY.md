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
