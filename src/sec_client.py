import os

import requests
from dotenv import load_dotenv


load_dotenv()

SEC_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json"

user_agent = os.getenv("SEC_USER_AGENT")

headers = {
    "User-Agent": user_agent
}

response = requests.get(SEC_URL, headers=headers, timeout=30)

response.raise_for_status()

data = response.json()

print(data["entityName"])