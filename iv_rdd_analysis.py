# Copilot Prompt:
# "Scrape index page, collect all report links, and extract infrastructure,
# funding, and metrics tables into separate DataFrames for merging"

import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
from urllib.parse import urljoin

base_url = "https://bana290-assignment4.netlify.app/"
response = requests.get(base_url)
soup = BeautifulSoup(response.text, "html.parser")

print(response.status_code)
print(soup.title.text)

links = [urljoin(base_url, a["href"]) for a in soup.find_all("a", href=True)]

print("Sample links:", links[:5])
print("Total links found:", len(links))
for link in links:
    print(link)

dfs = []

for link in links:
    page = requests.get(link)
    tables = pd.read_html(StringIO(page.text))

    df = tables[0]

    # use first row as header
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

    df["source_url"] = link
    dfs.append(df)

    print(f"Scraped: {link}")
    print(df.head(), "\n")
# Copilot Prompt:
# "Merge the three scraped tables into one master dataset using TEAM_REF as the common key"

infra_df = dfs[0]
metrics_df = dfs[1]
fund_df = dfs[2]

master_df = infra_df.merge(metrics_df, on="TEAM_REF").merge(fund_df, on="TEAM_REF")

master_df = master_df.loc[:, ~master_df.columns.duplicated()]
master_df["TEAM_REF"] = master_df["TEAM_REF"].astype(str).str.strip()

print(master_df.head())
print(master_df.columns)

master_df.to_csv("raw_master_data.csv", index=False)
print("Saved raw_master_data.csv")



# Copilot Prompt:
# "Clean messy numeric fields by removing text like km, thousand, commas, and convert to float"
import numpy as np
import re
# define columns first
clean_cols = [
    "DISTANCE_TO_NODE",
    "AI_INTENSITY",
    "INNOVATION_SCORE",
    "ELIGIBILITY_SCORE"
]
def clean_numeric(val):
    if pd.isna(val):
        return np.nan

    val = str(val).lower()
    val = val.replace(",", "")
    val = val.replace("~", "")

    if "thousand" in val or "k" in val:
        match = re.findall(r"\d+\.?\d*", val)
        if match:
            return float(match[0]) * 1000
        return np.nan

    match = re.findall(r"\d+\.?\d*", val)
    if match:
        return float(match[0])

    return np.nan


for col in clean_cols:
    master_df[col] = master_df[col].apply(clean_numeric)

master_df[clean_cols] = master_df[clean_cols].astype(float)

print(master_df[clean_cols].head())
print(master_df[clean_cols].dtypes)

master_df.to_csv("cleaned_master_data.csv", index=False)
print("Saved cleaned_master_data.csv")
# Copilot Prompt:
# "Cap outliers in AI intensity and innovation score using the IQR rule"

def cap_outliers(series):
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    return series.clip(lower=lower, upper=upper)

master_df["AI_INTENSITY"] = cap_outliers(master_df["AI_INTENSITY"])
master_df["INNOVATION_SCORE"] = cap_outliers(master_df["INNOVATION_SCORE"])

print(master_df[["AI_INTENSITY", "INNOVATION_SCORE"]].describe())

# Copilot Prompt:
# "Run naive OLS, IV first stage, IV second stage, and RDD analysis"

import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

# 1. Naive OLS
ols_model = smf.ols("INNOVATION_SCORE ~ AI_INTENSITY", data=master_df).fit()
print("\nNaive OLS Results")
print(ols_model.summary())


# 2. IV Analysis — First Stage
first_stage = smf.ols("AI_INTENSITY ~ DISTANCE_TO_NODE", data=master_df).fit()
print("\nFirst Stage Results")
print(first_stage.summary())


# Create predicted AI from first stage
master_df["predicted_ai"] = first_stage.fittedvalues


# 3. IV Analysis — Second Stage (manual 2SLS)
second_stage = smf.ols("INNOVATION_SCORE ~ predicted_ai", data=master_df).fit()
print("\nSecond Stage (2SLS) Results")
print(second_stage.summary())


# 4. RDD setup
cutoff = 85
master_df["eligible"] = (master_df["ELIGIBILITY_SCORE"] >= cutoff).astype(int)


# 5. RDD Plot
plt.figure(figsize=(8,5))
plt.scatter(master_df["ELIGIBILITY_SCORE"], master_df["INNOVATION_SCORE"], alpha=0.7)
plt.axvline(cutoff, linestyle="--")
plt.xlabel("Eligibility Score")
plt.ylabel("Innovation Score")
plt.title("RDD Plot: Innovation vs Eligibility Score")
plt.savefig("rdd_plot.png")
plt.show()


# 6. Density Plot (continuity check)
plt.figure(figsize=(8,5))
master_df["ELIGIBILITY_SCORE"].plot(kind="hist", bins=15)
plt.axvline(cutoff, linestyle="--")
plt.xlabel("Eligibility Score")
plt.title("Density Check Around RDD Cutoff")
plt.savefig("rdd_density_plot.png")
plt.show()