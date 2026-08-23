"""
Run coordinate-quality sensitivity, strict spatial sensitivity, and class-stability analyses.

Clean public version derived from the final manuscript-relevant notebook cell 73.
Personal Google Drive paths and notebook-only execution assumptions were removed.
Analytical logic is retained where it is verifiable from the uploaded notebook.
"""

# =====================================================================
# =====================================================================
# FINAL FREEZE CONTINUATION
# Jalankan SETELAH "✓ BOOTSTRAP BERHASIL"
#
# Menyelesaikan:
# A. Diana Water Park final assignment
# B. Corrected Table 10
# C. Independent non-manual sensitivity
# D. Strict spatial sensitivity
# E. Typology stability
# F. Final freeze checklist + exports
# =====================================================================
# =====================================================================

import os
import runpy
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import geopandas as gpd

from scipy.stats import spearmanr
from IPython.display import display


# =====================================================================
# 01. CHECK BOOTSTRAP VARIABLES
# =====================================================================

required_globals = [
    "grid_final",
    "Q33",
    "Q66",
    "ROOT",
    "GEOG_CRS",
    "METRIC_CRS"
]

missing_globals = [
    x for x in required_globals
    if x not in globals()
]

if missing_globals:
    bootstrap_path = Path(__file__).resolve().parent / "02_validate_hybrid_grid.py"
    bootstrap = runpy.run_path(str(bootstrap_path))
    for name in required_globals:
        if name in bootstrap:
            globals()[name] = bootstrap[name]

    missing_globals = [
        x for x in required_globals
        if x not in globals()
    ]

if missing_globals:
    raise RuntimeError(
        "Verified Hybrid grid bootstrap is incomplete. Missing variables: "
        + str(missing_globals)
    )


assert len(grid_final) == 1358
assert grid_final["grid_id"].nunique() == 1358


print("=" * 100)
print("FINAL FREEZE CONTINUATION")
print("=" * 100)

print("✓ Bootstrap variables available")
print("✓ Verified Hybrid grid:", len(grid_final), "grids")


# =====================================================================
# 02. PATHS
# =====================================================================

MAIN_ANALYSIS_DIR = (
    ROOT
    / "outputs"
    / "04_primary_demand_spatial_linkage"
)

PERCENTILE_DIR = (
    ROOT
    / "outputs"
    / "05_percentile_supply_demand_mismatch"
)

FINAL_DIR = (
    ROOT
    / "outputs"
    / "06_spatial_sensitivity_and_stability"
)

TABLE_DIR = FINAL_DIR / "tables"

FINAL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

TABLE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =====================================================================
# 03. HELPERS
# =====================================================================

def empirical_midrank_percentile(value, reference):

    arr = np.asarray(
        reference,
        dtype=float
    )

    arr = arr[
        np.isfinite(arr)
    ]

    arr = np.sort(arr)

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

    return (
        left + right
    ) / (
        2.0 * len(arr)
    )


def sample_midrank_percentile(series):

    x = pd.to_numeric(
        series,
        errors="coerce"
    )

    result = pd.Series(
        np.nan,
        index=x.index,
        dtype=float
    )

    ok = x.notna()

    n = ok.sum()

    if n == 0:
        return result

    ranks = x[
        ok
    ].rank(
        method="average"
    )

    result.loc[
        ok
    ] = (
        ranks - 0.5
    ) / n

    return result


def classify_typology(row):

    supply_high = (
        row["supply_percentile"]
        >=
        2/3
    )

    demand_high = (
        row["demand_percentile"]
        >=
        2/3
    )

    if supply_high and demand_high:
        return "High readiness–high demand"

    if supply_high and not demand_high:
        return "High readiness–lower demand"

    if (not supply_high) and demand_high:
        return "Lower readiness–high demand"

    return "Lower readiness–lower demand"


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

    n = len(d)

    if n < 5:
        return np.nan, np.nan

    rng = np.random.default_rng(
        seed
    )

    boot = []

    for _ in range(n_boot):

        idx = rng.integers(
            0,
            n,
            n
        )

        s = d.iloc[idx]

        if (
            s[x_col].nunique() < 2
            or
            s[y_col].nunique() < 2
        ):
            continue

        rho, _ = spearmanr(
            s[x_col],
            s[y_col]
        )

        if np.isfinite(rho):
            boot.append(rho)

    if not boot:
        return np.nan, np.nan

    return (
        np.percentile(
            boot,
            2.5
        ),
        np.percentile(
            boot,
            97.5
        )
    )


# =====================================================================
# =====================================================================
# PART A — DIANA WATER PARK FINAL
# =====================================================================
# =====================================================================

DIANA_LAT = -4.285604
DIANA_LON = 119.663559


diana_point = gpd.GeoDataFrame(
    {
        "destination": [
            "Diana Water Park"
        ]
    },
    geometry=
        gpd.points_from_xy(
            [DIANA_LON],
            [DIANA_LAT]
        ),
    crs=
        GEOG_CRS
)


diana_join = gpd.sjoin(
    diana_point,

    grid_final[
        [
            "grid_id",
            "AECS",
            "priority_final",
            "geometry"
        ]
    ],

    how="left",
    predicate="within"
)


if len(diana_join) != 1:

    raise RuntimeError(
        "Diana menghasilkan lebih/kurang dari satu spatial match."
    )


DIANA_GRID = (
    diana_join[
        "grid_id"
    ].iloc[0]
)

DIANA_AECS = float(
    diana_join[
        "AECS"
    ].iloc[0]
)

DIANA_PRIORITY = (
    diana_join[
        "priority_final"
    ].iloc[0]
)


DIANA_PASS = (
    DIANA_GRID == "G0444"
    and
    abs(
        DIANA_AECS
        -
        0.215775
    ) < 0.001
    and
    DIANA_PRIORITY
        == "Moderate priority"
)


print()
print("=" * 100)
print("A. DIANA WATER PARK FINAL VERIFICATION")
print("=" * 100)

print(
    "Coordinate:",
    DIANA_LAT,
    DIANA_LON
)

print(
    "Grid:",
    DIANA_GRID
)

print(
    "AECS:",
    round(
        DIANA_AECS,
        6
    )
)

print(
    "Priority:",
    DIANA_PRIORITY
)

print(
    "Status:",
    "PASS" if DIANA_PASS else "FAIL"
)


if not DIANA_PASS:

    raise RuntimeError(
        "Diana final verification failed."
    )


TABLE_DIANA = pd.DataFrame(
    {
        "Destination": [
            "Diana Water Park"
        ],

        "Latitude": [
            DIANA_LAT
        ],

        "Longitude": [
            DIANA_LON
        ],

        "Coordinate source": [
            "Singgah Barru official tourism portal"
        ],

        "Legacy manuscript grid": [
            "G0441"
        ],

        "Legacy manuscript AECS": [
            0.278
        ],

        "Legacy manuscript priority": [
            "High priority"
        ],

        "Final verified grid": [
            DIANA_GRID
        ],

        "Final verified AECS": [
            DIANA_AECS
        ],

        "Final verified priority": [
            DIANA_PRIORITY
        ]
    }
)


display(
    TABLE_DIANA
)


# =====================================================================
# =====================================================================
# PART B — CORRECTED TABLE 10
# =====================================================================
# =====================================================================

validation = pd.DataFrame(
    [
        [1, "Tourism village",
         "Desa Wisata Pancana",
         "Tanete Rilau", "G0060"],

        [2, "Tourism village",
         "Desa Wisata Kampung Habibie Kecil",
         "Mallusetasi", "G0766"],

        [3, "Tourism village",
         "Desa Wisata Kampung Laskar",
         "Soppeng Riaja", "G0912"],

        [4, "Tourism village",
         "Desa Wisata Air Terjun Baruttungnge",
         "Tanete Rilau", "G0056"],

        [5, "Tourism village",
         "Desa Wisata Kamiri",
         "Balusu", "G0441"],

        [6, "Tourism village",
         "Desa Wisata Wanua To Bentong",
         "Pujananting", "G0938"],

        [7, "Rated destination",
         "Diana Waterpark",
         "Balusu", DIANA_GRID],

        [8, "Rated destination",
         "Padang Indah Allepperengnge",
         "Pujananting", "G0705"],

        [9, "Rated destination",
         "Lappa Laona",
         "Tanete Riaja", "G1239"],

        [10, "Rated destination",
         "Taman Colliq Pujie",
         "Barru", "G0107"],

        [11, "Rated destination",
         "Pantai Sumpang Binangae",
         "Barru", "G0069"]
    ],

    columns=[
        "No.",
        "Validation dataset",
        "Name",
        "District",
        "Nearest grid"
    ]
)


lookup = (
    grid_final[
        [
            "grid_id",
            "AECS",
            "priority_final"
        ]
    ]
    .drop_duplicates(
        "grid_id"
    )
)


TABLE10_FINAL = (
    validation
    .merge(
        lookup,
        left_on=
            "Nearest grid",
        right_on=
            "grid_id",
        how=
            "left"
    )
)


if TABLE10_FINAL[
    "AECS"
].isna().any():

    bad = TABLE10_FINAL[
        TABLE10_FINAL[
            "AECS"
        ].isna()
    ]

    display(bad)

    raise RuntimeError(
        "Ada grid Table 10 yang tidak ditemukan."
    )


TABLE10_FINAL = (
    TABLE10_FINAL
    .rename(
        columns={
            "priority_final":
                "Priority class"
        }
    )
)


TABLE10_FINAL[
    "AECS"
] = TABLE10_FINAL[
    "AECS"
].round(3)


TABLE10_FINAL = TABLE10_FINAL[
    [
        "No.",
        "Validation dataset",
        "Name",
        "District",
        "Nearest grid",
        "Priority class",
        "AECS"
    ]
]


counts = (
    TABLE10_FINAL[
        "Priority class"
    ]
    .value_counts()
)


N_HIGH = int(
    counts.get(
        "High priority",
        0
    )
)

N_MOD = int(
    counts.get(
        "Moderate priority",
        0
    )
)

N_LOW = int(
    counts.get(
        "Low priority",
        0
    )
)


TABLE10_PASS = (
    len(TABLE10_FINAL) == 11
    and
    N_HIGH == 7
    and
    N_MOD == 1
    and
    N_LOW == 3
)


print()
print("=" * 100)
print("B. CORRECTED TABLE 10")
print("=" * 100)

display(
    TABLE10_FINAL
)


print(
    f"Distribution = "
    f"{N_HIGH} High / "
    f"{N_MOD} Moderate / "
    f"{N_LOW} Low"
)

print(
    "Status:",
    "PASS" if TABLE10_PASS else "FAIL"
)


if not TABLE10_PASS:

    raise RuntimeError(
        "Corrected Table 10 distribution unexpected."
    )


# =====================================================================
# =====================================================================
# PART C — LOAD VISITOR ANALYSIS
# =====================================================================
# =====================================================================

MAIN_EXCEL = (
    MAIN_ANALYSIS_DIR
    / "FINAL_HYBRID_AECS_VISITOR_DEMAND_RESULTS.xlsx"
)

SPATIAL_FILE = (
    PERCENTILE_DIR
    / "FINAL_PERCENTILE_Supply_Demand_Destinations.geojson"
)

PRIMARY_PERCENTILE_EXCEL = (
    PERCENTILE_DIR
    / "FINAL_PERCENTILE_SUPPLY_DEMAND_RESULTS.xlsx"
)


for f in [
    MAIN_EXCEL,
    SPATIAL_FILE,
    PRIMARY_PERCENTILE_EXCEL
]:

    if not f.exists():

        raise FileNotFoundError(
            f
        )


analysis_base = pd.read_excel(
    MAIN_EXCEL,
    sheet_name=
        "destination_demand"
)


spatial_meta = gpd.read_file(
    SPATIAL_FILE
)


# =====================================================================
# 04. PREPARE SPATIAL METADATA
# =====================================================================

wanted_meta = [
    "destination",
    "coordinate_status",
    "spatial_assignment_method",
    "distance_to_grid_m",
    "ALI",
    "TAI",
    "ASI",
    "RNAI",
    "EQI"
]


meta_cols = [
    c for c in wanted_meta
    if c in spatial_meta.columns
]


meta = (
    spatial_meta[
        meta_cols
    ]
    .drop_duplicates(
        "destination"
    )
)


# remove duplicates before merge
for c in meta.columns:

    if (
        c != "destination"
        and
        c in analysis_base.columns
    ):

        analysis_base = (
            analysis_base
            .drop(
                columns=[c]
            )
        )


analysis_full = (
    analysis_base
    .merge(
        meta,
        on=
            "destination",
        how=
            "left"
    )
)


# Diana hard consistency check
diana_analysis = analysis_full[
    analysis_full[
        "destination"
    ]
    ==
    "Diana Water Park"
]


if len(diana_analysis) != 1:

    raise RuntimeError(
        "Diana missing/duplicated in visitor analysis."
    )


assert (
    diana_analysis[
        "grid_id"
    ].iloc[0]
    ==
    "G0444"
)


# =====================================================================
# =====================================================================
# PART D — INDEPENDENT NON-MANUAL SENSITIVITY
# =====================================================================
# =====================================================================

nonmanual = (
    analysis_full[
        (
            analysis_full[
                "observed_years"
            ] >= 2
        )
        &
        (
            analysis_full[
                "coordinate_status"
            ]
            !=
            "manual_approximate"
        )
    ]
    .copy()
    .reset_index(
        drop=True
    )
)


print()
print("=" * 100)
print("C. INDEPENDENT NON-MANUAL SAMPLE")
print("=" * 100)

print(
    "n =",
    len(nonmanual)
)


if len(nonmanual) != 10:

    raise RuntimeError(
        f"Expected n=10, obtained n={len(nonmanual)}"
    )


FULL_AECS = (
    grid_final[
        "AECS"
    ]
    .dropna()
    .to_numpy(
        dtype=float
    )
)


# supply percentile unchanged reference = 1358 grids
nonmanual[
    "supply_percentile"
] = nonmanual[
    "AECS"
].apply(
    lambda x:
        empirical_midrank_percentile(
            x,
            FULL_AECS
        )
)


# IMPORTANT:
# demand percentile recalculated INSIDE n=10
nonmanual[
    "demand_percentile"
] = (
    sample_midrank_percentile(
        nonmanual[
            "mean_annual_visitors"
        ]
    )
)


nonmanual[
    "percentile_mismatch"
] = (
    nonmanual[
        "demand_percentile"
    ]
    -
    nonmanual[
        "supply_percentile"
    ]
)


nonmanual[
    "supply_demand_class"
] = nonmanual.apply(
    classify_typology,
    axis=1
)


TABLE_NONMANUAL = (
    nonmanual[
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
                "coordinate_status",
                "spatial_assignment_method",
                "distance_to_grid_m",
                "supply_percentile",
                "demand_percentile",
                "percentile_mismatch",
                "supply_demand_class"
            ]
            if c in nonmanual.columns
        ]
    ]
    .sort_values(
        "percentile_mismatch",
        ascending=False
    )
)


rho_nm, p_nm = spearmanr(
    nonmanual[
        "AECS"
    ],
    nonmanual[
        "mean_annual_visitors"
    ]
)


ci_nm_low, ci_nm_high = (
    bootstrap_spearman(
        nonmanual,
        "AECS",
        "mean_annual_visitors"
    )
)


NONMANUAL_ASSOC = pd.DataFrame(
    {
        "Analysis": [
            "Independent non-manual sensitivity"
        ],
        "n": [
            len(nonmanual)
        ],
        "Spearman_rho": [
            rho_nm
        ],
        "p_value": [
            p_nm
        ],
        "Bootstrap_95CI_low": [
            ci_nm_low
        ],
        "Bootstrap_95CI_high": [
            ci_nm_high
        ]
    }
)


display(
    NONMANUAL_ASSOC
)

display(
    TABLE_NONMANUAL
)


# =====================================================================
# =====================================================================
# PART E — STRICT HIGH-CONFIDENCE SPATIAL SENSITIVITY
# =====================================================================
# =====================================================================

strict = (
    analysis_full[
        (
            analysis_full[
                "observed_years"
            ] >= 2
        )
        &
        (
            analysis_full[
                "coordinate_status"
            ]
            !=
            "manual_approximate"
        )
        &
        (
            analysis_full[
                "spatial_assignment_method"
            ]
            ==
            "point_within_grid"
        )
    ]
    .copy()
    .reset_index(
        drop=True
    )
)


strict[
    "supply_percentile"
] = strict[
    "AECS"
].apply(
    lambda x:
        empirical_midrank_percentile(
            x,
            FULL_AECS
        )
)


strict[
    "demand_percentile"
] = (
    sample_midrank_percentile(
        strict[
            "mean_annual_visitors"
        ]
    )
)


strict[
    "percentile_mismatch"
] = (
    strict[
        "demand_percentile"
    ]
    -
    strict[
        "supply_percentile"
    ]
)


strict[
    "supply_demand_class"
] = strict.apply(
    classify_typology,
    axis=1
)


if len(strict) >= 5:

    rho_strict, p_strict = (
        spearmanr(
            strict["AECS"],
            strict["mean_annual_visitors"]
        )
    )

    (
        ci_strict_low,
        ci_strict_high
    ) = bootstrap_spearman(
        strict,
        "AECS",
        "mean_annual_visitors"
    )

else:

    rho_strict = np.nan
    p_strict = np.nan
    ci_strict_low = np.nan
    ci_strict_high = np.nan


STRICT_ASSOC = pd.DataFrame(
    {
        "Analysis": [
            "Strict non-manual point-within-grid sensitivity"
        ],

        "n": [
            len(strict)
        ],

        "Spearman_rho": [
            rho_strict
        ],

        "p_value": [
            p_strict
        ],

        "Bootstrap_95CI_low": [
            ci_strict_low
        ],

        "Bootstrap_95CI_high": [
            ci_strict_high
        ]
    }
)


print()
print("=" * 100)
print("D. STRICT HIGH-CONFIDENCE SPATIAL SENSITIVITY")
print("=" * 100)

display(
    STRICT_ASSOC
)


# =====================================================================
# =====================================================================
# PART F — TYPOLOGY STABILITY
# =====================================================================
# =====================================================================

primary = pd.read_excel(
    PRIMARY_PERCENTILE_EXCEL,
    sheet_name=
        "percentile_mismatch"
)


primary_classes = (
    primary[
        [
            "destination",
            "supply_demand_class"
        ]
    ]
    .rename(
        columns={
            "supply_demand_class":
                "primary_class"
        }
    )
)


STABILITY = (
    nonmanual[
        [
            "destination",
            "supply_demand_class"
        ]
    ]
    .rename(
        columns={
            "supply_demand_class":
                "reestimated_nonmanual_class"
        }
    )
    .merge(
        primary_classes,
        on=
            "destination",
        how=
            "left"
    )
)


STABILITY[
    "stable"
] = (
    STABILITY[
        "reestimated_nonmanual_class"
    ]
    ==
    STABILITY[
        "primary_class"
    ]
)


N_STABLE = int(
    STABILITY[
        "stable"
    ].sum()
)


STABILITY_RATE = (
    N_STABLE
    /
    len(STABILITY)
)


print()
print("=" * 100)
print("E. TYPOLOGY CLASS STABILITY")
print("=" * 100)

display(
    STABILITY
)

print(
    f"Stable = {N_STABLE}/{len(STABILITY)} "
    f"({STABILITY_RATE*100:.1f}%)"
)


# =====================================================================
# =====================================================================
# PART G — ROBUSTNESS SUMMARY
# =====================================================================
# =====================================================================

ROBUSTNESS = pd.concat(
    [
        pd.DataFrame(
            {
                "Analysis": [
                    "Primary 12-destination sensitivity"
                ],
                "n": [
                    12
                ],
                "Spearman_rho": [
                    0.055944
                ],
                "p_value": [
                    0.862898
                ],
                "Bootstrap_95CI_low": [
                    -0.542857
                ],
                "Bootstrap_95CI_high": [
                    0.607143
                ]
            }
        ),

        NONMANUAL_ASSOC,

        STRICT_ASSOC
    ],

    ignore_index=True
)


print()
print("=" * 100)
print("F. FINAL ROBUSTNESS SUMMARY")
print("=" * 100)

display(
    ROBUSTNESS
)


# =====================================================================
# =====================================================================
# PART H — FINAL MANUSCRIPT TEXT
# =====================================================================
# =====================================================================

TEXT_TABLE10 = f"""
Corrected external-validation statement

After correction of the Diana Waterpark spatial assignment, seven of the
eleven validation locations are situated in high-priority grids, one is
situated in a moderate-priority grid, and three are situated in low-priority
grids. Diana Waterpark was reassigned using the verified coordinate
({DIANA_LAT}, {DIANA_LON}), which falls within grid G0444. The grid has an
AECS of {DIANA_AECS:.3f} and is classified as moderate priority. The earlier
assignment to G0441 was therefore replaced. The external validation should
continue to be interpreted as a spatial consistency check rather than as a
predictive validation of visitor demand.
""".strip()


TEXT_ROBUSTNESS = f"""
Visitor-demand robustness statement

The primary visitor-demand diagnostic comprised 12 destinations with at
least two years of observations. An independent sensitivity analysis was
then conducted after removing manually approximated destination coordinates.
Demand percentiles were recalculated within the resulting non-manual sample
(n={len(nonmanual)}), whereas supply percentiles continued to reference the
full set of 1,358 analytical grids. In this sample, the association between
AECS and mean annual visitor demand was weak
(Spearman rho={rho_nm:.3f}, p={p_nm:.3f}, bootstrap 95% CI
[{ci_nm_low:.3f}, {ci_nm_high:.3f}]).

A stricter spatial-confidence analysis retained only non-manual locations
that fell directly within an analytical grid (n={len(strict)}). The
corresponding Spearman coefficient was {rho_strict:.3f}
(p={p_strict:.3f}, bootstrap 95% CI
[{ci_strict_low:.3f}, {ci_strict_high:.3f}]).

Among the ten non-manual destinations, {N_STABLE} supply-demand typology
assignments remained unchanged after independent re-estimation, corresponding
to a stability rate of {STABILITY_RATE*100:.1f}%.
""".strip()


# =====================================================================
# 05. EXPORTS
# =====================================================================

TABLE_DIANA.to_csv(
    TABLE_DIR
    / "Diana_Final_Verification.csv",
    index=False
)

TABLE10_FINAL.to_csv(
    TABLE_DIR
    / "Table10_CORRECTED.csv",
    index=False
)

TABLE_NONMANUAL.to_csv(
    TABLE_DIR
    / "Nonmanual_Reestimated_Mismatch.csv",
    index=False
)

STRICT_ASSOC.to_csv(
    TABLE_DIR
    / "Strict_Spatial_Sensitivity.csv",
    index=False
)

STABILITY.to_csv(
    TABLE_DIR
    / "Typology_Stability.csv",
    index=False
)

ROBUSTNESS.to_csv(
    TABLE_DIR
    / "Final_Robustness_Summary.csv",
    index=False
)


FINAL_EXCEL = (
    FINAL_DIR
    / "FINAL_100_PERCENT_RESULTS.xlsx"
)


with pd.ExcelWriter(
    FINAL_EXCEL,
    engine="openpyxl"
) as writer:

    TABLE_DIANA.to_excel(
        writer,
        sheet_name=
            "Diana_final",
        index=False
    )

    TABLE10_FINAL.to_excel(
        writer,
        sheet_name=
            "Table10_corrected",
        index=False
    )

    NONMANUAL_ASSOC.to_excel(
        writer,
        sheet_name=
            "nonmanual_assoc",
        index=False
    )

    TABLE_NONMANUAL.to_excel(
        writer,
        sheet_name=
            "nonmanual_mismatch",
        index=False
    )

    STRICT_ASSOC.to_excel(
        writer,
        sheet_name=
            "strict_assoc",
        index=False
    )

    STABILITY.to_excel(
        writer,
        sheet_name=
            "class_stability",
        index=False
    )

    ROBUSTNESS.to_excel(
        writer,
        sheet_name=
            "robustness",
        index=False
    )


TEXT_FILE = (
    FINAL_DIR
    / "MANUSCRIPT_FINAL_REPLACEMENT_TEXT.txt"
)


with open(
    TEXT_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        TEXT_TABLE10
    )

    f.write(
        "\n\n"
        + "=" * 80
        + "\n\n"
    )

    f.write(
        TEXT_ROBUSTNESS
    )


# =====================================================================
# =====================================================================
# PART I — FINAL FREEZE CHECKLIST
# =====================================================================
# =====================================================================

FREEZE = pd.DataFrame(
    {
        "Check": [
            "Verified Hybrid grid = 1,358 units",
            "AECS mean matches final manuscript model",
            "Diana coordinate maps to G0444",
            "Diana final AECS = 0.215775",
            "Diana final class = Moderate priority",
            "Corrected Table 10 = 11 locations",
            "Corrected Table 10 = 7 High / 1 Moderate / 3 Low",
            "Independent non-manual sample recalculated",
            "Non-manual n = 10",
            "Strict point-within-grid sensitivity calculated",
            "Typology class stability calculated",
            "Final robustness table exported",
            "Final manuscript replacement text exported"
        ],

        "PASS": [
            len(grid_final) == 1358,

            abs(
                grid_final["AECS"].mean()
                -
                0.203551
            ) < 0.001,

            DIANA_GRID == "G0444",

            abs(
                DIANA_AECS
                -
                0.215775
            ) < 0.001,

            DIANA_PRIORITY
                == "Moderate priority",

            len(TABLE10_FINAL)
                == 11,

            TABLE10_PASS,

            len(nonmanual)
                > 0,

            len(nonmanual)
                == 10,

            len(strict)
                >= 5,

            len(STABILITY)
                == 10,

            len(ROBUSTNESS)
                == 3,

            TEXT_FILE.exists()
        ]
    }
)


ALL_PASS = bool(
    FREEZE[
        "PASS"
    ].all()
)


print()
print("=" * 100)
print("FINAL FREEZE CHECKLIST")
print("=" * 100)

display(
    FREEZE
)


print()
print("=" * 100)

if ALL_PASS:

    print(
        "PASS — ANALYTICAL WORKFLOW FROZEN AT 100%"
    )

else:

    print(
        "FAIL — REVIEW ITEMS MARKED FALSE"
    )

print("=" * 100)


print()
print(
    "Final Excel:"
)
print(
    FINAL_EXCEL
)

print()
print(
    "Final manuscript text:"
)
print(
    TEXT_FILE
)


print()
print("=" * 100)
print("KIRIMKAN 5 OUTPUT INI")
print("=" * 100)


print()
print("1. FINAL FREEZE CHECKLIST")
display(FREEZE)


print()
print("2. CORRECTED TABLE 10")
display(TABLE10_FINAL)


print()
print("3. FINAL ROBUSTNESS SUMMARY")
display(ROBUSTNESS)


print()
print("4. TYPOLOGY STABILITY")
display(STABILITY)


print()
print("5. RE-ESTIMATED NON-MANUAL MISMATCH")
display(TABLE_NONMANUAL)