#!/usr/bin/env python3
"""
Create 3 separate CSVs for PARAKH dashboard data - one per stage:
1. foundational_stage.csv - Grade 3
2. preparatory_stage.csv - Grade 6  
3. middle_stage.csv - Grade 9

Columns: State, District, Subject, LO_Code, Description, Score
"""

import json
import pandas as pd
import re

# Subject mapping from series codes
SUBJECT_FROM_SERIES = {
    "FSLANG": "Language",
    "FSMAT": "Mathematics",
    "PSLANG": "Language",
    "PSMAT": "Mathematics",
    "PSWAU": "World Around Us",
    "MSLANG": "Language",
    "MSMAT": "Mathematics",
    "MSSC": "Science",
    "MSSS": "Social Science"
}

def get_subject_from_series(series_name):
    """Extract subject from series name prefix."""
    for code, subject in SUBJECT_FROM_SERIES.items():
        if series_name.startswith(code):
            return subject
    return None

def get_subject_from_title(title):
    """Extract subject from chart title like 'All competencies for X at a glance'."""
    title_lower = title.lower()
    if 'language' in title_lower:
        return 'Language'
    elif 'mathematics' in title_lower:
        return 'Mathematics'
    elif 'world around us' in title_lower:
        return 'World Around Us'
    elif 'science' in title_lower and 'social' not in title_lower:
        return 'Science'
    elif 'social science' in title_lower:
        return 'Social Science'
    return None

def extract_lo_code(text):
    """Extract LO code (C-X.X pattern)."""
    if isinstance(text, dict):
        text = text.get('name', text.get('userOptions', ''))
    if not isinstance(text, str):
        return None
    match = re.search(r'(C-\d+\.\d+)', text)
    return match.group(1) if match else None

def extract_name(name_field):
    """Extract string name from name field."""
    if isinstance(name_field, dict):
        return name_field.get('name', name_field.get('userOptions', '')).strip()
    return str(name_field).strip() if name_field else ''

def load_data():
    with open('/Users/avra/paragh/all_results.json', 'r') as f:
        return json.load(f)

def infer_subject_from_description(description):
    """Infer subject from the LO description text."""
    desc_lower = description.lower()
    
    # World Around Us indicators (check first - more specific)
    if any(kw in desc_lower for kw in ['natural', 'insects', 'plants', 'birds', 'animals',
                                        'environment', 'sun', 'moon', 'stars', 'planets',
                                        'resources', 'houses', 'relationships', 'geographical features']):
        return 'World Around Us'
    
    # Language indicators
    if any(kw in desc_lower for kw in ['reading', 'listening', 'comprehension', 'stories', 
                                        'summarises', 'editorials', 'reports', 'articles',
                                        'text', 'visualising']):
        return 'Language'
    
    # Mathematics indicators
    if any(kw in desc_lower for kw in ['numbers', 'place value', 'patterns', 'multiples', 
                                        'powers', 'prime', 'fractions', 'ratio', 'shapes',
                                        'geometric', 'mathematics', 'math']):
        return 'Mathematics'
    
    # Science indicators  
    if any(kw in desc_lower for kw in ['matter', 'solid', 'liquid', 'gas', 'density',
                                        'magnetic', 'conducting', 'chemical', 'physical',
                                        'cells', 'photosynthesis', 'reproduction', 'inheritance',
                                        'motion', 'friction', 'pressure', 'force', 'classifies matter']):
        return 'Science'
    
    # Social Science indicators
    if any(kw in desc_lower for kw in ['historical', 'cultural', 'socio-political',
                                        'government', 'society', 'archaeological', 'sources',
                                        'primary and secondary']):
        return 'Social Science'
    
    return None

def process_stage(data, stage_name):
    """Process all data for a specific stage."""
    rows = []
    
    # Collect chart info: {(lo_code, description): subject}
    chart_info = {}
    
    # First pass: collect all charts with district data and infer subjects
    for entry in data:
        if entry.get('stage') != stage_name:
            continue
        for chart in entry.get('charts', []):
            title = chart.get('title', '')
            lo_code = extract_lo_code(title)
            
            # Skip summary charts
            if 'glance' in title.lower() or not lo_code:
                continue
            
            # Check if this chart has district data (more than 2 points)
            has_district_data = False
            for series in chart.get('series', []):
                if len(series.get('data', [])) > 2:
                    has_district_data = True
                    break
            
            if has_district_data:
                # Try to get subject from series name first
                subject = None
                for series in chart.get('series', []):
                    subject = get_subject_from_series(series.get('name', ''))
                    if subject:
                        break
                
                # If not found, infer from title/description
                if not subject:
                    subject = infer_subject_from_description(title)
                
                if subject:
                    # Use (lo_code, title) as key since same LO code can have different subjects
                    chart_info[(lo_code, title)] = subject
    
    # Second pass: extract district-level data
    for entry in data:
        if entry.get('stage') != stage_name:
            continue
        
        state = entry.get('state', '')
        
        for chart in entry.get('charts', []):
            title = chart.get('title', '')
            chart_lo_code = extract_lo_code(title)
            
            # Skip summary charts or no LO code
            if 'glance' in title.lower() or not chart_lo_code:
                continue
            
            # Get subject for this specific chart
            subject = chart_info.get((chart_lo_code, title))
            if not subject:
                continue
            
            for series in chart.get('series', []):
                series_name = series.get('name', '')
                series_data = series.get('data', [])
                
                # Skip if only 2 data points (India + State comparison)
                if len(series_data) <= 2:
                    continue
                
                for point in series_data:
                    name = extract_name(point.get('name', ''))
                    score = point.get('y')
                    
                    # Skip if no score or no name
                    if score is None or not name:
                        continue
                    
                    # Skip India (national average) and state name
                    if name.lower() in ['india', state.lower()]:
                        continue
                    
                    rows.append({
                        'State': state,
                        'District': name,
                        'Subject': subject,
                        'LO_Code': chart_lo_code,
                        'Description': title.strip(),
                        'Score': score
                    })
    
    return pd.DataFrame(rows)

def validate_and_save(df, filename, stage_name):
    """Validate dataframe and save to CSV."""
    if df.empty:
        print(f"WARNING: No data for {stage_name}")
        return
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['State', 'District', 'Subject', 'LO_Code'])
    
    # Sort
    df = df.sort_values(['State', 'Subject', 'LO_Code', 'District'])
    
    # Check for missing values
    print(f"\n{stage_name}:")
    print(f"  Total rows: {len(df)}")
    print(f"  States: {sorted(df['State'].unique())}")
    print(f"  Subjects: {sorted(df['Subject'].unique())}")
    print(f"  LO Codes: {sorted(df['LO_Code'].unique())}")
    print(f"  Districts: {df['District'].nunique()}")
    
    missing = {}
    for col in df.columns:
        if df[col].dtype == 'object':
            miss = df[col].isna().sum() + (df[col] == '').sum()
        else:
            miss = df[col].isna().sum()
        if miss > 0:
            missing[col] = miss
    
    if missing:
        print(f"  WARNING - Missing values: {missing}")
    else:
        print(f"  ✓ All entries complete")
    
    # Save
    df.to_csv(f'/Users/avra/paragh/{filename}', index=False)
    print(f"  Saved to {filename}")

def main():
    print("Creating 3 separate CSVs for PARAKH dashboard data...")
    print("=" * 60)
    
    data = load_data()
    
    # Process each stage
    foundational_df = process_stage(data, 'Foundational Stage')
    preparatory_df = process_stage(data, 'Preparatory Stage')
    middle_df = process_stage(data, 'Middle Stage')
    
    # Validate and save
    validate_and_save(foundational_df, 'foundational_stage.csv', 'Foundational Stage (Grade 3)')
    validate_and_save(preparatory_df, 'preparatory_stage.csv', 'Preparatory Stage (Grade 6)')
    validate_and_save(middle_df, 'middle_stage.csv', 'Middle Stage (Grade 9)')
    
    print("\n" + "=" * 60)
    print("Done!")

if __name__ == "__main__":
    main()
