"""
Explore the PARAKH dashboard to understand the structure and find competencies.
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def explore_dashboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        

        url = "https://dashboard.parakh.ncert.gov.in/en/dashboard/IND28?tab=foundation"
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        

        await asyncio.sleep(3)
        

        content = await page.content()
        

        with open("/Users/avra/paragh/page_foundation.html", "w") as f:
            f.write(content)
        print("Saved foundation page HTML")
        

        subjects = await page.query_selector_all("select, .dropdown, [class*='subject'], [class*='competenc']")
        print(f"Found {len(subjects)} potential subject/competency elements")
        

        tabs = await page.query_selector_all("[role='tab'], .tab, button")
        print(f"Found {len(tabs)} tabs/buttons")
        for tab in tabs[:20]:
            text = await tab.inner_text()
            if text.strip():
                print(f"  Tab/Button: {text.strip()[:50]}")
        

        learning_section = await page.query_selector("text=Learning Achievements")
        if learning_section:
            print("Found Learning Achievements section")
        

        foundation_tab = await page.query_selector("text=Foundational Stage")
        if foundation_tab:
            print("Found Foundational Stage tab, clicking...")
            await foundation_tab.click()
            await asyncio.sleep(2)
        

        await page.screenshot(path="/Users/avra/paragh/dashboard_screenshot.png", full_page=True)
        print("Screenshot saved")
        

        tables = await page.query_selector_all("table")
        print(f"Found {len(tables)} tables")
        

        charts = await page.query_selector_all("[class*='chart'], [class*='graph'], canvas, svg")
        print(f"Found {len(charts)} chart/graph elements")
        

        scores = await page.query_selector_all("[class*='score'], [class*='grade'], [class*='percent']")
        print(f"Found {len(scores)} score/grade elements")
        for score in scores[:10]:
            text = await score.inner_text()
            if text.strip():
                print(f"  Score element: {text.strip()[:50]}")
        

        subject_keywords = ["Language", "Mathematics", "EVS", "Science", "Social"]
        for keyword in subject_keywords:
            elements = await page.query_selector_all(f"text={keyword}")
            print(f"Found {len(elements)} elements with '{keyword}'")
        

        print("\nLooking for data in page...")
        

        scripts = await page.query_selector_all("script")
        print(f"Found {len(scripts)} script tags")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(explore_dashboard())
