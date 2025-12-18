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
        
        # Go to Andhra Pradesh foundation stage
        url = "https://dashboard.parakh.ncert.gov.in/en/dashboard/IND28?tab=foundation"
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Wait for page to fully load
        await asyncio.sleep(3)
        
        # Get the page content
        content = await page.content()
        
        # Save the HTML for inspection
        with open("/Users/avra/paragh/page_foundation.html", "w") as f:
            f.write(content)
        print("Saved foundation page HTML")
        
        # Look for subject/competency selectors
        # Try to find dropdown or selection elements
        subjects = await page.query_selector_all("select, .dropdown, [class*='subject'], [class*='competenc']")
        print(f"Found {len(subjects)} potential subject/competency elements")
        
        # Try to find any tabs or buttons for subjects
        tabs = await page.query_selector_all("[role='tab'], .tab, button")
        print(f"Found {len(tabs)} tabs/buttons")
        for tab in tabs[:20]:
            text = await tab.inner_text()
            if text.strip():
                print(f"  Tab/Button: {text.strip()[:50]}")
        
        # Look for Learning Achievements section
        learning_section = await page.query_selector("text=Learning Achievements")
        if learning_section:
            print("Found Learning Achievements section")
        
        # Try clicking on Foundation Stage tab to see competencies
        foundation_tab = await page.query_selector("text=Foundational Stage")
        if foundation_tab:
            print("Found Foundational Stage tab, clicking...")
            await foundation_tab.click()
            await asyncio.sleep(2)
        
        # Take a screenshot
        await page.screenshot(path="/Users/avra/paragh/dashboard_screenshot.png", full_page=True)
        print("Screenshot saved")
        
        # Look for any data tables
        tables = await page.query_selector_all("table")
        print(f"Found {len(tables)} tables")
        
        # Look for chart/graph containers that might have data
        charts = await page.query_selector_all("[class*='chart'], [class*='graph'], canvas, svg")
        print(f"Found {len(charts)} chart/graph elements")
        
        # Try to find score/grade elements
        scores = await page.query_selector_all("[class*='score'], [class*='grade'], [class*='percent']")
        print(f"Found {len(scores)} score/grade elements")
        for score in scores[:10]:
            text = await score.inner_text()
            if text.strip():
                print(f"  Score element: {text.strip()[:50]}")
        
        # Look for subject names like Language, Mathematics, EVS
        subject_keywords = ["Language", "Mathematics", "EVS", "Science", "Social"]
        for keyword in subject_keywords:
            elements = await page.query_selector_all(f"text={keyword}")
            print(f"Found {len(elements)} elements with '{keyword}'")
        
        # Try to intercept network requests to find API endpoints
        print("\nLooking for data in page...")
        
        # Get all scripts to find API calls
        scripts = await page.query_selector_all("script")
        print(f"Found {len(scripts)} script tags")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(explore_dashboard())
