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

# Biomasse

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from src.datasources import biomasse
from src.constants import *
```

```python
EXTREMENORD_ALT = "CM04"
EOS_DEKAD = 24
```

```python
# biomasse.download_biomasse(admin_level="ADM1")
```

```python
df = biomasse.load_dmp(admin_level="ADM1")
```

```python
df_en = df.set_index("admin1Pcod").loc[EXTREMENORD_ALT]
# df_en = df_en[df_en["index"].str.endswith(str(EOS_DEKAD))]
df_en
```

```python
years = range(1999, 2024)

mean_val = df_en.loc["DMP_MEA_24"]

dicts = []
for year in years:
    abs_val = df_en.loc[f"DMP_{year}24"]
    dicts.append({"year": year, "abs": abs_val, "anom": abs_val / mean_val})

df_anom = pd.DataFrame(dicts)
```

```python
mean_val
```

```python
df_anom["rank"] = df_anom["anom"].rank().astype(int)
df_anom["rp"] = len(df_anom) / df_anom["rank"]
for rp in [3, 5]:
    thresh = df_anom["anom"].quantile(1 / rp)
    print(rp, thresh)
    df_anom[f"trig_rp{rp}"] = df_anom["anom"] <= thresh
df_anom
```

```python
rp = 7
thresh = df_anom["anom"].quantile(1 / rp)

fig, ax = plt.subplots(dpi=300)
df_anom.plot(x="year", y="anom", ax=ax, legend=False, color="dodgerblue")

ax.axhline(y=thresh, color="grey", linestyle="--", alpha=0.5)
ax.annotate(
    f" seuil 1-an-sur-{rp}\n = {thresh:.1%}",
    xy=(2024, thresh),
    color="grey",
    ha="left",
    va="center",
)

for year, row in df_anom.set_index("year").iterrows():
    tp = row["anom"]
    if tp <= thresh:
        ax.annotate(
            year,
            xy=(year, tp),
            color="crimson",
            ha="center",
            va="top",
        )

ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlabel("Année")
ax.set_ylabel("Anomalie de biomasse, évalué fin août")
ax.set_title("Anomalie de biomasse, fin août, Extrême-Nord")
```

```python
rp = 9
thresh = df_anom["anom"].quantile(1 / rp)

fig, ax = plt.subplots(dpi=300)
df_anom.plot(x="year", y="anom", ax=ax, legend=False, color="dodgerblue")

ax.axhline(y=thresh, color="grey", linestyle="--", alpha=0.5)
ax.annotate(
    f" seuil 1-an-sur-{rp}\n = {thresh:.1%}",
    xy=(2024, thresh),
    color="grey",
    ha="left",
    va="center",
)

for year, row in df_anom.set_index("year").iterrows():
    tp = row["anom"]
    if tp <= thresh:
        ax.annotate(
            year,
            xy=(year, tp),
            color="crimson",
            ha="center",
            va="top",
        )

ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlabel("Année")
ax.set_ylabel("Anomalie de biomasse, évalué fin août")
ax.set_title("Anomalie de biomasse, fin août, Extrême-Nord")
```

```python

```
