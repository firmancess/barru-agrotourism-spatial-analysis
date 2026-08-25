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
- evaluating realized component contributions and temporal class stability;
- testing fixed-sample temporal-window sensitivity by comparing 2023–2025 with
  2021–2025; and
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
│   ├── 09_temporal_window_sensitivity_2021_2025.py
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
```

## Fixed-sample temporal-window sensitivity

`scripts/09_temporal_window_sensitivity_2021_2025.py` compares the primary
2023–2025 visitor-demand window with an extended 2021–2025 window for the same
destination sample. It reads the official 2021 and 2022 visitor workbooks and
the frozen primary destination-demand output. Missing destination-year values
remain missing and are not replaced by zero.

The earlier observations expand temporal coverage but do not increase the
number of independent destination-level observations. Historical destinations
without frozen AECS and spatial metadata are retained in the input audit but
excluded from the fixed-sample comparison.

Example:

```bash
python scripts/09_temporal_window_sensitivity_2021_2025.py \
  --visitor-2021 "/private/path/visitor_2021.xlsx" \
  --visitor-2022 "/private/path/visitor_2022.xlsx" \
  --primary-demand "/private/path/FINAL_HYBRID_AECS_VISITOR_DEMAND_RESULTS.xlsx" \
  --output-dir "outputs/09_temporal_window_sensitivity_2021_2025"
```

The administrative visitor workbooks are not distributed in this public
repository. See `DATA_SOURCES.md` and `data/raw/visitor_records/README.md`.
