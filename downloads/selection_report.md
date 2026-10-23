# CHQ variable selection: research results

Version: chq_selection_v1. Data processed 23 October 2026.

The original 41-variable baseline remains the default. The 5-, 10- and
18-variable scores are research candidates, not validated replacements.

## Design

All 41 variables were audited. Thirty-two passed the general-purpose candidate
rules; nine were retained as auxiliary attributes because of structural
applicability, contested direction, historical missingness or near-constant
facility prevalence. These eligibility rules are methodological choices.

Discovery: 250,000 distinct housing entities, latest sales in 2012–2019.
Tuning: 100,000, 2020–2021. Final test: 120,000, 2022–2024.
Entities were grouped using UPRN, with EPC fallback and conservative merging of
conflicting EPC links. No entity crossed the time partitions. UPRN coverage was
99.738%; fallback identifiers cannot detect every re-certified dwelling.

Text calibration and P1/P99 scaling were refitted within discovery data.
Selection used signed Spearman correlation, average-linkage variable clustering
and actual variable representatives. Five geographic folds and 100 grouped
re-fits examined stability. Sparse PCA was a discovery-only comparison.

Fixed reconstruction targets excluded all predictors in the target's declared
encoding/dependency family. Ridge models used training-median-filled predictors
and missing indicators; only observed targets were evaluated. Loss was
normalised by discovery standard deviations and balanced across dependency
families and local authorities. Thus the task measures cross-family information
retention, not independent climate outcomes.

## Results

| Variables | Tuning loss | Final-test loss | Test rank correlation with discovery-coded 41-variable baseline | Complete-score coverage, full sales sample |
|---|---:|---:|---:|---:|
| 5 | 0.68184 | 0.71202 | 0.810 | 81.8% |
| 10 | 0.56329 | 0.61816 | 0.922 | 73.4% |
| 18 | 0.48497 | 0.61468 | 0.965 | 68.2% |
| 32 | 0.45764 | 0.58456 | 0.999 | 67.3% |

Lower reconstruction loss is better. Final-test null loss was 0.93570.
Correlations compare complete records and do not measure climate validity.
The score sets contain different information and their numerical levels are
not calibrated to the same distribution.

The one-standard-error rule selected 32 among the tested counts
3–15, 18, 20, 24 and 32. Counts 25–31 were not evaluated; 24 was only 0.00098
above the threshold. This does not prove that exactly 32 variables are necessary.
The 32-variable result retains redundancy and fails the intended small,
low-redundancy goal. Eighteen variables passed a secondary tuning threshold of
90% of the attainable error reduction; this is not 90% of variance or quality.

## Stability and coverage limits

The ten-variable reference set includes current energy efficiency, roof rating,
window description, main heating energy rating, heating controls, low-energy
lighting proportion, main fuel, heated-room share, fireplace density and
hot-water cost per area.

Eight reference representatives appeared in at least 90% of grouped re-fits.
Main heating energy rating appeared in 17%, with the environmental rating often
substituted (83%). Lighting share appeared in 51%, with near-equivalent lighting
description substituted (49%). Cluster coverage is more stable than the literal
variable list. No post-test substitution was made.

Ten-variable complete-score coverage was only 22.8% for flats, versus 84.3%
for houses. Neither the five- nor ten-variable score was computable for any of
the 795,478 report_type=3 records, largely because of recording mechanisms for
heated-room information. Do not impute structural absence as poor quality.
The type codes are reported without inferring their textual meaning.

The website therefore provides completeness coverage and the original baseline
on the exact same scored sales. Comparing a candidate's restricted cohort to
the unrestricted original map mixes score changes with sample composition.

## Scores and publication

Each candidate is 100 times the arithmetic mean of its frozen 0–1 scores, only
where every selected variable is observed. Missing scores remain unavailable.
No variable selection used prices or climate outcomes. No independent energy,
indoor-temperature, overheating or disaster-loss validation was performed.
These candidates do not establish physical climate resilience or causation.

Only local authority aggregates, variable dictionaries and research summaries
are published. Source transactions, addresses and identifiers remain outside
the website repository. The detailed Chinese analysis report and full score
files are retained in the private local analysis workspace.
