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