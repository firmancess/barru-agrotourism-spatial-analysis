"""
Run the additional Q1 robustness audit used in the revised manuscript.

Clean public version derived from the final manuscript-relevant notebook cell 75.
Personal Google Drive paths and notebook-only execution assumptions were removed.
Analytical logic is retained where it is verifiable from the uploaded notebook.
"""

from __future__ import annotations

"""
Colab-ready additional audit for the Barru AECS manuscript.

Purpose
-------
This script does not rebuild the AECS. It reads the frozen final grid/demand
files when they are available and adds reviewer-facing diagnostics:

1. Spearman correlation with permutation p-values.
2. Bootstrap confidence intervals, leave-one-destination-out ranges, and the
   two-sided critical |rho| implied by each sample size.
3. Monte Carlo power for true Spearman effects of 0.30, 0.50, 0.70, and 0.80.
4. Temporal bootstrap uncertainty for destination mismatch percentiles/classes.
5. Hybrid-weight contribution audit, especially the ASI contribution.
6. ASI zero-inflation and ALI/MAUP diagnostics when the final grid is present.
7. A leave-TAI-out spatial-consistency check to reduce direct circularity.

The embedded 12-destination table is used only as a transparent fallback when
the frozen Excel/GeoJSON files cannot be found. Edit ROOT or set environment
variable AECS_ROOT if your Google Drive folder is different.
"""


import itertools
import os
import re
import warnings
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-aecs-q1")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

warnings.filterwarnings("ignore", category=RuntimeWarning)


# ---------------------------------------------------------------------------
# 00. CONFIGURATION
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(
    os.environ.get("AECS_PROJECT_ROOT", SCRIPT_DIR.parent)
).resolve()

ROOT = REPO_ROOT

OUT_DIR = Path(
    os.environ.get(
        "AECS_AUDIT_OUT",
        str(REPO_ROOT / "outputs" / "07_q1_robustness_audit"),
    )
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

GRID_CANDIDATES = [
    REPO_ROOT / "data" / "processed" / "agrotourism_corridor_grid_result_HYBRID.geojson",
]

DEMAND_CANDIDATES = [
    REPO_ROOT
    / "outputs"
    / "04_primary_demand_spatial_linkage"
    / "FINAL_HYBRID_AECS_VISITOR_DEMAND_RESULTS.xlsx",
    REPO_ROOT
    / "outputs"
    / "06_spatial_sensitivity_and_stability"
    / "FINAL_100_PERCENT_RESULTS.xlsx",
]

SEED = 20260822
N_PERM = 250_000
N_BOOT = 20_000
N_POWER = 50_000
ALPHA = 0.05


# ---------------------------------------------------------------------------
# 01. EMBEDDED, MANUSCRIPT-VERIFIED FALLBACK DATA
# ---------------------------------------------------------------------------

DESTINATION_FALLBACK = pd.DataFrame(
    columns=[
        "destination",
        "visitors_2023",
        "visitors_2024",
        "visitors_2025",
        "AECS",
        "supply_percentile",
        "coordinate_status",
        "spatial_assignment_method",
    ]
)


VALIDATION_FALLBACK = pd.DataFrame(
    [
        ("Desa Wisata Pancana", "G0060"),
        ("Desa Wisata Kampung Habibie Kecil", "G0766"),
        ("Desa Wisata Kampung Laskar", "G0912"),
        ("Desa Wisata Air Terjun Baruttungnge", "G0056"),
        ("Desa Wisata Kamiri", "G0441"),
        ("Desa Wisata Wanua To Bentong", "G0938"),
        ("Diana Waterpark", "G0444"),
        ("Padang Indah Allepperengnge", "G0705"),
        ("Lappa Laona", "G1239"),
        ("Taman Colliq Pujie", "G0107"),
        ("Pantai Sumpang Binangae", "G0069"),
    ],
    columns=["validation_name", "grid_id"],
)

WEIGHTS = pd.Series(
    {"ALI": 0.1678, "TAI": 0.1186, "ASI": 0.5281, "RNAI": 0.1093, "EQI": 0.0763}
)

ALL_GRID_MEANS_FALLBACK = pd.Series(
    {"ALI": 0.455, "TAI": 0.294, "ASI": 0.011, "RNAI": 0.283, "EQI": 0.726}
)

TOP20_COMPONENT_MEANS_FALLBACK = pd.Series(
    {"ALI": 0.5050, "TAI": 0.6181, "ASI": 0.2373, "RNAI": 0.4870, "EQI": 0.6665}
)


# ---------------------------------------------------------------------------
# 02. GENERIC HELPERS
# ---------------------------------------------------------------------------

def clean_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def find_col(df: pd.DataFrame, candidates: list[str], required: bool = True) -> str | None:
    lookup = {clean_key(c): c for c in df.columns}
    for candidate in candidates:
        if clean_key(candidate) in lookup:
            return lookup[clean_key(candidate)]
    if required:
        raise KeyError(f"Missing column. Candidates={candidates}; available={list(df.columns)}")
    return None


def canonical_grid_id(value: object) -> str:
    match = re.search(r"(\d+)", str(value))
    return f"G{int(match.group(1)):04d}" if match else str(value)


def sample_midrank_percentile(values: pd.Series) -> pd.Series:
    n = values.notna().sum()
    return (values.rank(method="average") - 0.5) / n


def mismatch_class(supply: np.ndarray, demand: np.ndarray, threshold: float = 2 / 3) -> np.ndarray:
    s_high = supply >= threshold
    d_high = demand >= threshold
    labels = np.full(len(supply), "Lower readiness–lower demand", dtype=object)
    labels[(~s_high) & d_high] = "Lower readiness–high demand"
    labels[s_high & (~d_high)] = "High readiness–lower demand"
    labels[s_high & d_high] = "High readiness–high demand"
    return labels


def paired_bootstrap_spearman(x: np.ndarray, y: np.ndarray, n_boot: int, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(x)
    values: list[float] = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        xb, yb = x[idx], y[idx]
        if np.unique(xb).size < 2 or np.unique(yb).size < 2:
            continue
        rho = float(spearmanr(xb, yb).statistic)
        if np.isfinite(rho):
            values.append(rho)
    if not values:
        return np.nan, np.nan
    return tuple(np.quantile(values, [0.025, 0.975]))


def rank_corr_against_permutations(x: np.ndarray, permuted_y: np.ndarray) -> np.ndarray:
    rx = np.argsort(np.argsort(x)).astype(float)
    rx -= rx.mean()
    ry = np.argsort(np.argsort(permuted_y, axis=1), axis=1).astype(float)
    ry -= ry.mean(axis=1, keepdims=True)
    return (ry * rx).sum(axis=1) / np.sqrt((rx * rx).sum() * (ry * ry).sum(axis=1))


def permutation_pvalue(x: np.ndarray, y: np.ndarray, n_perm: int, seed: int) -> float:
    observed = abs(float(spearmanr(x, y).statistic))
    n = len(x)
    if n <= 8:
        permuted = np.asarray(list(itertools.permutations(y)), dtype=float)
        rho_null = rank_corr_against_permutations(x, permuted)
        return float(np.mean(np.abs(rho_null) >= observed - 1e-12))
    rng = np.random.default_rng(seed)
    order = np.argsort(rng.random((n_perm, n)), axis=1)
    permuted = y[order]
    rho_null = rank_corr_against_permutations(x, permuted)
    return float((np.sum(np.abs(rho_null) >= observed - 1e-12) + 1) / (n_perm + 1))


def critical_spearman(n: int, alpha: float, n_perm: int, seed: int) -> tuple[float, float]:
    """Smallest attainable |rho| whose two-sided null tail is <= alpha."""
    base = np.arange(n, dtype=float)
    if n <= 8:
        permuted = np.asarray(list(itertools.permutations(base)), dtype=float)
    else:
        rng = np.random.default_rng(seed)
        permuted = np.argsort(rng.random((n_perm, n)), axis=1).astype(float)
    rho_null = np.abs(rank_corr_against_permutations(base, permuted))
    for critical in np.unique(np.round(rho_null, 12)):
        tail = float(np.mean(rho_null >= critical - 1e-12))
        if tail <= alpha:
            return float(critical), tail
    return 1.0, float(np.mean(rho_null >= 1.0 - 1e-12))


def gaussian_copula_power(n: int, true_spearman: float, critical: float, n_sim: int, seed: int) -> float:
    rng = np.random.default_rng(seed)
    pearson = 2 * np.sin(np.pi * true_spearman / 6)
    x = rng.normal(size=(n_sim, n))
    z = rng.normal(size=(n_sim, n))
    y = pearson * x + np.sqrt(1 - pearson**2) * z
    rx = np.argsort(np.argsort(x, axis=1), axis=1).astype(float)
    ry = np.argsort(np.argsort(y, axis=1), axis=1).astype(float)
    rx -= rx.mean(axis=1, keepdims=True)
    ry -= ry.mean(axis=1, keepdims=True)
    rho = (rx * ry).sum(axis=1) / np.sqrt((rx * rx).sum(axis=1) * (ry * ry).sum(axis=1))
    return float(np.mean(np.abs(rho) >= critical))


def gini(values: pd.Series) -> float:
    x = np.sort(pd.to_numeric(values, errors="coerce").dropna().to_numpy(float))
    if len(x) == 0 or np.isclose(x.sum(), 0):
        return np.nan
    index = np.arange(1, len(x) + 1)
    return float((2 * np.sum(index * x) / (len(x) * x.sum())) - (len(x) + 1) / len(x))


# ---------------------------------------------------------------------------
# 03. LOAD FROZEN DATA, WITH FALLBACK
# ---------------------------------------------------------------------------

def load_demand() -> tuple[pd.DataFrame, str]:
    for path in DEMAND_CANDIDATES:
        if not path.exists():
            continue
        try:
            book = pd.ExcelFile(path)
            for sheet in book.sheet_names:
                df = pd.read_excel(path, sheet_name=sheet)
                dest_col = find_col(df, ["destination", "Destination"], required=False)
                aecs_col = find_col(df, ["AECS", "AECS_final"], required=False)
                if dest_col and aecs_col and len(df) >= 7:
                    df = df.rename(columns={dest_col: "destination", aecs_col: "AECS"})
                    return standardize_demand(df), f"{path}::{sheet}"
        except Exception as exc:
            print(f"Warning: could not read {path}: {exc}")
    raise FileNotFoundError(
        "No processed demand workbook was found. Run scripts 01, 04, 05, and 06 "
        "with visitor data that you are permitted to use before running this audit."
    )


def standardize_demand(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for year in (2023, 2024, 2025):
        source = find_col(df, [f"visitors_{year}", str(year)], required=False)
        if source and source != f"visitors_{year}":
            df = df.rename(columns={source: f"visitors_{year}"})
        if f"visitors_{year}" not in df:
            df[f"visitors_{year}"] = np.nan
        df[f"visitors_{year}"] = pd.to_numeric(df[f"visitors_{year}"], errors="coerce")
    for target, aliases in {
        "coordinate_status": ["coordinate_status"],
        "spatial_assignment_method": ["spatial_assignment_method"],
        "supply_percentile": ["supply_percentile"],
    }.items():
        if target not in df:
            source = find_col(df, aliases, required=False)
            if source:
                df = df.rename(columns={source: target})
    for target in ["coordinate_status", "spatial_assignment_method", "supply_percentile"]:
        if target not in df:
            df[target] = np.nan
    df["AECS"] = pd.to_numeric(df["AECS"], errors="coerce")
    annual = ["visitors_2023", "visitors_2024", "visitors_2025"]
    df["observed_years"] = df[annual].notna().sum(axis=1)
    df["mean_annual_visitors"] = df[annual].mean(axis=1, skipna=True)
    return df[df["observed_years"] >= 2].dropna(subset=["AECS", "mean_annual_visitors"]).reset_index(drop=True)


def load_grid():
    try:
        import geopandas as gpd
    except Exception:
        return None, "geopandas unavailable"
    for path in GRID_CANDIDATES:
        if path.exists():
            try:
                return gpd.read_file(path), str(path)
            except Exception as exc:
                print(f"Warning: could not read {path}: {exc}")
    return None, "final grid not found"


# ---------------------------------------------------------------------------
# 04. CORRELATION, CRITICAL EFFECT, POWER, AND LEAVE-ONE-OUT
# ---------------------------------------------------------------------------

def association_audit(demand: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    samples = {
        "Primary": demand,
        "Non-manual": demand[demand["coordinate_status"] != "manual_approximate"],
        "Strict point-within-grid": demand[
            (demand["coordinate_status"] != "manual_approximate")
            & (demand["spatial_assignment_method"] == "point_within_grid")
        ],
    }
    association_rows = []
    loo_rows = []
    power_rows = []
    for offset, (label, sample) in enumerate(samples.items()):
        x = sample["AECS"].to_numpy(float)
        y = sample["mean_annual_visitors"].to_numpy(float)
        n = len(sample)
        rho, asymptotic_p = spearmanr(x, y)
        ci_low, ci_high = paired_bootstrap_spearman(x, y, N_BOOT, SEED + offset)
        permutation_p = permutation_pvalue(x, y, N_PERM, SEED + 100 + offset)
        critical, actual_tail = critical_spearman(n, ALPHA, N_PERM, SEED + 200 + offset)
        loo = []
        for i, destination in enumerate(sample["destination"]):
            rho_i = float(spearmanr(np.delete(x, i), np.delete(y, i)).statistic)
            loo.append(rho_i)
            loo_rows.append({"sample": label, "omitted_destination": destination, "rho": rho_i})
        association_rows.append(
            {
                "sample": label,
                "n": n,
                "rho": rho,
                "asymptotic_p": asymptotic_p,
                "permutation_p": permutation_p,
                "bootstrap_95CI_low": ci_low,
                "bootstrap_95CI_high": ci_high,
                "critical_abs_rho_alpha_0.05": critical,
                "actual_null_tail_at_critical": actual_tail,
                "leave_one_out_min": np.min(loo),
                "leave_one_out_max": np.max(loo),
            }
        )
        for true_rho in (0.30, 0.50, 0.70, 0.80):
            power_rows.append(
                {
                    "sample": label,
                    "n": n,
                    "true_spearman_rho": true_rho,
                    "simulated_power": gaussian_copula_power(
                        n, true_rho, critical, N_POWER, SEED + 300 + offset + int(true_rho * 100)
                    ),
                }
            )
    return pd.DataFrame(association_rows), pd.DataFrame(loo_rows), pd.DataFrame(power_rows)


# ---------------------------------------------------------------------------
# 05. TEMPORAL UNCERTAINTY OF THE DESCRIPTIVE MISMATCH TYPOLOGY
# ---------------------------------------------------------------------------

def temporal_mismatch_audit(demand: pd.DataFrame, n_boot: int = N_BOOT) -> pd.DataFrame:
    df = demand.copy().reset_index(drop=True)
    if df["supply_percentile"].isna().any():
        raise ValueError("Supply percentiles are required for the temporal mismatch audit.")
    rng = np.random.default_rng(SEED + 500)
    n = len(df)
    boot_means = np.empty((n_boot, n), dtype=float)
    annual_cols = ["visitors_2023", "visitors_2024", "visitors_2025"]
    for j, row in df.iterrows():
        annual = row[annual_cols].dropna().to_numpy(float)
        draw = rng.integers(0, len(annual), size=(n_boot, len(annual)))
        boot_means[:, j] = annual[draw].mean(axis=1)
    ranks = np.argsort(np.argsort(boot_means, axis=1), axis=1) + 1
    demand_percentile = (ranks - 0.5) / n
    supply = df["supply_percentile"].to_numpy(float)
    mismatch = demand_percentile - supply[None, :]
    primary_demand = sample_midrank_percentile(df["mean_annual_visitors"]).to_numpy(float)
    primary_class = mismatch_class(supply, primary_demand)
    rows = []
    for j, destination in enumerate(df["destination"]):
        boot_classes = mismatch_class(np.repeat(supply[j], n_boot), demand_percentile[:, j])
        values, counts = np.unique(boot_classes, return_counts=True)
        probabilities = dict(zip(values, counts / n_boot))
        ci_low, median, ci_high = np.quantile(mismatch[:, j], [0.025, 0.5, 0.975])
        rows.append(
            {
                "destination": destination,
                "primary_mismatch": primary_demand[j] - supply[j],
                "temporal_bootstrap_mismatch_median": median,
                "temporal_bootstrap_95CI_low": ci_low,
                "temporal_bootstrap_95CI_high": ci_high,
                "primary_class": primary_class[j],
                "probability_primary_class": probabilities.get(primary_class[j], 0.0),
                "modal_class": max(probabilities, key=probabilities.get),
                "probability_modal_class": max(probabilities.values()),
            }
        )
    return pd.DataFrame(rows).sort_values("primary_mismatch", ascending=False)


# ---------------------------------------------------------------------------
# 06. WEIGHT CONTRIBUTIONS, ASI ZERO-INFLATION, MAUP, LEAVE-TAI-OUT
# ---------------------------------------------------------------------------

def standardize_grid(grid: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "grid_id": ["grid_id", "unit_id"],
        "district": ["district", "district_name", "kecamatan"],
        "ALI": ["ALI", "agricultural_landscape_index"],
        "TAI": ["TAI", "tourism_attraction_index"],
        "ASI": ["ASI", "amenity_support_index"],
        "RNAI": ["RNAI", "road_network_accessibility_index"],
        "EQI": ["EQI", "environmental_quality_index"],
        "AECS": ["AECS", "AECS_final", "AECS_HYBRID", "agrotourism_experience_corridor_score"],
    }
    rename = {}
    for target, options in aliases.items():
        source = find_col(grid, options, required=(target not in {"district", "AECS"}))
        if source and source != target:
            rename[source] = target
    df = grid.rename(columns=rename).copy()
    df["grid_id"] = df["grid_id"].map(canonical_grid_id)
    for col in WEIGHTS.index:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "AECS" not in df:
        df["AECS"] = df[WEIGHTS.index].mul(WEIGHTS, axis=1).sum(axis=1)
    return df


def contribution_audit(grid: pd.DataFrame | None) -> pd.DataFrame:
    if grid is None:
        groups = {
            "All 1,358 grids (Table 6 means)": ALL_GRID_MEANS_FALLBACK,
            "Top 20 grids (Table 8 means)": TOP20_COMPONENT_MEANS_FALLBACK,
        }
    else:
        g = standardize_grid(grid)
        groups = {
            "All analytical grids": g[WEIGHTS.index].mean(),
            "Top 20 grids": g.nlargest(20, "AECS")[WEIGHTS.index].mean(),
        }
    rows = []
    for group_name, means in groups.items():
        weighted = means * WEIGHTS
        shares = weighted / weighted.sum()
        for component in WEIGHTS.index:
            rows.append(
                {
                    "group": group_name,
                    "component": component,
                    "weight": WEIGHTS[component],
                    "component_mean": means[component],
                    "mean_weighted_contribution": weighted[component],
                    "share_of_mean_AECS": shares[component],
                }
            )
    return pd.DataFrame(rows)


def spatial_structure_audit(grid: pd.DataFrame | None) -> pd.DataFrame:
    if grid is None:
        return pd.DataFrame(
            [
                {"diagnostic": "ASI zero share", "value": ">= 0.75", "note": "Q3=0.000 in Table 6; exact share requires grid file"},
                {"diagnostic": "ALI unique values", "value": 7, "note": "one inherited district value per district"},
            ]
        )
    g = standardize_grid(grid)
    rows = [
        {"diagnostic": "ASI zero share", "value": float(np.mean(np.isclose(g["ASI"], 0))), "note": "observed grid layer"},
        {"diagnostic": "ASI Gini", "value": gini(g["ASI"]), "note": "0=equal, 1=concentrated"},
        {"diagnostic": "ASI unique values", "value": int(g["ASI"].nunique()), "note": "observed grid layer"},
        {"diagnostic": "ALI unique values", "value": int(g["ALI"].nunique()), "note": "scale-inheritance/MAUP diagnostic"},
    ]
    if "district" in g:
        within_sd = g.groupby("district")["ALI"].std(ddof=0)
        rows.append(
            {
                "diagnostic": "Maximum within-district ALI SD",
                "value": float(within_sd.max()),
                "note": "expected 0 when district ALI is inherited by all 1-km grids",
            }
        )
    return pd.DataFrame(rows)


def leave_tai_out_validation(grid: pd.DataFrame | None) -> pd.DataFrame:
    if grid is None:
        return pd.DataFrame(
            [{"status": "not run", "reason": "final grid file required for leave-TAI-out analysis"}]
        )
    g = standardize_grid(grid)
    retained = WEIGHTS.drop("TAI")
    retained = retained / retained.sum()
    g["AECS_no_TAI"] = g[retained.index].mul(retained, axis=1).sum(axis=1)
    q33, q66 = g["AECS_no_TAI"].quantile([1 / 3, 2 / 3])
    g["class_no_TAI"] = np.select(
        [g["AECS_no_TAI"] <= q33, g["AECS_no_TAI"] > q66],
        ["Low priority", "High priority"],
        default="Moderate priority",
    )
    result = VALIDATION_FALLBACK.merge(
        g[["grid_id", "AECS_no_TAI", "class_no_TAI"]], on="grid_id", how="left"
    )
    result["interpretation"] = (
        "Sensitivity only: excluding TAI reduces direct construct overlap but does not create fully independent validation."
    )
    return result


# ---------------------------------------------------------------------------
# 07. FIGURES AND PASTE-READY SUMMARY
# ---------------------------------------------------------------------------

def plot_power(power: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for label, sample in power.groupby("sample"):
        ax.plot(sample["true_spearman_rho"], sample["simulated_power"], marker="o", label=label)
    ax.axhline(0.80, color="black", linestyle="--", linewidth=0.9, label="80% power")
    ax.set(xlabel="Assumed true Spearman rho", ylabel="Simulated two-sided power", ylim=(0, 1.02))
    ax.set_title("Power limitations of the destination-level association tests")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "Fig_Q1_Spearman_Power.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_association(association: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    y = np.arange(len(association))
    rho = association["rho"].to_numpy(float)
    low = association["bootstrap_95CI_low"].to_numpy(float)
    high = association["bootstrap_95CI_high"].to_numpy(float)
    ax.errorbar(rho, y, xerr=[rho - low, high - rho], fmt="o", color="black", capsize=3)
    ax.axvline(0, color="black", linestyle="--", linewidth=0.9)
    ax.set_yticks(y, association["sample"])
    ax.invert_yaxis()
    ax.set_xlim(-1, 1)
    ax.set_xlabel("Spearman rho with percentile-bootstrap 95% CI")
    ax.set_title("AECS–visitor demand association: uncertainty across specifications")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "Fig_Q1_Association_Uncertainty.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_summary(
    demand_source: str,
    grid_source: str,
    association: pd.DataFrame,
    contribution: pd.DataFrame,
    mismatch: pd.DataFrame,
) -> None:
    primary = association.iloc[0]
    nonmanual = association.iloc[1]
    strict = association.iloc[2]
    all_asi = contribution[
        contribution["group"].str.startswith("All") & (contribution["component"] == "ASI")
    ].iloc[0]
    top_asi = contribution[
        contribution["group"].str.startswith("Top") & (contribution["component"] == "ASI")
    ].iloc[0]
    unstable = mismatch[mismatch["probability_primary_class"] < 0.80]
    text = f"""Q1 ADDITIONAL ROBUSTNESS AUDIT
================================

Demand source: {demand_source}
Grid source: {grid_source}

Association diagnosis
---------------------
Primary n={int(primary.n)}: rho={primary.rho:.3f}; permutation p={primary.permutation_p:.3f};
bootstrap 95% CI [{primary.bootstrap_95CI_low:.3f}, {primary.bootstrap_95CI_high:.3f}];
two-sided critical |rho|≈{primary['critical_abs_rho_alpha_0.05']:.3f}.

Non-manual n={int(nonmanual.n)}: rho={nonmanual.rho:.3f}; permutation p={nonmanual.permutation_p:.3f};
bootstrap 95% CI [{nonmanual.bootstrap_95CI_low:.3f}, {nonmanual.bootstrap_95CI_high:.3f}];
critical |rho|≈{nonmanual['critical_abs_rho_alpha_0.05']:.3f}.

Strict n={int(strict.n)}: rho={strict.rho:.3f}; permutation p={strict.permutation_p:.3f};
bootstrap 95% CI [{strict.bootstrap_95CI_low:.3f}, {strict.bootstrap_95CI_high:.3f}];
critical |rho|≈{strict['critical_abs_rho_alpha_0.05']:.3f}.

Interpretation: point estimates are near zero, but the tests are underpowered and the
confidence intervals are compatible with materially negative and positive relationships.
Coordinate restrictions test spatial-assignment sensitivity; they do not establish a
robust null association because n and power decrease.

Weight contribution diagnosis
-----------------------------
ASI nominal hybrid weight: {WEIGHTS['ASI']:.4f}.
ASI share of mean AECS across all grids: {all_asi.share_of_mean_AECS:.1%}.
ASI share of mean AECS among top-20 grids: {top_asi.share_of_mean_AECS:.1%}.

Interpretation: ASI does not contribute one-half of every AECS value. Its realized mean
contribution is small over all grids because ASI is mostly zero, but it becomes the largest
mean contribution in the top-priority tail. Report both nominal weights and realized
contribution shares.

Temporal mismatch uncertainty
-----------------------------
Destinations with <80% probability of retaining the primary class under within-destination
annual resampling: {', '.join(unstable['destination']) if len(unstable) else 'none'}.

Use the mismatch values as sample-relative descriptive diagnostics, round them to two
decimals in narrative text, and avoid population-level or causal claims.
"""
    (OUT_DIR / "AUDIT_SUMMARY.txt").write_text(text, encoding="utf-8")
    print(text)


# ---------------------------------------------------------------------------
# 08. RUN
# ---------------------------------------------------------------------------

def main() -> None:
    demand, demand_source = load_demand()
    grid, grid_source = load_grid()

    association, loo, power = association_audit(demand)
    mismatch = temporal_mismatch_audit(demand)
    contribution = contribution_audit(grid)
    spatial_structure = spatial_structure_audit(grid)
    validation_no_tai = leave_tai_out_validation(grid)

    association.to_csv(OUT_DIR / "Table_Q1_Association_Diagnostics.csv", index=False)
    loo.to_csv(OUT_DIR / "Table_Q1_Leave_One_Out.csv", index=False)
    power.to_csv(OUT_DIR / "Table_Q1_Power.csv", index=False)
    mismatch.to_csv(OUT_DIR / "Table_Q1_Temporal_Mismatch_Uncertainty.csv", index=False)
    contribution.to_csv(OUT_DIR / "Table_Q1_Weight_Contributions.csv", index=False)
    spatial_structure.to_csv(OUT_DIR / "Table_Q1_ASI_MAUP_Audit.csv", index=False)
    validation_no_tai.to_csv(OUT_DIR / "Table_Q1_Leave_TAI_Out_Validation.csv", index=False)

    with pd.ExcelWriter(OUT_DIR / "AECS_Q1_ADDITIONAL_AUDIT.xlsx", engine="openpyxl") as writer:
        association.to_excel(writer, sheet_name="association", index=False)
        loo.to_excel(writer, sheet_name="leave_one_out", index=False)
        power.to_excel(writer, sheet_name="power", index=False)
        mismatch.to_excel(writer, sheet_name="mismatch_uncertainty", index=False)
        contribution.to_excel(writer, sheet_name="weight_contribution", index=False)
        spatial_structure.to_excel(writer, sheet_name="ASI_MAUP", index=False)
        validation_no_tai.to_excel(writer, sheet_name="leave_TAI_out", index=False)

    plot_power(power)
    plot_association(association)
    write_summary(demand_source, grid_source, association, contribution, mismatch)

    print(f"Outputs saved to: {OUT_DIR}")


if __name__ == "__main__":
    main()