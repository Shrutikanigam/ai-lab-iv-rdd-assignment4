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

print(master_df.head())
print(master_df.columns)

master_df.to_csv("raw_master_data.csv", index=False)
print("Saved raw_master_data.csv")
