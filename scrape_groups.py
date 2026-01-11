#!/usr/bin/env python3
"""
Scrape remaining PARAKH states using the EXACT working method
Based on scrape_parakh_angular.py that created all_results_complete.json
"""
import asyncio
import json
import sys
from playwright.async_api import async_playwright

# States to scrape in groups
STATE_GROUPS = {
    1: {
        "IND02": "Himachal Pradesh",
        "IND03": "Punjab",
        "IND04": "Chandigarh",
        "IND05": "Uttarakhand",
        "IND06": "Haryana"
    },
    2: {
        "IND07": "NCT of Delhi",
        "IND09": "Uttar Pradesh",
        "IND10": "Bihar",
        "IND11": "Sikkim",
        "IND12": "Arunachal Pradesh"
    },
    3: {
        "IND13": "Nagaland",
        "IND14": "Manipur",
        "IND15": "Mizoram",
        "IND16": "Tripura",
        "IND17": "Meghalaya"
    },
    4: {
        "IND18": "Assam",
        "IND19": "West Bengal",
        "IND21": "Odisha",
        "IND23": "Madhya Pradesh",
        "IND24": "Gujarat"
    },
    5: {
        "IND27": "Maharashtra",
        "IND29": "Karnataka",
        "IND30": "Goa",
        "IND31": "Lakshadweep",
        "IND33": "Tamil Nadu"
    },
    6: {
        "IND34": "Puducherry",
        "IND35": "Andaman & Nicobar Islands",
        "IND36": "Telangana",
        "IND37": "Ladakh",
        "IND38": "Daman & Diu and Dadra & Nagar Haveli"
    }
}

STAGES = {
    "foundation": "Foundational Stage",
    "preparatory": "Preparatory Stage",
    "middle": "Middle Stage"
}

async def get_competency_dropdowns(frame):
    """Find all custom AngularJS competency dropdowns."""
    return await frame.evaluate('''
        () => {
            const result = [];
            const customDropdowns = document.querySelectorAll(".custom-dropdown-list");
            customDropdowns.forEach((dropdown, idx) => {
                const optionNodes = dropdown.querySelectorAll(".tree-view-node .node-item");
                const options = Array.from(optionNodes).map(node => node.textContent.trim());
                
                const hasCompetency = options.some(o => /C-\\d+\\.\\d+/.test(o));
                if (hasCompetency && options.length > 0) {
                    const selectedSpan = dropdown.querySelector(".select-list-selected-val");
                    const selected = selectedSpan ? selectedSpan.textContent.trim().split('<')[0].trim() : null;
                    
                    result.push({
                        index: idx,
                        selected: selected,
                        options: options.filter(o => /C-\\d+\\.\\d+/.test(o)),
                        type: 'custom-dropdown'
                    });
                }
            });
            return result;
        }
    ''')

async def select_competency(frame, dropdown_info, option_text):
    """Select a competency from dropdown."""
    return await frame.evaluate('''
        ({dropdownIndex, dropdownType, optionText}) => {
            try {
                if (dropdownType === 'custom-dropdown') {
                    const dropdowns = document.querySelectorAll(".custom-dropdown-list");
                    const dropdown = dropdowns[dropdownIndex];
                    if (!dropdown) return false;
                    
                    const selectedSpan = dropdown.querySelector(".select-list-selected-val");
                    if (selectedSpan) {
                        selectedSpan.click();
                    }
                    
                    setTimeout(() => {
                        const options = dropdown.querySelectorAll(".tree-view-node .node-item");
                        for (let opt of options) {
                            if (opt.textContent.trim() === optionText) {
                                opt.click();
                                return true;
                            }
                        }
                    }, 100);
                    
                    return true;
                }
                return false;
            } catch (e) {
                return false;
            }
        }
    ''', {'dropdownIndex': dropdown_info['index'], 'dropdownType': dropdown_info['type'], 'optionText': option_text})

async def get_chart_data(frame):
    """Extract Highcharts data."""
    return await frame.evaluate('''
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
            return [];
        }
    ''')

async def scrape_state_stage(page, state_code, state_name, stage_key, stage_name):
    """Scrape all competencies for a state and stage."""
    url = f"https://dashboard.parakh.ncert.gov.in/en/dashboard/{state_code}?tab={stage_key}"
    print(f"\n  {state_name} - {stage_name}...")
    
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=120000)
        await asyncio.sleep(8)
        
        # Find dashboard iframe
        dashboard_frame = None
        for frame in page.frames:
            if 'parakh.ncert.gov.in/dashboard' in frame.url:
                dashboard_frame = frame
                break
        
        if not dashboard_frame:
            print(f"    No dashboard iframe")
            return []
        
        results = []
        dropdowns = await get_competency_dropdowns(dashboard_frame)
        print(f"    Found {len(dropdowns)} dropdowns")
        
        for dd in dropdowns:
            options = dd['options']
            for option_text in options:
                success = await select_competency(dashboard_frame, dd, option_text)
                if not success:
                    continue
                
                await asyncio.sleep(2)
                charts = await get_chart_data(dashboard_frame)
                
                for chart in charts:
                    title = chart.get('title', '')
                    if 'glance' in title.lower() or option_text not in title:
                        continue
                    
                    for series in chart.get('series', []):
                        series_data = series.get('data', [])
                        if len(series_data) <= 2:
                            continue
                        
                        for point in series_data:
                            # Handle point.name being either string or dict
                            district_name = point.get('name', '')
                            if isinstance(district_name, dict):
                                district_name = district_name.get('name', '') or district_name.get('userOptions', '')
                            if isinstance(district_name, str):
                                district_name = district_name.strip()
                            
                            score = point.get('y')
                            
                            if district_name and score is not None:
                                results.append({
                                    'state': state_name,
                                    'stage': stage_name,
                                    'competency_code': option_text.split()[0],
                                    'chart_title': title,
                                    'series_name': series.get('name', ''),
                                    'data': [{
                                        'name': {'userOptions': district_name, 'name': district_name, 'parent': None},
                                        'y': score,
                                        'x': point.get('x', 0)
                                    }]
                                })
        
        print(f"    Collected {len(results)} records")
        return results
        
    except Exception as e:
        print(f"    Error: {e}")
        return []

async def scrape_group(group_num):
    """Scrape a group of states."""
    if group_num not in STATE_GROUPS:
        print(f"Invalid group. Use 1-6")
        return
    
    states = STATE_GROUPS[group_num]
    print(f"\n{'='*60}")
    print(f"GROUP {group_num}: {', '.join(states.values())}")
    print(f"{'='*60}")
    
    all_results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(90000)
        
        for state_code, state_name in states.items():
            print(f"\n{state_name} ({state_code})")
            
            for stage_key, stage_name in STAGES.items():
                results = await scrape_state_stage(page, state_code, state_name, stage_key, stage_name)
                all_results.extend(results)
            
            await asyncio.sleep(2)
        
        await browser.close()
    
    # Save to JSON
    if all_results:
        filename = f'group{group_num}_results.json'
        with open(filename, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n✓ Saved {len(all_results)} records to {filename}")
    else:
        print(f"\n✗ No data found for group {group_num}")

async def main():
    if len(sys.argv) != 2:
        print("Usage: python scrape_groups.py <group_number>")
        print("\nAvailable groups:")
        for num, states in STATE_GROUPS.items():
            print(f"  Group {num}: {', '.join(states.values())}")
        return
    
    group_num = int(sys.argv[1])
    await scrape_group(group_num)

if __name__ == "__main__":
    asyncio.run(main())
