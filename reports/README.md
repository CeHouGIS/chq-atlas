# CHQ research report

Chinese report snapshot dated 2026-10-31, covering all current published CHQ
results. It documents existing outputs; no score or model is changed.

- `CHQ_research_report_zh.html`: standalone figures for browser/offline reading.
  Appendix links require this repository or the hosted site.
- `CHQ_research_report_zh.pdf`: printable report with embedded CJK font.
- `CHQ_research_report_zh.md`: editable source, generated from aggregates.
- `report_manifest.json`: SHA-256 of source files and final report outputs,
  plus the site commit from which the report was compiled.

## Rebuild

From the repository root, with Python 3, pandas, numpy, Markdown and WeasyPrint
installed:

```bash
python3 analysis/build_research_report.py
```

PDF generation uses `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc` (Debian/Ubuntu
package `fonts-wqy-zenhei`). Adjust the PDF-only font path for another system.
WeasyPrint also requires its platform rendering dependencies. Site use and
report downloads require no Python dependencies.

The generator uses published aggregates and figures from `downloads/`. The new
`chq_report_score_distributions.csv` describes the unchanged local score files:
for each model and each of transactions/latest-home cohorts, it reports total
rows, scored rows, coverage, mean, sample SD (`ddof=1`), median, P10 and P90.
Percentiles use pandas' default linear interpolation; latest-home flags come
from the existing building-only score file. Each model's available rows are used
for these descriptive statistics; they are not common-cohort comparisons.
Source-level transactions, addresses, entity keys and scores remain on the
research server and are not part of this report package.

The report is a computational-results synthesis, not a new literature search or
a fresh audit of historical cleaning and model fitting.
