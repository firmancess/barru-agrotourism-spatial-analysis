"""
Apply the verified Diana Water Park assignment and compute percentile-based supply–demand mismatch.

Clean public version derived from the final manuscript-relevant notebook cell 70.
Personal Google Drive paths and notebook-only execution assumptions were removed.
Analytical logic is retained where it is verifiable from the uploaded notebook.
"""

# =====================================================================
# =====================================================================
# FINAL CORRECTION CELL
# DIANA SPATIAL AUDIT + PERCENTILE-RANK SUPPLY–DEMAND MISMATCH
#
# Jalankan SETELAH analisis final sebelumnya.
#
# Memerlukan variable:
# - grid
# - analysis
# - destination_grid
#
# Jika variable hilang, script akan mencoba membaca output sebelumnya.
#
# OUTPUT FINAL:
# 1. Diana Water Park spatial assignment audit
# 2. Percentile-based supply-demand mismatch
# 3. Robust four-quadrant typology
# 4. Fig. 02 FINAL supply-demand matrix
# 5. Fig. 03 FINAL spatial mismatch map
# 6. Final manuscript-ready mismatch tables
# =====================================================================
# =====================================================================


# =====================================================================
# 00. IMPORT
# =====================================================================

import os
import re
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from IPython.display import display


# =====================================================================
# 01. PATH
# =====================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(
    os.environ.get("AECS_PROJECT_ROOT", SCRIPT_DIR.parent)
).resolve()

ROOT = REPO_ROOT

GRID_FILE = (
    REPO_ROOT
    / "data"
    / "processed"
    / "agrotourism_corridor_grid_result_HYBRID.geojson"
)

PREVIOUS_DIR = (
    REPO_ROOT
    / "outputs"
    / "04_primary_demand_spatial_linkage"
)

FINAL_DIR_V2 = (
    REPO_ROOT
    / "outputs"
    / "05_percentile_supply_demand_mismatch"
)

FIG_DIR_V2 = (
    FINAL_DIR_V2
    / "figures_600dpi"
)

TABLE_DIR_V2 = (
    FINAL_DIR_V2
    / "tables"
)

for p in [
    FINAL_DIR_V2,
    FIG_DIR_V2,
    TABLE_DIR_V2
]:
    p.mkdir(
        parents=True,
        exist_ok=True
    )


GEOG_CRS = "EPSG:4326"
METRIC_CRS = "EPSG:32750"


print("=" * 95)
print("FINAL CORRECTION")
print("DIANA AUDIT + PERCENTILE-RANK SUPPLY–DEMAND MISMATCH")
print("=" * 95)


# =====================================================================
# 02. HELPER
# =====================================================================

def normalize_grid_id(x):

    if pd.isna(x):
        return np.nan

    s = str(x).strip()

    m = re.search(
        r"(\d+)",
        s
    )

    if not m:
        return s

    return (
        "G"
        + str(
            int(
                m.group(1)
            )
        ).zfill(4)
    )


def midrank_percentile_against_reference(
    value,
    reference_array
):
    """
    Empirical mid-rank percentile.

    Nilai berada sekitar:
    0 < percentile < 1

    Lebih baik daripada min-max untuk membandingkan
    dua distribusi yang berbeda.
    """

    arr = np.asarray(
        reference_array,
        dtype=float
    )

    arr = arr[
        np.isfinite(
            arr
        )
    ]

    arr = np.sort(
        arr
    )

    if (
        len(arr) == 0
        or
        not np.isfinite(value)
    ):
        return np.nan

    left = np.searchsorted(
        arr,
        value,
        side="left"
    )

    right = np.searchsorted(
        arr,
        value,
        side="right"
    )

    # Mid-rank empirical percentile
    return (
        (left + right)
        /
        (2.0 * len(arr))
    )


def sample_midrank_percentile(series):
    """
    Percentile dalam sample menggunakan mid-rank:

        P = (rank - 0.5) / n

    Cocok dengan empirical percentile supply.
    """

    x = pd.to_numeric(
        series,
        errors="coerce"
    )

    result = pd.Series(
        np.nan,
        index=x.index,
        dtype=float
    )

    valid = x.notna()

    n = valid.sum()

    if n == 0:
        return result

    ranks = x[
        valid
    ].rank(
        method="average"
    )

    result.loc[
        valid
    ] = (
        ranks - 0.5
    ) / n

    return result


def save_final_fig(
    filename
):

    path = (
        FIG_DIR_V2
        / filename
    )

    plt.tight_layout()

    plt.savefig(
        path,
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

    print(
        "Saved:",
        path
    )


# =====================================================================
# 03. LOAD + STANDARDIZE VERIFIED HYBRID GRID
# FIXED ROBUST VERSION
# =====================================================================

if not GRID_FILE.exists():
    raise FileNotFoundError(
        f"Verified Hybrid grid tidak ditemukan:\n{GRID_FILE}"
    )


grid_final = gpd.read_file(
    GRID_FILE
)


print()
print("=" * 100)
print("GRID SCHEMA CHECK")
print("=" * 100)

print("Rows:", len(grid_final))
print()
print("Original columns:")
print(list(grid_final.columns))


# ---------------------------------------------------------------------
# CRS
# ---------------------------------------------------------------------

if grid_final.crs is None:

    grid_final = grid_final.set_crs(
        GEOG_CRS
    )


grid_final = grid_final.to_crs(
    GEOG_CRS
)


# ---------------------------------------------------------------------
# FLEXIBLE COLUMN FINDER
# ---------------------------------------------------------------------

def _clean_colname(x):

    return (
        str(x)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


def find_existing_column(
    df,
    candidates
):

    lookup = {
        _clean_colname(c): c
        for c in df.columns
    }


    for candidate in candidates:

        key = _clean_colname(
            candidate
        )

        if key in lookup:

            return lookup[
                key
            ]


    return None


# ---------------------------------------------------------------------
# GRID ID
# ---------------------------------------------------------------------

grid_id_source = find_existing_column(
    grid_final,
    [
        "grid_id",
        "gridid",
        "grid",
        "GRID_ID",
        "Grid_ID",
        "unit_id",
        "unitid"
    ]
)


# Kalau belum ketemu, cari nama kolom yang mengandung "grid"
if grid_id_source is None:

    possible_grid_cols = [
        c
        for c in grid_final.columns
        if "grid" in str(c).lower()
    ]


    print()
    print(
        "Possible grid-related columns:",
        possible_grid_cols
    )


    # Cari kolom grid yang nilainya mirip G0001, G0231, dst.
    for c in possible_grid_cols:

        sample_values = (
            grid_final[c]
            .dropna()
            .astype(str)
            .head(30)
        )


        if sample_values.str.contains(
            r"^[Gg]0*\d+$",
            regex=True
        ).mean() > 0.5:

            grid_id_source = c
            break


if grid_id_source is None:

    raise RuntimeError(
        "\nTidak dapat menemukan kolom ID grid.\n"
        "Kolom tersedia:\n"
        +
        "\n".join(
            map(
                str,
                grid_final.columns
            )
        )
    )


print()
print(
    "Detected grid ID column:",
    grid_id_source
)


# Rename menjadi standar
if grid_id_source != "grid_id":

    grid_final = grid_final.rename(
        columns={
            grid_id_source:
                "grid_id"
        }
    )


# ---------------------------------------------------------------------
# NORMALIZE GRID ID
# G00231 -> G0231
# G231   -> G0231
# ---------------------------------------------------------------------

grid_final[
    "grid_id"
] = grid_final[
    "grid_id"
].apply(
    normalize_grid_id
)


# ---------------------------------------------------------------------
# STANDARDIZE AECS + COMPONENT COLUMNS
# ---------------------------------------------------------------------

COLUMN_ALIASES_FINAL = {

    "ALI": [
        "ALI",
        "agricultural_landscape_index"
    ],

    "TAI": [
        "TAI",
        "tourism_attraction_index"
    ],

    "ASI": [
        "ASI",
        "amenity_support_index"
    ],

    "RNAI": [
        "RNAI",
        "road_network_accessibility_index"
    ],

    "EQI": [
        "EQI",
        "environmental_quality_index"
    ],

    "AECS": [
        "AECS",
        "aecs",
        "AECS_hybrid",
        "hybrid_aecs",
        "aecs_final"
    ]
}


rename_map = {}


for target, candidates in COLUMN_ALIASES_FINAL.items():

    source = find_existing_column(
        grid_final,
        candidates
    )


    if source is None:

        raise RuntimeError(
            f"Kolom {target} tidak ditemukan.\n"
            f"Candidates = {candidates}"
        )


    if source != target:

        rename_map[
            source
        ] = target


if rename_map:

    grid_final = grid_final.rename(
        columns=
            rename_map
    )


# ---------------------------------------------------------------------
# NUMERIC CONVERSION
# ---------------------------------------------------------------------

for c in [
    "ALI",
    "TAI",
    "ASI",
    "RNAI",
    "EQI",
    "AECS"
]:

    grid_final[c] = pd.to_numeric(
        grid_final[c],
        errors="coerce"
    )


# ---------------------------------------------------------------------
# DUPLICATE ID CHECK
# ---------------------------------------------------------------------

n_unique_grid = (
    grid_final[
        "grid_id"
    ].nunique()
)


print()
print(
    "Unique grid IDs:",
    n_unique_grid
)


if n_unique_grid != 1358:

    raise RuntimeError(
        f"Expected 1358 unique grids, obtained {n_unique_grid}."
    )


# ---------------------------------------------------------------------
# REQUIRED COLUMN CHECK
# ---------------------------------------------------------------------

required_columns = [
    "grid_id",
    "ALI",
    "TAI",
    "ASI",
    "RNAI",
    "EQI",
    "AECS",
    "geometry"
]


missing = [
    c
    for c in required_columns
    if c not in grid_final.columns
]


if missing:

    raise RuntimeError(
        f"Required columns missing: {missing}"
    )


print()
print("✓ Grid schema successfully standardized.")

print()
print(
    "Final standardized columns:"
)

print(
    [
        c
        for c in required_columns
        if c in grid_final.columns
    ]
)


# ---------------------------------------------------------------------
# QUICK FINGERPRINT
# ---------------------------------------------------------------------

print()
print("=" * 100)
print("QUICK VERIFIED-GRID FINGERPRINT")
print("=" * 100)


print(
    "N      :",
    len(grid_final)
)

print(
    "Mean   :",
    round(
        grid_final["AECS"].mean(),
        6
    )
)

print(
    "Std    :",
    round(
        grid_final["AECS"].std(),
        6
    )
)

print(
    "Min    :",
    round(
        grid_final["AECS"].min(),
        6
    )
)

print(
    "Median :",
    round(
        grid_final["AECS"].median(),
        6
    )
)

print(
    "Max    :",
    round(
        grid_final["AECS"].max(),
        6
    )
)


# =====================================================================
# 04. HARD CHECK VERIFIED GRID
# =====================================================================

assert (
    len(grid) == 1358
), "Grid bukan verified 1,358-grid Hybrid."

assert (
    abs(
        grid["AECS"].mean()
        -
        0.203551
    )
    < 0.003
), "Mean AECS tidak cocok."


assert (
    abs(
        grid["AECS"].max()
        -
        0.522073
    )
    < 0.003
), "Max AECS tidak cocok."


print()
print(
    "✓ Verified Hybrid AECS grid loaded."
)

print(
    "N:",
    len(grid)
)

print(
    "Mean:",
    round(
        grid["AECS"].mean(),
        6
    )
)

print(
    "Range:",
    round(
        grid["AECS"].min(),
        6
    ),
    "–",
    round(
        grid["AECS"].max(),
        6
    )
)


# =====================================================================
# 05. ENSURE PREVIOUS ANALYSIS AVAILABLE
# =====================================================================

if (
    "analysis" not in globals()
    or
    not isinstance(
        analysis,
        pd.DataFrame
    )
):

    prev_excel = (
        PREVIOUS_DIR
        / "FINAL_HYBRID_AECS_VISITOR_DEMAND_RESULTS.xlsx"
    )

    if not prev_excel.exists():

        raise FileNotFoundError(
            "Previous final visitor-demand analysis tidak ditemukan."
        )

    analysis = pd.read_excel(
        prev_excel,
        sheet_name="destination_demand"
    )


# =====================================================================
# 06. ENSURE DESTINATION GRID AVAILABLE
# =====================================================================

if (
    "destination_grid" not in globals()
    or
    not isinstance(
        destination_grid,
        gpd.GeoDataFrame
    )
):

    prev_geojson = (
        PREVIOUS_DIR
        / "FINAL_Supply_Demand_Destinations.geojson"
    )

    if not prev_geojson.exists():

        raise FileNotFoundError(
            "Destination spatial output tidak ditemukan."
        )

    destination_grid = (
        gpd.read_file(
            prev_geojson
        )
    )


if destination_grid.crs is None:

    destination_grid = (
        destination_grid
        .set_crs(
            GEOG_CRS
        )
    )


destination_grid = (
    destination_grid
    .to_crs(
        GEOG_CRS
    )
)


destination_grid[
    "grid_id"
] = destination_grid[
    "grid_id"
].apply(
    normalize_grid_id
)


# =====================================================================
# 07. REBUILD SPATIAL ASSIGNMENT METHOD
# =====================================================================

if (
    "distance_to_grid_m"
    not in destination_grid.columns
):

    destination_grid[
        "distance_to_grid_m"
    ] = 0.0


destination_grid[
    "distance_to_grid_m"
] = pd.to_numeric(
    destination_grid[
        "distance_to_grid_m"
    ],
    errors="coerce"
)


destination_grid[
    "spatial_assignment_method"
] = np.where(
    destination_grid[
        "distance_to_grid_m"
    ].fillna(0)
    >
    0.01,

    "nearest_grid",

    "point_within_grid"
)


# =====================================================================
# =====================================================================
# PART A — DIANA WATER PARK SPATIAL AUDIT
# =====================================================================
# =====================================================================


# =====================================================================
# 08. DIANA CURRENT POINT
# =====================================================================

diana_rows = destination_grid[
    destination_grid[
        "destination"
    ]
    ==
    "Diana Water Park"
].copy()


if len(
    diana_rows
) == 0:

    raise RuntimeError(
        "Diana Water Park tidak ditemukan."
    )


diana = (
    diana_rows
    .iloc[0]
)


DIANA_CURRENT_GRID = (
    diana[
        "grid_id"
    ]
)

DIANA_CURRENT_AECS = float(
    diana[
        "AECS"
    ]
)


# Legacy manuscript assignment
LEGACY_GRID = "G0441"
LEGACY_AECS_REPORTED = 0.278


print()
print("=" * 95)
print("PART A — DIANA WATER PARK SPATIAL ASSIGNMENT AUDIT")
print("=" * 95)

print(
    "Current coordinate assignment :",
    DIANA_CURRENT_GRID
)

print(
    "Current AECS                  :",
    round(
        DIANA_CURRENT_AECS,
        6
    )
)

print(
    "Legacy manuscript assignment  :",
    LEGACY_GRID
)

print(
    "Legacy manuscript AECS        :",
    LEGACY_AECS_REPORTED
)


# =====================================================================
# 09. GET CURRENT AND LEGACY GRID POLYGONS
# =====================================================================

current_grid_row = grid[
    grid[
        "grid_id"
    ]
    ==
    DIANA_CURRENT_GRID
].copy()


legacy_grid_row = grid[
    grid[
        "grid_id"
    ]
    ==
    LEGACY_GRID
].copy()


if len(
    current_grid_row
) == 0:

    raise RuntimeError(
        f"{DIANA_CURRENT_GRID} tidak ditemukan di final grid."
    )


if len(
    legacy_grid_row
) == 0:

    print(
        f"⚠ Legacy grid {LEGACY_GRID} tidak ditemukan."
    )


# =====================================================================
# 10. METRIC DISTANCE AUDIT
# =====================================================================

grid_metric = (
    grid
    .to_crs(
        METRIC_CRS
    )
)


diana_metric = (
    diana_rows
    .to_crs(
        METRIC_CRS
    )
)


diana_point = (
    diana_metric
    .geometry
    .iloc[0]
)


audit_records = []


for label, gid in [

    (
        "Current coordinate assignment",
        DIANA_CURRENT_GRID
    ),

    (
        "Legacy manuscript assignment",
        LEGACY_GRID
    )
]:

    g = grid_metric[
        grid_metric[
            "grid_id"
        ] == gid
    ]


    if len(g) == 0:

        audit_records.append(
            {
                "assignment":
                    label,

                "grid_id":
                    gid,

                "AECS":
                    np.nan,

                "point_inside_polygon":
                    False,

                "distance_point_to_polygon_m":
                    np.nan,

                "distance_point_to_centroid_m":
                    np.nan
            }
        )

        continue


    polygon = (
        g.geometry
        .iloc[0]
    )


    centroid = (
        polygon
        .centroid
    )


    point_inside = (
        polygon.contains(
            diana_point
        )
        or
        polygon.touches(
            diana_point
        )
    )


    dist_polygon = (
        diana_point.distance(
            polygon
        )
    )


    dist_centroid = (
        diana_point.distance(
            centroid
        )
    )


    audit_records.append(
        {
            "assignment":
                label,

            "grid_id":
                gid,

            "AECS":
                float(
                    g[
                        "AECS"
                    ].iloc[0]
                ),

            "point_inside_polygon":
                bool(
                    point_inside
                ),

            "distance_point_to_polygon_m":
                float(
                    dist_polygon
                ),

            "distance_point_to_centroid_m":
                float(
                    dist_centroid
                )
        }
    )


DIANA_AUDIT = pd.DataFrame(
    audit_records
)


print()
print("DIRECT GRID COMPARISON")

display(
    DIANA_AUDIT
)


# =====================================================================
# 11. ARE G0441 AND CURRENT GRID ADJACENT?
# =====================================================================

adjacent = np.nan


if (
    len(current_grid_row) > 0
    and
    len(legacy_grid_row) > 0
):

    current_geom = (
        current_grid_row
        .geometry
        .iloc[0]
    )

    legacy_geom = (
        legacy_grid_row
        .geometry
        .iloc[0]
    )


    adjacent = (
        current_geom.touches(
            legacy_geom
        )
        or
        current_geom.intersects(
            legacy_geom
        )
    )


print()
print(
    f"{DIANA_CURRENT_GRID} adjacent/intersects {LEGACY_GRID}:",
    adjacent
)


# =====================================================================
# 12. LOCAL NEIGHBORHOOD AROUND DIANA
# =====================================================================

BUFFER_M = 2500


nearby = (
    grid_metric[
        grid_metric
        .geometry
        .intersects(
            diana_point.buffer(
                BUFFER_M
            )
        )
    ]
    .copy()
)


nearby[
    "distance_to_centroid_m"
] = nearby.geometry.centroid.distance(
    diana_point
)


nearby[
    "distance_to_polygon_m"
] = nearby.geometry.distance(
    diana_point
)


nearby_table = (
    nearby[
        [
            "grid_id",
            "AECS",
            "distance_to_polygon_m",
            "distance_to_centroid_m"
        ]
    ]
    .sort_values(
        [
            "distance_to_polygon_m",
            "distance_to_centroid_m"
        ]
    )
    .reset_index(
        drop=True
    )
)


print()
print(
    "GRIDS WITHIN 2.5 km OF DIANA WATER PARK:"
)

display(
    nearby_table
    .head(20)
)


# =====================================================================
# 13. AUTOMATIC DIANA AUDIT STATUS
# =====================================================================

current_inside = bool(
    DIANA_AUDIT.loc[
        DIANA_AUDIT[
            "grid_id"
        ]
        ==
        DIANA_CURRENT_GRID,
        "point_inside_polygon"
    ].iloc[0]
)


legacy_inside = False


legacy_hit = DIANA_AUDIT[
    DIANA_AUDIT[
        "grid_id"
    ]
    ==
    LEGACY_GRID
]


if len(
    legacy_hit
) > 0:

    legacy_inside = bool(
        legacy_hit[
            "point_inside_polygon"
        ].iloc[0]
    )


if (
    current_inside
    and
    not legacy_inside
):

    DIANA_AUDIT_STATUS = (
        "REVIEW_MANUSCRIPT_LEGACY_ASSIGNMENT"
    )

elif legacy_inside:

    DIANA_AUDIT_STATUS = (
        "LEGACY_ASSIGNMENT_SPATIALLY_SUPPORTED"
    )

else:

    DIANA_AUDIT_STATUS = (
        "MANUAL_REVIEW_REQUIRED"
    )


print()
print("=" * 95)
print("DIANA AUDIT STATUS")
print("=" * 95)

print(
    DIANA_AUDIT_STATUS
)


if (
    DIANA_AUDIT_STATUS
    ==
    "REVIEW_MANUSCRIPT_LEGACY_ASSIGNMENT"
):

    print()
    print(
        "Current supplied coordinate lies in",
        DIANA_CURRENT_GRID,
        "rather than legacy",
        LEGACY_GRID
    )

    print(
        "Do NOT force the point into the legacy grid."
    )

    print(
        "The coordinate source or the legacy manuscript assignment "
        "must be reconciled before manuscript freeze."
    )


# =====================================================================
# =====================================================================
# PART B — PERCENTILE-RANK SUPPLY–DEMAND MISMATCH
# =====================================================================
# =====================================================================


# =====================================================================
# 14. BUILD FINAL MISMATCH SAMPLE
# =====================================================================

# Use destinations with >= 2 observed years.
mismatch_final = (
    analysis[
        analysis[
            "observed_years"
        ]
        >=
        2
    ]
    .copy()
)


# Add coordinate metadata if missing
metadata_cols = [
    c
    for c in [
        "destination",
        "coordinate_status",
        "spatial_assignment_method",
        "distance_to_grid_m"
    ]
    if c in destination_grid.columns
]


metadata = (
    destination_grid[
        metadata_cols
    ]
    .drop_duplicates(
        "destination"
    )
)


for c in [
    "coordinate_status",
    "spatial_assignment_method",
    "distance_to_grid_m"
]:

    if c in mismatch_final.columns:

        mismatch_final = (
            mismatch_final
            .drop(
                columns=[
                    c
                ]
            )
        )


mismatch_final = (
    mismatch_final
    .merge(
        metadata,
        on=
            "destination",
        how=
            "left"
    )
)


# =====================================================================
# 15. SUPPLY PERCENTILE
#
# Supply percentile relative to ALL 1,358 AECS grids.
# =====================================================================

full_grid_aecs = (
    grid[
        "AECS"
    ]
    .dropna()
    .to_numpy(
        dtype=float
    )
)


mismatch_final[
    "supply_percentile"
] = mismatch_final[
    "AECS"
].apply(
    lambda x:
        midrank_percentile_against_reference(
            x,
            full_grid_aecs
        )
)


# =====================================================================
# 16. DEMAND PERCENTILE
#
# Demand percentile relative to the observed destination sample.
# =====================================================================

mismatch_final[
    "demand_percentile"
] = (
    sample_midrank_percentile(
        mismatch_final[
            "mean_annual_visitors"
        ]
    )
)


# =====================================================================
# 17. FINAL PERCENTILE MISMATCH
#
# Positive:
# demand ranking > readiness ranking
#
# Negative:
# readiness ranking > demand ranking
#
# ~0:
# relative readiness and demand approximately aligned
# =====================================================================

mismatch_final[
    "percentile_mismatch"
] = (
    mismatch_final[
        "demand_percentile"
    ]
    -
    mismatch_final[
        "supply_percentile"
    ]
)


# Absolute mismatch for magnitude
mismatch_final[
    "absolute_percentile_mismatch"
] = (
    mismatch_final[
        "percentile_mismatch"
    ].abs()
)


# =====================================================================
# 18. HIGH/LOW THRESHOLDS
#
# Both dimensions now use exactly the same conceptual threshold:
# upper third of their own reference distribution.
# =====================================================================

HIGH_PERCENTILE = 2 / 3


mismatch_final[
    "supply_high"
] = (
    mismatch_final[
        "supply_percentile"
    ]
    >=
    HIGH_PERCENTILE
)


mismatch_final[
    "demand_high"
] = (
    mismatch_final[
        "demand_percentile"
    ]
    >=
    HIGH_PERCENTILE
)


# =====================================================================
# 19. FOUR-QUADRANT FINAL TYPOLOGY
# =====================================================================

def final_typology(row):

    S = row[
        "supply_high"
    ]

    D = row[
        "demand_high"
    ]


    if S and D:

        return (
            "High readiness–high demand"
        )


    if S and not D:

        return (
            "High readiness–lower demand"
        )


    if not S and D:

        return (
            "Lower readiness–high demand"
        )


    return (
        "Lower readiness–lower demand"
    )


mismatch_final[
    "supply_demand_class"
] = mismatch_final.apply(
    final_typology,
    axis=1
)


# =====================================================================
# 20. MISMATCH INTERPRETATION
# =====================================================================

def mismatch_interpretation(x):

    if pd.isna(x):

        return np.nan


    if x >= 0.25:

        return (
            "Demand substantially exceeds relative readiness"
        )


    if x >= 0.10:

        return (
            "Demand moderately exceeds relative readiness"
        )


    if x <= -0.25:

        return (
            "Readiness substantially exceeds realized demand"
        )


    if x <= -0.10:

        return (
            "Readiness moderately exceeds realized demand"
        )


    return (
        "Broadly aligned readiness and demand"
    )


mismatch_final[
    "mismatch_interpretation"
] = mismatch_final[
    "percentile_mismatch"
].apply(
    mismatch_interpretation
)


# =====================================================================
# 21. FLAG SPATIAL CONFIDENCE
# =====================================================================

mismatch_final[
    "spatial_confidence"
] = np.where(

    mismatch_final[
        "coordinate_status"
    ]
    ==
    "manual_approximate",

    "Lower – approximate coordinate",

    np.where(

        mismatch_final[
            "spatial_assignment_method"
        ]
        ==
        "nearest_grid",

        "Moderate – nearest-grid assignment",

        "Higher – point within grid"
    )
)


# =====================================================================
# 22. FINAL TABLE SORTED BY MISMATCH
# =====================================================================

TABLE_MISMATCH_FINAL = (
    mismatch_final[
        [
            c
            for c in [
                "destination",
                "grid_id",
                "district",

                "AECS",
                "priority_final",

                "observed_years",
                "mean_annual_visitors",

                "supply_percentile",
                "demand_percentile",

                "percentile_mismatch",
                "absolute_percentile_mismatch",

                "supply_demand_class",
                "mismatch_interpretation",

                "coordinate_status",
                "spatial_assignment_method",
                "distance_to_grid_m",
                "spatial_confidence"
            ]
            if c in mismatch_final.columns
        ]
    ]
    .sort_values(
        "percentile_mismatch",
        ascending=False
    )
    .reset_index(
        drop=True
    )
)


print()
print("=" * 95)
print("FINAL PERCENTILE-RANK SUPPLY–DEMAND MISMATCH")
print("=" * 95)

display(
    TABLE_MISMATCH_FINAL
)


# =====================================================================
# 23. FINAL CLASS SUMMARY
# =====================================================================

MISMATCH_SUMMARY_FINAL = (
    mismatch_final
    .groupby(
        "supply_demand_class",
        as_index=False
    )
    .agg(

        n_destinations=(
            "destination",
            "count"
        ),

        mean_AECS=(
            "AECS",
            "mean"
        ),

        mean_annual_visitors=(
            "mean_annual_visitors",
            "mean"
        ),

        mean_supply_percentile=(
            "supply_percentile",
            "mean"
        ),

        mean_demand_percentile=(
            "demand_percentile",
            "mean"
        ),

        mean_percentile_mismatch=(
            "percentile_mismatch",
            "mean"
        )
    )
)


print()
print("=" * 95)
print("FINAL SUPPLY–DEMAND CLASS SUMMARY")
print("=" * 95)

display(
    MISMATCH_SUMMARY_FINAL
)


# =====================================================================
# 24. MOST IMPORTANT MISMATCHES
# =====================================================================

print()
print("=" * 95)
print("TOP POSITIVE MISMATCH")
print("DEMAND > RELATIVE READINESS")
print("=" * 95)


display(
    TABLE_MISMATCH_FINAL[
        [
            "destination",
            "AECS",
            "mean_annual_visitors",
            "supply_percentile",
            "demand_percentile",
            "percentile_mismatch",
            "supply_demand_class"
        ]
    ]
    .head(5)
)


print()
print("=" * 95)
print("TOP NEGATIVE MISMATCH")
print("READINESS > REALIZED DEMAND")
print("=" * 95)


display(
    TABLE_MISMATCH_FINAL[
        [
            "destination",
            "AECS",
            "mean_annual_visitors",
            "supply_percentile",
            "demand_percentile",
            "percentile_mismatch",
            "supply_demand_class"
        ]
    ]
    .tail(5)
    .sort_values(
        "percentile_mismatch"
    )
)


# =====================================================================
# 25. FIGURE 02 FINAL
# PERCENTILE × PERCENTILE MATRIX
# =====================================================================

plt.figure(
    figsize=(
        8.6,
        7.0
    )
)


plt.scatter(
    mismatch_final[
        "supply_percentile"
    ],

    mismatch_final[
        "demand_percentile"
    ],

    s=105,
    alpha=0.85,
    edgecolor="black",
    linewidth=0.6
)


# Same 2/3 threshold on both axes
plt.axvline(
    HIGH_PERCENTILE,
    linestyle="--",
    linewidth=1
)

plt.axhline(
    HIGH_PERCENTILE,
    linestyle="--",
    linewidth=1
)


# 1:1 alignment line
plt.plot(
    [0, 1],
    [0, 1],
    linestyle=":",
    linewidth=1
)


for _, row in mismatch_final.iterrows():

    suffix = (
        "*"
        if row.get(
            "coordinate_status",
            ""
        )
        ==
        "manual_approximate"
        else
        ""
    )


    plt.annotate(

        str(
            row[
                "destination"
            ]
        )
        +
        suffix,

        (
            row[
                "supply_percentile"
            ],

            row[
                "demand_percentile"
            ]
        ),

        xytext=(
            4,
            4
        ),

        textcoords=
            "offset points",

        fontsize=7
    )


plt.xlim(
    0,
    1
)

plt.ylim(
    0,
    1
)


plt.xlabel(
    "AECS percentile among all 1,358 spatial grids"
)

plt.ylabel(
    "Observed visitor-demand percentile among destinations"
)

plt.title(
    "Relative Spatial Readiness–Demand Mismatch"
)


plt.grid(
    alpha=0.20
)


save_final_fig(
    "Fig_02_FINAL_Percentile_Supply_Demand_Matrix.png"
)


# =====================================================================
# 26. FIGURE 03 FINAL
# SPATIAL SUPPLY–DEMAND TYPOLOGY
# =====================================================================

point_geometry = (
    destination_grid[
        [
            "destination",
            "geometry"
        ]
    ]
    .drop_duplicates(
        "destination"
    )
)


map_final = (
    point_geometry
    .merge(
        mismatch_final[
            [
                "destination",
                "mean_annual_visitors",
                "supply_demand_class",
                "coordinate_status"
            ]
        ],

        on=
            "destination",

        how=
            "inner"
    )
)


map_final = gpd.GeoDataFrame(
    map_final,
    geometry="geometry",
    crs=GEOG_CRS
)


fig, ax = plt.subplots(
    figsize=(
        8,
        11
    )
)


# Background: continuous verified AECS
grid.plot(
    column=
        "AECS",

    ax=
        ax,

    legend=
        True,

    linewidth=
        0.10,

    edgecolor=
        "lightgrey",

    legend_kwds={
        "label":
            "Agrotourism Experience Corridor Score (AECS)"
    }
)


MARKERS = {

    "High readiness–high demand":
        "o",

    "High readiness–lower demand":
        "^",

    "Lower readiness–high demand":
        "s",

    "Lower readiness–lower demand":
        "D"
}


for class_name, marker in MARKERS.items():

    temp = map_final[
        map_final[
            "supply_demand_class"
        ]
        ==
        class_name
    ]


    if len(
        temp
    ) == 0:

        continue


    sizes = (
        np.sqrt(
            temp[
                "mean_annual_visitors"
            ]
            + 1
        )
        * 5
    )


    temp.plot(
        ax=ax,

        marker=
            marker,

        markersize=
            sizes,

        edgecolor=
            "black",

        linewidth=
            0.65,

        alpha=
            0.85,

        label=
            class_name
    )


for _, row in map_final.iterrows():

    suffix = (
        "*"
        if row[
            "coordinate_status"
        ]
        ==
        "manual_approximate"
        else
        ""
    )


    ax.annotate(

        row[
            "destination"
        ]
        +
        suffix,

        (
            row.geometry.x,
            row.geometry.y
        ),

        xytext=(
            3,
            3
        ),

        textcoords=
            "offset points",

        fontsize=6
    )


ax.set_title(
    "Spatial Readiness–Demand Mismatch in Barru"
)

ax.set_axis_off()


ax.legend(
    loc=
        "lower left",

    fontsize=
        7
)


save_final_fig(
    "Fig_03_FINAL_Spatial_Supply_Demand_Map.png"
)


# =====================================================================
# 27. DIANA LOCAL AUDIT MAP
# Supplementary diagnostic only
# =====================================================================

nearby_geo = (
    nearby
    .to_crs(
        GEOG_CRS
    )
)


diana_geo = (
    diana_metric
    .to_crs(
        GEOG_CRS
    )
)


fig, ax = plt.subplots(
    figsize=(
        7,
        7
    )
)


nearby_geo.plot(
    column=
        "AECS",

    ax=
        ax,

    legend=
        True,

    edgecolor=
        "black",

    linewidth=
        0.5
)


diana_geo.plot(
    ax=
        ax,

    marker=
        "*",

    markersize=
        180,

    edgecolor=
        "black"
)


for _, r in nearby_geo.iterrows():

    centroid = (
        r.geometry
        .centroid
    )

    ax.annotate(
        r[
            "grid_id"
        ],

        (
            centroid.x,
            centroid.y
        ),

        ha="center",
        va="center",
        fontsize=6
    )


ax.set_title(
    "Diana Water Park: Local Grid Assignment Audit"
)

ax.set_axis_off()


save_final_fig(
    "Fig_S2_Diana_Water_Park_Grid_Assignment_Audit.png"
)


# =====================================================================
# 28. EXPORT DIANA AUDIT
# =====================================================================

DIANA_AUDIT[
    "audit_status"
] = DIANA_AUDIT_STATUS


DIANA_AUDIT[
    "current_coordinate_lat"
] = float(
    destination_grid.loc[
        destination_grid[
            "destination"
        ]
        ==
        "Diana Water Park",
        "lat"
    ].iloc[0]
) if "lat" in destination_grid.columns else np.nan


DIANA_AUDIT[
    "current_coordinate_lon"
] = float(
    destination_grid.loc[
        destination_grid[
            "destination"
        ]
        ==
        "Diana Water Park",
        "lon"
    ].iloc[0]
) if "lon" in destination_grid.columns else np.nan


DIANA_AUDIT.to_csv(
    TABLE_DIR_V2
    / "Table_Diana_Spatial_Assignment_Audit.csv",
    index=False
)


nearby_table.to_csv(
    TABLE_DIR_V2
    / "Table_Diana_Nearby_Grid_Audit.csv",
    index=False
)


# =====================================================================
# 29. EXPORT FINAL MISMATCH TABLES
# =====================================================================

TABLE_MISMATCH_FINAL.to_csv(
    TABLE_DIR_V2
    / "Table_FINAL_Percentile_Supply_Demand_Mismatch.csv",
    index=False
)


MISMATCH_SUMMARY_FINAL.to_csv(
    TABLE_DIR_V2
    / "Table_FINAL_Percentile_Mismatch_Summary.csv",
    index=False
)


# =====================================================================
# 30. PRIMARY NON-MANUAL SENSITIVITY TABLE
#
# Useful for Supplementary robustness:
# removes the two manual approximate coordinates.
# =====================================================================

MISMATCH_NONMANUAL = (
    mismatch_final[
        mismatch_final[
            "coordinate_status"
        ]
        !=
        "manual_approximate"
    ]
    .copy()
)


MISMATCH_NONMANUAL.to_csv(
    TABLE_DIR_V2
    / "Table_Sensitivity_Nonmanual_Coordinates.csv",
    index=False
)


# =====================================================================
# 31. EXPORT FINAL EXCEL
# =====================================================================

FINAL_EXCEL = (
    FINAL_DIR_V2
    / "FINAL_PERCENTILE_SUPPLY_DEMAND_RESULTS.xlsx"
)


with pd.ExcelWriter(
    FINAL_EXCEL,
    engine="openpyxl"
) as writer:

    DIANA_AUDIT.to_excel(
        writer,
        sheet_name=
            "Diana_audit",
        index=False
    )


    nearby_table.to_excel(
        writer,
        sheet_name=
            "Diana_nearby_grids",
        index=False
    )


    TABLE_MISMATCH_FINAL.to_excel(
        writer,
        sheet_name=
            "percentile_mismatch",
        index=False
    )


    MISMATCH_SUMMARY_FINAL.to_excel(
        writer,
        sheet_name=
            "mismatch_summary",
        index=False
    )


    MISMATCH_NONMANUAL.to_excel(
        writer,
        sheet_name=
            "nonmanual_sensitivity",
        index=False
    )


# =====================================================================
# 32. EXPORT FINAL SPATIAL GEOJSON
# =====================================================================

spatial_final = (
    destination_grid[
        [
            c
            for c in destination_grid.columns
            if c
            not in [
                "supply_index",
                "demand_index",
                "mismatch_score",
                "supply_demand_class"
            ]
        ]
    ]
    .merge(
        mismatch_final[
            [
                "destination",
                "supply_percentile",
                "demand_percentile",
                "percentile_mismatch",
                "absolute_percentile_mismatch",
                "supply_demand_class",
                "mismatch_interpretation",
                "spatial_confidence"
            ]
        ],

        on=
            "destination",

        how=
            "inner"
    )
)


SPATIAL_FINAL_OUT = (
    FINAL_DIR_V2
    / "FINAL_PERCENTILE_Supply_Demand_Destinations.geojson"
)


spatial_final.to_file(
    SPATIAL_FINAL_OUT,
    driver=
        "GeoJSON"
)


# =====================================================================
# 33. FINAL DECISION OUTPUT
# =====================================================================

print()
print("=" * 95)
print("FINAL CORRECTION COMPLETE")
print("=" * 95)


print()
print(
    "Diana audit status:"
)

print(
    DIANA_AUDIT_STATUS
)


print()
print(
    "Percentile mismatch range:"
)

print(
    round(
        mismatch_final[
            "percentile_mismatch"
        ].min(),
        4
    ),
    "to",
    round(
        mismatch_final[
            "percentile_mismatch"
        ].max(),
        4
    )
)


print()
print(
    "Final Excel:"
)

print(
    FINAL_EXCEL
)


print()
print(
    "Final Figures:"
)

print(
    FIG_DIR_V2
)


print()
print(
    "Final Tables:"
)

print(
    TABLE_DIR_V2
)


print()
print(
    "Final GeoJSON:"
)

print(
    SPATIAL_FINAL_OUT
)


# =====================================================================
# 34. OUTPUTS TO SEND BACK
# =====================================================================

print()
print("=" * 95)
print("KIRIMKAN 4 OUTPUT BERIKUT KE CHATGPT")
print("=" * 95)


print()
print("1. DIANA WATER PARK AUDIT")

display(
    DIANA_AUDIT
)


print()
print("2. FINAL PERCENTILE MISMATCH")

display(
    TABLE_MISMATCH_FINAL
)


print()
print("3. FINAL MISMATCH SUMMARY")

display(
    MISMATCH_SUMMARY_FINAL
)


print()
print("4. NON-MANUAL COORDINATE SENSITIVITY")

display(
    MISMATCH_NONMANUAL[
        [
            c
            for c in [
                "destination",
                "AECS",
                "mean_annual_visitors",
                "supply_percentile",
                "demand_percentile",
                "percentile_mismatch",
                "supply_demand_class"
            ]
            if c in MISMATCH_NONMANUAL.columns
        ]
    ]
)