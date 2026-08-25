# Recommended execution order

## Routine manuscript reproduction

Run from the repository root:

1. `python scripts/01_prepare_visitor_demand_2023_2025.py`
   - Harmonizes destination-level visitor records for 2023–2025.
   - Input files remain local/private unless redistribution is permitted.

2. `python scripts/02_validate_hybrid_grid.py`
   - Loads and validates the frozen 1,358-grid Hybrid AECS layer.

3. `python scripts/03_priority_classification.py`
   - Applies the final 33rd and 66th percentile priority thresholds.

4. `python scripts/04_primary_demand_spatial_linkage.py`
   - Links destinations to the verified Hybrid AECS grid and produces the primary
     readiness–demand analysis.

5. `python scripts/05_percentile_supply_demand_mismatch.py`
   - Applies the verified Diana Water Park coordinate and calculates the final
     percentile-based supply–demand mismatch.

6. `python scripts/06_spatial_sensitivity_and_stability.py`
   - Produces the non-manual n=10 and strict n=7 sensitivity analyses and class-stability
     outputs.

7. `python scripts/07_q1_additional_robustness_audit.py`
   - Produces permutation/bootstrap diagnostics, critical |rho| thresholds, realized
     component contributions, and temporal class-retention diagnostics.

8. `python scripts/08_manuscript_figures_and_tables.py`
   - Generates the manuscript-ready tables and figures from the final outputs.

9. Run the fixed-sample temporal-window sensitivity analysis with explicit
   paths to the private administrative visitor workbooks:

   ```bash
   python scripts/09_temporal_window_sensitivity_2021_2025.py \
     --visitor-2021 "/private/path/visitor_2021.xlsx" \
     --visitor-2022 "/private/path/visitor_2022.xlsx" \
     --primary-demand "/private/path/FINAL_HYBRID_AECS_VISITOR_DEMAND_RESULTS.xlsx" \
     --output-dir "outputs/09_temporal_window_sensitivity_2021_2025"
   ```

   - Compares the primary 2023–2025 and extended 2021–2025 windows for the same
     destination sample.
   - Produces the association comparison, destination-level class-retention
     results, input audit, and Supplementary Table S8 source tables.
   - Earlier years increase temporal coverage but not the number of independent
     destination-level observations.

## Optional provenance audit

`python scripts/audit/09_optional_find_verified_grid_parent.py`

This historical audit was used to identify the parent 1,358-grid file matching a
verified top-20 reference. It is **not required** for routine reproduction once the
frozen processed Hybrid AECS GeoJSON is supplied.
