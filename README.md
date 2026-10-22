# CHQ Atlas

Interactive administrative-area maps of exploratory Climate Housing Quality
(CHQ) across England and Wales. The site covers 318 local authority districts
using fixed ONS December 2024 boundaries, with linked sales from 2012–2024.

**Website:** https://cehougis.github.io/chq-atlas/

## Explore

- Switch between pooled and annual maps.
- Compare the 41-variable equal-weight baseline, the 49-variable version
  including potential attributes, transaction counts, and variable completeness.
- Search by district name or ONS code, click the map or ranking to select an area,
  and zoom or pan the map.
- Download administrative-area CSV tables and publication-quality figures.

CHQ is averaged across the available coded variables for each transaction,
then averaged across transactions in each area. These are sales-sample means,
unadjusted for sale year, dwelling mix or missing-variable mix. They should not
be interpreted as validated climate resilience or a census of housing stock.

## Run locally

No build, API key, account, package install, or external JavaScript is required.

```bash
python3 -m http.server 8000
```

Open http://localhost:8000. `index.html`, `assets/`, and `downloads/` form the
complete static site. GitHub Pages serves the root of the `main` branch.

`tests/verify_site.cjs` checks desktop/mobile rendering, selection, year/metric
controls, downloads and runtime errors using a local Chromium binary and Node
22 or later:

```bash
CHROME_BIN=/path/to/chrome node tests/verify_site.cjs http://localhost:8000
```

## Data and methods

See [METHODOLOGY.md](METHODOLOGY.md) for calculation and geographic definitions.
The published CSVs contain area-level aggregates only. No transaction identifiers,
addresses, certificates, private repository content or credentials are included.
The underlying row-level data and analysis pipeline are maintained separately;
this repository contains the published map snapshot and its website.

**Source boundary:** [ONS Local Authority Districts, December 2024 (BGC)](https://www.arcgis.com/home/item.html?id=6a05f93297cf4a438d08e972099f54b9).
Contains public sector information licensed under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
This attribution does not assert a blanket licence over other source datasets.

Data snapshot processed 2026-10-21. Neither house prices nor HadUK weather
values enter the published CHQ calculation.
