"""
Optional provenance audit to identify the parent grid matching a verified top-20 reference.

Clean public version derived from the final manuscript-relevant notebook cell 67.
Personal Google Drive paths and notebook-only execution assumptions were removed.
Analytical logic is retained where it is verifiable from the uploaded notebook.
"""

# =====================================================================
# FIND THE TRUE 1,358-GRID PARENT OF THE VERIFIED HYBRID TOP-20
# =====================================================================

import os
import re
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import geopandas as gpd
from IPython.display import display


# =====================================================================
# 01. PATH
# =====================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(
    os.environ.get("AECS_PROJECT_ROOT", SCRIPT_DIR.parents[1])
).resolve()

ROOT = REPO_ROOT

REF_FILE = (
    REPO_ROOT
    / "data"
    / "processed"
    / "table_7_top20_priority_grids_hybrid.csv"
)

if not REF_FILE.exists():
    raise FileNotFoundError(
        f"Top-20 hybrid tidak ditemukan:\n{REF_FILE}"
    )


print("=" * 95)
print("MENCARI FILE INDUK FINAL AECS 1.358 GRID")
print("=" * 95)

print("Reference Top-20:")
print(REF_FILE)


# =====================================================================
# 02. HELPER
# =====================================================================

def norm_id(x):

    if pd.isna(x):
        return np.nan

    s = str(x).strip()

    m = re.search(
        r"(\d+)",
        s
    )

    if m is None:
        return s

    # G00231 -> G0231
    # G231   -> G0231
    return "G" + str(
        int(
            m.group(1)
        )
    ).zfill(4)


def find_col(
    df,
    alternatives
):

    cmap = {
        str(c).strip().lower():
            c
        for c in df.columns
    }

    for name in alternatives:

        key = (
            name.strip().lower()
        )

        if key in cmap:
            return cmap[key]

    return None


ALIASES = {

    "grid_id": [
        "grid_id",
        "grid id",
        "grid",
        "unit_id",
        "unit id"
    ],

    "ALI": [
        "ALI",
        "agricultural_landscape_index",
        "Agricultural Landscape Index"
    ],

    "TAI": [
        "TAI",
        "tourism_attraction_index",
        "Tourism Attraction Index"
    ],

    "ASI": [
        "ASI",
        "amenity_support_index",
        "Amenity Support Index"
    ],

    "RNAI": [
        "RNAI",
        "road_network_accessibility_index",
        "Road Network Accessibility Index"
    ],

    "EQI": [
        "EQI",
        "environmental_quality_index",
        "Environmental Quality Index"
    ],

    "AECS": [
        "AECS",
        "aecs",
        "AECS_final",
        "aecs_final",
        "AECS_hybrid",
        "hybrid_AECS",
        "corridor_score"
    ]
}


def standardize_table(df):

    rename = {}

    for target, alternatives in ALIASES.items():

        found = find_col(
            df,
            alternatives
        )

        if found is not None:
            rename[
                found
            ] = target

    out = df.rename(
        columns=rename
    ).copy()

    if "grid_id" in out.columns:

        out[
            "grid_id"
        ] = out[
            "grid_id"
        ].apply(
            norm_id
        )

    for c in [
        "ALI",
        "TAI",
        "ASI",
        "RNAI",
        "EQI",
        "AECS"
    ]:

        if c in out.columns:

            out[c] = pd.to_numeric(
                out[c],
                errors="coerce"
            )

    return out


# =====================================================================
# 03. LOAD VERIFIED TOP-20 REFERENCE
# =====================================================================

ref = pd.read_csv(
    REF_FILE
)

ref = standardize_table(
    ref
)


needed_ref = [
    "grid_id",
    "ALI",
    "TAI",
    "ASI",
    "RNAI",
    "EQI",
    "AECS"
]


missing_ref = [
    c
    for c in needed_ref
    if c not in ref.columns
]

if missing_ref:

    raise RuntimeError(
        "Top-20 reference tidak memiliki "
        f"kolom berikut: {missing_ref}"
    )


ref = (
    ref[
        needed_ref
    ]
    .drop_duplicates(
        "grid_id"
    )
)


print()
print("VERIFIED TOP-20 REFERENCE:")
display(
    ref.head(20)
)


# =====================================================================
# 04. FILE READER
# =====================================================================

def read_file(path):

    ext = (
        path.suffix
        .lower()
    )

    try:

        if ext == ".csv":

            return pd.read_csv(
                path,
                low_memory=False
            )

        elif ext in [
            ".xlsx",
            ".xls"
        ]:

            # audit sheet pertama
            return pd.read_excel(
                path
            )

        elif ext in [
            ".geojson",
            ".gpkg",
            ".shp"
        ]:

            return gpd.read_file(
                path
            )

    except Exception:
        return None

    return None


# =====================================================================
# 05. COLLECT ALL TABULAR/SPATIAL FILES
#
# Tidak lagi menyaring berdasarkan nama.
# =====================================================================

extensions = {
    ".csv",
    ".xlsx",
    ".xls",
    ".geojson",
    ".gpkg",
    ".shp"
}


all_files = []

for p in ROOT.rglob("*"):

    if (
        p.is_file()
        and
        p.suffix.lower()
        in extensions
    ):

        # Abaikan file visitor baru supaya audit lebih bersih
        if (
            "visitor_demand_2023_2025_q1"
            in str(p)
            or
            "FINAL_AECS_VISITOR_DEMAND"
            in str(p)
        ):
            continue

        all_files.append(
            p
        )


print()
print(
    "Total file yang akan diperiksa:",
    len(all_files)
)


# =====================================================================
# 06. AUDIT AGAINST VERIFIED TOP-20
# =====================================================================

results = []

object_cache = {}


for i, path in enumerate(
    all_files,
    start=1
):

    # skip file sangat besar > 150 MB pada tahap ini
    try:

        size_mb = (
            path.stat().st_size
            /
            1024**2
        )

    except:
        size_mb = np.nan


    if (
        np.isfinite(size_mb)
        and
        size_mb > 150
    ):
        continue


    raw = read_file(
        path
    )

    if raw is None:
        continue


    df = standardize_table(
        raw
    )


    if (
        "grid_id"
        not in df.columns
    ):
        continue


    # Minimal harus punya salah satu:
    # AECS atau komponen AECS
    relevant_cols = [
        c
        for c in [
            "ALI",
            "TAI",
            "ASI",
            "RNAI",
            "EQI",
            "AECS"
        ]
        if c in df.columns
    ]


    if len(
        relevant_cols
    ) == 0:
        continue


    candidate = (
        df[
            [
                "grid_id"
            ]
            +
            relevant_cols
        ]
        .drop_duplicates(
            "grid_id"
        )
    )


    comparison = ref.merge(
        candidate,
        on="grid_id",
        how="inner",
        suffixes=(
            "_ref",
            "_cand"
        )
    )


    n_overlap = len(
        comparison
    )


    if n_overlap == 0:
        continue


    row = {

        "file":
            path.name,

        "path":
            str(path),

        "size_mb":
            size_mb,

        "n_rows":
            len(df),

        "n_unique_grid":
            df[
                "grid_id"
            ].nunique(),

        "top20_overlap":
            n_overlap,

        "has_geometry":
            isinstance(
                raw,
                gpd.GeoDataFrame
            )
    }


    # ---------------------------------------------------------
    # AECS agreement
    # ---------------------------------------------------------

    if (
        "AECS_ref"
        in comparison.columns
        and
        "AECS_cand"
        in comparison.columns
    ):

        valid = comparison[
            [
                "AECS_ref",
                "AECS_cand"
            ]
        ].dropna()


        if len(valid):

            differences = (
                valid[
                    "AECS_cand"
                ]
                -
                valid[
                    "AECS_ref"
                ]
            )


            row[
                "AECS_n_compared"
            ] = len(
                valid
            )

            row[
                "AECS_MAE"
            ] = (
                differences
                .abs()
                .mean()
            )

            row[
                "AECS_max_abs_error"
            ] = (
                differences
                .abs()
                .max()
            )

            row[
                "AECS_exact_001"
            ] = (
                differences
                .abs()
                .le(
                    0.0015
                )
                .sum()
            )

        else:

            row[
                "AECS_n_compared"
            ] = 0

            row[
                "AECS_MAE"
            ] = np.nan

            row[
                "AECS_max_abs_error"
            ] = np.nan

            row[
                "AECS_exact_001"
            ] = 0

    else:

        row[
            "AECS_n_compared"
        ] = 0

        row[
            "AECS_MAE"
        ] = np.nan

        row[
            "AECS_max_abs_error"
        ] = np.nan

        row[
            "AECS_exact_001"
        ] = 0


    # ---------------------------------------------------------
    # Component agreement
    # ---------------------------------------------------------

    component_match = 0
    component_tested = 0
    component_maes = []


    for comp in [
        "ALI",
        "TAI",
        "ASI",
        "RNAI",
        "EQI"
    ]:

        ref_col = (
            f"{comp}_ref"
        )

        cand_col = (
            f"{comp}_cand"
        )


        if (
            ref_col
            in comparison.columns
            and
            cand_col
            in comparison.columns
        ):

            temp = comparison[
                [
                    ref_col,
                    cand_col
                ]
            ].dropna()


            if len(temp):

                component_tested += 1

                mae = (
                    temp[
                        cand_col
                    ]
                    -
                    temp[
                        ref_col
                    ]
                ).abs().mean()


                component_maes.append(
                    mae
                )


                if mae <= 0.002:

                    component_match += 1


    row[
        "components_tested"
    ] = component_tested

    row[
        "components_matching"
    ] = component_match

    row[
        "component_mean_MAE"
    ] = (
        np.mean(
            component_maes
        )
        if component_maes
        else np.nan
    )


    # ---------------------------------------------------------
    # Variation check
    # ---------------------------------------------------------

    for comp in [
        "ALI",
        "TAI",
        "ASI",
        "RNAI",
        "EQI"
    ]:

        if comp in df.columns:

            row[
                f"{comp}_unique"
            ] = (
                pd.to_numeric(
                    df[comp],
                    errors="coerce"
                )
                .dropna()
                .nunique()
            )

        else:

            row[
                f"{comp}_unique"
            ] = 0


    # ---------------------------------------------------------
    # Candidate score
    # ---------------------------------------------------------

    # Sangat mengutamakan:
    # - 1358 unique grids
    # - 20/20 overlap
    # - AECS matching
    # - components matching
    # - geometry available
    # ---------------------------------------------------------

    score = 0


    if row[
        "n_unique_grid"
    ] == 1358:

        score += 100


    score += (
        row[
            "top20_overlap"
        ]
        * 2
    )


    score += (
        row[
            "AECS_exact_001"
        ]
        * 5
    )


    score += (
        row[
            "components_matching"
        ]
        * 15
    )


    if row[
        "has_geometry"
    ]:

        score += 20


    row[
        "match_score"
    ] = score


    results.append(
        row
    )


    object_cache[
        str(path)
    ] = raw


# =====================================================================
# 07. RESULT TABLE
# =====================================================================

audit2 = pd.DataFrame(
    results
)


if len(
    audit2
) == 0:

    raise RuntimeError(
        "Tidak ditemukan kandidat tabel/grid "
        "yang memiliki grid_id dan komponen/AECS."
    )


audit2 = (
    audit2
    .sort_values(
        [
            "match_score",
            "top20_overlap",
            "AECS_exact_001"
        ],
        ascending=[
            False,
            False,
            False
        ]
    )
    .reset_index(
        drop=True
    )
)


print()
print("=" * 95)
print("HASIL PENCARIAN FILE INDUK")
print("=" * 95)


show_cols = [

    "file",
    "n_rows",
    "n_unique_grid",

    "top20_overlap",

    "AECS_n_compared",
    "AECS_exact_001",
    "AECS_MAE",
    "AECS_max_abs_error",

    "components_tested",
    "components_matching",
    "component_mean_MAE",

    "ALI_unique",
    "TAI_unique",
    "ASI_unique",
    "RNAI_unique",
    "EQI_unique",

    "has_geometry",
    "match_score"
]


display(
    audit2[
        [
            c
            for c in show_cols
            if c in audit2.columns
        ]
    ]
    .head(30)
)


# =====================================================================
# 08. FILTER STRONG CANDIDATES
# =====================================================================

strong = audit2[
    (
        audit2[
            "n_unique_grid"
        ] == 1358
    )
    &
    (
        audit2[
            "top20_overlap"
        ] >= 15
    )
].copy()


print()
print("=" * 95)
print("STRONG 1,358-GRID CANDIDATES")
print("=" * 95)


if len(
    strong
) == 0:

    print(
        "Belum ada kandidat 1.358-grid dengan >=15 "
        "Top-20 IDs yang cocok."
    )

else:

    display(
        strong[
            [
                c
                for c in show_cols
                if c in strong.columns
            ]
        ]
    )


# =====================================================================
# 09. INSPECT BEST CANDIDATE
# =====================================================================

best_row = audit2.iloc[
    0
]

BEST_PATH = Path(
    best_row[
        "path"
    ]
)


print()
print("=" * 95)
print("BEST CANDIDATE")
print("=" * 95)

print(BEST_PATH)

print()
print(
    "Rows        :",
    best_row[
        "n_rows"
    ]
)

print(
    "Unique grid :",
    best_row[
        "n_unique_grid"
    ]
)

print(
    "Top20 match :",
    best_row[
        "top20_overlap"
    ],
    "/ 20"
)

print(
    "AECS exact  :",
    best_row[
        "AECS_exact_001"
    ],
    "/",
    best_row[
        "AECS_n_compared"
    ]
)


best_raw = object_cache[
    str(
        BEST_PATH
    )
]


best = standardize_table(
    best_raw
)


# =====================================================================
# 10. SHOW TOP-20 COMPARISON OF BEST FILE
# =====================================================================

best_compare = (
    ref.merge(
        best[
            [
                c
                for c in [
                    "grid_id",
                    "ALI",
                    "TAI",
                    "ASI",
                    "RNAI",
                    "EQI",
                    "AECS"
                ]
                if c in best.columns
            ]
        ],
        on="grid_id",
        how="left",
        suffixes=(
            "_reference",
            "_candidate"
        )
    )
)


print()
print("=" * 95)
print("TOP-20 REFERENCE vs BEST CANDIDATE")
print("=" * 95)


display(
    best_compare
)


# =====================================================================
# 11. IF STRONG MATCH FOUND, CHECK WHOLE GRID STATISTICS
# =====================================================================

if (
    best[
        "grid_id"
    ].nunique()
    == 1358
    and
    "AECS"
    in best.columns
):

    x = pd.to_numeric(
        best[
            "AECS"
        ],
        errors="coerce"
    )


    final_stats = pd.DataFrame(
        {
            "Statistic": [
                "N",
                "Mean",
                "Std",
                "Min",
                "Q1",
                "Median",
                "Q3",
                "Max"
            ],

            "Candidate": [
                len(best),
                x.mean(),
                x.std(),
                x.min(),
                x.quantile(0.25),
                x.median(),
                x.quantile(0.75),
                x.max()
            ],

            "Manuscript": [
                1358,
                0.204,
                0.052,
                0.088,
                0.166,
                0.210,
                0.239,
                0.522
            ]
        }
    )


    print()
    print("=" * 95)
    print("WHOLE-GRID FINGERPRINT")
    print("=" * 95)

    display(
        final_stats
    )


print()
print("=" * 95)
print("PENCARIAN SELESAI")
print("=" * 95)
