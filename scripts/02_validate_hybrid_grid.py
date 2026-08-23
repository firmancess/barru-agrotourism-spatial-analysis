"""
Validate and standardize the frozen 1,358-grid Hybrid AECS layer.

Clean public version derived from the final manuscript-relevant notebook cell 72.
Personal Google Drive paths and notebook-only execution assumptions were removed.
Analytical logic is retained where it is verifiable from the uploaded notebook.
"""

# =====================================================================
# FIX FINAL — BOOTSTRAP VERIFIED HYBRID GRID
# JALANKAN CELL INI SAJA TERLEBIH DAHULU
# =====================================================================

import os
import re
import numpy as np
import pandas as pd
import geopandas as gpd

from pathlib import Path
from IPython.display import display


# ---------------------------------------------------------------------
# PATH
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

GEOG_CRS = "EPSG:4326"
METRIC_CRS = "EPSG:32750"


print("=" * 100)
print("BOOTSTRAP VERIFIED HYBRID GRID")
print("=" * 100)

print("File:")
print(GRID_FILE)


# ---------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------

if not GRID_FILE.exists():
    raise FileNotFoundError(
        f"File tidak ditemukan:\n{GRID_FILE}"
    )


grid_final = gpd.read_file(
    GRID_FILE
)


print()
print("Rows:", len(grid_final))

print()
print("KOLOM ASLI:")
for i, c in enumerate(grid_final.columns):
    print(i, repr(c))


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
# HELPER
# ---------------------------------------------------------------------

def clean_name(x):

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(x).lower()
    )


def normalize_grid_id(x):

    if pd.isna(x):
        return np.nan

    s = str(x).strip()

    m = re.search(
        r"(\d+)",
        s
    )

    if m is None:
        return s

    return (
        "G"
        +
        str(
            int(m.group(1))
        ).zfill(4)
    )


# ---------------------------------------------------------------------
# DETECT GRID ID COLUMN
# ---------------------------------------------------------------------

print()
print("=" * 100)
print("MENCARI KOLOM GRID ID")
print("=" * 100)


candidate_names = [
    "grid_id",
    "gridid",
    "grid",
    "unit_id",
    "unitid"
]


lookup = {
    clean_name(c): c
    for c in grid_final.columns
}


grid_id_source = None


for name in candidate_names:

    key = clean_name(name)

    if key in lookup:

        grid_id_source = lookup[key]
        break


# Kalau belum ketemu, cek isi seluruh kolom
if grid_id_source is None:

    print(
        "Nama kolom standar tidak ditemukan."
    )

    print(
        "Sekarang mendeteksi berdasarkan isi kolom..."
    )

    for c in grid_final.columns:

        if c == "geometry":
            continue

        try:

            vals = (
                grid_final[c]
                .dropna()
                .astype(str)
                .head(100)
            )

        except Exception:
            continue


        if len(vals) == 0:
            continue


        ratio = (
            vals
            .str.match(
                r"^[Gg]\d+$"
            )
            .mean()
        )


        if ratio >= 0.50:

            grid_id_source = c
            break


if grid_id_source is None:

    raise RuntimeError(
        "Tidak berhasil menemukan kolom Grid ID.\n"
        "SALIN output 'KOLOM ASLI' dan kirimkan kepada saya."
    )


print(
    "✓ Kolom Grid ID ditemukan:",
    repr(grid_id_source)
)


# ---------------------------------------------------------------------
# RENAME TO grid_id
# ---------------------------------------------------------------------

if grid_id_source != "grid_id":

    # Hindari konflik bila ternyata sudah ada grid_id tersembunyi
    if "grid_id" in grid_final.columns:

        grid_final = grid_final.drop(
            columns=["grid_id"]
        )

    grid_final = grid_final.rename(
        columns={
            grid_id_source:
                "grid_id"
        }
    )


grid_final[
    "grid_id"
] = grid_final[
    "grid_id"
].apply(
    normalize_grid_id
)


print()
print(
    "Unique grid_id:",
    grid_final["grid_id"].nunique()
)

print(
    "Contoh:",
    grid_final["grid_id"].head(10).tolist()
)


# ---------------------------------------------------------------------
# COMPONENT COLUMN DETECTION
# ---------------------------------------------------------------------

ALIASES = {

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
        "AECS_hybrid",
        "hybrid_aecs",
        "aecs_final"
    ]
}


rename_map = {}


for target, names in ALIASES.items():

    source = None

    lookup = {
        clean_name(c): c
        for c in grid_final.columns
    }


    for name in names:

        k = clean_name(name)

        if k in lookup:

            source = lookup[k]
            break


    if source is None:

        raise RuntimeError(
            f"Kolom {target} tidak ditemukan."
        )


    if source != target:

        rename_map[source] = target


if rename_map:

    grid_final = grid_final.rename(
        columns=rename_map
    )


# ---------------------------------------------------------------------
# NUMERIC
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
# HARD VALIDATION
# ---------------------------------------------------------------------

fingerprint = pd.DataFrame(
    {
        "Statistic": [
            "N",
            "Unique grid",
            "Mean",
            "Std",
            "Min",
            "Q1",
            "Median",
            "Q3",
            "Max"
        ],

        "Observed": [
            len(grid_final),

            grid_final[
                "grid_id"
            ].nunique(),

            grid_final[
                "AECS"
            ].mean(),

            grid_final[
                "AECS"
            ].std(),

            grid_final[
                "AECS"
            ].min(),

            grid_final[
                "AECS"
            ].quantile(0.25),

            grid_final[
                "AECS"
            ].median(),

            grid_final[
                "AECS"
            ].quantile(0.75),

            grid_final[
                "AECS"
            ].max()
        ],

        "Expected": [
            1358,
            1358,
            0.203551,
            0.052062,
            0.087750,
            0.165734,
            0.209732,
            0.238988,
            0.522073
        ]
    }
)


print()
print("=" * 100)
print("FINAL GRID FINGERPRINT")
print("=" * 100)

display(
    fingerprint
)


PASS = (

    len(grid_final) == 1358

    and

    grid_final[
        "grid_id"
    ].nunique() == 1358

    and

    abs(
        grid_final[
            "AECS"
        ].mean()
        -
        0.203551
    ) < 0.001

    and

    abs(
        grid_final[
            "AECS"
        ].max()
        -
        0.522073
    ) < 0.001
)


if not PASS:

    raise RuntimeError(
        "Fingerprint belum cocok. STOP."
    )


# ---------------------------------------------------------------------
# PRIORITY
# ---------------------------------------------------------------------

Q33 = grid_final[
    "AECS"
].quantile(
    0.33
)

Q66 = grid_final[
    "AECS"
].quantile(
    0.66
)


grid_final[
    "priority_final"
] = np.select(

    [
        grid_final[
            "AECS"
        ] <= Q33,

        (
            grid_final[
                "AECS"
            ] > Q33
        )
        &
        (
            grid_final[
                "AECS"
            ] <= Q66
        ),

        grid_final[
            "AECS"
        ] > Q66
    ],

    [
        "Low priority",
        "Moderate priority",
        "High priority"
    ],

    default=
        "Moderate priority"
)


print()
print("=" * 100)
print("PRIORITY CHECK")
print("=" * 100)

print(
    "Q33:",
    round(Q33, 6)
)

print(
    "Q66:",
    round(Q66, 6)
)


display(
    grid_final[
        "priority_final"
    ]
    .value_counts()
    .rename_axis(
        "Priority"
    )
    .reset_index(
        name="N"
    )
)


# ---------------------------------------------------------------------
# TEST IMPORTANT IDS
# ---------------------------------------------------------------------

important = grid_final[
    grid_final[
        "grid_id"
    ].isin(
        [
            "G0231",
            "G0107",
            "G0106",
            "G0444",
            "G0441"
        ]
    )
][
    [
        "grid_id",
        "AECS",
        "priority_final"
    ]
].sort_values(
    "grid_id"
)


print()
print("=" * 100)
print("CRITICAL GRID CHECK")
print("=" * 100)

display(
    important
)


# ---------------------------------------------------------------------
# CREATE COMPATIBILITY VARIABLE
#
# Supaya script berikutnya yang masih memakai nama 'grid'
# juga otomatis menggunakan verified final grid.
# ---------------------------------------------------------------------

grid = grid_final.copy()


print()
print("=" * 100)
print("✓ BOOTSTRAP BERHASIL")
print("=" * 100)

print(
    "Variabel siap:"
)

print(
    "grid_final = verified 1,358-grid Hybrid"
)

print(
    "grid       = copy dari grid_final"
)

print(
    "Q33        =",
    round(Q33, 6)
)

print(
    "Q66        =",
    round(Q66, 6)
)

print()
print(
    "JANGAN jalankan ulang bagian load grid dari script lama."
)