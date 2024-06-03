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

# ERA5

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import matplotlib.pyplot as plt

from src.datasources import era5, codab
from src.constants import *
from src.utils import upsample_dataarray
```

```python
adm = codab.load_codab(admin_level=2)
adm = adm[adm["ADM1_PCODE"] == EXTREMENORD]
```

```python
ds = era5.load_raw_reanalysis()
```

```python
ds
```

```python
da = ds["tp"]
da = da.groupby("time.year").first()
da *= 1000 * 30
da_up = upsample_dataarray(da, resolution=0.01)
da_up = da_up.rio.write_crs(4326)
da_clip = da_up.rio.clip(adm.geometry, all_touched=True)
```

```python
fig, ax = plt.subplots(dpi=300)
adm.boundary.plot(ax=ax, color="white")
da_clip.isel(year=0).plot(ax=ax)
ax.axis("off")
ax.set_title("Exemple de ERA5 sur Extrême-Nord")
```

```python
da_mean = da_clip.mean(dim=["latitude", "longitude"])
```

```python
df
```

```python
df = da_mean.to_dataframe()["tp"].reset_index()
df = df.rename(columns={"tp": "precip"})


df["rank"] = df["precip"].rank().astype(int)
df["rp"] = len(df) / df["rank"]
for rp in [3, 5]:
    thresh = df["precip"].quantile(1 / rp)
    print(rp, thresh)
    df[f"trig_rp{rp}"] = df["precip"] <= thresh

df
```

```python
rp = 5
thresh = df["precip"].quantile(1 / rp)

fig, ax = plt.subplots(dpi=300)
df.plot(x="year", y="precip", ax=ax, legend=False, color="dodgerblue")

ax.axhline(y=thresh, color="grey", linestyle="--", alpha=0.5)
ax.annotate(
    f" seuil 1-an-sur-{rp}\n = {thresh:.0f} mm",
    xy=(2025, thresh),
    color="grey",
    ha="left",
    va="center",
)

for year, row in df.set_index("year").iterrows():
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
ax.set_title("Précipitations ERA5 juillet")
ax.set_ylabel("Précipitations mensuelles prévues,\nmoyenne sur région (mm)")
```
