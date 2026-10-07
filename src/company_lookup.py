import requests


def find_company(ticker, user_agent):
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Enter a ticker, such as MSFT or AAPL.")

    if not user_agent or not user_agent.strip():
        raise ValueError("Set SEC_USER_AGENT in your .env file.")

    response = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers={"User-Agent": user_agent},
        timeout=30,
    )
    response.raise_for_status()

    for company in response.json().values():
        if company["ticker"].upper() == ticker:
            return {
                "ticker": ticker,
                "cik": str(company["cik_str"]).zfill(10),
                "name": company["title"],
            }

    raise ValueError(f"Ticker '{ticker}' was not found in the SEC list.")