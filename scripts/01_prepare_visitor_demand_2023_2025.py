"""
Prepare and harmonize observed visitor demand for 2023–2025.

Clean public version derived from the final manuscript-relevant notebook cell 63.
Personal Google Drive paths and notebook-only execution assumptions were removed.
Analytical logic is retained where it is verifiable from the uploaded notebook.
"""

# =====================================================================
# =====================================================================
# BARRU AGROTOURISM Q1 EXTENSION
# MULTI-YEAR OBSERVED VISITOR DEMAND 2023–2025
#
# LANJUTAN NOTEBOOK AGROTOURISM BARRU SEBELUMNYA
#
# SCRIPT INI:
# 01. Upload langsung Excel 2023, 2024, 2025 satu per satu
# 02. Membaca struktur asli masing-masing workbook
# 03. Audit row-total dan annual-total
# 04. Harmonisasi nama destinasi lintas tahun
# 05. Membentuk Destination × Month × Year panel
# 06. Wisman + Wisnus + total visitors
# 07. Analisis tahunan 2023–2025
# 08. Seasonality analysis
# 09. Longitudinal change
# 10. Reconciliation dengan rekap Dinas
# 11. Menggunakan grid AECS dari analisis sebelumnya
# 12. Spatial join destination → AECS
# 13. Multi-year observed demand validation
# 14. Spearman + bootstrap CI
# 15. ALI/TAI/ASI/RNAI/EQI vs observed demand
# 16. Supply–demand mismatch
# 17. Publication-ready figures 600 dpi
# 18. Export Excel, CSV, GeoJSON
#
# CATATAN METODOLOGIS:
# Visitor data TIDAK dimasukkan ke formula AECS.
# AECS = spatial supply/readiness
# Visitor = observed/revealed tourism demand
# =====================================================================
# =====================================================================


# =====================================================================
# 00. INSTALL LIBRARY
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

from scipy.stats import spearmanr
from IPython.display import display


# =====================================================================
# 01. BASIC SETTINGS
# =====================================================================

GEOG_CRS = "EPSG:4326"
METRIC_CRS = "EPSG:32750"   # UTM Zone 50S, Sulawesi Selatan

MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

MONTH_NUM = {
    month: i + 1
    for i, month in enumerate(MONTHS)
}


# =====================================================================
# 02. REPOSITORY PATHS AND VISITOR INPUTS
# =====================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(
    os.environ.get("AECS_PROJECT_ROOT", SCRIPT_DIR.parent)
).resolve()

RAW_VISITOR_DIR = REPO_ROOT / "data" / "raw" / "visitor_records"

OUT_DIR_NEW = REPO_ROOT / "outputs" / "01_visitor_demand"
FIG_DIR_NEW = OUT_DIR_NEW / "figures"
TABLE_DIR_NEW = OUT_DIR_NEW / "tables"

for p in [RAW_VISITOR_DIR, OUT_DIR_NEW, FIG_DIR_NEW, TABLE_DIR_NEW]:
    p.mkdir(parents=True, exist_ok=True)


def find_visitor_file(year):
    """Find one Excel workbook for the requested year."""
    preferred = [
        RAW_VISITOR_DIR / f"visitor_{year}.xlsx",
        RAW_VISITOR_DIR / f"visitors_{year}.xlsx",
        RAW_VISITOR_DIR / f"visitor_demand_{year}.xlsx",
    ]
    for path in preferred:
        if path.exists():
            return path

    candidates = sorted(
        p for p in RAW_VISITOR_DIR.glob("*.xlsx")
        if str(year) in p.name
    )

    if len(candidates) == 1:
        return candidates[0]

    if len(candidates) == 0:
        raise FileNotFoundError(
            f"No Excel file for {year} was found in {RAW_VISITOR_DIR}. "
            f"Place one workbook there and include {year} in its filename."
        )

    raise RuntimeError(
        f"More than one workbook matches {year}: "
        + ", ".join(p.name for p in candidates)
    )


FILES = {year: find_visitor_file(year) for year in (2023, 2024, 2025)}

print("=" * 78)
print("VISITOR INPUT FILES")
print("=" * 78)
for year, path in FILES.items():
    print(year, "->", path)

print("Repository root:", REPO_ROOT)
print("Output:", OUT_DIR_NEW)


# =====================================================================
# 04. HELPER FUNCTIONS
# =====================================================================

def num0(x):
    """
    Mengubah cell angka menjadi numeric.
    '-' / blank / NaN -> 0 untuk perhitungan row detail.

    CATATAN:
    Absennya suatu DESTINASI pada suatu tahun tetap tidak
    dibuat sebagai zero-year observation.
    """

    if pd.isna(x):
        return 0.0

    if isinstance(
        x,
        (
            int,
            float,
            np.integer,
            np.floating
        )
    ):
        return float(x)

    s = (
        str(x)
        .strip()
        .replace(",", "")
    )

    if s in [
        "",
        "-",
        "–",
        "—",
        "- "
    ]:
        return 0.0

    try:
        return float(s)

    except:
        return 0.0


def normalize_text(x):

    if pd.isna(x):
        return ""

    s = str(x).strip().lower()

    s = (
        s.replace("’", "'")
        .replace("`", "'")
    )

    s = re.sub(
        r"\s+",
        " ",
        s
    )

    return s.strip()


def name_key(x):

    s = normalize_text(x)

    s = re.sub(
        r"[^a-z0-9'\s/-]",
        "",
        s
    )

    s = re.sub(
        r"\s+",
        " ",
        s
    )

    return s.strip()


def minmax(series):

    s = pd.to_numeric(
        series,
        errors="coerce"
    )

    if s.notna().sum() == 0:

        return pd.Series(
            np.nan,
            index=series.index
        )

    mn = s.min()
    mx = s.max()

    if mx == mn:

        return pd.Series(
            0.5,
            index=series.index
        )

    return (
        (s - mn)
        /
        (mx - mn)
    )


def safe_pct_change(new, old):

    if (
        pd.isna(new)
        or pd.isna(old)
        or old <= 0
    ):
        return np.nan

    return (
        (new - old)
        /
        old
        * 100
    )


def save_fig(filename):

    output = (
        FIG_DIR_NEW
        / filename
    )

    plt.tight_layout()

    plt.savefig(
        output,
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

    print(
        "Saved:",
        output
    )


def find_col(
    df,
    candidates,
    required=True
):

    lower_map = {
        str(c).lower(): c
        for c in df.columns
    }

    for candidate in candidates:

        if candidate.lower() in lower_map:

            return lower_map[
                candidate.lower()
            ]

    if required:

        raise ValueError(
            "Kolom tidak ditemukan.\n"
            f"Kandidat: {candidates}\n"
            f"Tersedia: {list(df.columns)}"
        )

    return None


# =====================================================================
# 05. CEK STRUKTUR WORKBOOK
# =====================================================================

print()
print("=" * 78)
print("STRUKTUR WORKBOOK")
print("=" * 78)


for year in [
    2023,
    2024,
    2025
]:

    xls = pd.ExcelFile(
        FILES[year]
    )

    print()
    print(
        year,
        ":",
        xls.sheet_names
    )


# =====================================================================
# 06. PARSER 2023 & 2024
#
# CATATAN:
# Hanya sheet utama:
# - WISNUS
# - WISMAN
#
# Sheet WISNUS (2), WISMAN (2), DESA WISATA pada 2024
# adalah representasi/format alternatif, sehingga TIDAK
# dijumlahkan lagi ke sheet utama agar tidak terjadi
# double counting.
# =====================================================================

def parse_2023_2024(
    filepath,
    year
):

    records = []
    row_audit = []

    source_sheets = [
        (
            "WISNUS",
            "wisnus"
        ),
        (
            "WISMAN",
            "wisman"
        )
    ]

    available = (
        pd.ExcelFile(
            filepath
        )
        .sheet_names
    )

    for sheet_name, visitor_type in source_sheets:

        if sheet_name not in available:

            raise ValueError(
                f"Sheet {sheet_name} tidak ditemukan "
                f"dalam workbook {year}."
            )

        raw = pd.read_excel(
            filepath,
            sheet_name=sheet_name,
            header=None
        )

        header_row = None

        for r in range(
            min(
                20,
                len(raw)
            )
        ):

            vals = [
                normalize_text(v)
                for v in raw.iloc[r].tolist()
            ]

            has_destination = any(
                "daya tarik wisata" in v
                for v in vals
            )

            has_month = any(
                (
                    "januari" in v
                    or v == "jan"
                )
                for v in vals
            )

            if (
                has_destination
                and has_month
            ):

                header_row = r
                break

        if header_row is None:

            raise ValueError(
                f"Header tidak ditemukan "
                f"pada {year} / {sheet_name}"
            )

        for r in range(
            header_row + 1,
            len(raw)
        ):

            no = (
                raw.iat[r, 0]
                if raw.shape[1] > 0
                else None
            )

            destination = (
                raw.iat[r, 1]
                if raw.shape[1] > 1
                else None
            )

            if pd.isna(destination):
                continue

            destination = (
                str(destination)
                .strip()
            )

            # hanya baris destinasi bernomor
            is_numbered = (
                isinstance(
                    no,
                    (
                        int,
                        float,
                        np.integer,
                        np.floating
                    )
                )
                and not pd.isna(no)
            )

            if not is_numbered:
                continue

            if normalize_text(
                destination
            ) == "jumlah":
                continue

            monthly_values = []

            # Januari = col 4
            # ...
            # Desember = col 15
            for c in range(
                4,
                16
            ):

                value = (
                    num0(
                        raw.iat[r, c]
                    )
                    if c < raw.shape[1]
                    else 0
                )

                monthly_values.append(
                    value
                )

            computed_total = sum(
                monthly_values
            )

            source_total = (
                num0(
                    raw.iat[r, 16]
                )
                if raw.shape[1] > 16
                else np.nan
            )

            row_audit.append(
                {
                    "year":
                        year,

                    "source_sheet":
                        sheet_name,

                    "source_row":
                        r + 1,

                    "destination_raw":
                        destination,

                    "visitor_type":
                        visitor_type,

                    "computed_month_sum":
                        computed_total,

                    "source_annual_total":
                        source_total,

                    "difference":
                        computed_total
                        - source_total
                }
            )

            for month, value in zip(
                MONTHS,
                monthly_values
            ):

                records.append(
                    {
                        "year":
                            year,

                        "destination_raw":
                            destination,

                        "parent_village":
                            "",

                        "source_section":
                            "REGISTERED_DESTINATION",

                        "source_sheet":
                            sheet_name,

                        "source_row":
                            r + 1,

                        "month":
                            month,

                        "visitor_type":
                            visitor_type,

                        "visitors":
                            value
                    }
                )

    return (
        pd.DataFrame(
            records
        ),
        pd.DataFrame(
            row_audit
        )
    )


# =====================================================================
# 07. PARSER 2025
#
# Struktur:
# destination
#   - Wisman
#   - Wisnus
#
# Bulanan:
# Lk + Pr
#
# Bagian:
# DTW
# DESA WISATA
# =====================================================================

def find_2025_sheet(filepath):

    sheets = (
        pd.ExcelFile(
            filepath
        )
        .sheet_names
    )

    preferred = (
        "DATA KUNJUNGAN TAHUNAN"
    )

    if preferred in sheets:

        return preferred

    for sheet in sheets:

        if (
            "kunjungan"
            in sheet.lower()
            and
            "tahunan"
            in sheet.lower()
        ):

            return sheet

    raise ValueError(
        "Sheet DATA KUNJUNGAN TAHUNAN "
        "tidak ditemukan."
    )


def clean_child_label(x):

    s = str(x).strip()

    s = re.sub(
        r"^[A-Za-z]\.\s*",
        "",
        s
    )

    return s.strip()


def parse_2025(filepath):

    sheet_name = (
        find_2025_sheet(
            filepath
        )
    )

    raw = pd.read_excel(
        filepath,
        sheet_name=sheet_name,
        header=None
    )

    header_row = None

    for r in range(
        min(
            30,
            len(raw)
        )
    ):

        vals = [
            normalize_text(v)
            for v in raw.iloc[r].tolist()
        ]

        has_destination = any(
            "daya tarik wisata" in v
            for v in vals
        )

        has_january = any(
            "januari" in v
            for v in vals
        )

        has_december = any(
            "desember" in v
            for v in vals
        )

        if (
            has_destination
            and has_january
            and has_december
        ):

            header_row = r
            break

    if header_row is None:

        raise ValueError(
            "Header data 2025 "
            "tidak ditemukan."
        )

    section = "DTW"
    parent_village = ""
    current_destination = None

    records = []
    row_audit = []

    for r in range(
        header_row + 1,
        len(raw)
    ):

        no = (
            raw.iat[r, 0]
            if raw.shape[1] > 0
            else None
        )

        label = (
            raw.iat[r, 1]
            if raw.shape[1] > 1
            else None
        )

        if pd.isna(label):
            continue

        label = str(label).strip()
        low = normalize_text(label)

        # --------------------------------
        # Section desa wisata
        # --------------------------------

        if low == "desa wisata":

            section = (
                "DESA_WISATA"
            )

            parent_village = ""
            current_destination = None

            continue

        # --------------------------------
        # Abaikan subtotal
        # --------------------------------

        if (
            low.startswith(
                "total kunj."
            )
            or low == "jumlah"
            or low == "ub"
        ):

            continue

        # --------------------------------
        # Wisman / Wisnus row
        # --------------------------------

        if (
            low.startswith(
                "- wisman"
            )
            or
            low.startswith(
                "- wisnus"
            )
        ):

            if current_destination is None:
                continue

            visitor_type = (
                "wisman"
                if "wisman" in low
                else "wisnus"
            )

            monthly_values = []

            # Jan Lk/Pr = 4,5
            # Feb = 6,7
            # ...
            # Dec = 26,27

            for k in range(12):

                col_lk = (
                    4
                    + 2 * k
                )

                col_pr = (
                    col_lk
                    + 1
                )

                lk = (
                    num0(
                        raw.iat[
                            r,
                            col_lk
                        ]
                    )
                    if col_lk
                    < raw.shape[1]
                    else 0
                )

                pr = (
                    num0(
                        raw.iat[
                            r,
                            col_pr
                        ]
                    )
                    if col_pr
                    < raw.shape[1]
                    else 0
                )

                monthly_values.append(
                    lk + pr
                )

            computed_total = sum(
                monthly_values
            )

            # TOTAL tahunan pada col 30
            source_total = (
                num0(
                    raw.iat[r, 30]
                )
                if raw.shape[1] > 30
                else np.nan
            )

            row_audit.append(
                {
                    "year":
                        2025,

                    "source_sheet":
                        sheet_name,

                    "source_section":
                        section,

                    "source_row":
                        r + 1,

                    "parent_village":
                        parent_village,

                    "destination_raw":
                        current_destination,

                    "visitor_type":
                        visitor_type,

                    "computed_month_sum":
                        computed_total,

                    "source_annual_total":
                        source_total,

                    "difference":
                        computed_total
                        - source_total
                }
            )

            for month, value in zip(
                MONTHS,
                monthly_values
            ):

                records.append(
                    {
                        "year":
                            2025,

                        "destination_raw":
                            current_destination,

                        "parent_village":
                            parent_village,

                        "source_section":
                            section,

                        "source_sheet":
                            sheet_name,

                        "source_row":
                            r + 1,

                        "month":
                            month,

                        "visitor_type":
                            visitor_type,

                        "visitors":
                            value
                    }
                )

            continue

        # --------------------------------
        # Apakah nomor destinasi/village?
        # --------------------------------

        is_numbered = (
            isinstance(
                no,
                (
                    int,
                    float,
                    np.integer,
                    np.floating
                )
            )
            and
            not pd.isna(no)
        )

        # --------------------------------
        # DTW
        # --------------------------------

        if section == "DTW":

            if is_numbered:

                current_destination = (
                    label
                )

                parent_village = ""

        # --------------------------------
        # DESA WISATA
        # --------------------------------

        else:

            if (
                is_numbered
                and
                low.startswith(
                    "desa wisata"
                )
            ):

                parent_village = (
                    label
                )

                current_destination = None

            elif re.match(
                r"^[A-Za-z]\.\s*",
                label
            ):

                current_destination = (
                    clean_child_label(
                        label
                    )
                )

            elif (
                is_numbered
                and
                not low.startswith(
                    "desa wisata"
                )
            ):

                current_destination = (
                    label
                )

    return (
        pd.DataFrame(
            records
        ),
        pd.DataFrame(
            row_audit
        ),
        raw
    )


# =====================================================================
# 08. PARSE SEMUA DATA
# =====================================================================

raw_2023, audit_2023 = (
    parse_2023_2024(
        FILES[2023],
        2023
    )
)

raw_2024, audit_2024 = (
    parse_2023_2024(
        FILES[2024],
        2024
    )
)

raw_2025, audit_2025, source_2025 = (
    parse_2025(
        FILES[2025]
    )
)


print()
print("=" * 78)
print("PARSING SELESAI")
print("=" * 78)

print(
    "2023 records:",
    len(raw_2023)
)

print(
    "2024 records:",
    len(raw_2024)
)

print(
    "2025 records:",
    len(raw_2025)
)


# =====================================================================
# 09. HARMONISASI NAMA DESTINASI
# =====================================================================

ALIASES = {

    "ujung batu":
        "Pantai Ujung Batu",

    "pantai ujung batu":
        "Pantai Ujung Batu",

    "diana waterpark":
        "Diana Water Park",

    "diana water park":
        "Diana Water Park",

    "pekkae ecolodge":
        "PekkaE Ecolodge",

    "pekkae ecolodge ":
        "PekkaE Ecolodge",

    # Pada dataset tahun berikutnya PekkaE tercatat
    # di bawah Desa Wisata Kading
    "desa wisata kading":
        "PekkaE Ecolodge",

    "lappalaona":
        "Lappa Laona",

    "lappa laona":
        "Lappa Laona",

    "danau pakue":
        "Danau Paku'e",

    "danau paku'e":
        "Danau Paku'e",

    "bola batue":
        "Goa Bola Batue",

    "goa bola batue":
        "Goa Bola Batue",

    "pulau pannikiang":
        "Pulau Pannikiang",

    "pulau dutungan":
        "Pulau Dutungan",

    "bukit maddo":
        "Bukit Maddo",

    "pantai laguna":
        "Pantai Laguna",

    "pantai padongko":
        "Pantai Padongko",

    "celebes canyon":
        "Celebes Canyon",

    "kampung nelayan mate'ne":
        "Kampung Nelayan Mate'ne",

    "embung paccekke":
        "Embung Paccekke",

    "bujung mattimboe":
        "Bujung Mattimboe",

    "bujung makkatoangnge":
        "Bujung Makkatoangnge",

    "pesantren alam indonesia":
        "Pesantren Alam Indonesia",

    "gunung kappire":
        "Gunung Kappire",

    "air terjun to magellie":
        "Air Terjun To Magellie",

    "air terjun baruttungnge":
        "Air Terjun Baruttungnge"
}


def canonical_destination(
    raw_name,
    parent_village=""
):

    raw_key = name_key(
        raw_name
    )

    parent_key = name_key(
        parent_village
    )

    # Desa Wisata Paccekke
    if (
        raw_key == "embung"
        and
        "paccekke"
        in parent_key
    ):

        return (
            "Embung Paccekke"
        )

    # Desa Wisata Pao-pao
    if (
        raw_key == "pantai laguna"
        and
        "pao-pao"
        in parent_key
    ):

        return (
            "Pantai Laguna"
        )

    # Desa Wisata Harapan
    if (
        raw_key == "lappa laona"
        and
        "harapan"
        in parent_key
    ):

        return (
            "Lappa Laona"
        )

    # Desa Wisata Nepo
    if (
        raw_key == "danau pakue"
        and
        "nepo"
        in parent_key
    ):

        return (
            "Danau Paku'e"
        )

    if (
        raw_key == "bola batue"
        and
        "nepo"
        in parent_key
    ):

        return (
            "Goa Bola Batue"
        )

    # Desa Wisata Kading
    if (
        raw_key == "pekkae ecolodge"
        and
        "kading"
        in parent_key
    ):

        return (
            "PekkaE Ecolodge"
        )

    if raw_key in ALIASES:

        return (
            ALIASES[
                raw_key
            ]
        )

    # title form tanpa merusak apostrophe
    return (
        re.sub(
            r"\s+",
            " ",
            str(raw_name)
            .strip()
        )
    )


# =====================================================================
# 10. COMBINE RAW TYPE-LONG DATA
# =====================================================================

visitor_type_long = pd.concat(
    [
        raw_2023,
        raw_2024,
        raw_2025
    ],
    ignore_index=True,
    sort=False
)


visitor_type_long[
    "destination"
] = visitor_type_long.apply(
    lambda row:
        canonical_destination(
            row[
                "destination_raw"
            ],
            row.get(
                "parent_village",
                ""
            )
        ),
    axis=1
)


visitor_type_long[
    "month_num"
] = visitor_type_long[
    "month"
].map(
    MONTH_NUM
)


visitor_type_long[
    "date"
] = pd.to_datetime(
    dict(
        year=
            visitor_type_long[
                "year"
            ],

        month=
            visitor_type_long[
                "month_num"
            ],

        day=1
    )
)


# =====================================================================
# 11. REVIEW HARMONISASI
# =====================================================================

name_harmonization = (
    visitor_type_long[
        [
            "year",
            "destination_raw",
            "parent_village",
            "source_section",
            "destination"
        ]
    ]
    .drop_duplicates()
    .sort_values(
        [
            "destination",
            "year"
        ]
    )
    .reset_index(
        drop=True
    )
)


print()
print("=" * 78)
print("HARMONISASI NAMA")
print("=" * 78)

display(
    name_harmonization
)


# =====================================================================
# 12. MASTER MONTHLY PANEL
#
# Destination × Month × Year
# =====================================================================

visitor_monthly = (
    visitor_type_long
    .pivot_table(
        index=[
            "year",
            "destination",
            "month",
            "month_num",
            "date"
        ],

        columns=
            "visitor_type",

        values=
            "visitors",

        aggfunc=
            "sum",

        fill_value=0
    )
    .reset_index()
)


visitor_monthly.columns.name = None


for c in [
    "wisman",
    "wisnus"
]:

    if c not in visitor_monthly.columns:

        visitor_monthly[
            c
        ] = 0.0


visitor_monthly[
    "total_visitors"
] = (
    visitor_monthly[
        "wisman"
    ]
    +
    visitor_monthly[
        "wisnus"
    ]
)


visitor_monthly = (
    visitor_monthly
    .sort_values(
        [
            "year",
            "destination",
            "month_num"
        ]
    )
    .reset_index(
        drop=True
    )
)


print()
print("=" * 78)
print("MASTER MONTHLY PANEL")
print("=" * 78)

display(
    visitor_monthly.head(40)
)


# =====================================================================
# 13. ANNUAL DESTINATION DEMAND
# =====================================================================

visitor_annual = (
    visitor_monthly
    .groupby(
        [
            "year",
            "destination"
        ],
        as_index=False
    )
    .agg(
        wisman=(
            "wisman",
            "sum"
        ),

        wisnus=(
            "wisnus",
            "sum"
        ),

        total_visitors=(
            "total_visitors",
            "sum"
        )
    )
)


visitor_annual[
    "log_visitors"
] = np.log1p(
    visitor_annual[
        "total_visitors"
    ]
)


visitor_annual[
    "wisman_share_pct"
] = np.where(
    visitor_annual[
        "total_visitors"
    ] > 0,

    visitor_annual[
        "wisman"
    ]
    /
    visitor_annual[
        "total_visitors"
    ]
    * 100,

    0
)


print()
print("=" * 78)
print("ANNUAL DESTINATION DEMAND")
print("=" * 78)

display(
    visitor_annual
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
)


# =====================================================================
# 14. DETAIL TOTAL PER TAHUN
# =====================================================================

detail_year_total = (
    visitor_annual
    .groupby(
        "year",
        as_index=False
    )
    .agg(
        detail_wisman=(
            "wisman",
            "sum"
        ),

        detail_wisnus=(
            "wisnus",
            "sum"
        ),

        detail_total=(
            "total_visitors",
            "sum"
        )
    )
)


print()
print("=" * 78)
print("TOTAL HASIL PENJUMLAHAN DETAIL")
print("=" * 78)

display(
    detail_year_total
)


# =====================================================================
# 15. ROW-LEVEL AUDIT
# =====================================================================

row_audit = pd.concat(
    [
        audit_2023,
        audit_2024,
        audit_2025
    ],
    ignore_index=True,
    sort=False
)


row_audit[
    "abs_difference"
] = (
    row_audit[
        "difference"
    ]
    .abs()
)


row_audit[
    "consistent"
] = (
    row_audit[
        "abs_difference"
    ]
    <= 0.001
)


print()
print("=" * 78)
print("ROW-LEVEL AUDIT")
print("=" * 78)

print(
    "Jumlah row audit:",
    len(row_audit)
)

print(
    "Row tidak konsisten:",
    (
        ~row_audit[
            "consistent"
        ]
    ).sum()
)


if (
    ~row_audit[
        "consistent"
    ]
).any():

    display(
        row_audit[
            ~row_audit[
                "consistent"
            ]
        ]
    )

else:

    print(
        "✓ Semua row bulanan konsisten "
        "dengan annual total pada row sumber."
    )


# =====================================================================
# 16. DECLARED WORKBOOK TOTAL 2023 & 2024
# =====================================================================

def declared_standard_total(
    filepath,
    sheet_name
):

    raw = pd.read_excel(
        filepath,
        sheet_name=sheet_name,
        header=None
    )

    for r in range(
        len(raw)
    ):

        label = (
            raw.iat[r, 1]
            if raw.shape[1] > 1
            else None
        )

        if (
            normalize_text(
                label
            )
            == "jumlah"
        ):

            if raw.shape[1] > 16:

                return num0(
                    raw.iat[r, 16]
                )

    return np.nan


# =====================================================================
# 17. DECLARED TOTAL 2025
# =====================================================================

def declared_2025_total(
    raw,
    requested_label
):

    requested = normalize_text(
        requested_label
    )

    for r in range(
        len(raw)
    ):

        label = (
            raw.iat[r, 1]
            if raw.shape[1] > 1
            else None
        )

        if (
            normalize_text(
                label
            )
            == requested
        ):

            if raw.shape[1] > 30:

                return num0(
                    raw.iat[r, 30]
                )

    return np.nan


workbook_declared = pd.DataFrame(
    [
        {
            "year":
                2023,

            "declared_wisman":
                declared_standard_total(
                    FILES[2023],
                    "WISMAN"
                ),

            "declared_wisnus":
                declared_standard_total(
                    FILES[2023],
                    "WISNUS"
                )
        },

        {
            "year":
                2024,

            "declared_wisman":
                declared_standard_total(
                    FILES[2024],
                    "WISMAN"
                ),

            "declared_wisnus":
                declared_standard_total(
                    FILES[2024],
                    "WISNUS"
                )
        },

        {
            "year":
                2025,

            "declared_wisman":
                declared_2025_total(
                    source_2025,
                    "TOTAL KUNJ. WISMAN"
                ),

            "declared_wisnus":
                declared_2025_total(
                    source_2025,
                    "TOTAL KUNJ. WISNUS"
                )
        }
    ]
)


workbook_declared[
    "declared_total"
] = (
    workbook_declared[
        "declared_wisman"
    ]
    +
    workbook_declared[
        "declared_wisnus"
    ]
)


# =====================================================================
# 18. INTERNAL RECONCILIATION
# =====================================================================

internal_reconciliation = (
    detail_year_total
    .merge(
        workbook_declared,
        on="year",
        how="left"
    )
)


internal_reconciliation[
    "difference_wisman"
] = (
    internal_reconciliation[
        "detail_wisman"
    ]
    -
    internal_reconciliation[
        "declared_wisman"
    ]
)


internal_reconciliation[
    "difference_wisnus"
] = (
    internal_reconciliation[
        "detail_wisnus"
    ]
    -
    internal_reconciliation[
        "declared_wisnus"
    ]
)


internal_reconciliation[
    "difference_total"
] = (
    internal_reconciliation[
        "detail_total"
    ]
    -
    internal_reconciliation[
        "declared_total"
    ]
)


print()
print("=" * 78)
print("INTERNAL RECONCILIATION")
print("DETAIL DESTINASI vs TOTAL YANG TERTULIS DI WORKBOOK")
print("=" * 78)

display(
    internal_reconciliation
)


# =====================================================================
# 19. KHUSUS AUDIT SUBTOTAL 2025
# =====================================================================

detail_2025_by_section = (
    visitor_type_long[
        visitor_type_long[
            "year"
        ] == 2025
    ]
    .groupby(
        [
            "source_section",
            "visitor_type"
        ],
        as_index=False
    )[
        "visitors"
    ]
    .sum()
)


detail_2025_pivot = (
    detail_2025_by_section
    .pivot(
        index=
            "source_section",

        columns=
            "visitor_type",

        values=
            "visitors"
    )
    .fillna(0)
    .reset_index()
)


for c in [
    "wisman",
    "wisnus"
]:

    if c not in detail_2025_pivot.columns:
        detail_2025_pivot[c] = 0


detail_2025_pivot[
    "detail_total"
] = (
    detail_2025_pivot[
        "wisman"
    ]
    +
    detail_2025_pivot[
        "wisnus"
    ]
)


declared_section_2025 = pd.DataFrame(
    [
        {
            "source_section":
                "DTW",

            "declared_wisman":
                declared_2025_total(
                    source_2025,
                    "TOTAL KUNJ. WISMAN DI DTW"
                ),

            "declared_wisnus":
                declared_2025_total(
                    source_2025,
                    "TOTAL KUNJ. WISNUS DI DTW"
                )
        },

        {
            "source_section":
                "DESA_WISATA",

            "declared_wisman":
                declared_2025_total(
                    source_2025,
                    "TOTAL KUNJ. WISMAN DI DESWITA"
                ),

            "declared_wisnus":
                declared_2025_total(
                    source_2025,
                    "TOTAL KUNJ. WISNUS DI DESWITA"
                )
        }
    ]
)


declared_section_2025[
    "declared_total"
] = (
    declared_section_2025[
        "declared_wisman"
    ]
    +
    declared_section_2025[
        "declared_wisnus"
    ]
)


section_audit_2025 = (
    detail_2025_pivot
    .merge(
        declared_section_2025,
        on="source_section",
        how="left"
    )
)


section_audit_2025[
    "diff_wisman"
] = (
    section_audit_2025[
        "wisman"
    ]
    -
    section_audit_2025[
        "declared_wisman"
    ]
)


section_audit_2025[
    "diff_wisnus"
] = (
    section_audit_2025[
        "wisnus"
    ]
    -
    section_audit_2025[
        "declared_wisnus"
    ]
)


section_audit_2025[
    "diff_total"
] = (
    section_audit_2025[
        "detail_total"
    ]
    -
    section_audit_2025[
        "declared_total"
    ]
)


print()
print("=" * 78)
print("AUDIT SUBTOTAL 2025")
print("=" * 78)

display(
    section_audit_2025
)


# =====================================================================
# 20. REKAP DINAS/PDF — HANYA UNTUK AUDIT
#
# TIDAK digunakan sebagai replacement data destinasi.
# =====================================================================

reference_recap = pd.DataFrame(
    {
        "year": [
            2023,
            2024,
            2025
        ],

        "reference_wisman": [
            153,
            136,
            4398
        ],

        "reference_wisnus": [
            64827,
            66677,
            90401
        ],

        "reference_total": [
            64980,
            66813,
            94799
        ]
    }
)


full_reconciliation = (
    internal_reconciliation
    .merge(
        reference_recap,
        on="year",
        how="left"
    )
)


full_reconciliation[
    "detail_minus_reference"
] = (
    full_reconciliation[
        "detail_total"
    ]
    -
    full_reconciliation[
        "reference_total"
    ]
)


full_reconciliation[
    "declared_minus_reference"
] = (
    full_reconciliation[
        "declared_total"
    ]
    -
    full_reconciliation[
        "reference_total"
    ]
)


full_reconciliation[
    "detail_reference_diff_pct"
] = np.where(
    full_reconciliation[
        "reference_total"
    ] != 0,

    full_reconciliation[
        "detail_minus_reference"
    ]
    /
    full_reconciliation[
        "reference_total"
    ]
    * 100,

    np.nan
)


print()
print("=" * 78)
print("RECONCILIATION DENGAN REKAP DINAS/PDF")
print("=" * 78)

display(
    full_reconciliation
)


# =====================================================================
# 21. SEASONALITY ANALYSIS
# =====================================================================

def seasonality_metrics(group):

    g = (
        group
        .sort_values(
            "month_num"
        )
    )

    values = (
        g[
            "total_visitors"
        ]
        .astype(float)
        .values
    )

    total = values.sum()
    mean_value = values.mean()

    sd_value = (
        values.std(
            ddof=1
        )
        if len(values) > 1
        else 0
    )

    if mean_value > 0:

        cv = (
            sd_value
            /
            mean_value
        )

    else:

        cv = np.nan

    if total > 0:

        share = (
            values
            /
            total
        )

        positive = (
            share[
                share > 0
            ]
        )

        hhi = (
            share ** 2
        ).sum()

        entropy = (
            -np.sum(
                positive
                *
                np.log(
                    positive
                )
            )
            /
            np.log(12)
        )

        peak_index = int(
            np.argmax(
                values
            )
        )

        peak_month = (
            MONTHS[
                peak_index
            ]
        )

        peak_visitors = (
            values[
                peak_index
            ]
        )

        peak_share = (
            peak_visitors
            /
            total
        )

    else:

        hhi = np.nan
        entropy = np.nan
        peak_month = None
        peak_visitors = 0
        peak_share = np.nan

    active_months = int(
        np.sum(
            values > 0
        )
    )

    return pd.Series(
        {
            "annual_visitors":
                total,

            "mean_monthly":
                mean_value,

            "sd_monthly":
                sd_value,

            "seasonality_cv":
                cv,

            "seasonality_hhi":
                hhi,

            "seasonal_entropy":
                entropy,

            "peak_month":
                peak_month,

            "peak_visitors":
                peak_visitors,

            "peak_share":
                peak_share,

            "active_months":
                active_months
        }
    )


seasonality = (
    visitor_monthly
    .groupby(
        [
            "year",
            "destination"
        ]
    )
    .apply(
        seasonality_metrics
    )
    .reset_index()
)


print()
print("=" * 78)
print("SEASONALITY")
print("=" * 78)

display(
    seasonality
    .sort_values(
        [
            "year",
            "annual_visitors"
        ],
        ascending=[
            True,
            False
        ]
    )
)


# =====================================================================
# 22. LONGITUDINAL DESTINATION TABLE
# =====================================================================

annual_pivot = (
    visitor_annual
    .pivot(
        index=
            "destination",

        columns=
            "year",

        values=
            "total_visitors"
    )
    .reset_index()
)


for year in [
    2023,
    2024,
    2025
]:

    if year not in annual_pivot.columns:

        annual_pivot[
            year
        ] = np.nan


annual_pivot[
    "observed_years"
] = annual_pivot[
    [
        2023,
        2024,
        2025
    ]
].notna().sum(
    axis=1
)


annual_pivot[
    "total_3yr"
] = annual_pivot[
    [
        2023,
        2024,
        2025
    ]
].sum(
    axis=1,
    min_count=1
)


annual_pivot[
    "mean_annual_visitors"
] = annual_pivot[
    [
        2023,
        2024,
        2025
    ]
].mean(
    axis=1,
    skipna=True
)


annual_pivot[
    "growth_2023_2024_pct"
] = annual_pivot.apply(
    lambda row:
        safe_pct_change(
            row[2024],
            row[2023]
        ),
    axis=1
)


annual_pivot[
    "growth_2024_2025_pct"
] = annual_pivot.apply(
    lambda row:
        safe_pct_change(
            row[2025],
            row[2024]
        ),
    axis=1
)


annual_pivot[
    "growth_2023_2025_pct"
] = annual_pivot.apply(
    lambda row:
        safe_pct_change(
            row[2025],
            row[2023]
        ),
    axis=1
)


def cagr_2yr(
    start,
    end
):

    if (
        pd.isna(start)
        or
        pd.isna(end)
        or
        start <= 0
        or
        end < 0
    ):

        return np.nan

    return (
        (
            end
            /
            start
        ) ** (1 / 2)
        - 1
    ) * 100


annual_pivot[
    "CAGR_2023_2025_pct"
] = annual_pivot.apply(
    lambda row:
        cagr_2yr(
            row[2023],
            row[2025]
        ),
    axis=1
)


annual_pivot = (
    annual_pivot
    .sort_values(
        "total_3yr",
        ascending=False
    )
    .reset_index(
        drop=True
    )
)


print()
print("=" * 78)
print("LONGITUDINAL VISITOR DEMAND")
print("=" * 78)

display(
    annual_pivot
)


# =====================================================================
# 23. TOTAL BULANAN KABUPATEN BERDASARKAN DETAIL DESTINASI
# =====================================================================

monthly_regency = (
    visitor_monthly
    .groupby(
        [
            "year",
            "month",
            "month_num"
        ],
        as_index=False
    )
    .agg(
        wisman=(
            "wisman",
            "sum"
        ),

        wisnus=(
            "wisnus",
            "sum"
        ),

        total_visitors=(
            "total_visitors",
            "sum"
        )
    )
    .sort_values(
        [
            "year",
            "month_num"
        ]
    )
)


# =====================================================================
# 24. FIGURE — ANNUAL DATA RECONCILIATION
# =====================================================================

plot_reconcile = (
    full_reconciliation
    .sort_values(
        "year"
    )
)


x = np.arange(
    len(
        plot_reconcile
    )
)

width = 0.25


plt.figure(
    figsize=(9, 5.5)
)


plt.bar(
    x - width,
    plot_reconcile[
        "detail_total"
    ],
    width,
    label=
        "Sum of destination detail"
)


plt.bar(
    x,
    plot_reconcile[
        "declared_total"
    ],
    width,
    label=
        "Workbook declared total"
)


plt.bar(
    x + width,
    plot_reconcile[
        "reference_total"
    ],
    width,
    label=
        "Reference recap"
)


plt.xticks(
    x,
    plot_reconcile[
        "year"
    ].astype(str)
)


plt.ylabel(
    "Visitors"
)

plt.xlabel(
    "Year"
)

plt.title(
    "Audit of Tourism Visitor Totals, Barru Regency"
)

plt.legend()

plt.grid(
    axis="y",
    alpha=0.25
)

save_fig(
    "fig_01_visitor_data_reconciliation.png"
)


# =====================================================================
# 25. FIGURE — MONTHLY VISITOR DYNAMICS
# =====================================================================

plt.figure(
    figsize=(10, 5.5)
)


for year in [
    2023,
    2024,
    2025
]:

    temp = (
        monthly_regency[
            monthly_regency[
                "year"
            ] == year
        ]
        .sort_values(
            "month_num"
        )
    )

    plt.plot(
        temp[
            "month_num"
        ],
        temp[
            "total_visitors"
        ],
        marker="o",
        label=str(year)
    )


plt.xticks(
    range(
        1,
        13
    ),
    MONTHS
)


plt.xlabel(
    "Month"
)

plt.ylabel(
    "Recorded destination-level visitors"
)

plt.title(
    "Monthly Observed Tourism Demand, 2023–2025"
)

plt.legend(
    title="Year"
)

plt.grid(
    alpha=0.25
)

save_fig(
    "fig_02_monthly_visitor_dynamics.png"
)


# =====================================================================
# 26. FIGURE — TOP DESTINATIONS MULTI-YEAR
# =====================================================================

top15 = (
    annual_pivot
    .dropna(
        subset=[
            "total_3yr"
        ]
    )
    .head(15)
    .sort_values(
        "total_3yr"
    )
)


plt.figure(
    figsize=(9, 7)
)


plt.barh(
    top15[
        "destination"
    ],
    top15[
        "total_3yr"
    ]
)


plt.xlabel(
    "Cumulative recorded visitors"
)

plt.ylabel(
    "Destination"
)

plt.title(
    "Multi-Year Observed Tourism Demand, 2023–2025"
)

plt.grid(
    axis="x",
    alpha=0.25
)

save_fig(
    "fig_03_top_destinations_2023_2025.png"
)




# =====================================================================
# 27. EXPORT VISITOR-DATA PRODUCTS
# =====================================================================

visitor_type_long.to_csv(
    TABLE_DIR_NEW / "visitor_type_long_2023_2025.csv",
    index=False
)

visitor_monthly.to_csv(
    TABLE_DIR_NEW / "visitor_monthly_demand_2023_2025.csv",
    index=False
)

visitor_annual.to_csv(
    TABLE_DIR_NEW / "visitor_annual_demand_2023_2025.csv",
    index=False
)

seasonality.to_csv(
    TABLE_DIR_NEW / "visitor_seasonality_2023_2025.csv",
    index=False
)

annual_pivot.to_csv(
    TABLE_DIR_NEW / "visitor_multiyear_summary_2023_2025.csv",
    index=False
)

if "full_reconciliation" in globals():
    full_reconciliation.to_csv(
        TABLE_DIR_NEW / "visitor_reconciliation_2023_2025.csv",
        index=False
    )

print()
print("Visitor-data preparation complete.")
print("Outputs:", TABLE_DIR_NEW)
