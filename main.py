import pandas as pd
import requests
import github
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import os
import io
from pathlib import Path

""" 
The api at useragents.me/api has been down for a while.
Scraping the site's content to keep things working for now.
"""

r1 = requests.get('https://www.useragents.me/')

id_blocklist = [
    "latest-tablet-useragents",
]

# Let's get the table containers.
soup = BeautifulSoup(r1.content, features="lxml")
titles = soup.select("div.container h2")
containers = [title.parent for title in titles]

# Types of ua
ua_types = ["most-common", "latest"]  # prefixes, we'll use them as keys on output
uas = {}  # output

for container in containers:
    title = container.select("h2")[0]
    table = container.select("table")

    # skip if there's no table,
    if len(table) > 0:
        table = table[0]
    else:
        continue  # skip if no table

    df = pd.read_html(io.StringIO(f"{table}"))[0]
    df['section'] = title.text

    for ua in ua_types:
        if title.attrs['id'] not in id_blocklist and title.attrs['id'].strip().startswith(ua):
            if ua not in uas.keys():
                uas[ua] = []

            uas[ua].append(df)


"""
 Let's just save the data now
"""

# Get date
date = datetime.now(tz=timezone.utc)

# Load env, read ghtoken, load github
load_dotenv()
token = os.getenv('ghtoken')
debug = os.getenv('DEBUG', False)

g = github.Github(token)
repo = g.get_repo("rubenvarela/useragents_me")


# Let's format things and output them
for ua in uas.keys():
    df = pd.concat(uas[ua])
    path = f"data/{date.year}/{date.month:02}/{date.strftime("%Y-%m-%d")}--{ua}.json"

    data = df.to_json(orient="records", indent=4)

    if debug:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as fd:
            fd.write(data)
        continue  # skip the rest

    repo.create_file(
        path,
        message=f"New export created {date.isoformat()} - {ua}",
        content=data,
        branch="main"
    )


