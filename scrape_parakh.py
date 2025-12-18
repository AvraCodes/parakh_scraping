"""
PARAKH Dashboard Scraper
Scrapes state and district level competency data from the PARAKH dashboard.
"""
import asyncio
import json
import csv
import re
from playwright.async_api import async_playwright
from datetime import datetime

# Target states with their codes
STATES = {
    "IND28": "Andhra Pradesh",
    "IND01": "Jammu & Kashmir",
    "IND20": "Jharkhand",
    "IND22": "Chhattisgarh",
    "IND32": "Kerala",
    "IND08": "Rajasthan"
}

# Stages and their dashboard IDs
STAGES = {
    "foundation": {"name": "Foundational Stage", "grade": "Grade 3", "dashboard_id": 745},
    "preparatory": {"name": "Preparatory Stage", "grade": "Grade 6", "dashboard_id": 747},
    "middle": {"name": "Middle Stage", "grade": "Grade 9", "dashboard_id": 749}
}

# Store all collected data
all_data = []

async def get_area_data(page):
    """Fetch area data from API"""
    response = await page.evaluate("""
        async () => {
            const resp = await fetch('https://dashboard.parakh.ncert.gov.in/api/getArea?isDashboard=true');
            return await resp.json();
        }
    """)
    return response

async def get_data_for_area(page, area_id):
    """Fetch data for a specific area"""
    response = await page.evaluate(f"""
        async () => {{
            const resp = await fetch('https://dashboard.parakh.ncert.gov.in/api/getData?areaId={area_id}');
            return await resp.json();
        }}
    """)
    return response

async def extract_competency_scores_from_page(page, state_code, state_name, stage_name, stage_info):
    """Extract competency scores from the dashboard page by parsing the chart data"""
    results = []
    
    # Wait for the page to fully load
    await asyncio.sleep(3)
    
    # Try to get data from the JavaScript variables in the page
    try:
        # Get the dashboard data from the JavaScript file
        dashboard_data = await page.evaluate("""
            () => {
                if (typeof dashboardVisualizations !== 'undefined') {
                    return dashboardVisualizations;
                }
                return null;
            }
        """)
        
        if dashboard_data:
            print(f"  Found dashboard visualizations for {state_name} - {stage_name}")
            return dashboard_data
    except Exception as e:
        print(f"  Could not get JS data: {e}")
    
    return results

async def scrape_state_data(page, state_code, state_name, stage_key, stage_info):
    """Scrape data for a specific state and stage"""
    url = f"https://dashboard.parakh.ncert.gov.in/en/dashboard/{state_code}?tab={stage_key}"
    print(f"\nScraping {state_name} - {stage_info['name']}...")
    print(f"  URL: {url}")
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)  # Wait for JavaScript to fully render
        
        # Get the visualization data
        data = await extract_competency_scores_from_page(page, state_code, state_name, stage_info['name'], stage_info)
        return data
    except Exception as e:
        print(f"  Error scraping {state_name} - {stage_info['name']}: {e}")
        return None

async def fetch_dashboard_js_data(page, dashboard_id):
    """Fetch and parse the dashboard JavaScript data file"""
    # Try different file patterns
    for suffix in range(50, 150):
        url = f"https://parakh.ncert.gov.in/dashboard/files/dashboardData/{dashboard_id}_dashData_{suffix}.js"
        try:
            response = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{url}');
                        if (resp.ok) {{
                            return await resp.text();
                        }}
                    }} catch(e) {{}}
                    return null;
                }}
            """)
            if response:
                print(f"  Found data file: {url}")
                return response
        except:
            pass
    return None

async def parse_competencies_from_js(js_content, stage_name):
    """Parse competency information from JavaScript content"""
    competencies = []
    
    # Extract competency codes and descriptions using regex
    # Pattern to match competency definitions like "C-1.1", "C-10.5", etc.
    pattern = r'"sg":\{"en":"(C-\d+\.\d+[^"]*)"'
    matches = re.findall(pattern, js_content)
    
    # Also extract the full indicator descriptions
    indicator_pattern = r'"sgtpid":"ind","sg":\{"en":"([^"]+)"'
    indicator_matches = re.findall(indicator_pattern, js_content)
    
    # Extract subjects
    subject_pattern = r'<h6>([^<]+)</h6>'
    subjects = re.findall(subject_pattern, js_content)
    
    seen = set()
    for match in matches:
        # Clean up the competency code
        code = match.strip()
        if code and code.startswith('C-') and code not in seen:
            seen.add(code)
            competencies.append({
                'code': code.split()[0] if ' ' in code else code,
                'description': code
            })
    
    return competencies, list(set(subjects))

async def extract_data_with_api(page, state_code, state_name):
    """Extract data using the API endpoints"""
    results = []
    
    try:
        # Fetch data from API
        api_data = await page.evaluate(f"""
            async () => {{
                const resp = await fetch('https://dashboard.parakh.ncert.gov.in/api/getData?areaId={state_code}');
                return await resp.json();
            }}
        """)
        
        if api_data and 'data' in api_data:
            return api_data
    except Exception as e:
        print(f"  API Error for {state_name}: {e}")
    
    return None

async def scrape_all_states():
    """Main scraping function"""
    print("=" * 60)
    print("PARAKH Dashboard Scraper")
    print("=" * 60)
    print(f"Target States: {', '.join(STATES.values())}")
    print(f"Stages: {', '.join([s['name'] for s in STAGES.values()])}")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # First, get the area data to understand the structure
        print("\nFetching area data...")
        await page.goto("https://dashboard.parakh.ncert.gov.in/en", wait_until="networkidle", timeout=60000)
        
        area_data = await get_area_data(page)
        if area_data:
            print(f"  Found {len(area_data.get('data', []))} areas")
            
            # Save area data for reference
            with open("/Users/avra/paragh/area_data.json", "w") as f:
                json.dump(area_data, f, indent=2)
        
        # Collect all data
        all_results = []
        
        # For each state
        for state_code, state_name in STATES.items():
            print(f"\n{'=' * 40}")
            print(f"Processing: {state_name} ({state_code})")
            print('=' * 40)
            
            # Get state-level data from API
            state_api_data = await extract_data_with_api(page, state_code, state_name)
            if state_api_data:
                print(f"  Got API data for {state_name}")
                
                # Save raw API data
                with open(f"/Users/avra/paragh/api_data_{state_code}.json", "w") as f:
                    json.dump(state_api_data, f, indent=2)
            
            # For each stage, navigate to the page and extract data
            for stage_key, stage_info in STAGES.items():
                url = f"https://dashboard.parakh.ncert.gov.in/en/dashboard/{state_code}?tab={stage_key}"
                print(f"\n  Stage: {stage_info['name']} ({stage_info['grade']})")
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                    await asyncio.sleep(3)
                    
                    # Extract visible data from the page
                    page_data = await page.evaluate("""
                        () => {
                            const results = [];
                            
                            // Try to get data from any visible charts
                            const charts = document.querySelectorAll('[class*="highcharts"]');
                            
                            // Get any text content that looks like scores
                            const scoreElements = document.querySelectorAll('[class*="score"], [class*="percent"], [class*="value"]');
                            scoreElements.forEach(el => {
                                const text = el.innerText.trim();
                                if (text && /^\d+(\.\d+)?%?$/.test(text)) {
                                    results.push({type: 'score', value: text});
                                }
                            });
                            
                            // Get competency labels
                            const labels = document.querySelectorAll('[class*="competenc"], [class*="label"]');
                            labels.forEach(el => {
                                const text = el.innerText.trim();
                                if (text && text.startsWith('C-')) {
                                    results.push({type: 'competency', value: text});
                                }
                            });
                            
                            return results;
                        }
                    """)
                    
                    print(f"    Found {len(page_data)} data points on page")
                    
                    # Also intercept the data from the embedded iframe
                    frames = page.frames
                    for frame in frames:
                        try:
                            frame_url = frame.url
                            if 'parakh.ncert.gov.in/dashboard' in frame_url:
                                print(f"    Found dashboard iframe: {frame_url[:80]}...")
                                
                                # Try to get data from the iframe
                                iframe_data = await frame.evaluate("""
                                    () => {
                                        if (typeof Highcharts !== 'undefined') {
                                            const charts = Highcharts.charts.filter(c => c);
                                            return charts.map(chart => ({
                                                title: chart.title ? chart.title.textStr : '',
                                                series: chart.series ? chart.series.map(s => ({
                                                    name: s.name,
                                                    data: s.data ? s.data.map(d => ({
                                                        name: d.name || d.category,
                                                        y: d.y,
                                                        x: d.x
                                                    })) : []
                                                })) : []
                                            }));
                                        }
                                        return null;
                                    }
                                """)
                                
                                if iframe_data:
                                    print(f"    Got Highcharts data: {len(iframe_data)} charts")
                                    all_results.append({
                                        'state': state_name,
                                        'state_code': state_code,
                                        'stage': stage_info['name'],
                                        'grade': stage_info['grade'],
                                        'charts': iframe_data
                                    })
                        except Exception as e:
                            pass
                    
                except Exception as e:
                    print(f"    Error: {e}")
        
        await browser.close()
        
        # Save all results
        with open("/Users/avra/paragh/all_results.json", "w") as f:
            json.dump(all_results, f, indent=2)
        
        print("\n" + "=" * 60)
        print("Scraping complete!")
        print("=" * 60)
        
        return all_results

async def main():
    results = await scrape_all_states()
    print(f"\nCollected data for {len(results)} state-stage combinations")

if __name__ == "__main__":
    asyncio.run(main())
