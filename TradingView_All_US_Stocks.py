# This script scrapes the TradingView website and saves all active US stocks in a .csv-file

import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from tqdm.asyncio import tqdm

async def scrape_data():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        page = await browser.new_page()

        # Load page
        await page.goto("https://www.tradingview.com/markets/stocks-usa/market-movers-all-stocks/")
        
        # Click 'Load More' until no more button is found
        while True:
            try:
                load_more_btn = await page.wait_for_selector('span.content-D4RPB3ZC', timeout=5000)
                await load_more_btn.click()
            except Exception as e:
                print("No more 'Load More' buttons or error occurred:", e)
                break
        
        # Get all <tr> elements with class 'row-RdUXZpkv listRow'
        tr_elements = await page.query_selector_all('tr.row-RdUXZpkv.listRow')
        print(f"Number of <tr> elements found: {len(tr_elements)}")

        # Extract headers
        table = await page.query_selector('table.table-Ngq2xrcG')
        headers = [await header.inner_text() for header in await table.query_selector_all("th")]
        headers.insert(1, 'Name')
        print(f"Extracting table with headers: {headers}")

        data = []
        # Process rows with a progress bar
        async for row in tqdm(tr_elements, desc="Processing rows", unit="row"):
            cols = await row.query_selector_all("td")
            if cols:  # Skip the header row
                row_data = []
                for i, col in enumerate(cols):
                    text = await col.inner_text()
                    if i == 0:  # First column with symbol and company name
                        parts = text.split('\n')
                        symbol = parts[0]
                        name = parts[1].rstrip('D').strip()  # Remove trailing 'D' and whitespace
                        row_data.append(symbol)
                        row_data.append(name)
                    else:
                        row_data.append(text)
                data.append(row_data)
        
        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(data, columns=headers)
        df.to_csv("symbols.csv", index=False)
        
        # Close the browser
        await browser.close()

        return df

if __name__ == "__main__":
    asyncio.run(scrape_data())