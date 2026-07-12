"""Build the audited, evidence-supported figure set for Lecture 1.

The output inventory is intentionally smaller than the original slide plan.  A
figure is emitted only when the normalized Task 2 data can support its visual
form; header-only and single-period time-series inputs remain withheld.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import Callable, NamedTuple, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt


INK = "#172132"
PAPER = "#F7F3EA"
BRICK = "#C9583E"
BLUE = "#4B718A"
GOLD = "#C59A45"
MUTED = "#6F746F"
PALE = "#D8D1C3"
RULE = PALE

ECONOMY_COLORS = {
    "China": BRICK,
    "United States": BLUE,
    "Euro area": GOLD,
    "Japan": INK,
}

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "lecture1"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "assets" / "figures" / "lecture1"

OWNED_FILENAMES = {
    "payment_inclusion.svg",
    "private_credit_gdp_four_systems.svg",
    "deposits_relative_to_gdp.svg",
    "afre_relative_to_gdp.svg",
    "tsf_composition.svg",
    "market_cap_gdp_available_systems.svg",
    "china_banking_insurance_assets_two_quarters.svg",
    "afre_channels.svg",
    "sector_leverage.svg",
    "broad_local_debt.svg",
    # Known planned or superseded outputs are cleaned without touching caller files.
    "deposits_timeseries.svg",
    "credit_allocation.svg",
    "tsf_total_timeseries.svg",
    "tsf_mix_timeseries.svg",
    "bond_market_gdp_four_systems.svg",
    "market_cap_gdp_four_systems.svg",
    "financial_structure_small_multiples.svg",
}

LEGACY_CLEANUP_FILENAMES = {
    "bank_efficiency.svg",
}

PRIVATE_CREDIT_ECONOMIES = {"China", "United States", "Euro area", "Japan"}
MARKET_CAP_ECONOMIES = {"China", "United States", "Japan"}
ASSET_SERIES = {
    "Banking institutions assets",
    "Insurance and insurance asset-management assets",
}
TSF_CATEGORIES = {
    "RMB loans to real economy",
    "Government bonds",
    "Corporate bonds",
    "Domestic equity of non-financial enterprises",
    "Other components",
}
DEPOSIT_SERIES = {
    "Household RMB deposits",
    "Non-financial enterprise RMB deposits",
}
AFRE_SERIES = {"AFRE annual flow", "AFRE year-end stock"}
AFRE_CHANNEL_SERIES = {
    "Bank loans", "Off-balance-sheet financing",
    "Market-based direct financing", "Other forms of financing",
}
LEVERAGE_SERIES = {
    "Household", "Nonfinancial corporations", "Central government", "Local government",
}


class FigureJob(NamedTuple):
    render: Callable[[Path], None]


def _configure() -> None:
    mpl.rcParams.update(
        {
            "font.family": ["Arial", "Helvetica Neue", "DejaVu Sans"],
            "font.size": 11,
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "text.color": INK,
            "axes.labelcolor": MUTED,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "svg.fonttype": "none",
            "svg.hashsalt": "lecture1-evidence-led-v1",
        }
    )


def _read(dataset_id: str, data_dir: Path = DATA_DIR) -> list[dict[str, str]]:
    with (data_dir / f"{dataset_id}.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if row.get("value", "").strip()]


def _manifest(data_dir: Path = DATA_DIR) -> dict[str, dict[str, str]]:
    with (data_dir / "source_manifest.csv").open(encoding="utf-8", newline="") as handle:
        return {row["dataset_id"]: row for row in csv.DictReader(handle)}


def _style_axis(ax: mpl.axes.Axes, *, grid: str | None = "y") -> None:
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="both", length=0, pad=7)
    if grid:
        ax.grid(axis=grid, color=INK, alpha=0.10, linewidth=0.8)
        ax.set_axisbelow(True)


def _footer(fig: mpl.figure.Figure, source: str) -> None:
    fig.text(0.965, 0.028, f"Source: {source}", ha="right", color=MUTED, fontsize=8.8)


def save_svg(fig: mpl.figure.Figure, path: Path) -> None:
    """Write a deterministic fixed 864 x 486 point SVG."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.set_size_inches(12, 6.75, forward=True)
    fig.savefig(
        path,
        format="svg",
        metadata={"Date": None, "Creator": "make_lecture1_figures.py"},
    )
    plt.close(fig)


def line_chart(
    ax: mpl.axes.Axes,
    series: dict[str, Sequence[tuple[str, float]]],
    *,
    colors: dict[str, str],
    ylabel: str,
    endpoint_format: Callable[[float], str] = lambda value: f"{value:.1f}",
) -> None:
    """Draw lines with direct endpoint labels instead of a detached legend."""
    all_periods = sorted({period for values in series.values() for period, _ in values})
    x_lookup = {period: index for index, period in enumerate(all_periods)}
    for label, values in series.items():
        x = [x_lookup[period] for period, _ in values]
        y = [value for _, value in values]
        color = colors[label]
        ax.plot(x, y, color=color, linewidth=2.5, marker="o", markersize=3.8)
        ax.text(
            x[-1] + 0.28,
            y[-1],
            f"{label}  {endpoint_format(y[-1])}",
            color=color,
            va="center",
            fontsize=10.2,
            weight="bold",
            clip_on=False,
        )
    tick_indexes = sorted({*range(0, len(all_periods), 5), len(all_periods) - 1})
    ax.set_xticks(tick_indexes, [all_periods[index] for index in tick_indexes])
    ax.set_xlim(-0.4, len(all_periods) + 3.7)
    ax.set_ylabel(ylabel)
    _style_axis(ax)


def stacked_share(
    ax: mpl.axes.Axes,
    labels: Sequence[str],
    shares: Sequence[float],
    colors: Sequence[str],
) -> None:
    """Draw one exhaustive stacked share with category/value labels on or adjacent."""
    left = 0.0
    centers: list[float] = []
    for label, share, color in zip(labels, shares, colors):
        ax.barh(0, share, left=left, height=0.36, color=color)
        centers.append(left + share / 2)
        left += share
    ax.text(centers[0], 0, f"{labels[0]} · {shares[0]:g}%", ha="center", va="center",
            color=PAPER, fontsize=9, weight="bold")
    placements = (
        (centers[1], 0.46, "center"),
        (centers[2] + 1.0, 0.72, "right"),
        (98.0, 1.00, "right"),
        (98.0, -0.48, "right"),
    )
    for index, (text_x, text_y, align) in enumerate(placements, start=1):
        ax.annotate(
            f"{labels[index]} · {shares[index]:g}%",
            xy=(centers[index], 0.19 if text_y > 0 else -0.19),
            xytext=(text_x, text_y), ha=align, va="center", fontsize=8.4,
            weight="bold", color=INK,
            arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.8},
        )
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.72, 1.18)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    _style_axis(ax, grid="x")


def dot_plot(
    ax: mpl.axes.Axes,
    periods: Sequence[str],
    values: Sequence[float],
    *,
    color: str,
    value_format: Callable[[float], str],
) -> None:
    """Draw a compact observed-period dot plot with direct value labels."""
    x = list(range(len(periods)))
    ax.plot(x, values, color=color, linewidth=2.6)
    ax.scatter(x, values, s=70, color=color, zorder=3)
    spread = max(values) - min(values)
    pad = max(spread * 6, max(values) * 0.025, 0.04)
    ax.set_ylim(min(values) - pad, max(values) + pad)
    ax.set_xticks(x, periods)
    for index, value in enumerate(values):
        ax.text(index, value + pad * 0.22, value_format(value), ha="center",
                va="bottom", color=color, weight="bold")
    _style_axis(ax)


def two_period_bars(
    axes: Sequence[mpl.axes.Axes],
    series: Sequence[tuple[str, Sequence[str], Sequence[float], str]],
    *,
    unit: str,
) -> None:
    """Draw level bars on explicit separate panel scales; no trend slopes."""
    for ax, (label, periods, values, color) in zip(axes, series):
        x = list(range(len(periods)))
        ax.bar(x, values, color=color, width=0.52)
        ax.set_xticks(x, periods)
        ax.set_ylabel(unit)
        ax.text(0.0, 1.08, label, transform=ax.transAxes, fontsize=12, weight="bold")
        for index, value in enumerate(values):
            ax.text(index, value + max(values) * 0.025, f"{value:.1f}", color=color,
                    ha="center", va="bottom", weight="bold")
        ax.set_ylim(0, max(values) * 1.18)
        _style_axis(ax)


def _group(rows: list[dict[str, str]]) -> dict[str, list[tuple[str, float]]]:
    grouped: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for row in rows:
        grouped[row["economy"]].append((row["period"], float(row["value"])))
    for values in grouped.values():
        values.sort(key=lambda item: item[0])
    return dict(grouped)


def _payment_inclusion(path: Path, source: str, data_dir: Path) -> None:
    rows = _read("payment_adoption", data_dir)
    by_series: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_series[row["series"]].append(row)
    users = sorted(by_series["Online payment users"], key=lambda row: row["period"])
    rates = sorted(by_series["Online payment utilization rate"], key=lambda row: row["period"])
    segments = ((2007, 2018), (2020, 2024))
    milestones = {2007, 2014, 2018, 2020, 2024}
    fig, (ax_users, ax_rate) = plt.subplots(
        2, 1, figsize=(12, 6.75), sharex=True,
        gridspec_kw={"height_ratios": [1.45, 1]},
    )
    fig.subplots_adjust(left=0.10, right=0.93, top=0.90, bottom=0.15, hspace=0.18)
    user_values = [float(row["value"]) for row in users]
    for start, end in segments:
        segment = [row for row in users if start <= int(row["period"]) <= end]
        years = [int(row["period"]) for row in segment]
        values = [float(row["value"]) for row in segment]
        ax_users.plot(years, values, color=BLUE, marker="o", markersize=3.8, linewidth=2.5)
        ax_users.fill_between(years, values, 0, color=BLUE, alpha=0.10)
    ax_users.set_ylabel("Million users")
    ax_users.set_ylim(0, max(user_values) * 1.20)
    for row in users:
        year = int(row["period"])
        if year in milestones:
            value = float(row["value"])
            ax_users.text(year, value + 22, f"{value:,.2f}", ha="center", weight="bold")
    ax_users.text(0, 1.06, "China · Online/network payment",
                  transform=ax_users.transAxes, weight="bold", fontsize=12)
    _style_axis(ax_users)

    rate_values = [float(row["value"]) for row in rates]
    for start, end in segments:
        segment = [row for row in rates if start <= int(row["period"]) <= end]
        years = [int(row["period"]) for row in segment]
        values = [float(row["value"]) for row in segment]
        ax_rate.plot(years, values, color=BRICK, marker="o", markersize=3.8, linewidth=2.5)
    ax_rate.set_ylabel("Percent of internet users")
    ax_rate.set_ylim(min(rate_values) - 3, max(rate_values) + 3)
    ax_rate.set_xticks([2007, 2010, 2014, 2018, 2020, 2024])
    for row in rates:
        year = int(row["period"])
        if year in milestones:
            value = float(row["value"])
            ax_rate.text(year, value + 0.7, f"{value:.1f}%", ha="center",
                         color=BRICK, weight="bold")
    for axis in (ax_users, ax_rate):
        axis.axvline(2019, color=RULE, linewidth=1.2, linestyle=(0, (3, 3)))
    ax_users.text(2019, ax_users.get_ylim()[1] * 0.88,
                  "2019: no year-end observation", ha="center", color=MUTED, fontsize=9)
    _style_axis(ax_rate)
    _footer(fig, source)
    save_svg(fig, path)


def _private_credit(path: Path, source: str, data_dir: Path) -> None:
    series = _group(_read("private_credit_gdp", data_dir))
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.10, right=0.78, top=0.91, bottom=0.15)
    line_chart(ax, series, colors=ECONOMY_COLORS, ylabel="Percent of GDP",
               endpoint_format=lambda value: f"{value:.1f}%")
    ax.text(0, 1.04, "Credit to private non-financial sector", transform=ax.transAxes,
            color=MUTED, fontsize=10)
    _footer(fig, source)
    save_svg(fig, path)


def _deposits_relative_to_gdp(path: Path, source: str, data_dir: Path) -> None:
    """Render two deposit stocks in RMB tn and as percentages of 2025 GDP."""
    deposits = {row["series"]: row for row in _read("deposits_by_holder", data_dir)}
    gdp = _read("nominal_gdp", data_dir)[0]
    ordered = ["Household RMB deposits", "Non-financial enterprise RMB deposits"]
    values = [float(deposits[name]["value"]) for name in ordered]
    denominator = float(gdp["value"])
    ratios = [100 * value / denominator for value in values]

    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.34, right=0.94, top=0.78, bottom=0.20)
    y = [1, 0]
    ax.barh(y, values, color=[BLUE, GOLD], height=0.48)
    ax.set_yticks(y, ordered)
    ax.set_xlabel("RMB trillion")
    ax.set_xlim(0, max(values) * 1.28)
    for position, value, ratio, color in zip(y, values, ratios, [BLUE, GOLD]):
        ax.text(value + max(values) * 0.025, position,
                f"{value:.4f}  |  {ratio:.1f}%",
                va="center", color=color, weight="bold", fontsize=11.5)
    ax.text(0, 1.22, f"China deposit stocks at {deposits[ordered[0]]['period']}",
            transform=ax.transAxes, fontsize=13, weight="bold")
    ax.text(0, 1.12,
            f"Percent labels: stock / annual GDP ({gdp['period']} GDP = {denominator:.4f} RMB trillion)",
            transform=ax.transAxes, color=MUTED, fontsize=10)
    _style_axis(ax, grid="x")
    _footer(fig, source)
    save_svg(fig, path)


def _afre_relative_to_gdp(path: Path, source: str, data_dir: Path) -> None:
    """Render AFRE annual flow/GDP separately from year-end stock/annual GDP."""
    afre = {row["series"]: row for row in _read("tsf_total", data_dir)}
    gdp = _read("nominal_gdp", data_dir)[0]
    denominator = float(gdp["value"])
    flow = float(afre["AFRE annual flow"]["value"])
    stock = float(afre["AFRE year-end stock"]["value"])
    values = [100 * flow / denominator, 100 * stock / denominator]

    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.30, right=0.94, top=0.78, bottom=0.20)
    y = [1, 0]
    ax.barh(y, values, color=[BRICK, BLUE], height=0.48)
    ax.set_yticks(y, ["AFRE annual flow", "AFRE year-end stock"])
    ax.set_xlabel("Percent of 2025 nominal GDP")
    ax.set_xlim(0, max(values) * 1.18)
    details = [
        (flow, values[0], "flow / annual GDP"),
        (stock, values[1], "stock / annual GDP - scale benchmark"),
    ]
    for position, (amount, ratio, definition), color in zip(y, details, [BRICK, BLUE]):
        ax.text(ratio + max(values) * 0.018, position,
                f"{amount:.1f} RMB tn  |  {ratio:.1f}%",
                va="center", color=color, weight="bold", fontsize=11.5)
        ax.text(0, position - 0.32, definition, color=MUTED, fontsize=9.3)
    ax.text(0, 1.22, "China AFRE scale relative to the economy", transform=ax.transAxes,
            fontsize=13, weight="bold")
    ax.text(0, 1.12,
            f"2025 nominal GDP = {denominator:.4f} RMB trillion; stock is not an annual financing rate",
            transform=ax.transAxes, color=MUTED, fontsize=10)
    _style_axis(ax, grid="x")
    _footer(fig, source)
    save_svg(fig, path)


def _tsf_composition(path: Path, source: str, data_dir: Path) -> None:
    rows = _read("tsf_mix", data_dir)
    period = next(iter({row["period"] for row in rows}))
    labels = [row["series"] for row in rows]
    shares = [float(row["value"]) for row in rows]
    colors = [BLUE, BRICK, GOLD, INK, MUTED]
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.08, right=0.95, top=0.72, bottom=0.20)
    stacked_share(ax, labels, shares, colors)
    ax.text(0, 1.24, f"China · {period}", transform=ax.transAxes, fontsize=13, weight="bold")
    ax.text(0, 1.15, "Percent of TSF stock", transform=ax.transAxes, color=MUTED, fontsize=10)
    _footer(fig, source)
    save_svg(fig, path)


def _market_cap(path: Path, source: str, data_dir: Path) -> None:
    series = _group(_read("market_cap_gdp", data_dir))
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.10, right=0.78, top=0.91, bottom=0.15)
    colors = {economy: ECONOMY_COLORS[economy] for economy in series}
    line_chart(ax, series, colors=colors, ylabel="Percent of GDP",
               endpoint_format=lambda value: f"{value:.1f}%")
    ax.text(0, 1.04, "Listed domestic companies market capitalization", transform=ax.transAxes,
            color=MUTED, fontsize=10)
    fig.text(0.10, 0.955, "Available economies: China · United States · Japan",
             fontsize=9.5, weight="bold")
    _footer(fig, source)
    save_svg(fig, path)


def _financial_structure(path: Path, source: str, data_dir: Path) -> None:
    rows = _read("financial_sector_assets", data_dir)
    by_series: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_series[row["series"]].append(row)
    ordered_names = [
        "Banking institutions assets",
        "Insurance and insurance asset-management assets",
    ]
    panel_data = []
    for index, name in enumerate(ordered_names):
        observations = sorted(by_series[name], key=lambda row: row["period"])
        panel_data.append(
            (name, [row["period"] for row in observations],
             [float(row["value"]) for row in observations], [BLUE, GOLD][index])
        )
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.75))
    fig.subplots_adjust(left=0.10, right=0.95, top=0.72, bottom=0.20, wspace=0.34)
    two_period_bars(axes, panel_data, unit="RMB trillion")
    fig.text(0.10, 0.94, "China", weight="bold", fontsize=13)
    fig.text(0.10, 0.89, "NFRA observations: 2025Q4 and 2026Q1", color=MUTED, fontsize=10)
    fig.text(0.95, 0.89, "Separate panel scales", ha="right", color=MUTED, fontsize=9)
    _footer(fig, source)
    save_svg(fig, path)


def _afre_channels(path: Path, source: str, data_dir: Path) -> None:
    rows = _read("afre_channels", data_dir)
    order = [
        "Bank loans", "Off-balance-sheet financing",
        "Market-based direct financing", "Other forms of financing",
    ]
    by_series = {
        name: sorted(
            [(int(row["period"]), float(row["value"])) for row in rows if row["series"] == name]
        )
        for name in order
    }
    years = [year for year, _ in by_series[order[0]]]
    values = [[value for _, value in by_series[name]] for name in order]
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.08, right=0.78, top=0.91, bottom=0.12)
    colors = [GOLD, PALE, BLUE, BRICK]
    ax.stackplot(years, values, colors=colors, alpha=0.94)
    ax.set_ylabel("Percent of GDP")
    ax.set_xlim(years[0], years[-1] + 4.6)
    ax.set_ylim(0, 300)
    ax.set_xticks([2002, 2005, 2008, 2011, 2014, 2017, 2021])
    cumulative = 0.0
    for name, series_values, color in zip(order, values, colors):
        endpoint = series_values[-1]
        label_y = cumulative + endpoint / 2
        ax.text(2021.35, label_y, f"{name}  {endpoint:.1f}%",
                color=INK if color != BRICK else BRICK, va="center",
                fontsize=9.3, weight="bold", clip_on=False)
        cumulative += endpoint
    ax.text(0, 1.04, "AFRE stock / GDP by financing channel · China",
            transform=ax.transAxes, fontsize=12.5, weight="bold")
    ax.text(0, 0.98, "Published chart values vector-digitized; plotted approximations",
            transform=ax.transAxes, fontsize=9.2, color=MUTED)
    _style_axis(ax)
    _footer(fig, source)
    save_svg(fig, path)


def _sector_leverage(path: Path, source: str, data_dir: Path) -> None:
    rows = _read("sector_leverage", data_dir)
    order = ["Nonfinancial corporations", "Household", "Local government", "Central government"]
    colors = {
        "Nonfinancial corporations": BRICK,
        "Household": BLUE,
        "Local government": GOLD,
        "Central government": INK,
    }
    series = {
        name: sorted(
            [(row["period"], float(row["value"])) for row in rows if row["series"] == name]
        )
        for name in order
    }
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.08, right=0.78, top=0.90, bottom=0.12)
    line_chart(ax, series, colors=colors, ylabel="Percent of GDP",
               endpoint_format=lambda value: f"{value:.0f}%")
    ax.set_ylim(0, 185)
    ax.text(0, 1.05, "Debt / GDP by sector · China",
            transform=ax.transAxes, fontsize=12.5, weight="bold")
    ax.text(0, 0.99, "LGFV debt is included in nonfinancial corporations, not local government",
            transform=ax.transAxes, fontsize=9.2, color=MUTED)
    _footer(fig, source)
    save_svg(fig, path)


def _broad_local_debt(path: Path, source: str, data_dir: Path) -> None:
    rows = sorted(_read("broad_local_debt", data_dir), key=lambda row: row["period"])
    years = [int(row["period"]) for row in rows]
    values = [float(row["value"]) for row in rows]
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.08, right=0.94, top=0.90, bottom=0.13)
    ax.plot(years, values, color=BRICK, linewidth=3.2, marker="o", markersize=5.5)
    ax.fill_between(years, values, min(values) - 3, color=BRICK, alpha=0.08)
    ax.set_ylabel("Percent of GDP")
    ax.set_xticks(years)
    ax.set_ylim(38, 73)
    ax.text(years[0], values[0] - 2.2, f"{values[0]:.2f}%", color=BRICK,
            ha="center", va="top", fontsize=11, weight="bold")
    ax.text(years[-1], values[-1] + 1.4, f"{values[-1]:.2f}%", color=BRICK,
            ha="center", va="bottom", fontsize=11, weight="bold")
    ax.text(0, 1.05, "Broad local government debt · China",
            transform=ax.transAxes, fontsize=12.5, weight="bold")
    ax.text(0, 0.99, "Broad measure = official local debt + LGFV liabilities",
            transform=ax.transAxes, fontsize=9.2, color=MUTED)
    ax.text(1, 0.99, "Published chart values vector-digitized",
            transform=ax.transAxes, fontsize=9.2, color=MUTED, ha="right")
    _style_axis(ax)
    _footer(fig, source)
    save_svg(fig, path)


def _common_periods(rows: list[dict[str, str]], field: str) -> set[str]:
    groups: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        groups[row[field]].add(row["period"])
    return set.intersection(*groups.values()) if groups else set()


def determine_figure_jobs(data_dir: Path) -> dict[str, FigureJob]:
    """Return render jobs only when the audited data satisfy each figure contract."""
    records = _manifest(data_dir)

    def available(dataset_id: str) -> bool:
        row = records.get(dataset_id)
        return row is not None and "coverage_unavailable" not in row["notes"]

    jobs: dict[str, FigureJob] = {}

    payment = _read("payment_adoption", data_dir)
    payment_series = {row["series"] for row in payment}
    payment_period_sets = {
        series: {row["period"] for row in payment if row["series"] == series}
        for series in payment_series
    }
    audited_payment_periods = (
        {str(year) for year in range(2007, 2019)}
        | {str(year) for year in range(2020, 2025)}
    )
    if (available("payment_adoption") and {row["economy"] for row in payment} == {"China"}
            and payment_series == {"Online payment users", "Online payment utilization rate"}
            and all(periods == audited_payment_periods
                    for periods in payment_period_sets.values())):
        jobs["payment_inclusion.svg"] = FigureJob(
            partial(_payment_inclusion, source="CNNIC", data_dir=data_dir))

    credit = _read("private_credit_gdp", data_dir)
    if (available("private_credit_gdp")
            and {row["economy"] for row in credit} == PRIVATE_CREDIT_ECONOMIES
            and {row["series"] for row in credit} == {"Credit to private non-financial sector"}
            and len(_common_periods(credit, "economy")) >= 2):
        jobs["private_credit_gdp_four_systems.svg"] = FigureJob(
            partial(_private_credit, source="BIS via Federal Reserve Bank of St. Louis (FRED)", data_dir=data_dir))

    gdp = _read("nominal_gdp", data_dir)
    exact_gdp = (
        available("nominal_gdp") and len(gdp) == 1
        and {row["series"] for row in gdp} == {"Nominal gross domestic product"}
        and {row["economy"] for row in gdp} == {"China"}
        and {row["period"] for row in gdp} == {"2025"}
        and {row["unit"] for row in gdp} == {"RMB trillion"}
    )

    deposits = _read("deposits_by_holder", data_dir)
    if (exact_gdp and available("deposits_by_holder") and len(deposits) == 2
            and {row["series"] for row in deposits} == DEPOSIT_SERIES
            and {row["economy"] for row in deposits} == {"China"}
            and {row["period"] for row in deposits} == {"2025-11"}
            and {row["unit"] for row in deposits} == {"RMB trillion"}):
        jobs["deposits_relative_to_gdp.svg"] = FigureJob(
            partial(_deposits_relative_to_gdp, source="PBOC; NBS", data_dir=data_dir))

    afre = _read("tsf_total", data_dir)
    if (exact_gdp and available("tsf_total") and len(afre) == 2
            and {row["series"] for row in afre} == AFRE_SERIES
            and {row["economy"] for row in afre} == {"China"}
            and {row["period"] for row in afre} == {"2025"}
            and {row["unit"] for row in afre} == {"RMB trillion"}):
        jobs["afre_relative_to_gdp.svg"] = FigureJob(
            partial(_afre_relative_to_gdp, source="PBOC; NBS", data_dir=data_dir))

    tsf = _read("tsf_mix", data_dir)
    tsf_common = _common_periods(tsf, "series")
    if (available("tsf_mix") and {row["economy"] for row in tsf} == {"China"}
            and {row["series"] for row in tsf} == TSF_CATEGORIES
            and len(tsf) == len(TSF_CATEGORIES) and len(tsf_common) == 1
            and abs(sum(float(row["value"]) for row in tsf) - 100.0) < 1e-9):
        jobs["tsf_composition.svg"] = FigureJob(
            partial(_tsf_composition, source="PBOC", data_dir=data_dir))

    market = _read("market_cap_gdp", data_dir)
    if (available("market_cap_gdp") and {row["economy"] for row in market} == MARKET_CAP_ECONOMIES
            and {row["series"] for row in market} == {"Listed domestic companies market capitalization"}
            and len(_common_periods(market, "economy")) >= 2):
        jobs["market_cap_gdp_available_systems.svg"] = FigureJob(
            partial(_market_cap, source="World Bank, WDI", data_dir=data_dir))

    assets = _read("financial_sector_assets", data_dir)
    exact_asset_periods = {"2025Q4", "2026Q1"}
    asset_period_sets = {
        series: {row["period"] for row in assets if row["series"] == series}
        for series in ASSET_SERIES
    }
    if (available("financial_sector_assets") and {row["economy"] for row in assets} == {"China"}
            and {row["series"] for row in assets} == ASSET_SERIES
            and len(assets) == 4
            and all(periods == exact_asset_periods for periods in asset_period_sets.values())):
        jobs["china_banking_insurance_assets_two_quarters.svg"] = FigureJob(
            partial(_financial_structure, source="NFRA", data_dir=data_dir))

    afre_channels = _read("afre_channels", data_dir)
    if (available("afre_channels") and len(afre_channels) == 80
            and {row["series"] for row in afre_channels} == AFRE_CHANNEL_SERIES
            and {row["economy"] for row in afre_channels} == {"China"}
            and {row["period"] for row in afre_channels} == {str(y) for y in range(2002, 2022)}
            and {row["unit"] for row in afre_channels} == {"percent of GDP"}):
        jobs["afre_channels.svg"] = FigureJob(
            partial(_afre_channels, source="He & Wei (2022), Figure 1 (vector-digitized)", data_dir=data_dir))

    leverage = _read("sector_leverage", data_dir)
    if (available("sector_leverage") and len(leverage) == 96
            and {row["series"] for row in leverage} == LEVERAGE_SERIES
            and {row["economy"] for row in leverage} == {"China"}
            and {row["period"] for row in leverage} == {str(y) for y in range(2000, 2024)}
            and {row["unit"] for row in leverage} == {"percent of GDP"}):
        jobs["sector_leverage.svg"] = FigureJob(
            partial(_sector_leverage, source="Chang, Wang & Xiong (2025), Figure 5 public data", data_dir=data_dir))

    broad_debt = _read("broad_local_debt", data_dir)
    if (available("broad_local_debt") and len(broad_debt) == 8
            and {row["series"] for row in broad_debt} == {"Broad local government debt"}
            and {row["economy"] for row in broad_debt} == {"China"}
            and {row["period"] for row in broad_debt} == {str(y) for y in range(2015, 2023)}
            and {row["unit"] for row in broad_debt} == {"percent of GDP"}):
        jobs["broad_local_debt.svg"] = FigureJob(
            partial(_broad_local_debt, source="Chang, Wang & Xiong (2025), Figure 6 (vector-digitized)", data_dir=data_dir))

    return jobs


def main(output_dir: Path = DEFAULT_OUTPUT_DIR, *, data_dir: Path = DATA_DIR) -> None:
    """Generate only the jobs selected by audited manifest and data gates."""
    _configure()
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in OWNED_FILENAMES | LEGACY_CLEANUP_FILENAMES:
        stale = output_dir / filename
        if stale.exists():
            stale.unlink()
    for filename, job in determine_figure_jobs(data_dir).items():
        job.render(output_dir / filename)


if __name__ == "__main__":
    main()
