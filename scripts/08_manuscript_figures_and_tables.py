"""
Generate manuscript-ready tables and figures from the final processed outputs.

Clean public version derived from the final manuscript-relevant notebook cell 74.
Personal Google Drive paths and notebook-only execution assumptions were removed.
Analytical logic is retained where it is verifiable from the uploaded notebook.
"""

# =====================================================================
# =====================================================================
# FINAL MANUSCRIPT FIGURES + TABLES
# Supply–Demand Agrotourism Manuscript
#
# OUTPUT:
#   Fig_05_CORRECTED_External_Validation.png
#   Fig_07_Supply_Demand_Percentile_Matrix.png
#   Fig_08_Spatial_Supply_Demand_Map.png
#   Fig_S1_Demand_Robustness_ForestPlot.png
#
#   Table_10_Corrected_External_Validation
#   Table_11_Visitor_Demand_AECS
#   Table_12_Supply_Demand_Mismatch
#   Table_13_Demand_Robustness
#   Table_S1_Typology_Stability
#
# PNG = 600 DPI
# Tables are ALSO exported as Excel/CSV for editable manuscript use.
# =====================================================================
# =====================================================================


# =====================================================================
# 00. IMPORT
# =====================================================================

import os
import re
import textwrap
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import geopandas as gpd

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from IPython.display import display


# =====================================================================
# 02. PATH
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

DEMAND_FILE = (
    REPO_ROOT
    / "outputs"
    / "04_primary_demand_spatial_linkage"
    / "FINAL_HYBRID_AECS_VISITOR_DEMAND_RESULTS.xlsx"
)

PERCENTILE_FILE = (
    REPO_ROOT
    / "outputs"
    / "05_percentile_supply_demand_mismatch"
    / "FINAL_PERCENTILE_SUPPLY_DEMAND_RESULTS.xlsx"
)

SPATIAL_FILE = (
    REPO_ROOT
    / "outputs"
    / "05_percentile_supply_demand_mismatch"
    / "FINAL_PERCENTILE_Supply_Demand_Destinations.geojson"
)

FREEZE_FILE = (
    REPO_ROOT
    / "outputs"
    / "06_spatial_sensitivity_and_stability"
    / "FINAL_100_PERCENT_RESULTS.xlsx"
)

OUT_DIR = (
    REPO_ROOT
    / "outputs"
    / "08_manuscript_figures_tables"
)

FIG_DIR = (
    OUT_DIR
    / "FIGURES_600DPI"
)

TABLE_DIR = (
    OUT_DIR
    / "TABLES"
)

TABLE_PNG_DIR = (
    TABLE_DIR
    / "PNG_600DPI"
)


for folder in [
    OUT_DIR,
    FIG_DIR,
    TABLE_DIR,
    TABLE_PNG_DIR
]:

    folder.mkdir(
        parents=True,
        exist_ok=True
    )


# =====================================================================
# 03. CHECK FILES
# =====================================================================

required_files = [
    GRID_FILE,
    DEMAND_FILE,
    PERCENTILE_FILE,
    SPATIAL_FILE,
    FREEZE_FILE
]


for f in required_files:

    if not f.exists():

        raise FileNotFoundError(
            f"\nFile tidak ditemukan:\n{f}"
        )


print("=" * 100)
print("FINAL MANUSCRIPT FIGURE + TABLE GENERATOR")
print("=" * 100)

print()
print("Output:")
print(OUT_DIR)


# =====================================================================
# 04. PUBLICATION STYLE
# =====================================================================

plt.rcParams.update({

    "font.family":
        "DejaVu Sans",

    "font.size":
        9,

    "axes.titlesize":
        10,

    "axes.labelsize":
        9,

    "xtick.labelsize":
        8,

    "ytick.labelsize":
        8,

    "legend.fontsize":
        8,

    "figure.dpi":
        150,

    "savefig.dpi":
        600,

    "axes.linewidth":
        0.8,

    "lines.linewidth":
        1.0
})


# =====================================================================
# 05. HELPERS
# =====================================================================

def clean_col(x):

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(x).lower()
    )


def find_column(
    df,
    candidates,
    required=True
):

    lookup = {
        clean_col(c): c
        for c in df.columns
    }


    for candidate in candidates:

        key = clean_col(
            candidate
        )

        if key in lookup:

            return lookup[
                key
            ]


    if required:

        raise KeyError(
            f"Kolom tidak ditemukan. Candidates = {candidates}\n"
            f"Available = {list(df.columns)}"
        )


    return None


def save_figure(
    fig,
    filename
):

    out = (
        FIG_DIR
        / filename
    )

    fig.savefig(
        out,
        dpi=600,
        bbox_inches="tight",
        facecolor="white"
    )

    plt.show()

    plt.close(
        fig
    )

    print(
        "✓ Figure:",
        out
    )


def wrap_value(
    value,
    width=22
):

    if pd.isna(value):

        return "—"


    if isinstance(
        value,
        float
    ):

        return str(value)


    return "\n".join(
        textwrap.wrap(
            str(value),
            width=width
        )
    )


def export_table_png(
    df,
    title,
    filename,
    column_width_wrap=19,
    font_size=7.5
):

    d = (
        df.copy()
    )


    # -------------------------------------------------------------
    # Convert NaN
    # -------------------------------------------------------------

    for c in d.columns:

        d[c] = d[c].apply(
            lambda x:
                "—"
                if pd.isna(x)
                else x
        )


    # -------------------------------------------------------------
    # Wrap long text
    # -------------------------------------------------------------

    display_df = (
        d.astype(str)
    )


    for c in display_df.columns:

        display_df[c] = (
            display_df[c]
            .apply(
                lambda x:
                    "\n".join(
                        textwrap.wrap(
                            x,
                            width=
                                column_width_wrap
                        )
                    )
            )
        )


    headers = [
        "\n".join(
            textwrap.wrap(
                str(c),
                width=
                    column_width_wrap
            )
        )
        for c in display_df.columns
    ]


    nrows = len(
        display_df
    )

    ncols = len(
        display_df.columns
    )


    width = max(
        8.0,
        ncols * 1.55
    )


    height = max(
        2.8,
        1.3 + nrows * 0.48
    )


    fig, ax = plt.subplots(
        figsize=(
            width,
            height
        )
    )


    ax.axis(
        "off"
    )


    table = ax.table(

        cellText=
            display_df.values,

        colLabels=
            headers,

        cellLoc=
            "center",

        colLoc=
            "center",

        loc=
            "center"
    )


    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        font_size
    )


    table.scale(
        1,
        1.6
    )


    # -------------------------------------------------------------
    # Header format
    # -------------------------------------------------------------

    for (
        row,
        col
    ), cell in table.get_celld().items():

        cell.set_edgecolor(
            "black"
        )

        cell.set_linewidth(
            0.45
        )


        if row == 0:

            cell.set_text_props(
                weight="bold"
            )


        if col == 0 and row > 0:

            cell.set_text_props(
                ha="left"
            )


    ax.set_title(
        title,
        fontweight="bold",
        pad=10
    )


    fig.tight_layout()


    out = (
        TABLE_PNG_DIR
        / filename
    )


    fig.savefig(
        out,
        dpi=600,
        bbox_inches="tight",
        facecolor="white"
    )


    plt.show()

    plt.close(
        fig
    )


    print(
        "✓ Table PNG:",
        out
    )


# =====================================================================
# 06. LOAD FINAL DATA
# =====================================================================

# Corrected Table 10
table10_raw = pd.read_excel(
    FREEZE_FILE,
    sheet_name=
        "Table10_corrected"
)


# Destination demand
demand = pd.read_excel(
    DEMAND_FILE,
    sheet_name=
        "destination_demand"
)


# Primary percentile mismatch
mismatch = pd.read_excel(
    PERCENTILE_FILE,
    sheet_name=
        "percentile_mismatch"
)


# Final robustness
robustness = pd.read_excel(
    FREEZE_FILE,
    sheet_name=
        "robustness"
)


# Stability
stability = pd.read_excel(
    FREEZE_FILE,
    sheet_name=
        "class_stability"
)


# Spatial
grid = gpd.read_file(
    GRID_FILE
)

dest_spatial = gpd.read_file(
    SPATIAL_FILE
)


# =====================================================================
# 07. STANDARDIZE GRID AECS
# =====================================================================

GRID_ID = find_column(
    grid,
    [
        "grid_id",
        "unit_id"
    ]
)


GRID_AECS = find_column(
    grid,
    [
        "AECS_HYBRID",
        "AECS",
        "agrotourism_experience_corridor_score"
    ]
)


DISTRICT_COL = find_column(
    grid,
    [
        "kecamatan",
        "district"
    ],
    required=False
)


grid[
    "grid_id_final"
] = grid[
    GRID_ID
].astype(str)


grid[
    "AECS_final"
] = pd.to_numeric(
    grid[
        GRID_AECS
    ],
    errors="coerce"
)


# =====================================================================
# 08. TABLE 10 — CORRECTED EXTERNAL VALIDATION
# =====================================================================

TABLE10 = (
    table10_raw.copy()
)


# Standardize AECS rounding
if "AECS" in TABLE10.columns:

    TABLE10[
        "AECS"
    ] = pd.to_numeric(
        TABLE10[
            "AECS"
        ],
        errors="coerce"
    ).round(
        3
    )


print()
print("=" * 100)
print("TABLE 10 — CORRECTED EXTERNAL VALIDATION")
print("=" * 100)

display(
    TABLE10
)


# =====================================================================
# 09. FIGURE 5 — CORRECTED EXTERNAL VALIDATION
# =====================================================================

dataset_col = find_column(
    TABLE10,
    [
        "Validation dataset"
    ]
)

priority_col = find_column(
    TABLE10,
    [
        "Priority class"
    ]
)

name_col = find_column(
    TABLE10,
    [
        "Name"
    ]
)

aecs_col = find_column(
    TABLE10,
    [
        "AECS"
    ]
)


priority_order = [
    "Low priority",
    "Moderate priority",
    "High priority"
]


dataset_order = [
    "Tourism village",
    "Rated destination"
]


count_table = (
    TABLE10
    .groupby(
        [
            dataset_col,
            priority_col
        ]
    )
    .size()
    .unstack(
        fill_value=0
    )
    .reindex(
        index=
            dataset_order,
        fill_value=0
    )
    .reindex(
        columns=
            priority_order,
        fill_value=0
    )
)


# Sort AECS
bars = (
    TABLE10
    .sort_values(
        aecs_col,
        ascending=True
    )
    .reset_index(
        drop=True
    )
)


priority_colors = {
    "Low priority":
        "#f6e8c3",

    "Moderate priority":
        "#f6a65a",

    "High priority":
        "#d95f45"
}


fig, axes = plt.subplots(
    1,
    2,
    figsize=(
        11.5,
        5.3
    )
)


# ---------------------------------------------------------------------
# Panel A
# ---------------------------------------------------------------------

x = np.arange(
    len(
        priority_order
    )
)

width = 0.34


for idx, dataset in enumerate(
    dataset_order
):

    vals = [
        int(
            count_table.loc[
                dataset,
                p
            ]
        )
        for p in priority_order
    ]


    offset = (
        idx - 0.5
    ) * width


    axes[0].bar(
        x + offset,
        vals,
        width=width,
        label=dataset
    )


    for xx, yy in zip(
        x + offset,
        vals
    ):

        if yy > 0:

            axes[0].text(
                xx,
                yy + 0.07,
                str(yy),
                ha="center",
                va="bottom",
                fontsize=8
            )


axes[0].set_xticks(
    x
)

axes[0].set_xticklabels(
    [
        "Low",
        "Moderate",
        "High"
    ]
)

axes[0].set_ylabel(
    "Number of validation locations"
)

axes[0].set_title(
    "a. Validation locations by priority class",
    fontweight="bold"
)

axes[0].legend(
    frameon=False
)

axes[0].spines[
    "top"
].set_visible(
    False
)

axes[0].spines[
    "right"
].set_visible(
    False
)


# ---------------------------------------------------------------------
# Panel B
# ---------------------------------------------------------------------

bar_colors = [
    priority_colors.get(
        p,
        "#bdbdbd"
    )
    for p in bars[
        priority_col
    ]
]


axes[1].barh(
    np.arange(
        len(
            bars
        )
    ),
    bars[
        aecs_col
    ],
    color=
        bar_colors,
    edgecolor=
        "black",
    linewidth=
        0.35
)


axes[1].set_yticks(
    np.arange(
        len(
            bars
        )
    )
)


axes[1].set_yticklabels(
    bars[
        name_col
    ],
    fontsize=7.5
)


axes[1].set_xlabel(
    "Agrotourism Experience Corridor Score"
)


axes[1].set_title(
    "b. AECS of external validation locations",
    fontweight="bold"
)


for i, value in enumerate(
    bars[
        aecs_col
    ]
):

    axes[1].text(
        value + 0.006,
        i,
        f"{value:.3f}",
        va="center",
        fontsize=7
    )


axes[1].spines[
    "top"
].set_visible(
    False
)

axes[1].spines[
    "right"
].set_visible(
    False
)


legend_handles = [
    Patch(
        facecolor=
            priority_colors[p],
        edgecolor=
            "black",
        label=
            p
    )
    for p in priority_order
]


axes[1].legend(
    handles=
        legend_handles,
    title=
        "Priority class",
    frameon=
        False,
    loc=
        "lower right"
)


fig.tight_layout()


save_figure(
    fig,
    "Fig_05_CORRECTED_External_Validation.png"
)


# =====================================================================
# 10. TABLE 11 — VISITOR DEMAND × AECS
# =====================================================================

# flexible names
dest_col = find_column(
    demand,
    [
        "destination"
    ]
)

years_col = find_column(
    demand,
    [
        "observed_years"
    ]
)

mean_col = find_column(
    demand,
    [
        "mean_annual_visitors"
    ]
)

grid_col = find_column(
    demand,
    [
        "grid_id"
    ]
)

district_demand_col = find_column(
    demand,
    [
        "district"
    ],
    required=False
)

aecs_demand_col = find_column(
    demand,
    [
        "AECS"
    ]
)

priority_demand_col = find_column(
    demand,
    [
        "priority_final"
    ]
)


visitor_2023_col = find_column(
    demand,
    [
        "visitors_2023"
    ],
    required=False
)

visitor_2024_col = find_column(
    demand,
    [
        "visitors_2024"
    ],
    required=False
)

visitor_2025_col = find_column(
    demand,
    [
        "visitors_2025"
    ],
    required=False
)


cols_table11 = [
    dest_col
]


if visitor_2023_col:
    cols_table11.append(
        visitor_2023_col
    )

if visitor_2024_col:
    cols_table11.append(
        visitor_2024_col
    )

if visitor_2025_col:
    cols_table11.append(
        visitor_2025_col
    )


cols_table11 += [
    years_col,
    mean_col,
    grid_col
]


if district_demand_col:
    cols_table11.append(
        district_demand_col
    )


cols_table11 += [
    aecs_demand_col,
    priority_demand_col
]


TABLE11 = (
    demand[
        cols_table11
    ]
    .copy()
)


rename11 = {

    dest_col:
        "Destination",

    years_col:
        "Observed years",

    mean_col:
        "Mean annual visitors",

    grid_col:
        "Grid ID",

    aecs_demand_col:
        "AECS",

    priority_demand_col:
        "Priority class"
}


if visitor_2023_col:

    rename11[
        visitor_2023_col
    ] = "2023"

if visitor_2024_col:

    rename11[
        visitor_2024_col
    ] = "2024"

if visitor_2025_col:

    rename11[
        visitor_2025_col
    ] = "2025"

if district_demand_col:

    rename11[
        district_demand_col
    ] = "District"


TABLE11 = (
    TABLE11
    .rename(
        columns=
            rename11
    )
)


TABLE11[
    "Mean annual visitors"
] = (
    pd.to_numeric(
        TABLE11[
            "Mean annual visitors"
        ],
        errors="coerce"
    )
    .round(0)
)


TABLE11[
    "AECS"
] = (
    pd.to_numeric(
        TABLE11[
            "AECS"
        ],
        errors="coerce"
    )
    .round(3)
)


for y in [
    "2023",
    "2024",
    "2025"
]:

    if y in TABLE11.columns:

        TABLE11[y] = (
            pd.to_numeric(
                TABLE11[y],
                errors="coerce"
            )
            .round(0)
        )


TABLE11 = (
    TABLE11
    .sort_values(
        "Mean annual visitors",
        ascending=False
    )
    .reset_index(
        drop=True
    )
)


print()
print("=" * 100)
print("TABLE 11 — OBSERVED VISITOR DEMAND AND AECS")
print("=" * 100)

display(
    TABLE11
)


# =====================================================================
# 11. TABLE 12 — SUPPLY–DEMAND MISMATCH
# =====================================================================

m_dest = find_column(
    mismatch,
    [
        "destination"
    ]
)

m_aecs = find_column(
    mismatch,
    [
        "AECS"
    ]
)

m_mean = find_column(
    mismatch,
    [
        "mean_annual_visitors"
    ]
)

m_supply = find_column(
    mismatch,
    [
        "supply_percentile"
    ]
)

m_demand = find_column(
    mismatch,
    [
        "demand_percentile"
    ]
)

m_score = find_column(
    mismatch,
    [
        "percentile_mismatch"
    ]
)

m_class = find_column(
    mismatch,
    [
        "supply_demand_class"
    ]
)


TABLE12 = (
    mismatch[
        [
            m_dest,
            m_aecs,
            m_mean,
            m_supply,
            m_demand,
            m_score,
            m_class
        ]
    ]
    .copy()
    .rename(
        columns={
            m_dest:
                "Destination",

            m_aecs:
                "AECS",

            m_mean:
                "Mean annual visitors",

            m_supply:
                "Supply percentile",

            m_demand:
                "Demand percentile",

            m_score:
                "Percentile mismatch",

            m_class:
                "Supply–demand class"
        }
    )
)


TABLE12[
    "AECS"
] = TABLE12[
    "AECS"
].round(
    3
)


TABLE12[
    "Mean annual visitors"
] = TABLE12[
    "Mean annual visitors"
].round(
    0
)


for c in [
    "Supply percentile",
    "Demand percentile",
    "Percentile mismatch"
]:

    TABLE12[c] = (
        pd.to_numeric(
            TABLE12[c],
            errors="coerce"
        )
        .round(3)
    )


TABLE12 = (
    TABLE12
    .sort_values(
        "Percentile mismatch",
        ascending=False
    )
    .reset_index(
        drop=True
    )
)


print()
print("=" * 100)
print("TABLE 12 — SUPPLY–DEMAND MISMATCH")
print("=" * 100)

display(
    TABLE12
)


# =====================================================================
# 12. FIGURE 7 — SUPPLY–DEMAND PERCENTILE MATRIX
# =====================================================================

plot_mismatch = (
    mismatch
    .copy()
    .reset_index(
        drop=True
    )
)


CLASS_MARKERS = {

    "High readiness–high demand":
        "o",

    "High readiness–lower demand":
        "^",

    "Lower readiness–high demand":
        "s",

    "Lower readiness–lower demand":
        "D"
}


# Stable numbering by mean demand descending
number_order = (
    plot_mismatch
    .sort_values(
        m_mean,
        ascending=False
    )
    .reset_index(
        drop=True
    )
)


number_lookup = {
    row[
        m_dest
    ]:
        i + 1

    for i, (_, row)
    in enumerate(
        number_order.iterrows()
    )
}


fig = plt.figure(
    figsize=(
        10.4,
        7.2
    )
)


ax = fig.add_axes(
    [
        0.09,
        0.12,
        0.62,
        0.80
    ]
)


for class_name, marker in CLASS_MARKERS.items():

    temp = plot_mismatch[
        plot_mismatch[
            m_class
        ]
        ==
        class_name
    ]


    if len(temp) == 0:
        continue


    ax.scatter(

        temp[
            m_supply
        ],

        temp[
            m_demand
        ],

        marker=
            marker,

        s=
            85,

        facecolor=
            "white",

        edgecolor=
            "black",

        linewidth=
            1.0,

        label=
            class_name,

        zorder=
            3
    )


    for _, row in temp.iterrows():

        n = number_lookup[
            row[
                m_dest
            ]
        ]


        ax.text(
            row[
                m_supply
            ],
            row[
                m_demand
            ],
            str(n),
            ha="center",
            va="center",
            fontsize=6.5,
            zorder=4
        )


# Threshold
threshold = 2 / 3


ax.axvline(
    threshold,
    linestyle="--",
    color="black",
    linewidth=0.8
)

ax.axhline(
    threshold,
    linestyle="--",
    color="black",
    linewidth=0.8
)


# Diagonal
ax.plot(
    [
        0,
        1
    ],
    [
        0,
        1
    ],
    linestyle=":",
    color="black",
    linewidth=0.8
)


ax.set_xlim(
    0,
    1
)

ax.set_ylim(
    0,
    1
)


ax.set_xlabel(
    "AECS percentile among all 1,358 analytical grids"
)

ax.set_ylabel(
    "Observed visitor-demand percentile among evaluated destinations"
)


ax.set_title(
    "Relative spatial readiness–visitor demand mismatch",
    fontweight="bold"
)


ax.grid(
    alpha=0.15
)


# ---------------------------------------------------------------------
# Destination list at right
# ---------------------------------------------------------------------

ax_text = fig.add_axes(
    [
        0.75,
        0.14,
        0.24,
        0.76
    ]
)

ax_text.axis(
    "off"
)


ax_text.text(
    0,
    1.02,
    "Destination key",
    fontsize=9,
    fontweight="bold",
    va="top"
)


y = 0.97


for i, row in number_order.iterrows():

    num = i + 1

    label = row[
        m_dest
    ]


    ax_text.text(
        0,
        y,
        f"{num}. {label}",
        fontsize=7.4,
        va="top"
    )

    y -= 0.069


# Class legend
handles = [

    Line2D(
        [0],
        [0],
        marker=
            marker,
        color=
            "none",
        markerfacecolor=
            "white",
        markeredgecolor=
            "black",
        markersize=
            7,
        label=
            class_name
    )

    for class_name, marker
    in CLASS_MARKERS.items()
]


ax.legend(
    handles=
        handles,
    loc=
        "lower left",
    frameon=
        False,
    fontsize=
        7
)


save_figure(
    fig,
    "Fig_07_Supply_Demand_Percentile_Matrix.png"
)


# =====================================================================
# 13. FIGURE 8 — SPATIAL SUPPLY–DEMAND MAP
# =====================================================================

# Standardize destination columns
sp_dest_col = find_column(
    dest_spatial,
    [
        "destination"
    ]
)


sp_class_col = find_column(
    dest_spatial,
    [
        "supply_demand_class"
    ]
)


# Ensure same CRS
if grid.crs is None:

    grid = grid.set_crs(
        "EPSG:4326"
    )


if dest_spatial.crs is None:

    dest_spatial = (
        dest_spatial
        .set_crs(
            "EPSG:4326"
        )
    )


dest_spatial = (
    dest_spatial
    .to_crs(
        grid.crs
    )
)


fig = plt.figure(
    figsize=(
        9.4,
        10.5
    )
)


ax = fig.add_axes(
    [
        0.07,
        0.06,
        0.66,
        0.90
    ]
)


# ---------------------------------------------------------------------
# AECS background
# ---------------------------------------------------------------------

grid.plot(
    column=
        "AECS_final",

    ax=
        ax,

    cmap=
        "viridis",

    legend=
        True,

    linewidth=
        0.08,

    edgecolor=
        "lightgrey",

    legend_kwds={
        "label":
            "Agrotourism Experience Corridor Score (AECS)",
        "shrink":
            0.58
    }
)


# ---------------------------------------------------------------------
# District boundaries
# ---------------------------------------------------------------------

if DISTRICT_COL:

    district_boundary = (
        grid[
            [
                DISTRICT_COL,
                "geometry"
            ]
        ]
        .dissolve(
            by=
                DISTRICT_COL
        )
    )


    district_boundary.boundary.plot(
        ax=
            ax,
        color=
            "black",
        linewidth=
            0.65
    )


# ---------------------------------------------------------------------
# Destination points
# ---------------------------------------------------------------------

for class_name, marker in CLASS_MARKERS.items():

    temp = dest_spatial[
        dest_spatial[
            sp_class_col
        ]
        ==
        class_name
    ]


    if len(temp) == 0:
        continue


    temp.plot(
        ax=
            ax,

        marker=
            marker,

        markersize=
            75,

        facecolor=
            "white",

        edgecolor=
            "black",

        linewidth=
            1.0,

        zorder=
            5
    )


# ---------------------------------------------------------------------
# Add destination numbers
# ---------------------------------------------------------------------

for _, row in dest_spatial.iterrows():

    name = row[
        sp_dest_col
    ]


    if name not in number_lookup:
        continue


    n = number_lookup[
        name
    ]


    x = row.geometry.x
    y = row.geometry.y


    ax.text(
        x,
        y,
        str(n),
        ha="center",
        va="center",
        fontsize=6,
        zorder=6
    )


ax.set_title(
    "Spatial distribution of agrotourism readiness–demand typologies",
    fontweight="bold"
)


ax.set_axis_off()


# ---------------------------------------------------------------------
# Right-side destination list
# ---------------------------------------------------------------------

ax_text = fig.add_axes(
    [
        0.75,
        0.10,
        0.24,
        0.82
    ]
)


ax_text.axis(
    "off"
)


ax_text.text(
    0,
    1.02,
    "Destination key",
    fontweight="bold",
    fontsize=9,
    va="top"
)


y = 0.975


for i, row in number_order.iterrows():

    ax_text.text(
        0,
        y,
        f"{i+1}. {row[m_dest]}",
        fontsize=7.2,
        va="top"
    )

    y -= 0.065


# ---------------------------------------------------------------------
# Typology legend
# ---------------------------------------------------------------------

legend_handles = [

    Line2D(
        [0],
        [0],
        marker=
            marker,

        color=
            "none",

        markerfacecolor=
            "white",

        markeredgecolor=
            "black",

        markersize=
            7,

        label=
            class_name
    )

    for class_name, marker
    in CLASS_MARKERS.items()
]


ax_text.legend(
    handles=
        legend_handles,
    loc=
        "lower left",
    frameon=
        False,
    fontsize=
        7
)


save_figure(
    fig,
    "Fig_08_Spatial_Supply_Demand_Map.png"
)


# =====================================================================
# 14. TABLE 13 — ROBUSTNESS
# =====================================================================

TABLE13 = (
    robustness.copy()
)


rename13 = {}


for c in TABLE13.columns:

    key = clean_col(
        c
    )


    if key == "analysis":
        rename13[c] = "Specification"

    elif key == "n":
        rename13[c] = "n"

    elif "spearmanrho" in key:
        rename13[c] = "Spearman ρ"

    elif key == "pvalue":
        rename13[c] = "p-value"

    elif "bootstrap95cilow" in key:
        rename13[c] = "Bootstrap 95% CI low"

    elif "bootstrap95cihigh" in key:
        rename13[c] = "Bootstrap 95% CI high"


TABLE13 = (
    TABLE13
    .rename(
        columns=
            rename13
    )
)


for c in [
    "Spearman ρ",
    "p-value",
    "Bootstrap 95% CI low",
    "Bootstrap 95% CI high"
]:

    if c in TABLE13.columns:

        TABLE13[c] = (
            pd.to_numeric(
                TABLE13[c],
                errors="coerce"
            )
            .round(3)
        )


print()
print("=" * 100)
print("TABLE 13 — DEMAND-SIDE ROBUSTNESS")
print("=" * 100)

display(
    TABLE13
)


# =====================================================================
# 15. FIGURE S1 — ROBUSTNESS FOREST PLOT
# =====================================================================

rho_col = find_column(
    TABLE13,
    [
        "Spearman ρ"
    ]
)

low_col = find_column(
    TABLE13,
    [
        "Bootstrap 95% CI low"
    ]
)

high_col = find_column(
    TABLE13,
    [
        "Bootstrap 95% CI high"
    ]
)

spec_col = find_column(
    TABLE13,
    [
        "Specification"
    ]
)


plot_robust = (
    TABLE13
    .copy()
    .iloc[::-1]
    .reset_index(
        drop=True
    )
)


rho = (
    plot_robust[
        rho_col
    ].to_numpy(
        dtype=float
    )
)


low = (
    plot_robust[
        low_col
    ].to_numpy(
        dtype=float
    )
)


high = (
    plot_robust[
        high_col
    ].to_numpy(
        dtype=float
    )
)


lower_err = (
    rho - low
)

upper_err = (
    high - rho
)


fig, ax = plt.subplots(
    figsize=(
        8.5,
        4.2
    )
)


y = np.arange(
    len(
        plot_robust
    )
)


ax.errorbar(
    rho,
    y,
    xerr=[
        lower_err,
        upper_err
    ],
    fmt="o",
    capsize=4,
    color="black",
    ecolor="black",
    markersize=5
)


ax.axvline(
    0,
    linestyle="--",
    linewidth=0.8,
    color="black"
)


ax.set_yticks(
    y
)


ax.set_yticklabels(
    plot_robust[
        spec_col
    ]
)


ax.set_xlabel(
    "Spearman rank correlation (ρ) with bootstrap 95% CI"
)


ax.set_title(
    "Robustness of the AECS–visitor demand association",
    fontweight="bold"
)


ax.set_xlim(
    -1,
    1
)


ax.spines[
    "top"
].set_visible(
    False
)

ax.spines[
    "right"
].set_visible(
    False
)


save_figure(
    fig,
    "Fig_S1_Demand_Robustness_ForestPlot.png"
)


# =====================================================================
# 16. TABLE S1 — TYPOLOGY STABILITY
# =====================================================================

TABLE_S1 = (
    stability.copy()
)


rename_s1 = {}


for c in TABLE_S1.columns:

    key = clean_col(
        c
    )


    if key == "destination":

        rename_s1[c] = (
            "Destination"
        )

    elif "reestimatednonmanualclass" in key:

        rename_s1[c] = (
            "Re-estimated non-manual class"
        )

    elif "primaryclass" in key:

        rename_s1[c] = (
            "Primary class"
        )

    elif key == "stable":

        rename_s1[c] = (
            "Stable"
        )


TABLE_S1 = TABLE_S1.rename(
    columns=
        rename_s1
)


print()
print("=" * 100)
print("TABLE S1 — TYPOLOGY STABILITY")
print("=" * 100)

display(
    TABLE_S1
)


# =====================================================================
# 17. SANITY CHECKS
# =====================================================================

print()
print("=" * 100)
print("SANITY CHECKS")
print("=" * 100)


# Table 10
counts = (
    TABLE10[
        priority_col
    ]
    .value_counts()
)


print(
    "Table 10:"
)

print(
    "High =",
    counts.get(
        "High priority",
        0
    )
)

print(
    "Moderate =",
    counts.get(
        "Moderate priority",
        0
    )
)

print(
    "Low =",
    counts.get(
        "Low priority",
        0
    )
)


assert (
    counts.get(
        "High priority",
        0
    )
    ==
    7
)


assert (
    counts.get(
        "Moderate priority",
        0
    )
    ==
    1
)


assert (
    counts.get(
        "Low priority",
        0
    )
    ==
    3
)


assert len(
    TABLE11
) == 12


assert len(
    TABLE12
) == 12


assert len(
    TABLE13
) == 3


# Stability
stable_col = find_column(
    TABLE_S1,
    [
        "Stable"
    ]
)


stable_count = (
    TABLE_S1[
        stable_col
    ]
    .astype(bool)
    .sum()
)


stability_rate = (
    stable_count
    /
    len(
        TABLE_S1
    )
)


print()
print(
    "Typology stability:",
    f"{stable_count}/{len(TABLE_S1)} "
    f"({100*stability_rate:.1f}%)"
)


assert (
    stable_count == 9
)


print()
print(
    "✓ Semua sanity checks PASS"
)


# =====================================================================
# 18. EXPORT TABLE CSV
# =====================================================================

TABLE10.to_csv(
    TABLE_DIR
    / "Table_10_Corrected_External_Validation.csv",
    index=False
)

TABLE11.to_csv(
    TABLE_DIR
    / "Table_11_Visitor_Demand_AECS.csv",
    index=False
)

TABLE12.to_csv(
    TABLE_DIR
    / "Table_12_Supply_Demand_Mismatch.csv",
    index=False
)

TABLE13.to_csv(
    TABLE_DIR
    / "Table_13_Demand_Robustness.csv",
    index=False
)

TABLE_S1.to_csv(
    TABLE_DIR
    / "Table_S1_Typology_Stability.csv",
    index=False
)


# =====================================================================
# 19. EXPORT MASTER EXCEL
# =====================================================================

MASTER_XLSX = (
    TABLE_DIR
    / "MANUSCRIPT_TABLES_FINAL.xlsx"
)


with pd.ExcelWriter(
    MASTER_XLSX,
    engine=
        "openpyxl"
) as writer:

    TABLE10.to_excel(
        writer,
        sheet_name=
            "Table10_validation",
        index=False
    )

    TABLE11.to_excel(
        writer,
        sheet_name=
            "Table11_demand",
        index=False
    )

    TABLE12.to_excel(
        writer,
        sheet_name=
            "Table12_mismatch",
        index=False
    )

    TABLE13.to_excel(
        writer,
        sheet_name=
            "Table13_robustness",
        index=False
    )

    TABLE_S1.to_excel(
        writer,
        sheet_name=
            "TableS1_stability",
        index=False
    )


print()
print(
    "✓ Master Excel:",
    MASTER_XLSX
)


# =====================================================================
# 20. EXPORT TABLE PNG 600 DPI
# =====================================================================

export_table_png(

    TABLE10,

    (
        "Table 10. External validation results "
        "of agrotourism corridor prioritization"
    ),

    "Table_10_Corrected_External_Validation.png",

    column_width_wrap=
        18,

    font_size=
        7.2
)


export_table_png(

    TABLE11,

    (
        "Table 11. Observed visitor demand "
        "and spatial readiness of evaluated destinations"
    ),

    "Table_11_Visitor_Demand_AECS.png",

    column_width_wrap=
        17,

    font_size=
        6.8
)


export_table_png(

    TABLE12,

    (
        "Table 12. Percentile-based spatial "
        "supply–demand mismatch"
    ),

    "Table_12_Supply_Demand_Mismatch.png",

    column_width_wrap=
        19,

    font_size=
        6.8
)


export_table_png(

    TABLE13,

    (
        "Table 13. Robustness of the association "
        "between AECS and observed visitor demand"
    ),

    "Table_13_Demand_Robustness.png",

    column_width_wrap=
        23,

    font_size=
        8.0
)


export_table_png(

    TABLE_S1,

    (
        "Table S1. Stability of supply–demand "
        "typology under independent non-manual re-estimation"
    ),

    "Table_S1_Typology_Stability.png",

    column_width_wrap=
        25,

    font_size=
        7.2
)


# =====================================================================
# 21. CAPTIONS + PLACEMENT FILE
# =====================================================================

captions = """
============================================================
FINAL MANUSCRIPT PLACEMENT
============================================================

SECTION 4.5
External validation using tourism villages and rated destinations

Insert:
Table 10. External validation results of agrotourism corridor prioritization

Then insert:
Fig. 5. External validation of agrotourism corridor
prioritization under the Hybrid AECS. Panel a shows the
distribution of tourism village and rated-destination validation
locations across low-, moderate-, and high-priority classes.
Panel b compares the AECS values of individual validation
locations. The corrected validation contains seven high-priority,
one moderate-priority, and three low-priority locations.


============================================================

SECTION 4.6
Observed Visitor Demand and Spatial Readiness

Place Table 11 AFTER the first paragraph describing Diana,
Pulau Dutungan, Pantai Laguna, Pulau Pannikiang, and PekkaE.

Table 11. Observed visitor demand and spatial readiness
of evaluated destinations.

After Table 11 continue with the paragraph beginning:
"The spatial-readiness rankings did not closely follow..."


============================================================

SECTION 4.7
Component profile of top-priority grids

KEEP THIS SECTION AS IT IS.

Keep existing Fig. 6.


============================================================

SECTION 4.8
Spatial Supply–Demand Mismatches

Insert a NEW Section 4.8 after current Section 4.7.

Recommended order:

Paragraph 1:
Explain why correlation alone masks destination-specific mismatch.

Insert Fig. 7.

Fig. 7. Relative spatial readiness and observed visitor demand
among evaluated tourism destinations. Spatial readiness is
expressed as the empirical AECS percentile relative to all
1,358 analytical grids, whereas demand is expressed as the
percentile rank of mean annual visitor observations among
evaluated destinations. Dashed lines indicate the upper-third
threshold used to distinguish high and lower readiness/demand
categories. The diagonal represents approximate percentile
alignment.

Then discuss:
- Pulau Dutungan
- Diana Water Park
- Bukit Maddo
- Celebes Canyon
- Pantai Ujung Batu
- Pantai Laguna

Insert Table 12.

Table 12. Percentile-based spatial supply–demand mismatch
of evaluated tourism destinations.

Then insert Fig. 8.

Fig. 8. Spatial distribution of agrotourism readiness–demand
typologies in Barru Regency. Destination symbols distinguish
high readiness–high demand, high readiness–lower demand,
lower readiness–high demand, and lower readiness–lower demand
conditions against the continuous Hybrid AECS surface.


============================================================

SECTION 4.9
Robustness of the Demand-Side Diagnosis

Insert Table 13 after the first paragraph.

Table 13. Robustness of the association between AECS and
observed visitor demand under progressively stricter
spatial-confidence specifications.

Discuss:
Primary n=12
Non-manual n=10
Strict point-within-grid n=7
Typology stability = 9/10 = 90%

Do NOT put Fig. S1 in main manuscript unless journal page
space permits.

Supplementary:
Fig. S1. Robustness of the AECS–visitor demand association.
Points show Spearman rank correlations and horizontal bars
show bootstrap 95% confidence intervals.

Supplementary:
Table S1. Stability of supply–demand typology under
independent non-manual re-estimation.


============================================================

SECTION 4.10
Synthesis: from spatial diagnosis to planning strategy

Rename the CURRENT Section 4.8 to 4.10.

============================================================
"""


CAPTION_FILE = (
    OUT_DIR
    / "FIGURE_TABLE_CAPTIONS_AND_PLACEMENT.txt"
)


with open(
    CAPTION_FILE,
    "w",
    encoding=
        "utf-8"
) as f:

    f.write(
        captions
    )


# =====================================================================
# 22. FINAL OUTPUT
# =====================================================================

print()
print("=" * 100)
print("✓ ALL FINAL FIGURES AND TABLES CREATED")
print("=" * 100)

print()
print(
    "Figures 600 dpi:"
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
    "Table PNG 600 dpi:"
)
print(
    TABLE_PNG_DIR
)

print()
print(
    "Placement + captions:"
)
print(
    CAPTION_FILE
)

print()
print("=" * 100)
print("EXPECTED MAIN MANUSCRIPT OUTPUTS")
print("=" * 100)

print(
    "Fig. 5 corrected external validation"
)

print(
    "Table 10 corrected external validation"
)

print(
    "Table 11 observed visitor demand × AECS"
)

print(
    "Fig. 7 percentile supply–demand matrix"
)

print(
    "Table 12 supply–demand mismatch"
)

print(
    "Fig. 8 spatial supply–demand typology"
)

print(
    "Table 13 demand-side robustness"
)

print(
    "Fig. S1 + Table S1 = Supplementary"
)