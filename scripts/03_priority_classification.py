"""
Classify Hybrid AECS into low, moderate, and high priority using the 33rd and 66th percentiles.

Clean public version derived from the final manuscript-relevant notebook cell 68.
Personal Google Drive paths and notebook-only execution assumptions were removed.
Analytical logic is retained where it is verifiable from the uploaded notebook.
"""


from pathlib import Path
import os
import re
import numpy as np
import pandas as pd
import geopandas as gpd

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(
    os.environ.get("AECS_PROJECT_ROOT", SCRIPT_DIR.parent)
).resolve()

GRID_FILE = (
    REPO_ROOT / "data" / "processed"
    / "agrotourism_corridor_grid_result_HYBRID.geojson"
)
OUT_DIR = REPO_ROOT / "outputs" / "03_priority_classification"
OUT_DIR.mkdir(parents=True, exist_ok=True)

if not GRID_FILE.exists():
    raise FileNotFoundError(
        f"Processed Hybrid AECS grid not found: {GRID_FILE}"
    )

grid = gpd.read_file(GRID_FILE)


def clean_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


lookup = {clean_name(c): c for c in grid.columns}
aecs_source = None
for candidate in [
    "AECS", "AECS_HYBRID", "hybrid_aecs",
    "agrotourism_experience_corridor_score"
]:
    key = clean_name(candidate)
    if key in lookup:
        aecs_source = lookup[key]
        break

if aecs_source is None:
    raise KeyError(
        "Could not identify the final AECS column in the processed grid."
    )

if aecs_source != "AECS":
    grid = grid.rename(columns={aecs_source: "AECS"})

grid["AECS"] = pd.to_numeric(grid["AECS"], errors="coerce")

Q33 = grid["AECS"].quantile(0.33)
Q66 = grid["AECS"].quantile(0.66)

grid["priority_final"] = np.select(
    [
        grid["AECS"] <= Q33,
        (grid["AECS"] > Q33) & (grid["AECS"] <= Q66),
        grid["AECS"] > Q66,
    ],
    [
        "Low priority",
        "Moderate priority",
        "High priority",
    ],
    default="Moderate priority",
).astype(object)

summary = (
    grid["priority_final"]
    .value_counts()
    .rename_axis("priority_class")
    .reset_index(name="n_grids")
)

summary.to_csv(OUT_DIR / "priority_class_summary.csv", index=False)
grid.to_file(
    OUT_DIR / "hybrid_aecs_priority_classified.geojson",
    driver="GeoJSON"
)

print(f"AECS Q33 = {Q33:.6f}")
print(f"AECS Q66 = {Q66:.6f}")
print(summary.to_string(index=False))
print("Saved:", OUT_DIR)
