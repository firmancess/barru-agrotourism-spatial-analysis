# Manuscript-to-script coverage

The cleaned repository was checked against the uploaded Applied Geography manuscript.

| Manuscript analysis | Public script |
|---|---|
| Visitor records 2023–2025 | `01_prepare_visitor_demand_2023_2025.py` |
| Verified 1,358-grid Hybrid AECS input | `02_validate_hybrid_grid.py` |
| §3.11 priority classification | `03_priority_classification.py` |
| §3.16 spatial linkage | `04_primary_demand_spatial_linkage.py` |
| §3.17 primary AECS–demand association | `04_primary_demand_spatial_linkage.py` |
| §3.18 percentile supply–demand mismatch | `05_percentile_supply_demand_mismatch.py` |
| §3.19 coordinate-quality sensitivity and class stability | `06_spatial_sensitivity_and_stability.py` |
| Robustness statistics reported in §4.9 | `07_q1_additional_robustness_audit.py` |
| ASI realized contribution diagnostic | `07_q1_additional_robustness_audit.py` |
| Final demand-side figures/tables | `08_manuscript_figures_and_tables.py` |

## Not fully reproducible from the uploaded source notebook

Two manuscript components should not be represented as fully reproducible from this
repository unless the original final source code is located and added:

1. The complete raw-data-to-final-Hybrid-AECS construction pipeline for
   ALI, TAI, ASI, RNAI, EQI, and AECS.
2. The exact final code/weight definitions that generated all seven weighting-sensitivity
   scenarios reported in the manuscript.

Earlier notebook prototype cells exist for index construction and clustering, but they
do not match the final manuscript specification closely enough to be labelled as the
final production pipeline.
