import os
from pathlib import Path

import xarray as xr

DATA_DIR = Path(os.getenv("AA_DATA_DIR_NEW"))
RAW_PATH = (
    DATA_DIR
    / "public"
    / "raw"
    / "cmr"
    / "era5"
    / "cmr-extremenord-era5-julyonly.grib"
)


def load_raw_reanalysis():
    return xr.load_dataset(RAW_PATH)
