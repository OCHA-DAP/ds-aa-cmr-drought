import os
from pathlib import Path
from typing import Literal, Optional
from urllib.request import urlretrieve

import numpy as np
import pandas as pd

DATA_DIR = Path(os.getenv("AA_DATA_DIR"))
BM_RAW_DIR = DATA_DIR / "public" / "raw" / "glb" / "biomasse"
_RAW_FILENAME = "WA_DMP_{admin_level}_ef_v0.csv"
_BASE_URL = (
    "http://213.206.230.89:8080/geoserver"
    "/Biomass/wfs?&REQUEST="
    "GetFeature&SERVICE=wfs&VERSION=1.1.0"
    "&TYPENAME=WA_DMP_{admin_level}_ef_v1&"
    "outputformat=csv&srsName=EPSG:4326"
)

_PROCESSED_FILENAME = "biomasse_{iso3}_{admin_level}_dekad_{start_dekad}.csv"

AdminArgument = Literal["ADM0", "ADM1", "ADM2"]


def download_biomasse(admin_level: AdminArgument = "ADM2"):
    url = _BASE_URL.format(admin_level=admin_level)
    filename = _RAW_FILENAME.format(admin_level=admin_level)
    save_path = BM_RAW_DIR / filename
    urlretrieve(url, filename=save_path)


def load_dmp(admin_level: AdminArgument = "ADM2") -> pd.DataFrame:
    """Load raw DMP data

    Parameters
    ----------
    admin: AdminArgument
        Admin area to load DMP for, one of
        'ADM0', 'ADM1', or 'ADM2'.

    Returns
    -------
    pd.DataFrame
    """
    filename = _RAW_FILENAME.format(admin_level=admin_level)
    raw_path = BM_RAW_DIR / filename
    if not raw_path.is_file():
        raise OSError(
            "Raw DMP data not available, run `download_dmp()` first."
        )
    # na values set by Biomasse as -9998.8 or -9999.0
    df = pd.read_csv(raw_path, na_values=["-9998.8", "-9999.0"])
    df.dropna(axis="columns", how="all", inplace=True)
    return df


def calculate_biomasse(
    admin_level: AdminArgument = "ADM2",
    start_dekad: int = 10,
) -> pd.DataFrame:
    """Calculate Biomasse from DMP raw data

    DMP raw data is received in a wide format
    dataset that needs processing. This pivots
    the data from wide to long format with
    DMP dekadal observations for all years, while
    also pivoting the mean values to allow for
    calculation of biomasse anomaly. Outputs
    dataframe of Biomasse values.

    Parameters
    ----------
    admin_level: AdminArgument
        Admin area to load DMP for, one of
        'ADM0', 'ADM1', or 'ADM2'.
    start_dekad: int
        Starting dekad of the season to use
        in calculations. Season will start
        in starting dekad and end in the
        previous dekad.
    Returns
    -------
    pd.DataFrame
    """
    df = load_dmp(admin_level)

    # process mean and DMP separately since mean values
    # are dekadal and DMP are year/dekadal
    # keep ID column for working with multipolygon admin areas
    id_col = "IDBIOHYDRO"
    df_mean = df.filter(regex=f"(^admin|^DMP_MEA|^{id_col}|^AREA)")
    df_dmp = df.filter(regex=f"(^admin|^DMP_[0-9]+|^{id_col}|^AREA)")
    admin_cols = [col for col in df_mean.columns if col.startswith("admin")]

    # groupby to average out for the few cases where admin areas
    # are not contiguous, because noncontiguous polygons
    # appear as separate rows in the data frame
    # happens in Cote d'Ivoire and Liberia
    df_mean_long = (
        pd.wide_to_long(
            df_mean,
            i=admin_cols + [id_col],
            j="dekad",
            stubnames="DMP_MEA",
            sep="_",
        )
        .reset_index()
        .drop(labels=id_col, axis=1)
        .groupby(admin_cols + ["dekad"])
        .apply(
            lambda x: pd.Series(
                {"DMP_MEA": np.average(x["DMP_MEA"], weights=x["AREA"])}
            )
        )
        .reset_index()
    )

    # calculate anomaly for mean separate from
    # observed to ensure unique dekadal values
    # based on what we removed in the above code
    df_mean_long["season_index"] = np.where(
        df_mean_long["dekad"] >= start_dekad,
        df_mean_long["dekad"] - start_dekad,
        df_mean_long["dekad"] + (36 - start_dekad),
    )
    df_mean_long.sort_values(by=admin_cols + ["season_index"], inplace=True)
    df_mean_long["biomasse_mean"] = df_mean_long.groupby(by=admin_cols)[
        "DMP_MEA"
    ].apply(lambda x: x.cumsum() * 365.25 / 36)

    df_dmp_long = (
        pd.wide_to_long(
            df_dmp,
            i=admin_cols + [id_col],
            j="time",
            stubnames="DMP",
            sep="_",
        )
        .reset_index()
        .drop(labels=id_col, axis=1)
        .groupby(admin_cols + ["time"])
        .apply(
            lambda x: pd.Series(
                {"DMP": np.average(x["DMP"], weights=x["AREA"])}
            )
        )
        .reset_index()
    )

    # convert time into year and dekad
    df_dmp_long[["year", "dekad"]] = (
        df_dmp_long["time"].apply(str).str.extract("([0-9]{4})([0-9]{2})")
    )
    df_dmp_long = df_dmp_long.astype({"year": int, "dekad": int})

    # drop values from 1999 that are not from a complete season
    df_dmp_long = df_dmp_long[
        ~((df_dmp_long["year"] == 1999) & (df_dmp_long["dekad"] < start_dekad))
    ]

    # join mean and observed values
    df_merged = pd.merge(
        left=df_dmp_long, right=df_mean_long, on=admin_cols + ["dekad"]
    )

    # calculate biomasse (cumulative sum of DMP across the season
    # starting with the start_dekad and ending at start_dekad - 1
    df_merged.sort_values(
        by=admin_cols + ["year", "dekad"], inplace=True, ignore_index=True
    )
    df_merged["season"] = (
        df_merged["year"] + (df_merged["dekad"] >= start_dekad) - 1
    )
    # if the season isn't starting from 1
    # create clear season definition of year1-year2
    if start_dekad > 1:
        df_merged["season_end"] = (df_merged["season"] + 1).astype("str")
        df_merged["season"] = df_merged["season"].astype("str")
        df_merged["season"] = df_merged[["season", "season_end"]].agg(
            "-".join, axis=1
        )

    df_merged["biomasse"] = df_merged.groupby(by=admin_cols + ["season"])[
        "DMP"
    ].apply(lambda x: x.cumsum() * 365.25 / 36)
    df_merged["biomasse_anomaly"] = (
        100 * df_merged["biomasse"] / df_merged["biomasse_mean"]
    )

    # re-arrange columns
    df_merged = df_merged[
        admin_cols
        + [
            "year",
            "dekad",
            "season",
            "DMP_MEA",
            "DMP",
            "biomasse_mean",
            "biomasse",
            "biomasse_anomaly",
        ]
    ]

    # save file to processed filepath
    # processed_path = _get_processed_path(
    #     admin_level=admin_level, start_dekad=start_dekad, iso3=None
    # )
    # df_merged.to_csv(processed_path, index=False)

    return df_merged


def _get_processed_path(
    admin_level: AdminArgument, start_dekad: int, iso3: Optional[str] = None
):
    if iso3 is None:
        iso3 = "glb"

    _processed_path = Path(
        os.getenv("AA_DATA_DIR"), "public", "processed", iso3, "biomasse"
    )

    return Path(
        _processed_path,
        _PROCESSED_FILENAME.format(
            iso3=iso3, admin_level=admin_level, start_dekad=start_dekad
        ),
    )
