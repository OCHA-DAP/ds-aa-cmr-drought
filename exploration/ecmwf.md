---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.1
  kernelspec:
    display_name: ds-aa-cmr-drought
    language: python
    name: ds-aa-cmr-drought
---

# ECMWF

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import matplotlib.pyplot as plt
import xarray as xr

from src.datasources import ecmwf, codab
from src.constants import *
from src.utils import upsample_dataarray
```

```python
DATE_LT_STRS = ["m4-l456", "m5-l345"]
```

```python
adm = codab.load_codab(admin_level=2)
adm = adm[adm["ADM1_PCODE"] == EXTREMENORD]
```

```python
adm.plot()
```

```python
dss = []
for date_lt_str in DATE_LT_STRS:
    ds_in = ecmwf.load_ecmwf_specific_cmr(date_lt_str)
    ds_in["date_lt_str"] = date_lt_str
    dss.append(ds_in)

ds = xr.concat(dss, dim="date_lt_str")
```

```python
da = ds["tprate"].mean(dim=["number", "step"])
da = da.groupby("time.year").first()
da *= 3600 * 24 * 1000 * 30
da_up = upsample_dataarray(da, resolution=0.01)
```

```python
da_up = da_up.rio.write_crs(4326)
da_clip = da_up.rio.clip(adm.geometry, all_touched=True)
```

```python
da_clip
```

```python
fig, ax = plt.subplots(dpi=300)
adm.boundary.plot(ax=ax, color="white")
da_clip.isel(date_lt_str=1, year=0).plot(ax=ax)
ax.axis("off")
ax.set_title("Exemple de prévision ECMWF sur Extrême-Nord")
```

```python
da_mean = da_clip.mean(dim=["latitude", "longitude"])
```

```python
df = da_mean.to_dataframe()["tprate"].reset_index()
df = df.rename(columns={"tprate": "precip"})


def calc_rp(group):
    group["rank"] = group["precip"].rank().astype(int)
    group["rp"] = len(group) / group["rank"]
    for rp in [3, 5]:
        thresh = group["precip"].quantile(1 / rp)
        print(rp, thresh)
        group[f"trig_rp{rp}"] = group["precip"] <= thresh
    return group


df = (
    df.groupby("date_lt_str")
    .apply(calc_rp, include_groups=False)
    .reset_index(level=1, drop=True)
    .reset_index()
)
df
```

```python
dfs = []

for date_lt_str, month_str in zip(DATE_LT_STRS, ["apr", "may"]):
    df_out = df[df["date_lt_str"] == date_lt_str]
    df_out = df_out.rename(
        columns={
            x: f"{month_str}_{x}"
            for x in df_out.columns
            if x not in ["year", "date_lt_str"]
        }
    )
    dfs.append(df_out.drop(columns="date_lt_str"))

df_save = dfs[0]

for df_in in dfs[1:]:
    df_save = df_save.merge(df_in)

df_save
```

```python
rp = 5

for date_lt_str, month_str in zip(DATE_LT_STRS, ["avril", "mai"]):
    dff = df[(df["date_lt_str"] == date_lt_str) & (df["year"] >= 1999)]
    thresh = dff["precip"].quantile(1 / rp)

    fig, ax = plt.subplots(dpi=300)
    dff.plot(x="year", y="precip", ax=ax, legend=False, color="dodgerblue")

    ax.axhline(y=thresh, color="grey", linestyle="--", alpha=0.5)
    ax.annotate(
        f" seuil 1-an-sur-{rp}\n = {thresh:.0f} mm",
        xy=(2025, thresh),
        color="grey",
        ha="left",
        va="center",
    )

    for year, row in dff.set_index("year").iterrows():
        tp = row["precip"]
        if tp <= thresh:
            ax.annotate(
                year,
                xy=(year, tp),
                color="crimson",
                ha="center",
                va="top",
            )

    # ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel("Année")
    ax.set_title(f"Prévision ECMWF pour jui-aoû-sep, publiée {month_str}")
    ax.set_ylabel(
        "Précipitations mensuelles prévues,\nmoyenne sur région (mm)"
    )
    break
```

```python
rp = 9

for date_lt_str, month_str in zip(DATE_LT_STRS, ["avril", "mai"]):
    dff = df[(df["date_lt_str"] == date_lt_str) & (df["year"] >= 1999)]
    thresh = dff["precip"].quantile(1 / rp)

    fig, ax = plt.subplots(dpi=300)
    dff.plot(x="year", y="precip", ax=ax, legend=False, color="dodgerblue")

    ax.axhline(y=thresh, color="grey", linestyle="--", alpha=0.5)
    ax.annotate(
        f" seuil 1-an-sur-{rp}\n = {thresh:.0f} mm",
        xy=(2025, thresh),
        color="grey",
        ha="left",
        va="center",
    )

    for year, row in dff.set_index("year").iterrows():
        tp = row["precip"]
        if tp <= thresh:
            ax.annotate(
                year,
                xy=(year, tp),
                color="crimson",
                ha="center",
                va="top",
            )

    # ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel("Année")
    ax.set_title(f"Prévision ECMWF pour jui-aoû-sep, publiée {month_str}")
    ax.set_ylabel(
        "Précipitations mensuelles prévues,\nmoyenne sur région (mm)"
    )
    break
```
