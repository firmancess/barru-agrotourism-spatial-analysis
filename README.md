# Barru Agrotourism Spatial Supply–Demand Analysis

This repository contains cleaned analysis code supporting the manuscript:

**Spatial Supply–Demand Mismatches in Agrotourism Corridor Planning: Integrating
Multi-Criteria Readiness and Observed Visitor Demand in Barru Regency, Indonesia**

## Repository purpose

The code reproduces the manuscript-relevant analysis **from the verified processed
Hybrid AECS grid onward**, including visitor-data harmonization, priority
classification, destination-to-grid linkage, percentile mismatch, coordinate-quality
sensitivity, robustness diagnostics, and manuscript figures/tables.

The public code is derived from the final notebook cells, but notebook-specific Google
Drive paths and interactive Colab upload commands have been removed.

## Important scope limitation

The uploaded source notebook does **not** contain a fully verified end-to-end script
that recreates the final Hybrid AECS grid from all raw ALI, TAI, ASI, RNAI, and EQI
inputs, nor the exact final construction code for all seven weighting-sensitivity
scenarios reported in the manuscript. Therefore, this repository must not claim full
raw-data-to-AECS reproducibility unless those original scripts are later added.

## Structure

```text
.
├── README.md
├── RUN_ORDER.md
├── MANUSCRIPT_SCRIPT_COVERAGE.md
├── requirements.txt
├── .gitignore
├── scripts/
│   ├── 01_prepare_visitor_demand_2023_2025.py
│   ├── 02_validate_hybrid_grid.py
│   ├── 03_priority_classification.py
│   ├── 04_primary_demand_spatial_linkage.py
│   ├── 05_percentile_supply_demand_mismatch.py
│   ├── 06_spatial_sensitivity_and_stability.py
│   ├── 07_q1_additional_robustness_audit.py
│   ├── 08_manuscript_figures_and_tables.py
│   └── audit/
│       └── 09_optional_find_verified_grid_parent.py
├── data/
│   ├── raw/visitor_records/
│   └── processed/
├── outputs/
└── provenance/
```

## Data handling

Administrative visitor workbooks are excluded from Git by default. Do not publish them
unless redistribution is explicitly permitted by the data provider.

The final processed Hybrid AECS GeoJSON may be placed in `data/processed/` when the
team has confirmed that it can be shared.

## Environment

Install dependencies with:

```bash
pip install -r requirements.txt
```

Then follow `RUN_ORDER.md`.

## GitHub and Zenodo

The GitHub account/repository owner does not need to be the corresponding author.
When the repository is ready for public release, archive a tagged GitHub release in
Zenodo and ensure the Zenodo creator/contributor metadata accurately represents the
research team.

Do not insert a Zenodo DOI into the manuscript until the archived release has actually
been created.
