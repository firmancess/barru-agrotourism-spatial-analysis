"""
Link observed visitor demand to the verified Hybrid AECS grid and run the primary association analysis.

Clean public version derived from the final manuscript-relevant notebook cell 69.
Personal Google Drive paths and notebook-only execution assumptions were removed.
Analytical logic is retained where it is verifiable from the uploaded notebook.
"""

# =====================================================================
# 07. LOAD VISITOR ANNUAL DATA
# =====================================================================

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from scipy.stats import spearmanr
from IPython.display import display


# ---------------------------------------------------------------------
# Pastikan path tersedia
# ---------------------------------------------------------------------

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

VISITOR_DIR = REPO_ROOT / "outputs" / "01_visitor_demand"

FINAL_DIR = (
    REPO_ROOT
    / "outputs"
    / "04_primary_demand_spatial_linkage"
)

FIG_DIR = (
    FINAL_DIR
    / "figures_600dpi"
)

TABLE_DIR = (
    FINAL_DIR
    / "tables"
)

for p in [
    FINAL_DIR,
    FIG_DIR,
    TABLE_DIR
]:
    p.mkdir(
        parents=True,
        exist_ok=True
    )


GEOG_CRS = "EPSG:4326"
METRIC_CRS = "EPSG:32750"


# ---------------------------------------------------------------------
# Load the frozen final Hybrid AECS grid when the script is run directly.
# ---------------------------------------------------------------------

if "grid" not in globals():
    if not GRID_FILE.exists():
        raise FileNotFoundError(
            f"Processed Hybrid AECS grid not found: {GRID_FILE}"
        )

    grid = gpd.read_file(GRID_FILE)

    # Standardize the final AECS field when a known alias is used.
    lower_lookup = {str(c).strip().lower(): c for c in grid.columns}
    if "aecs" not in grid.columns:
        for alias in ["aecs_hybrid", "hybrid_aecs"]:
            if alias in lower_lookup:
                grid = grid.rename(columns={lower_lookup[alias]: "AECS"})
                break

    if "AECS" not in grid.columns:
        raise KeyError("Final AECS column was not found in the processed grid.")

    grid["AECS"] = pd.to_numeric(grid["AECS"], errors="coerce")

    if "priority_final" not in grid.columns:
        q33 = grid["AECS"].quantile(0.33)
        q66 = grid["AECS"].quantile(0.66)
        grid["priority_final"] = np.select(
            [
                grid["AECS"] <= q33,
                (grid["AECS"] > q33) & (grid["AECS"] <= q66),
                grid["AECS"] > q66,
            ],
            ["Low priority", "Moderate priority", "High priority"],
            default="Moderate priority",
        ).astype(object)


# ---------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------

def minmax(series):

    x = pd.to_numeric(
        series,
        errors="coerce"
    )

    mn = x.min()
    mx = x.max()

    if pd.isna(mn) or pd.isna(mx):

        return pd.Series(
            np.nan,
            index=series.index
        )

    if mx == mn:

        return pd.Series(
            0.5,
            index=series.index
        )

    return (
        (x - mn)
        /
        (mx - mn)
    )


def save_fig(filename):

    path = (
        FIG_DIR
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


# ---------------------------------------------------------------------
# Gunakan visitor_annual jika masih ada di memory
# ---------------------------------------------------------------------

if (
    "visitor_annual" in globals()
    and
    isinstance(
        visitor_annual,
        pd.DataFrame
    )
):

    annual = (
        visitor_annual
        .copy()
    )

    print(
        "✓ Visitor annual menggunakan data dari memory."
    )

else:

    VISITOR_FILE = (
        VISITOR_DIR
        / "tables"
        / "visitor_annual_demand_2023_2025.csv"
    )

    if not VISITOR_FILE.exists():

        raise FileNotFoundError(
            "File visitor annual tidak ditemukan:\n"
            f"{VISITOR_FILE}\n\n"
            "Jalankan terlebih dahulu analisis visitor 2023–2025."
        )

    annual = pd.read_csv(
        VISITOR_FILE
    )

    print()
    print(
        "✓ Visitor annual dibaca dari:"
    )
    print(
        VISITOR_FILE
    )


annual[
    "year"
] = pd.to_numeric(
    annual[
        "year"
    ],
    errors="coerce"
)


annual[
    "total_visitors"
] = pd.to_numeric(
    annual[
        "total_visitors"
    ],
    errors="coerce"
)


print()
print("=" * 90)
print("VISITOR ANNUAL DATA")
print("=" * 90)

print(
    "Jumlah observation:",
    len(annual)
)

print(
    "Jumlah destination:",
    annual[
        "destination"
    ].nunique()
)

print(
    "Tahun:",
    sorted(
        annual[
            "year"
        ]
        .dropna()
        .unique()
        .astype(int)
    )
)

display(
    annual
    .sort_values(
        [
            "year",
            "total_visitors"
        ],
        ascending=[
            True,
            False
        ]
    )
    .head(30)
)


# =====================================================================
# 08. DESTINATION SPATIAL ANCHORS
# =====================================================================

ANCHORS = [

    [
        "Diana Water Park",
        -4.285604,
        119.663559,
        "direct_official"
    ],

    [
        "Pulau Dutungan",
        -4.179593,
        119.622431,
        "direct_official"
    ],

    [
        "Bukit Maddo",
        -4.475959,
        119.636852,
        "direct_official"
    ],

    [
        "Pantai Laguna",
        -4.486444,
        119.593632,
        "official_anchor"
    ],

    [
        "Pantai Ujung Batu",
        -4.400676,
        119.604687,
        "representative_anchor"
    ],

    [
        "Bujung Mattimboe",
        -4.188856,
        119.675620,
        "official_anchor"
    ],

    [
        "Lappa Laona",
        -4.562533,
        119.761963,
        "official_anchor"
    ],

    [
        "Pantai Padongko",
        -4.380000,
        119.610000,
        "manual_approximate"
    ],

    [
        "Embung Paccekke",
        -4.352000,
        119.720000,
        "manual_approximate"
    ],

    [
        "Pulau Pannikiang",
        -4.354473,
        119.599903,
        "direct_official"
    ],

    [
        "PekkaE Ecolodge",
        -4.538678,
        119.680367,
        "official_anchor"
    ],

    [
        "Celebes Canyon",
        -4.500644,
        119.716606,
        "direct_official"
    ]
]


anchor_df = pd.DataFrame(
    ANCHORS,
    columns=[
        "destination",
        "lat",
        "lon",
        "coordinate_status"
    ]
)


anchors = gpd.GeoDataFrame(
    anchor_df.copy(),

    geometry=
        gpd.points_from_xy(
            anchor_df[
                "lon"
            ],
            anchor_df[
                "lat"
            ]
        ),

    crs=
        GEOG_CRS
)


print()
print("=" * 90)
print("SPATIAL ANCHORS")
print("=" * 90)

display(
    anchor_df
)


# =====================================================================
# 09. DESTINATION → VERIFIED HYBRID AECS GRID
# =====================================================================

grid_m = (
    grid
    .to_crs(
        METRIC_CRS
    )
    .copy()
)


anchors_m = (
    anchors
    .to_crs(
        METRIC_CRS
    )
    .copy()
)


# Cari district bila tersedia
district_candidates = [
    "district",
    "district_name",
    "kecamatan"
]

district_col = None

for c in district_candidates:

    if c in grid_m.columns:

        district_col = c
        break


if (
    district_col is not None
    and
    district_col != "district"
):

    grid_m = grid_m.rename(
        columns={
            district_col:
                "district"
        }
    )


cols_grid = [
    c
    for c in [
        "grid_id",
        "district",
        "ALI",
        "TAI",
        "ASI",
        "RNAI",
        "EQI",
        "AECS",
        "priority_final",
        "geometry"
    ]
    if c in grid_m.columns
]


joined = gpd.sjoin(
    anchors_m,

    grid_m[
        cols_grid
    ],

    how="left",

    predicate="within"
)


inside = (
    joined[
        joined[
            "grid_id"
        ].notna()
    ]
    .copy()
)


outside = (
    joined[
        joined[
            "grid_id"
        ].isna()
    ]
    .copy()
)


print()
print(
    "Anchor inside grid:",
    len(inside)
)

print(
    "Anchor outside grid:",
    len(outside)
)


# ---------------------------------------------------------------------
# Titik yang tidak jatuh tepat dalam grid → nearest grid
# ---------------------------------------------------------------------

if len(
    outside
) > 0:

    nearest = gpd.sjoin_nearest(
        anchors_m.loc[
            outside.index
        ],

        grid_m[
            cols_grid
        ],

        how="left",

        distance_col=
            "distance_to_grid_m"
    )


    destination_grid = pd.concat(
        [
            inside,
            nearest
        ],
        ignore_index=True
    )

else:

    destination_grid = (
        inside.copy()
    )

    destination_grid[
        "distance_to_grid_m"
    ] = 0.0


if (
    "distance_to_grid_m"
    not in destination_grid.columns
):

    destination_grid[
        "distance_to_grid_m"
    ] = 0.0


if (
    "index_right"
    in destination_grid.columns
):

    destination_grid = (
        destination_grid
        .drop(
            columns=[
                "index_right"
            ]
        )
    )


destination_grid = gpd.GeoDataFrame(
    destination_grid,

    geometry=
        "geometry",

    crs=
        METRIC_CRS
).to_crs(
    GEOG_CRS
)


print()
print("=" * 90)
print("DESTINATION → VERIFIED HYBRID AECS GRID")
print("=" * 90)


display(
    destination_grid[
        [
            c
            for c in [
                "destination",
                "coordinate_status",
                "grid_id",
                "district",
                "ALI",
                "TAI",
                "ASI",
                "RNAI",
                "EQI",
                "AECS",
                "priority_final",
                "distance_to_grid_m"
            ]
            if c in destination_grid.columns
        ]
    ]
)


# =====================================================================
# 10. MULTI-YEAR VISITOR DEMAND
# =====================================================================

anchor_names = set(
    anchor_df[
        "destination"
    ]
)


annual_anchor = annual[
    annual[
        "destination"
    ].isin(
        anchor_names
    )
].copy()


print()
print(
    "Destinasi anchor yang memiliki visitor data:",
    annual_anchor[
        "destination"
    ].nunique(),
    "/",
    len(anchor_names)
)


missing_visitors = (
    anchor_names
    -
    set(
        annual_anchor[
            "destination"
        ].unique()
    )
)


if missing_visitors:

    print()
    print(
        "Anchor tanpa visitor record:"
    )

    print(
        sorted(
            missing_visitors
        )
    )


# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------

demand_summary = (
    annual_anchor
    .groupby(
        "destination",
        as_index=False
    )
    .agg(

        observed_years=(
            "year",
            "nunique"
        ),

        total_visitors_3yr=(
            "total_visitors",
            "sum"
        ),

        mean_annual_visitors=(
            "total_visitors",
            "mean"
        ),

        median_annual_visitors=(
            "total_visitors",
            "median"
        )
    )
)


# ---------------------------------------------------------------------
# Visitor per year
# ---------------------------------------------------------------------

year_pivot = (
    annual_anchor
    .pivot_table(
        index=
            "destination",

        columns=
            "year",

        values=
            "total_visitors",

        aggfunc=
            "sum"
    )
    .reset_index()
)


new_cols = []

for c in year_pivot.columns:

    if isinstance(
        c,
        (
            int,
            float,
            np.integer,
            np.floating
        )
    ):

        new_cols.append(
            f"visitors_{int(c)}"
        )

    else:

        new_cols.append(
            c
        )


year_pivot.columns = (
    new_cols
)


demand_summary = (
    demand_summary
    .merge(
        year_pivot,

        on=
            "destination",

        how=
            "left"
    )
)


# =====================================================================
# 11. JOIN DEMAND + SPATIAL READINESS
# =====================================================================

spatial_attr = (
    destination_grid
    .drop(
        columns=[
            "geometry"
        ]
    )
    .drop_duplicates(
        subset=[
            "destination"
        ]
    )
)


analysis = (
    demand_summary
    .merge(
        spatial_attr,

        on=
            "destination",

        how=
            "left"
    )
)


analysis[
    "log_mean_demand"
] = np.log1p(
    analysis[
        "mean_annual_visitors"
    ]
)


analysis[
    "demand_index"
] = minmax(
    analysis[
        "log_mean_demand"
    ]
)


# Supply normalization menggunakan seluruh 1.358 grid
AECS_MIN = (
    grid[
        "AECS"
    ].min()
)

AECS_MAX = (
    grid[
        "AECS"
    ].max()
)


analysis[
    "supply_index"
] = (
    analysis[
        "AECS"
    ]
    -
    AECS_MIN
) / (
    AECS_MAX
    -
    AECS_MIN
)


print()
print("=" * 90)
print("MULTI-YEAR VISITOR DEMAND × VERIFIED HYBRID AECS")
print("=" * 90)


display(
    analysis
    .sort_values(
        "mean_annual_visitors",
        ascending=False
    )
)


# =====================================================================
# 12. BOOTSTRAP SPEARMAN
# =====================================================================

def bootstrap_spearman(
    df,
    x_col,
    y_col,
    n_boot=10000,
    seed=42
):

    d = (
        df[
            [
                x_col,
                y_col
            ]
        ]
        .dropna()
        .reset_index(
            drop=True
        )
    )


    n = len(
        d
    )


    if n < 5:

        return (
            np.nan,
            np.nan
        )


    rng = np.random.default_rng(
        seed
    )


    boot_rho = []


    for _ in range(
        n_boot
    ):

        idx = rng.integers(
            0,
            n,
            n
        )


        sample = d.iloc[
            idx
        ]


        if (
            sample[
                x_col
            ].nunique()
            < 2
            or
            sample[
                y_col
            ].nunique()
            < 2
        ):

            continue


        rho, _ = spearmanr(
            sample[
                x_col
            ],

            sample[
                y_col
            ]
        )


        if np.isfinite(
            rho
        ):

            boot_rho.append(
                rho
            )


    if len(
        boot_rho
    ) == 0:

        return (
            np.nan,
            np.nan
        )


    return (
        np.percentile(
            boot_rho,
            2.5
        ),

        np.percentile(
            boot_rho,
            97.5
        )
    )


# =====================================================================
# 13. CORE + SENSITIVITY SAMPLES
# =====================================================================

core_sample = (
    analysis[
        (
            analysis[
                "observed_years"
            ] == 3
        )
        &
        (
            analysis[
                "coordinate_status"
            ]
            !=
            "manual_approximate"
        )
    ]
    .dropna(
        subset=[
            "AECS",
            "mean_annual_visitors"
        ]
    )
    .copy()
)


sensitivity_sample = (
    analysis[
        analysis[
            "observed_years"
        ] >= 2
    ]
    .dropna(
        subset=[
            "AECS",
            "mean_annual_visitors"
        ]
    )
    .copy()
)


print()
print(
    "Core sample n =",
    len(core_sample)
)

print(
    "Sensitivity sample n =",
    len(sensitivity_sample)
)


association_rows = []


for label, sample in [

    (
        "Core: 3-year and non-manual coordinates",
        core_sample
    ),

    (
        "Sensitivity: at least 2 years",
        sensitivity_sample
    )
]:

    n = len(
        sample
    )


    if n >= 5:

        rho, p = spearmanr(
            sample[
                "AECS"
            ],

            sample[
                "mean_annual_visitors"
            ]
        )


        ci_low, ci_high = (
            bootstrap_spearman(
                sample,

                "AECS",

                "mean_annual_visitors",

                n_boot=10000,

                seed=42
            )
        )

    else:

        rho = np.nan
        p = np.nan
        ci_low = np.nan
        ci_high = np.nan


    association_rows.append(
        {
            "sample":
                label,

            "n":
                n,

            "spearman_rho":
                rho,

            "p_value":
                p,

            "bootstrap_95CI_low":
                ci_low,

            "bootstrap_95CI_high":
                ci_high
        }
    )


association_results = pd.DataFrame(
    association_rows
)


print()
print("=" * 90)
print("RESULT 1 — AECS vs OBSERVED VISITOR DEMAND")
print("=" * 90)


display(
    association_results
)


# =====================================================================
# 14. COMPONENT-LEVEL ASSOCIATION
# =====================================================================

component_sample = (
    core_sample
    if len(
        core_sample
    ) >= 5
    else
    sensitivity_sample
)


component_rows = []


for component in [
    "ALI",
    "TAI",
    "ASI",
    "RNAI",
    "EQI"
]:

    temp = (
        component_sample[
            [
                component,
                "mean_annual_visitors"
            ]
        ]
        .dropna()
    )


    n = len(
        temp
    )


    if (
        n >= 5
        and
        temp[
            component
        ].nunique()
        >= 2
    ):

        rho, p = spearmanr(
            temp[
                component
            ],

            temp[
                "mean_annual_visitors"
            ]
        )


        ci_low, ci_high = (
            bootstrap_spearman(
                temp,

                component,

                "mean_annual_visitors",

                n_boot=10000,

                seed=42
            )
        )

    else:

        rho = np.nan
        p = np.nan
        ci_low = np.nan
        ci_high = np.nan


    component_rows.append(
        {
            "component":
                component,

            "n":
                n,

            "spearman_rho":
                rho,

            "p_value":
                p,

            "bootstrap_95CI_low":
                ci_low,

            "bootstrap_95CI_high":
                ci_high,

            "status":
                "Exploratory"
        }
    )


component_results = (
    pd.DataFrame(
        component_rows
    )
    .sort_values(
        "spearman_rho",
        ascending=False,
        na_position="last"
    )
)


print()
print("=" * 90)
print("RESULT 2 — AECS COMPONENTS vs VISITOR DEMAND")
print("=" * 90)


display(
    component_results
)


# =====================================================================
# 15. SUPPLY–DEMAND MISMATCH
# =====================================================================

mismatch = (
    sensitivity_sample
    .copy()
)


DEMAND_Q66 = (
    mismatch[
        "demand_index"
    ]
    .quantile(
        0.66
    )
)


mismatch[
    "supply_high"
] = (
    mismatch[
        "AECS"
    ]
    >
    Q66
)


mismatch[
    "demand_high"
] = (
    mismatch[
        "demand_index"
    ]
    >
    DEMAND_Q66
)


def classify_supply_demand(row):

    if (
        row[
            "supply_high"
        ]
        and
        row[
            "demand_high"
        ]
    ):

        return (
            "High readiness–high demand"
        )


    if (
        row[
            "supply_high"
        ]
        and
        not row[
            "demand_high"
        ]
    ):

        return (
            "High readiness–lower demand"
        )


    if (
        not row[
            "supply_high"
        ]
        and
        row[
            "demand_high"
        ]
    ):

        return (
            "Lower readiness–high demand"
        )


    return (
        "Lower readiness–lower demand"
    )


mismatch[
    "supply_demand_class"
] = mismatch.apply(
    classify_supply_demand,
    axis=1
)


mismatch[
    "mismatch_score"
] = (
    mismatch[
        "demand_index"
    ]
    -
    mismatch[
        "supply_index"
    ]
)


mismatch_summary = (
    mismatch
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

        mean_supply_index=(
            "supply_index",
            "mean"
        ),

        mean_demand_index=(
            "demand_index",
            "mean"
        ),

        mean_mismatch_score=(
            "mismatch_score",
            "mean"
        )
    )
)


print()
print("=" * 90)
print("RESULT 3 — SUPPLY–DEMAND MISMATCH")
print("=" * 90)


display(
    mismatch[
        [
            c
            for c in [
                "destination",
                "observed_years",
                "grid_id",
                "district",
                "AECS",
                "priority_final",
                "mean_annual_visitors",
                "supply_index",
                "demand_index",
                "mismatch_score",
                "supply_demand_class"
            ]
            if c in mismatch.columns
        ]
    ]
    .sort_values(
        "mean_annual_visitors",
        ascending=False
    )
)


print()
print("SUPPLY–DEMAND SUMMARY")

display(
    mismatch_summary
)


# =====================================================================
# 16. FIGURE 1 — AECS vs OBSERVED DEMAND
# =====================================================================

plot_data = (
    sensitivity_sample
    .copy()
)


sens_result = (
    association_results[
        association_results[
            "sample"
        ]
        ==
        "Sensitivity: at least 2 years"
    ]
)


if len(
    sens_result
) > 0:

    rho_plot = float(
        sens_result[
            "spearman_rho"
        ].iloc[0]
    )

    p_plot = float(
        sens_result[
            "p_value"
        ].iloc[0]
    )

else:

    rho_plot = np.nan
    p_plot = np.nan


plt.figure(
    figsize=(
        8.5,
        6.5
    )
)


plt.scatter(
    plot_data[
        "AECS"
    ],

    plot_data[
        "log_mean_demand"
    ],

    s=90,
    alpha=0.8,
    edgecolor="black",
    linewidth=0.5
)


for _, row in plot_data.iterrows():

    plt.annotate(
        row[
            "destination"
        ],

        (
            row[
                "AECS"
            ],
            row[
                "log_mean_demand"
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


plt.xlabel(
    "Agrotourism Experience Corridor Score (AECS)"
)

plt.ylabel(
    "log(1 + mean annual visitors)"
)

plt.title(
    "Spatial Readiness versus Observed Tourism Demand, 2023–2025\n"
    f"Spearman ρ={rho_plot:.3f}; "
    f"p={p_plot:.3f}; "
    f"n={len(plot_data)}"
)

plt.grid(
    alpha=0.25
)


save_fig(
    "Fig_01_AECS_vs_Observed_Visitor_Demand.png"
)


# =====================================================================
# 17. FIGURE 2 — SUPPLY–DEMAND MATRIX
# =====================================================================

plt.figure(
    figsize=(
        8.5,
        6.5
    )
)


plt.scatter(
    mismatch[
        "AECS"
    ],

    mismatch[
        "demand_index"
    ],

    s=100,
    alpha=0.8,
    edgecolor="black",
    linewidth=0.5
)


plt.axvline(
    Q66,
    linestyle="--",
    linewidth=1
)


plt.axhline(
    DEMAND_Q66,
    linestyle="--",
    linewidth=1
)


for _, row in mismatch.iterrows():

    plt.annotate(
        row[
            "destination"
        ],

        (
            row[
                "AECS"
            ],
            row[
                "demand_index"
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


plt.xlabel(
    "Spatial readiness (AECS)"
)

plt.ylabel(
    "Observed multi-year visitor demand index"
)

plt.title(
    "Spatial Supply–Demand Diagnostic"
)

plt.grid(
    alpha=0.25
)


save_fig(
    "Fig_02_Supply_Demand_Matrix.png"
)


# =====================================================================
# 18. FIGURE 3 — SPATIAL SUPPLY–DEMAND MAP
# =====================================================================

mismatch_points = (
    destination_grid[
        [
            "destination",
            "geometry"
        ]
    ]
    .merge(

        mismatch[
            [
                "destination",
                "mean_annual_visitors",
                "supply_demand_class"
            ]
        ],

        on=
            "destination",

        how=
            "inner"
    )
)


mismatch_points = gpd.GeoDataFrame(
    mismatch_points,

    geometry=
        "geometry",

    crs=
        GEOG_CRS
)


fig, ax = plt.subplots(
    figsize=(
        8,
        11
    )
)


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
            "AECS"
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

    temp = mismatch_points[
        mismatch_points[
            "supply_demand_class"
        ] == class_name
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
            0.6,

        alpha=
            0.85,

        label=
            class_name
    )


for _, row in mismatch_points.iterrows():

    ax.annotate(
        row[
            "destination"
        ],

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
    "Spatial Readiness and Observed Tourism Demand in Barru"
)

ax.set_axis_off()

ax.legend(
    loc=
        "lower left",

    fontsize=
        7
)


save_fig(
    "Fig_03_Spatial_Supply_Demand_Map.png"
)


# =====================================================================
# 19. OPTIONAL FIGURE — COMPONENT CORRELATIONS
# =====================================================================

valid_components = (
    component_results[
        component_results[
            "spearman_rho"
        ].notna()
    ]
    .sort_values(
        "spearman_rho"
    )
)


if len(
    valid_components
) > 0:

    plt.figure(
        figsize=(
            7,
            5
        )
    )


    plt.barh(
        valid_components[
            "component"
        ],

        valid_components[
            "spearman_rho"
        ]
    )


    plt.axvline(
        0,
        linewidth=0.8
    )


    plt.xlabel(
        "Spearman correlation with observed tourism demand"
    )

    plt.ylabel(
        "AECS component"
    )

    plt.title(
        "Component-Level Association with Observed Demand"
    )

    plt.grid(
        axis="x",
        alpha=0.25
    )


    save_fig(
        "Fig_S1_Component_Demand_Association.png"
    )


# =====================================================================
# 20. MANUSCRIPT-READY TABLES
# =====================================================================

TABLE_DEMAND = (
    analysis[
        [
            c
            for c in [
                "destination",
                "visitors_2023",
                "visitors_2024",
                "visitors_2025",
                "observed_years",
                "total_visitors_3yr",
                "mean_annual_visitors",
                "grid_id",
                "district",
                "AECS",
                "priority_final"
            ]
            if c in analysis.columns
        ]
    ]
    .sort_values(
        "mean_annual_visitors",
        ascending=False
    )
)


TABLE_ASSOCIATION = (
    association_results
    .copy()
)


TABLE_COMPONENTS = (
    component_results
    .copy()
)


TABLE_MISMATCH = (
    mismatch[
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
                "supply_index",
                "demand_index",
                "mismatch_score",
                "supply_demand_class"
            ]
            if c in mismatch.columns
        ]
    ]
    .sort_values(
        "mean_annual_visitors",
        ascending=False
    )
)


# =====================================================================
# 21. DISPLAY FINAL TABLES
# =====================================================================

print()
print("=" * 90)
print("TABLE A — DESTINATION DEMAND")
print("=" * 90)

display(
    TABLE_DEMAND
)


print()
print("=" * 90)
print("TABLE B — AECS–DEMAND ASSOCIATION")
print("=" * 90)

display(
    TABLE_ASSOCIATION
)


print()
print("=" * 90)
print("TABLE C — COMPONENT ASSOCIATION")
print("=" * 90)

display(
    TABLE_COMPONENTS
)


print()
print("=" * 90)
print("TABLE D — SUPPLY–DEMAND TYPOLOGY")
print("=" * 90)

display(
    TABLE_MISMATCH
)


# =====================================================================
# 22. EXPORT EXCEL
# =====================================================================

EXCEL_OUT = (
    FINAL_DIR
    / "FINAL_HYBRID_AECS_VISITOR_DEMAND_RESULTS.xlsx"
)


with pd.ExcelWriter(
    EXCEL_OUT,
    engine=
        "openpyxl"
) as writer:

    TABLE_DEMAND.to_excel(
        writer,
        sheet_name=
            "destination_demand",
        index=False
    )

    TABLE_ASSOCIATION.to_excel(
        writer,
        sheet_name=
            "AECS_demand",
        index=False
    )

    TABLE_COMPONENTS.to_excel(
        writer,
        sheet_name=
            "component_demand",
        index=False
    )

    TABLE_MISMATCH.to_excel(
        writer,
        sheet_name=
            "supply_demand",
        index=False
    )

    mismatch_summary.to_excel(
        writer,
        sheet_name=
            "mismatch_summary",
        index=False
    )


# =====================================================================
# 23. EXPORT CSV
# =====================================================================

TABLE_DEMAND.to_csv(
    TABLE_DIR
    / "Table_Destination_Demand.csv",
    index=False
)


TABLE_ASSOCIATION.to_csv(
    TABLE_DIR
    / "Table_AECS_Demand_Association.csv",
    index=False
)


TABLE_COMPONENTS.to_csv(
    TABLE_DIR
    / "Table_Component_Demand_Association.csv",
    index=False
)


TABLE_MISMATCH.to_csv(
    TABLE_DIR
    / "Table_Supply_Demand_Typology.csv",
    index=False
)


mismatch_summary.to_csv(
    TABLE_DIR
    / "Table_Supply_Demand_Summary.csv",
    index=False
)


# =====================================================================
# 24. EXPORT GEOJSON
# =====================================================================

spatial_export = (
    destination_grid
    .merge(

        mismatch[
            [
                "destination",
                "observed_years",
                "total_visitors_3yr",
                "mean_annual_visitors",
                "demand_index",
                "supply_index",
                "mismatch_score",
                "supply_demand_class"
            ]
        ],

        on=
            "destination",

        how=
            "inner"
    )
)


SPATIAL_OUT = (
    FINAL_DIR
    / "FINAL_Supply_Demand_Destinations.geojson"
)


spatial_export.to_file(
    SPATIAL_OUT,
    driver=
        "GeoJSON"
)


# =====================================================================
# 25. FINAL OUTPUT
# =====================================================================

print()
print("=" * 90)
print("✓ ANALISIS FINAL SELESAI")
print("=" * 90)

print()
print(
    "Excel:"
)
print(
    EXCEL_OUT
)

print()
print(
    "Figures:"
)
print(
    FIG_DIR
)

print()
print(
    "Tables:"
)
print(
    TABLE_DIR
)

print()
print(
    "GeoJSON:"
)
print(
    SPATIAL_OUT
)


print()
print("=" * 90)
print("HASIL YANG PERLU DIKIRIM KE SAYA")
print("=" * 90)


print()
print("1. AECS vs observed demand")

display(
    association_results
)


print()
print("2. Component-level associations")

display(
    component_results
)


print()
print("3. Supply-demand mismatch")

display(
    TABLE_MISMATCH
)


print()
print("4. Supply-demand summary")

display(
    mismatch_summary
)