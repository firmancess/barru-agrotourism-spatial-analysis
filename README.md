# Barru Agrotourism Spatial Supply–Demand Analysis

This repository contains analysis code and processed spatial data supporting the manuscript:

**Spatial Supply–Demand Mismatches in Agrotourism Corridor Planning: Integrating Multi-Criteria Readiness and Observed Visitor Demand in Barru Regency, Indonesia**

## Authors

1. Muhammad Anshar
2. Irsyadi Siradjuddin
3. Andi Idham AP
4. Ahmad Firman Ashari

Repository maintenance: **Ahmad Firman Ashari**

## Repository purpose

This repository supports reproducibility of the manuscript-relevant analyses conducted after construction of the verified Hybrid Agrotourism Experience Corridor Score (AECS) grid.

The repository includes code for:

- harmonizing destination-level visitor observations for 2023–2025;
- validating the final 1,358-grid Hybrid AECS layer;
- classifying low-, moderate-, and high-priority grids;
- linking observed tourism destinations to the AECS grid;
- calculating percentile-based spatial supply–demand mismatch;
- evaluating coordinate-quality sensitivity;
- assessing AECS–visitor demand associations;
- conducting bootstrap and permutation-based robustness diagnostics;
- evaluating realized component contributions and temporal class stability; and
- generating manuscript-related tables and figures.

## Repository structure

```text
.
├── README.md
├── CITATION.cff
├── DATA_SOURCES.md
├── DATA_TERMS.md
├── MANUSCRIPT_SCRIPT_COVERAGE.md
├── RUN_ORDER.md
├── requirements.txt
├── .gitignore
│
├── scripts/
│   ├── 01_prepare_visitor_demand_2023_2025.py
│   ├── 02_validate_hybrid_grid.py
│   ├── 03_priority_classification.py
│   ├── 04_primary_demand_spatial_linkage.py
│   ├── 05_percentile_supply_demand_mismatch.py
│   ├── 06_spatial_sensitivity_and_stability.py
│   ├── 07_q1_additional_robustness_audit.py
│   ├── 08_manuscript_figures_and_tables.py
│   ├── LICENSE
│   └── audit/
│       └── 09_optional_find_verified_grid_parent.py
│
├── data/
│   ├── processed/
│   │   ├── README.md
│   │   └── agrotourism_corridor_grid_result_HYBRID.geojson
│   └── raw/
│       └── visitor_records/
│           └── README.md
│
├── provenance/
│   ├── README.md
│   └── notebook_cell_mapping.csv
│
└── outputs/
