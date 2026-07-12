"""Build the normalized, auditable Lecture 1 data layer.

Unavailable datasets are header-only. Availability and evidence-design status
belong exclusively in ``source_manifest.csv``, never in observation rows.
"""

from __future__ import annotations

import csv
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
RETRIEVED_ON = "2026-07-10"

DATASET_FILES = {
    "payment_adoption": "payment_adoption.csv",
    "financial_sector_assets": "financial_sector_assets.csv",
    "deposits_by_holder": "deposits_by_holder.csv",
    "nominal_gdp": "nominal_gdp.csv",
    "bank_credit_allocation": "bank_credit_allocation.csv",
    "private_credit_gdp": "private_credit_gdp.csv",
    "bank_efficiency": "bank_efficiency.csv",
    "tsf_total": "tsf_total.csv",
    "tsf_mix": "tsf_mix.csv",
    "market_cap_gdp": "market_cap_gdp.csv",
    "bond_market_gdp": "bond_market_gdp.csv",
    "afre_channels": "afre_channels.csv",
    "sector_leverage": "sector_leverage.csv",
    "broad_local_debt": "broad_local_debt.csv",
}

NORMALIZED_COLUMNS = ("series", "economy", "period", "value", "unit", "source_id")
PAYMENT_SOURCE_FILE = "payment_adoption_sources.csv"
PAYMENT_SOURCE_COLUMNS = ("period", "report", "source_url")
MANIFEST_COLUMNS = (
    "dataset_id", "source_institution", "source_url", "retrieved_on",
    "definition", "frequency", "unit", "coverage", "notes",
)

# Official CNNIC report observations; 2019 is unavailable and not interpolated.
CNNIC_PAYMENT_VALUES: tuple[tuple[str, float, float], ...] = (
    ("2007", 33.00, 15.8), ("2008", 52.00, 17.6),
    ("2009", 94.06, 24.5), ("2010", 137.19, 30.0),
    ("2011", 166.76, 32.5), ("2012", 220.65, 39.1),
    ("2013", 260.20, 42.1), ("2014", 304.31, 46.9),
    ("2015", 416.18, 60.5), ("2016", 474.50, 64.9),
    ("2017", 531.10, 68.8), ("2018", 600.40, 72.5),
    ("2020", 854.34, 86.4), ("2021", 903.63, 87.6),
    ("2022", 911.44, 85.4), ("2023", 953.86, 87.3),
    ("2024", 1028.91, 92.8),
)

CNNIC_PAYMENT_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("2007", "23rd Statistical Report", "https://www3.cnnic.cn/NMediaFile/2022/0830/MAIN1661848328683YK36NWDGG4.pdf"),
    ("2008", "23rd Statistical Report", "https://www3.cnnic.cn/NMediaFile/2022/0830/MAIN1661848328683YK36NWDGG4.pdf"),
    ("2009", "25th Statistical Report", "https://www.cnnic.cn/NMediaFile/old_attach/P020120612484949500779.pdf"),
    ("2010", "27th Statistical Report", "https://www.cac.gov.cn/files/pdf/hlwtjbg/hlwlfzzkdctjbg027.pdf"),
    ("2011", "29th Statistical Report", "https://www.cnnic.cn/n4/2022/0401/c88-803.html"),
    ("2012", "32nd Statistical Report", "https://www.cnnic.cn/NMediaFile/old_attach/P020130717505343100851.pdf"),
    ("2013", "35th Statistical Report", "https://www3.cnnic.cn/NMediaFile/old_attach/P020150203548852631921.pdf"),
    ("2014", "35th Statistical Report", "https://www3.cnnic.cn/NMediaFile/old_attach/P020150203548852631921.pdf"),
    ("2015", "37th Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/201604/P020160419390562421055.pdf"),
    ("2016", "39th Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/201706/P020170608523740585924.pdf"),
    ("2017", "41st Statistical Report", "https://www.cac.gov.cn/files/pdf/cnnic/CNNIC41.pdf"),
    ("2018", "43rd Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/201911/P020191112538996067898.pdf"),
    ("2020", "51st Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/202307/P020230829505026163347.pdf"),
    ("2021", "51st Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/202307/P020230829505026163347.pdf"),
    ("2022", "51st Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/202307/P020230829505026163347.pdf"),
    ("2023", "55th Statistical Report", "https://www2.cnnic.cn/NMediaFile/2025/0428/MAIN17458061595875K4FP1NEUO.pdf"),
    ("2024", "55th Statistical Report", "https://www2.cnnic.cn/NMediaFile/2025/0428/MAIN17458061595875K4FP1NEUO.pdf"),
)

# Exact official observations approved for the 27-slide Lecture 1 refinement.
NBS_NOMINAL_GDP_2025 = 140.1879
PBOC_HOUSEHOLD_RMB_DEPOSITS_2025_11 = 163.3084
PBOC_NONFINANCIAL_ENTERPRISE_RMB_DEPOSITS_2025_11 = 79.3387
PBOC_AFRE_FLOW_2025 = 35.6
PBOC_AFRE_STOCK_2025 = 442.1

# PBOC 2025 year-end AFRE/TSF composition, audited in comments-0709.md and the deck.
PBOC_TSF_MIX_2025 = {
    "RMB loans to real economy": 60.7,
    "Government bonds": 21.5,
    "Corporate bonds": 7.7,
    "Domestic equity of non-financial enterprises": 2.8,
    "Other components": 7.3,
}

# Digitized from the vector paths in He & Wei (2022), Figure 1. Values are
# plotted percentages of GDP rounded to one decimal, not official exact rows.
HE_WEI_AFRE_CHANNELS = (
    (2002, 100.9, 5.0, 6.0, 9.5), (2003, 108.7, 6.4, 6.3, 10.2),
    (2004, 105.6, 7.2, 5.7, 7.0), (2005, 103.3, 6.7, 6.1, 3.0),
    (2006, 102.2, 8.2, 6.8, 2.7), (2007, 96.9, 11.0, 7.9, 2.6),
    (2008, 96.8, 11.9, 9.4, 0.2), (2009, 117.2, 15.4, 13.0, 0.5),
    (2010, 118.7, 22.4, 15.1, 0.7), (2011, 116.3, 23.0, 16.4, 0.8),
    (2012, 121.7, 26.6, 19.6, 1.0), (2013, 125.9, 32.0, 21.2, 1.3),
    (2014, 131.2, 33.3, 23.9, 1.5), (2015, 138.3, 32.0, 27.7, 1.5),
    (2016, 143.7, 31.2, 31.6, 1.4), (2017, 145.3, 32.2, 30.5, 38.3),
    (2018, 148.1, 26.0, 30.0, 41.6), (2019, 155.0, 22.4, 31.1, 45.0),
    (2020, 170.5, 20.5, 35.2, 53.3), (2021, 168.6, 15.9, 34.3, 54.5),
)

# Chang, Wang & Xiong (2025), Figure 5 public workbook, Data_WEB.xlsx.
SECTOR_LEVERAGE = (
    (2000, 10, 90, 16, 5), (2001, 12, 88, 17, 6),
    (2002, 15, 96, 18, 7), (2003, 19, 102, 20, 8),
    (2004, 17, 105, 19, 8), (2005, 17, 100, 18, 9),
    (2006, 18, 99, 17, 10), (2007, 19, 96, 20, 11),
    (2008, 18, 95, 17, 11), (2009, 24, 116, 18, 16),
    (2010, 27, 121, 17, 16), (2011, 28, 118, 15, 17),
    (2012, 30, 128, 14, 18), (2013, 34, 136, 15, 21),
    (2014, 36, 142, 15, 24), (2015, 39, 152, 16, 21),
    (2016, 45, 157, 16, 21), (2017, 49, 157, 16, 20),
    (2018, 52, 151, 16, 20), (2019, 56, 152, 17, 22),
    (2020, 62, 163, 21, 25), (2021, 62, 154, 20, 27),
    (2022, 62, 162, 22, 29), (2023, 64, 168, 24, 32),
)

# Vector-digitized from Chang, Wang & Xiong (2025), Figure 6. The values are
# recovered from the published line coordinates and axis scale.
BROAD_LOCAL_DEBT = (
    (2015, 42.97), (2016, 47.61), (2017, 49.55), (2018, 49.89),
    (2019, 53.52), (2020, 61.25), (2021, 62.84), (2022, 68.47),
)


def _row(dataset_id: str, series: str, economy: str, period: str,
         value: str | float, unit: str) -> dict[str, str | float]:
    return {
        "series": series, "economy": economy, "period": period,
        "value": value, "unit": unit, "source_id": dataset_id,
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _private_credit_rows() -> list[dict[str, str | float]]:
    source = WORKSPACE / "data" / "fred_private_credit_gdp_2000_latest.csv"
    rows = []
    for item in _read_csv(source):
        # BIS quarterly observations are dated at quarter starts; October is Q4
        # and is the audited annual year-end observation used here.
        if item["date"][5:7] == "10":
            rows.append(_row(
                "private_credit_gdp", "Credit to private non-financial sector",
                item["country"], item["date"][:4],
                item["credit_to_private_nonfinancial_sector_percent_gdp"],
                "percent of GDP",
            ))
    return rows


def _market_cap_rows() -> list[dict[str, str | float]]:
    source = WORKSPACE / "data" / "wdi_market_cap_gdp_1995_2025_china_us_japan.csv"
    return [
        _row("market_cap_gdp", "Listed domestic companies market capitalization",
             item["country"], item["year"], item["market_cap_percent_gdp"],
             "percent of GDP")
        for item in _read_csv(source)
    ]


def _financial_asset_rows() -> list[dict[str, str | float]]:
    source = WORKSPACE / "data" / "nfra_banking_assets_2025q4_2026q1.csv"
    rows: list[dict[str, str | float]] = []
    for item in _read_csv(source):
        rows.extend([
            _row("financial_sector_assets", "Banking institutions assets", "China",
                 item["period"], item["banking_institutions_assets_rmb_trillion"], "RMB trillion"),
            _row("financial_sector_assets", "Insurance and insurance asset-management assets",
                 "China", item["period"],
                 item["insurance_and_insurance_am_assets_rmb_trillion"], "RMB trillion"),
        ])
    return rows


def _datasets() -> dict[str, list[dict[str, str | float]]]:
    payment = []
    for year, user_value, rate in CNNIC_PAYMENT_VALUES:
        payment.extend([
            _row("payment_adoption", "Online payment users", "China", year, user_value, "million users"),
            _row("payment_adoption", "Online payment utilization rate", "China", year, rate, "percent of internet users"),
        ])

    afre_names = (
        "Bank loans", "Off-balance-sheet financing",
        "Market-based direct financing", "Other forms of financing",
    )
    leverage_names = (
        "Household", "Nonfinancial corporations",
        "Central government", "Local government",
    )

    return {
        "payment_adoption": payment,
        "financial_sector_assets": _financial_asset_rows(),
        "deposits_by_holder": [
            _row("deposits_by_holder", "Household RMB deposits", "China",
                 "2025-11", PBOC_HOUSEHOLD_RMB_DEPOSITS_2025_11, "RMB trillion"),
            _row("deposits_by_holder", "Non-financial enterprise RMB deposits", "China",
                 "2025-11", PBOC_NONFINANCIAL_ENTERPRISE_RMB_DEPOSITS_2025_11,
                 "RMB trillion"),
        ],
        "nominal_gdp": [
            _row("nominal_gdp", "Nominal gross domestic product", "China",
                 "2025", NBS_NOMINAL_GDP_2025, "RMB trillion"),
        ],
        "bank_credit_allocation": [],
        "private_credit_gdp": _private_credit_rows(),
        "bank_efficiency": [
            _row("bank_efficiency", "Bank nonperforming loans to total gross loans", "China", "2025Q4", 1.50, "percent"),
            _row("bank_efficiency", "Bank nonperforming loans to total gross loans", "China", "2026Q1", 1.51, "percent"),
        ],
        "tsf_total": [
            _row("tsf_total", "AFRE annual flow", "China", "2025",
                 PBOC_AFRE_FLOW_2025, "RMB trillion"),
            _row("tsf_total", "AFRE year-end stock", "China", "2025",
                 PBOC_AFRE_STOCK_2025, "RMB trillion"),
        ],
        "tsf_mix": [
            _row("tsf_mix", name, "China", "2025", value, "percent of TSF stock")
            for name, value in PBOC_TSF_MIX_2025.items()
        ],
        "market_cap_gdp": _market_cap_rows(),
        "bond_market_gdp": [],
        "afre_channels": [
            _row("afre_channels", name, "China", str(year), value, "percent of GDP")
            for year, *values in HE_WEI_AFRE_CHANNELS
            for name, value in zip(afre_names, values)
        ],
        "sector_leverage": [
            _row("sector_leverage", name, "China", str(year), value, "percent of GDP")
            for year, *values in SECTOR_LEVERAGE
            for name, value in zip(leverage_names, values)
        ],
        "broad_local_debt": [
            _row("broad_local_debt", "Broad local government debt", "China",
                 str(year), value, "percent of GDP")
            for year, value in BROAD_LOCAL_DEBT
        ],
    }


def _manifest() -> list[dict[str, str]]:
    common = {"retrieved_on": RETRIEVED_ON}
    rows = [
        dict(dataset_id="payment_adoption", source_institution="China Internet Network Information Center (CNNIC)", source_url=" ; ".join(("https://www3.cnnic.cn/NMediaFile/2022/0830/MAIN1661848328683YK36NWDGG4.pdf", "https://www.cnnic.cn/NMediaFile/old_attach/P020120612484949500779.pdf", "https://www.cac.gov.cn/files/pdf/hlwtjbg/hlwlfzzkdctjbg027.pdf", "https://www.cnnic.cn/n4/2022/0401/c88-803.html", "https://www.cnnic.cn/NMediaFile/old_attach/P020130717505343100851.pdf", "https://www3.cnnic.cn/NMediaFile/old_attach/P020150203548852631921.pdf", "https://www.cnnic.com.cn/IDR/ReportDownloads/201604/P020160419390562421055.pdf", "https://www.cnnic.com.cn/IDR/ReportDownloads/201706/P020170608523740585924.pdf", "https://www.cac.gov.cn/files/pdf/cnnic/CNNIC41.pdf", "https://www.cnnic.com.cn/IDR/ReportDownloads/201911/P020191112538996067898.pdf", "https://www.cnnic.com.cn/IDR/ReportDownloads/202307/P020230829505026163347.pdf", "https://www2.cnnic.cn/NMediaFile/2025/0428/MAIN17458061595875K4FP1NEUO.pdf")), definition="Users of online/network payment and their share of internet users", frequency="annual year-end", unit="million users; percent of internet users", coverage="China, year-end 2007-2024; 2019 unavailable", notes="Official CNNIC report observations; terminology changes from online payment to network payment. The measure includes bank and third-party online payment, is not a causal estimate of third-party payment, and uses no interpolation for missing 2019. Period-level report provenance: payment_adoption_sources.csv.", **common),
        dict(dataset_id="financial_sector_assets", source_institution="NFRA; NAFMII / National Bureau of Statistics of China (crop only)", source_url="https://www.nfra.gov.cn/en/view/pages/ItemDetail.html?docId=1251267 ; https://www.nfra.gov.cn/en/view/pages/ItemDetail.html?docId=1259732 ; https://www.nafmii.org.cn/englishnew/overseasparticipation/pandabond/resources/202504/P020250423396158840864.pdf", definition="NFRA banking and insurance-sector total assets; NAFMII crop retained only as separate visual evidence", frequency="quarterly", unit="RMB trillion", coverage="Exact NFRA observations 2025Q4-2026Q1; separate NAFMII crop spans 2018-2024Q3", notes="Numeric rows are read from audited local input data/nfra_banking_assets_2025q4_2026q1.csv, sourced to sources/nfra_supervisory_stats_2025q4.pdf and sources/nfra_supervisory_stats_2026q1.pdf. Historical NAFMII/NBS chart labels cannot be recovered without approximation; distinct crop: html_lectures/assets/evidence/nafmii_financial_sector_assets_2018_2024q3.png.", **common),
        dict(dataset_id="deposits_by_holder", source_institution="People's Bank of China", source_url="https://www.pbc.gov.cn/diaochatongjisi/attachDir/2025/12/2025121517273312027.pdf", definition="RMB deposit stocks held by households and non-financial enterprises in the PBOC Sources and Uses of Credit Funds of Financial Institutions table", frequency="monthly", unit="RMB trillion", coverage="China, observation at 2025-11", notes="Official November 2025 RMB credit receipts-and-payments table; values converted from RMB 100 million to RMB trillion. Observation date is 2025-11, not year-end. stock-to-annual-GDP benchmark; not a savings rate", **common),
        dict(dataset_id="nominal_gdp", source_institution="National Bureau of Statistics of China", source_url="https://data.stats.gov.cn/easyquery.htm?cn=C01&zb=A0201&sj=2025", definition="Gross domestic product at current prices", frequency="annual", unit="RMB trillion", coverage="China, calendar year 2025", notes="Official 2025 nominal GDP, converted from RMB 100 million to RMB trillion; annual flow measure used as the denominator for explicitly labelled scale benchmarks.", **common),
        dict(dataset_id="bank_credit_allocation", source_institution="People's Bank of China / National Bureau of Statistics of China", source_url="https://data.stats.gov.cn/easyquery.htm", definition="Household and enterprise/institution lending stocks by holder/use", frequency="annual requested", unit="not available", coverage="China; no compatible observations recovered", notes="coverage_unavailable: same bounded official finance-table endpoint was unreachable; header-only observation file, no levels or categories inferred", **common),
        dict(dataset_id="private_credit_gdp", source_institution="Bank for International Settlements via Federal Reserve Bank of St. Louis (FRED)", source_url="https://fred.stlouisfed.org/series/QCNPAM770A ; https://fred.stlouisfed.org/series/QUSPAM770A ; https://fred.stlouisfed.org/series/QXMPAM770A ; https://fred.stlouisfed.org/series/QJPPAM770A", definition="Credit to the private non-financial sector from all sectors at market value", frequency="annual year-end sampled from quarterly Q4", unit="percent of GDP", coverage="China, United States, Euro area, Japan; 2000-2025 where present", notes="FRED/BIS series: China QCNPAM770A; United States QUSPAM770A; Euro area QXMPAM770A; Japan QJPPAM770A. October-dated Q4 observations represent year-end quarters.", **common),
        dict(dataset_id="bank_efficiency", source_institution="National Financial Regulatory Administration", source_url="https://www.nfra.gov.cn/en/view/pages/ItemDetail.html?docId=1251267 ; https://www.nfra.gov.cn/en/view/pages/ItemDetail.html?docId=1259732", definition="Commercial-bank nonperforming loan balance divided by total gross loans, legal-entity scope", frequency="quarterly", unit="percent", coverage="China, 2025Q4-2026Q1", notes="2025Q4 local official release: sources/nfra_supervisory_stats_2025q4.pdf; 2026Q1 local official release: sources/nfra_supervisory_stats_2026q1.pdf. Only directly comparable NFRA observations included; failed official cross-country endpoint attempt yielded no compatible series; no interpolation.", **common),
        dict(dataset_id="tsf_total", source_institution="People's Bank of China", source_url="https://www.pbc.gov.cn/diaochatongjisi/116219/116319/index.html ; https://jrj.sh.gov.cn/ZXYW178/20260116/88e3368ecfee4e639ae9aa8dd93729c3.html", definition="Annual flow and year-end stock of aggregate financing to the real economy (AFRE/TSF)", frequency="annual flow; year-end stock", unit="RMB trillion", coverage="China, calendar-year 2025 flow and end-2025 stock", notes="single_period_only; time_series_withheld: no historical flow/stock series is emitted until common definitions and observation dates are audited. Annual AFRE flow / annual GDP is flow / annual GDP; year-end AFRE stock / annual-GDP benchmark is a scale comparison, not an annual financing rate. AFRE is not all financial assets and is not exclusively corporate financing.", **common),
        dict(dataset_id="tsf_mix", source_institution="People's Bank of China", source_url="https://jrj.sh.gov.cn/ZXYW178/20260116/88e3368ecfee4e639ae9aa8dd93729c3.html", definition="Component shares of year-end AFRE/TSF stock", frequency="annual year-end", unit="percent of TSF stock", coverage="China, 2025 only", notes="single_period_only; time_series_withheld: the final Slide 23 single-period composition is an evidence limitation, not a historical mix series; common historical component dates remain unaudited. Other is a residual teaching group; shares sum to 100.0 percent.", **common),
        dict(dataset_id="market_cap_gdp", source_institution="World Bank, World Development Indicators", source_url="https://api.worldbank.org/v2/country/CHN;USA;JPN;EMU/indicator/CM.MKT.LCAP.GD.ZS", definition="Market capitalization of listed domestic companies divided by GDP", frequency="annual", unit="percent of GDP", coverage="China, United States, Japan, 1995-2025 where populated", notes="euro_area_unavailable: same-basis Euro area aggregate unavailable and excluded; no country substitute or constructed aggregate is used", **common),
        dict(dataset_id="bond_market_gdp", source_institution="Bank for International Settlements", source_url="https://data.bis.org/topics/DSS/tables-and-dashboards", definition="Outstanding debt securities divided by matching nominal GDP", frequency="annual requested", unit="not available", coverage="China, United States, Euro area, Japan; no compatible observations recovered", notes="coverage_unavailable: one bounded official data-endpoint attempt returned no results; header-only observation file, no bond/GDP estimates", **common),
        dict(dataset_id="afre_channels", source_institution="Zhiguo He and Wei Wei", source_url="https://www.nber.org/system/files/working_papers/w30324/w30324.pdf", definition="AFRE stock divided by GDP and decomposed into bank loans, off-balance-sheet financing, market-based direct financing, and other forms of financing", frequency="annual", unit="percent of GDP", coverage="China, 2002-2021", notes="Vector-digitized from published Figure 1 and rounded to one decimal; values are faithful plotted approximations, not official exact observations. Published text reports AFRE/GDP of 119% in 2008, 170% in 2012, and 275% in 2021.", **common),
        dict(dataset_id="sector_leverage", source_institution="Chang, Wang and Xiong / Brookings Papers on Economic Activity", source_url="https://www.brookings.edu/wp-content/uploads/2025/03/Data_WEB.xlsx", definition="Debt of households, nonfinancial corporations, central government, and local government divided by national GDP", frequency="annual", unit="percent of GDP", coverage="China, 2000-2023", notes="Exact values transcribed from the authors' public Figure 5 workbook. LGFV debt is excluded from the local-government series and included in nonfinancial corporations.", **common),
        dict(dataset_id="broad_local_debt", source_institution="Chang, Wang and Xiong / Brookings Papers on Economic Activity", source_url="https://www.brookings.edu/wp-content/uploads/2025/03/BPEA-SP25_WEB_Chang_Wang_Xiong.pdf", definition="Broad local government debt divided by national GDP, including official local government debt and LGFV liabilities", frequency="annual", unit="percent of GDP", coverage="China, 2015-2022", notes="Vector-digitized from published Figure 6 because the authors' public workbook omits Figure 6; values are plotted approximations recovered from vector line coordinates and axis scale.", **common),
    ]
    return rows


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str | float]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def prepare(output_dir: Path) -> list[Path]:
    """Write every Lecture 1 dataset and return all output paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "source_manifest.csv"
    _write_csv(manifest_path, MANIFEST_COLUMNS, _manifest())
    produced = [manifest_path]
    payment_source_path = output_dir / PAYMENT_SOURCE_FILE
    _write_csv(
        payment_source_path,
        PAYMENT_SOURCE_COLUMNS,
        [dict(zip(PAYMENT_SOURCE_COLUMNS, row)) for row in CNNIC_PAYMENT_SOURCES],
    )
    produced.append(payment_source_path)
    for dataset_id, filename in DATASET_FILES.items():
        path = output_dir / filename
        _write_csv(path, NORMALIZED_COLUMNS, _datasets()[dataset_id])
        produced.append(path)
    return produced


if __name__ == "__main__":
    prepare(Path(__file__).resolve().parents[1] / "data" / "lecture1")
