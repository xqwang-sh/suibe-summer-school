"""Reproducibly draw the quantitative figures used by the two lectures."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt

try:
    from scripts.prepare_lecture2_data import read_equity_submarket_cap
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from prepare_lecture2_data import read_equity_submarket_cap


INK = "#172132"
PAPER = "#F7F3EA"
BRICK = "#C9583E"
BLUE = "#4B718A"
GOLD = "#C59A45"
MUTED = "#6F746F"

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "assets" / "figures"
MARKET_CAP_DATA = Path(__file__).resolve().parents[1] / "data" / "lecture1" / "market_cap_gdp.csv"
FIGURE_NAMES = (
    "payment_adoption.svg",
    "tsf_composition_2025.svg",
    "bond_composition_2025.svg",
    "bond_venues_2025.svg",
    "interbank_investors.svg",
    "bond_market_by_venue_timeseries.svg",
    "stock_connect_adt.svg",
    "private_funds_2025.svg",
    "l2_market_cap_gdp_timeseries.svg",
    "l2_market_cap_gdp_latest.svg",
    "l2_equity_submarkets_market_cap.svg",
    "l2_stock_connect_adt.svg",
)

# Verified baseline for this build: the seven tables and references in
# comments-0709.md, sections IV–V. Primary-URL re-verification is deferred.
SOURCE_URLS = {
    "payment_adoption.svg": "https://www.cnnic.com.cn/IDR/ReportDownloads/202505/P020250514564119130448.pdf",
    "tsf_composition_2025.svg": "https://jrj.sh.gov.cn/ZXYW178/20260116/88e3368ecfee4e639ae9aa8dd93729c3.html",
    "bond_composition_2025.svg": "https://cif.mofcom.gov.cn/cif/html/upload/20251201140144995_2025%E5%B9%B410%E6%9C%88%E4%BB%BD%E9%87%91%E8%9E%8D%E5%B8%82%E5%9C%BA%E8%BF%90%E8%A1%8C%E6%83%85%E5%86%B5.pdf",
    "bond_venues_2025.svg": "https://cif.mofcom.gov.cn/cif/html/upload/20251201140144995_2025%E5%B9%B410%E6%9C%88%E4%BB%BD%E9%87%91%E8%9E%8D%E5%B8%82%E5%9C%BA%E8%BF%90%E8%A1%8C%E6%83%85%E5%86%B5.pdf",
    "interbank_investors.svg": "https://www.nafmii.org.cn/englishnew/overseasparticipation/pandabond/resources/202504/P020250423396158840864.pdf",
    "bond_market_by_venue_timeseries.svg": "https://www.pbc.gov.cn/goutongjiaoliu/113456/113469/2025122616592613805/2025122616590775273.pdf",
    "stock_connect_adt.svg": "https://www.hkexgroup.com/Media-Centre/Insight/Insight/2026/HKEX-Insight/Stock-Connect-2025-Review?sc_lang=en",
    "private_funds_2025.svg": "https://www.amac.org.cn/sjtj/tjbg/smjj/202601/P020260126611919011850.pdf",
    "l2_market_cap_gdp_timeseries.svg": "https://api.worldbank.org/v2/country/CHN;USA;JPN/indicator/CM.MKT.LCAP.GD.ZS",
    "l2_market_cap_gdp_latest.svg": "https://api.worldbank.org/v2/country/CHN;USA;JPN/indicator/CM.MKT.LCAP.GD.ZS",
    "l2_equity_submarkets_market_cap.svg": "data/lecture2/source_manifest.csv",
    "l2_stock_connect_adt.svg": "https://www.hkexgroup.com/Media-Centre/Insight/Insight/2026/HKEX-Insight/Stock-Connect-2025-Review?sc_lang=en",
}


def _configure() -> None:
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlecolor": INK,
            "axes.labelcolor": MUTED,
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "text.color": INK,
            "xtick.color": MUTED,
            "ytick.color": INK,
            "svg.fonttype": "none",
            "svg.hashsalt": "summer-school-figures-v1",
        }
    )


def save_svg(fig: mpl.figure.Figure, path: Path) -> None:
    """Save a fixed-canvas SVG without time-varying metadata, then close it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path,
        format="svg",
        metadata={"Date": None, "Creator": "summer-school/scripts/make_figures.py"},
    )
    plt.close(fig)


def style_axis(ax: mpl.axes.Axes, *, grid: str | None = "x") -> None:
    """Apply the shared restrained lecture-deck axis treatment."""
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="both", length=0, pad=7)
    if grid:
        ax.grid(axis=grid, color=INK, alpha=0.10, linewidth=0.8)
        ax.set_axisbelow(True)


def horizontal_bars(
    ax: mpl.axes.Axes,
    labels: Sequence[str],
    values: Sequence[float],
    *,
    colors: Sequence[str] | None = None,
    value_labels: Sequence[str] | None = None,
    xmax: float | None = None,
) -> None:
    """Draw labelled horizontal bars with consistent spacing and end labels."""
    palette = list(colors) if colors is not None else [BLUE] * len(values)
    y = list(range(len(labels)))
    ax.barh(y, values, color=palette, height=0.56)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    limit = xmax if xmax is not None else max(values) * 1.18
    ax.set_xlim(0, limit)
    labels_to_draw = value_labels or [f"{value:g}" for value in values]
    offset = limit * 0.015
    for row, (value, label) in enumerate(zip(values, labels_to_draw)):
        ax.text(value + offset, row, label, va="center", fontsize=11, weight="bold")
    style_axis(ax)


def stacked_share_bar(
    ax: mpl.axes.Axes,
    labels: Sequence[str],
    shares: Sequence[float],
    *,
    colors: Sequence[str],
) -> None:
    """Draw a 100% stacked bar with legible segment labels and a compact legend."""
    left = 0.0
    for label, share, color in zip(labels, shares, colors):
        ax.barh([0], [share], left=left, height=0.55, color=color, label=label)
        if share >= 7:
            text_color = PAPER if color in (INK, BRICK, BLUE, MUTED) else INK
            ax.text(
                left + share / 2,
                0,
                f"{share:g}%",
                ha="center",
                va="center",
                color=text_color,
                weight="bold",
                fontsize=11,
            )
        else:
            ax.annotate(
                f"{share:g}%",
                xy=(left + share / 2, 0.29),
                xytext=(left + share / 2, 0.58),
                ha="center",
                va="bottom",
                color=INK,
                weight="bold",
                fontsize=10.5,
                arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.9},
            )
        left += share
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.75, 0.75)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    style_axis(ax)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.24),
        ncol=2,
        frameon=False,
        fontsize=10,
        handlelength=1.2,
        columnspacing=1.5,
    )


def _title(ax: mpl.axes.Axes, title: str, subtitle: str) -> None:
    ax.set_title(title, loc="left", fontsize=20, weight="bold", pad=24)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=MUTED, fontsize=10.5)


def payment_adoption(path: Path) -> None:
    # CNNIC, 55th Statistical Report, Figure 26; December observations.
    data = [
        {"year": 2020, "users_mn": 854.34, "rate": 86.4},
        {"year": 2021, "users_mn": 903.63, "rate": 87.6},
        {"year": 2022, "users_mn": 911.44, "rate": 85.4},
        {"year": 2023, "users_mn": 953.86, "rate": 87.3},
        {"year": 2024, "users_mn": 1028.91, "rate": 92.8},
    ]
    years = [str(row["year"]) for row in data]
    users = [row["users_mn"] for row in data]
    rates = [row["rate"] for row in data]
    fig, (ax, rate_ax) = plt.subplots(
        2, 1, figsize=(12, 6.75), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]}
    )
    fig.subplots_adjust(left=0.09, right=0.96, top=0.82, bottom=0.13, hspace=0.18)
    x = list(range(len(years)))
    ax.bar(x, users, color=BLUE, width=0.58)
    ax.set_ylim(0, 1150)
    ax.set_ylabel("Million users")
    for i, value in enumerate(users):
        ax.text(i, value + 25, f"{value:,.2f}", ha="center", weight="bold")
    style_axis(ax, grid="y")
    _title(ax, "Online payment became mass infrastructure", "China online-payment users and share of internet users, Dec. 2020–Dec. 2024")

    rate_ax.plot(x, rates, color=BRICK, marker="o", linewidth=2.6, markersize=6)
    rate_ax.fill_between(x, rates, [80] * len(rates), color=BRICK, alpha=0.10)
    rate_ax.set_ylim(80, 96)
    rate_ax.set_ylabel("Utilisation")
    rate_ax.set_xticks(x, years)
    for i, value in enumerate(rates):
        rate_ax.text(i, value + 0.75, f"{value:.1f}%", ha="center", weight="bold", color=BRICK)
    style_axis(rate_ax, grid="y")
    fig.text(0.96, 0.025, "Source: CNNIC, 55th Statistical Report (Figure 26)", ha="right", color=MUTED, fontsize=9)
    save_svg(fig, path)


def tsf_composition(path: Path) -> None:
    # PBOC 2025 financial statistics; stock (not annual flow) at year-end.
    data = [
        ("RMB loans to real economy", 60.7, BLUE),
        ("Government bonds", 21.5, BRICK),
        ("Corporate bonds", 7.7, GOLD),
        ("Domestic equity of non-financial firms", 2.8, INK),
        ("Other components", 7.3, MUTED),
    ]
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.08, right=0.96, top=0.76, bottom=0.28)
    stacked_share_bar(
        ax,
        [row[0] for row in data],
        [row[1] for row in data],
        colors=[row[2] for row in data],
    )
    _title(ax, "Loans remain the largest component of TSF", "Share of total social financing stock at end-2025; total stock RMB 442.12tn")
    fig.text(0.96, 0.035, "Source: PBOC, 2025 Financial Statistics (preliminary)", ha="right", color=MUTED, fontsize=9)
    save_svg(fig, path)


def bond_composition(path: Path) -> None:
    # PBOC Financial Market Operations, end-October 2025 custody balances.
    data = [
        ("Local government bonds", 53.7),
        ("Financial bonds", 44.2),
        ("Treasury bonds", 39.4),
        ("Corporate credit bonds", 34.4),
        ("NCDs", 20.7),
        ("Credit ABS", 1.0),
    ]
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.25, right=0.94, top=0.78, bottom=0.14)
    horizontal_bars(
        ax,
        [row[0] for row in data],
        [row[1] for row in data],
        colors=[BRICK, BLUE, GOLD, INK, MUTED, "#B6AD9C"],
        value_labels=[f"{row[1]:.1f}" for row in data],
        xmax=62,
    )
    ax.set_xlabel("RMB trillion")
    _title(ax, "China's bond market is not mainly corporate debt", "Selected custody balances by bond type, end-October 2025")
    fig.text(0.94, 0.035, "Source: PBOC, Financial Market Operations, Oct. 2025", ha="right", color=MUTED, fontsize=9)
    save_svg(fig, path)


def bond_venues(path: Path) -> None:
    # PBOC Financial Market Operations, October 2025; turnover is monthly cash-bond turnover.
    data = [
        {"venue": "Interbank", "custody": 171.7, "turnover": 26.6},
        {"venue": "Exchange", "custody": 22.9, "turnover": 3.3},
    ]
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.18, right=0.94, top=0.77, bottom=0.17)
    horizontal_bars(
        ax,
        [row["venue"] for row in data],
        [row["custody"] for row in data],
        colors=[BLUE, GOLD],
        value_labels=[f'{row["custody"]:.1f}tn custody' for row in data],
        xmax=205,
    )
    for row, item in enumerate(data):
        ax.text(
            2,
            row + 0.20,
            f'October cash-bond turnover: RMB {item["turnover"]:.1f}tn',
            va="center",
            color=PAPER if item["custody"] > 50 else INK,
            fontsize=10,
        )
    ax.set_xlabel("Custody balance, RMB trillion")
    _title(ax, "The interbank venue dominates custody and trading", "Bond-market venue comparison, end-/during October 2025")
    fig.text(0.94, 0.035, "Source: PBOC, Financial Market Operations, Oct. 2025", ha="right", color=MUTED, fontsize=9)
    save_svg(fig, path)


def bond_market_by_venue_timeseries(path: Path) -> None:
    """Draw PBOC year-end bond custody split by trading venue."""
    years = list(range(2015, 2025))
    interbank = [43.9, 56.3, 65.4, 75.7, 86.4, 100.7, 114.7, 125.3, 137.0, 155.8]
    exchange = [4.0, 7.4, 8.6, 10.7, 12.7, 16.3, 18.8, 19.5, 20.9, 21.2]
    totals = [left + right for left, right in zip(interbank, exchange)]
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.09, right=0.97, top=0.94, bottom=0.13)
    ax.stackplot(
        years,
        interbank,
        exchange,
        labels=["Interbank market", "Exchange market"],
        colors=[BLUE, GOLD],
        alpha=0.92,
    )
    ax.plot(years, totals, color=INK, linewidth=1.8)
    ax.set_xlim(2014.7, 2024.35)
    ax.set_ylim(0, 190)
    ax.set_xticks(years)
    ax.set_ylabel("RMB trillion")
    style_axis(ax, grid="y")
    ax.legend(loc="upper left", frameon=False, ncol=2, fontsize=12)
    ax.annotate(
        "Total 177.0",
        xy=(2024, totals[-1]),
        xytext=(-8, 10),
        textcoords="offset points",
        ha="right",
        color=INK,
        fontsize=13,
        fontweight="bold",
    )
    ax.text(2023.9, 78, "Interbank\n155.8 · 88%", ha="right", color=PAPER, fontsize=13, fontweight="bold")
    ax.text(2023.9, 165.5, "Exchange 21.2 · 12%", ha="right", color=INK, fontsize=11, fontweight="bold")
    save_svg(fig, path)


def interbank_investors(path: Path) -> None:
    # NAFMII Figure 1-6, CIBM holdings at end-November 2024 (CCDC and SHCH).
    data = [
        ("Deposit-taking financial institutions", 56, BLUE),
        ("Asset-management products", 29, BRICK),
        ("Non-bank financial institutions", 9, GOLD),
        ("Others", 6, MUTED),
    ]
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.08, right=0.96, top=0.76, bottom=0.28)
    stacked_share_bar(
        ax,
        [row[0] for row in data],
        [row[1] for row in data],
        colors=[row[2] for row in data],
    )
    _title(ax, "Banks anchor the interbank bond investor base", "Share of China Interbank Bond Market holdings, end-November 2024")
    fig.text(0.96, 0.035, "Source: NAFMII (2025), Figure 1-6; CCDC and SHCH", ha="right", color=MUTED, fontsize=9)
    save_svg(fig, path)


def stock_connect_adt(path: Path) -> None:
    # HKEX Stock Connect 2025 Review; northbound only, in RMB (not southbound HKD).
    data = [
        (2014, 5.6), (2015, 6.4), (2016, 4.8), (2017, 9.6),
        (2018, 20.4), (2019, 41.7), (2020, 91.3), (2021, 120.1),
        (2022, 100.4), (2023, 108.3), (2024, 150.1), (2025, 212.4),
    ]
    years = [row[0] for row in data]
    values = [row[1] for row in data]
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.11, right=0.95, top=0.78, bottom=0.15)
    ax.plot(years, values, color=BLUE, marker="o", linewidth=3, markersize=6)
    ax.fill_between(years, values, color=BLUE, alpha=0.12)
    ax.set_xlim(2013.6, 2025.4)
    ax.set_ylim(0, 235)
    ax.set_xticks(years)
    ax.set_ylabel("RMB billion, average daily turnover")
    style_axis(ax, grid="y")
    _title(ax, "Northbound Stock Connect turnover scaled sharply", "Average daily turnover; northbound RMB series only, 2014–2025")
    ax.annotate("Shanghai Connect", xy=(2014, 5.6), xytext=(2014.2, 55), arrowprops={"arrowstyle": "-", "color": MUTED}, color=MUTED, fontsize=10)
    ax.annotate("Shenzhen Connect", xy=(2016, 4.8), xytext=(2016.1, 82), arrowprops={"arrowstyle": "-", "color": MUTED}, color=MUTED, fontsize=10)
    ax.text(2025, 212.4 + 10, "212.4", ha="center", weight="bold", color=BRICK, fontsize=12)
    fig.text(0.95, 0.035, "Source: HKEX, Stock Connect 2025 Review (Feb. 2026 data)", ha="right", color=MUTED, fontsize=9)
    save_svg(fig, path)


def lecture2_stock_connect_adt(path: Path) -> None:
    """Plot HKEX's complete annual Northbound and Southbound ADT series."""
    years = list(range(2014, 2026))
    northbound = [5.6, 6.4, 4.8, 9.6, 20.4, 41.7, 91.3, 120.1, 100.4, 108.3, 150.1, 212.4]
    southbound = [0.9, 3.4, 4.1, 9.8, 12.7, 10.8, 24.4, 41.7, 31.7, 31.1, 48.2, 121.1]

    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.11, right=0.94, top=0.88, bottom=0.16)
    ax.plot(years, northbound, color=BLUE, marker="o", linewidth=2.8, markersize=5)
    ax.plot(years, southbound, color=INK, marker="o", linewidth=2.8, markersize=5)
    ax.set_xlim(2013.6, 2027.0)
    ax.set_ylim(0, 235)
    ax.set_xticks(years)
    ax.set_ylabel("Average daily turnover (RMB bn northbound; HK$ bn southbound)")
    style_axis(ax, grid="y")
    fig.text(
        0.11,
        0.925,
        "Annual Stock Connect average daily turnover · 2014–2025",
        color=MUTED,
        fontsize=11,
    )
    ax.text(
        2025.25,
        northbound[-1],
        f"Northbound  {northbound[-1]:.1f} RMB bn",
        color=BLUE,
        va="center",
        fontsize=11,
        weight="bold",
    )
    ax.text(
        2025.25,
        southbound[-1],
        f"Southbound  {southbound[-1]:.1f} HK$ bn",
        color=INK,
        va="center",
        fontsize=11,
        weight="bold",
    )
    fig.text(
        0.11,
        0.075,
        "2014 covers the post-launch period from 17 Nov.",
        color=MUTED,
        fontsize=9,
    )
    fig.text(
        0.94,
        0.04,
        "Source: HKEX, Stock Connect 2025 Review (HKEX data, February 2026)",
        ha="right",
        color=MUTED,
        fontsize=9,
    )
    save_svg(fig, path)


def private_funds(path: Path) -> None:
    # AMAC monthly report, December 2025; surviving registered funds and managed AUM.
    data = [
        ("Private equity funds", 11.19, 29_820),
        ("Private securities funds", 7.08, 80_390),
        ("Venture capital funds", 3.58, 27_342),
    ]
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.25, right=0.93, top=0.78, bottom=0.15)
    horizontal_bars(
        ax,
        [row[0] for row in data],
        [row[1] for row in data],
        colors=[BRICK, BLUE, GOLD],
        value_labels=[f"RMB {row[1]:.2f}tn  |  {row[2]:,} funds" for row in data],
        xmax=16.0,
    )
    ax.set_xlabel("Assets under management, RMB trillion")
    _title(ax, "Private equity is the largest private-fund category", "Surviving registered funds and managed AUM at end-2025")
    fig.text(0.93, 0.035, "Source: AMAC, Private Fund Monthly Report, Dec. 2025", ha="right", color=MUTED, fontsize=9)
    save_svg(fig, path)


def read_market_cap_gdp(path: Path = MARKET_CAP_DATA) -> dict[str, list[tuple[int, float]]]:
    """Read the audited World Bank market-cap/GDP observations by economy."""
    grouped: dict[str, list[tuple[int, float]]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            grouped[row["economy"]].append((int(row["period"]), float(row["value"])))
    return {economy: sorted(values) for economy, values in grouped.items()}


def market_cap_gdp_timeseries(path: Path) -> None:
    """Compare common-year listed-company market-cap/GDP series."""
    all_series = read_market_cap_gdp()
    common_years = set.intersection(
        *({year for year, _ in all_series[economy]} for economy in ("China", "United States", "Japan"))
    )
    colors = {"China": BRICK, "United States": BLUE, "Japan": INK}
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.10, right=0.79, top=0.79, bottom=0.14)
    for economy in ("United States", "Japan", "China"):
        values = [(year, value) for year, value in all_series[economy] if year in common_years]
        years = [year for year, _ in values]
        levels = [value for _, value in values]
        ax.plot(years, levels, color=colors[economy], linewidth=2.8)
        ax.text(
            years[-1] + 0.35,
            levels[-1],
            f"{economy}  {levels[-1]:.1f}%",
            color=colors[economy],
            va="center",
            fontsize=11,
            weight="bold",
            clip_on=False,
        )
    ax.set_xlim(min(common_years), max(common_years) + 4.5)
    ax.set_ylim(0, 245)
    ax.set_ylabel("Percent of GDP")
    ax.set_xticks(list(range(min(common_years), max(common_years) + 1, 4)) + [max(common_years)])
    style_axis(ax, grid="y")
    _title(ax, "Equity-market scale moves in valuation cycles", "Listed domestic companies' market capitalization, common years 2003–2025")
    fig.text(0.79, 0.035, "Source: World Bank WDI (World Federation of Exchanges)", ha="right", color=MUTED, fontsize=9)
    save_svg(fig, path)


def market_cap_gdp_latest(path: Path) -> None:
    """Compare the latest common market-cap/GDP observation without mixed cutoffs."""
    all_series = read_market_cap_gdp()
    economies = ("China", "Japan", "United States")
    common_year = max(
        set.intersection(*({year for year, _ in all_series[economy]} for economy in economies))
    )
    lookup = {
        economy: dict(all_series[economy])[common_year]
        for economy in economies
    }
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0.20, right=0.91, top=0.78, bottom=0.15)
    horizontal_bars(
        ax,
        list(economies),
        [lookup[economy] for economy in economies],
        colors=[BRICK, INK, BLUE],
        value_labels=[f"{lookup[economy]:.1f}%" for economy in economies],
        xmax=255,
    )
    ax.set_xlabel("Percent of GDP")
    _title(ax, "China is not the deepest equity market relative to GDP", f"Listed domestic companies' market capitalization, latest common year: {common_year}")
    fig.text(0.91, 0.035, "Source: World Bank WDI (World Federation of Exchanges)", ha="right", color=MUTED, fontsize=9)
    save_svg(fig, path)


def _contiguous_runs(
    observations: Sequence[tuple[int, float]],
) -> list[list[tuple[int, float]]]:
    """Split observations at missing years so plotted lines never interpolate."""
    runs: list[list[tuple[int, float]]] = []
    for observation in sorted(observations):
        if not runs or observation[0] != runs[-1][-1][0] + 1:
            runs.append([])
        runs[-1].append(observation)
    return runs


def equity_submarkets_market_cap(path: Path) -> None:
    """Show launch-aware equity-submarket histories on aligned local scales."""
    grouped: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for row in read_equity_submarket_cap():
        grouped[row["submarket"]].append((int(row["period"]), float(row["value"])))

    panels = (
        ("Main Boards", BRICK, 90.0, (0, 30, 60, 90)),
        ("STAR Market", BLUE, 12.0, (0, 4, 8, 12)),
        ("ChiNext", GOLD, 20.0, (0, 5, 10, 15, 20)),
        ("Beijing Stock Exchange", INK, 1.0, (0, 0.25, 0.5, 0.75, 1.0)),
    )
    fig, axes = plt.subplots(2, 2, figsize=(12, 6.75), sharex=True)
    fig.subplots_adjust(left=0.08, right=0.94, top=0.84, bottom=0.14, hspace=0.48, wspace=0.30)
    fig.text(
        0.08,
        0.925,
        "Year-end total market capitalisation · RMB trillion",
        color=MUTED,
        fontsize=10.5,
    )

    for ax, (submarket, color, ymax, yticks) in zip(axes.flat, panels):
        observations = sorted(grouped[submarket])
        for run in _contiguous_runs(observations):
            ax.plot(
                [year for year, _ in run],
                [value for _, value in run],
                color=color,
                marker="o",
                linewidth=2.5,
                markersize=4.5,
            )
        last_year, last_value = observations[-1]
        ax.text(
            last_year - 0.25,
            last_value,
            f"{submarket}\n{last_value:.1f}",
            color=color,
            va="center",
            ha="right",
            fontsize=10,
            weight="bold",
        )
        ax.set_xlim(2004.5, 2025.5)
        ax.set_ylim(0, ymax)
        ax.set_yticks(yticks)
        ax.set_ylabel(f"RMB tn · 0–{ymax:g} scale", fontsize=9.5)
        style_axis(ax, grid="y")

    for ax in axes[-1]:
        ax.set_xticks((2005, 2009, 2013, 2017, 2021, 2025))
        ax.set_xlabel("Year")
    fig.text(
        0.91,
        0.035,
        "Sources: SSE/SZSE/CSRC official year-end statistics;\n"
        "BSE 2022–23 & 2025: archive + year-specific secondary corroboration; see manifest",
        ha="right",
        color=MUTED,
        fontsize=8.5,
    )
    save_svg(fig, path)


def main(output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
    """Generate exactly the declared lecture figures under *output_dir*."""
    _configure()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generators = (
        (payment_adoption, "payment_adoption.svg"),
        (tsf_composition, "tsf_composition_2025.svg"),
        (bond_composition, "bond_composition_2025.svg"),
        (bond_venues, "bond_venues_2025.svg"),
        (interbank_investors, "interbank_investors.svg"),
        (bond_market_by_venue_timeseries, "bond_market_by_venue_timeseries.svg"),
        (stock_connect_adt, "stock_connect_adt.svg"),
        (private_funds, "private_funds_2025.svg"),
        (market_cap_gdp_timeseries, "l2_market_cap_gdp_timeseries.svg"),
        (market_cap_gdp_latest, "l2_market_cap_gdp_latest.svg"),
        (equity_submarkets_market_cap, "l2_equity_submarkets_market_cap.svg"),
        (lecture2_stock_connect_adt, "l2_stock_connect_adt.svg"),
    )
    for generator, filename in generators:
        generator(output_dir / filename)
    print(f"Wrote {len(generators)} SVG figures to {output_dir}")


if __name__ == "__main__":
    main()
