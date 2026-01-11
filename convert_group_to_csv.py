#!/usr/bin/env python3
"""
Convert group JSON results to CSV format matching parakh_competency_data.csv
"""
import json
import pandas as pd
import sys
import re

def extract_competency_code(text):
    """Extract competency code from text."""
    match = re.search(r'(C-\d+\.?\d*)', text)
    return match.group(1) if match else text

def get_subject(stage, comp_code):
    """Map competency code to subject based on stage."""
    # Competency to Subject mapping from PARAKH framework
    mapping = {
        'Foundational Stage': {
            'C-10.5': 'Language', 'C-10.7': 'Language', 'C-9.7': 'Language',
            'C-8.1': 'Mathematics', 'C-8.2': 'Mathematics', 'C-8.4': 'Mathematics',
            'C-8.5': 'Mathematics', 'C-8.6': 'Mathematics', 'C-8.7': 'Mathematics',
            'C-8.8': 'Mathematics', 'C-8.9': 'Mathematics', 'C-8.10': 'Mathematics',
            'C-8.11': 'Mathematics', 'C-8.12': 'Mathematics', 'C-8.13': 'Mathematics'
        },
        'Preparatory Stage': {
            'C-2.1': 'Language', 'C-2.2': 'Language',
            'C-1.1': 'Mathematics', 'C-1.2': 'Mathematics', 'C-1.3': 'Mathematics',
            'C-1.4': 'Mathematics', 'C-2.4': 'Mathematics', 'C-3.3': 'Mathematics',
            'C-3.5': 'Mathematics', 'C-4.1': 'Mathematics', 'C-4.3': 'Mathematics',
            'C-3.1': 'World Around Us', 'C-3.2': 'World Around Us', 'C-4.7': 'World Around Us', 'C-5.3': 'World Around Us'
        },
        'Middle Stage': {
            'C-1.1': 'Language',
            'C-1.2': 'Mathematics', 'C-2.1': 'Mathematics', 'C-3.1': 'Mathematics',
            'C-4.1': 'Mathematics', 'C-5.1': 'Mathematics', 'C-6.1': 'Mathematics',
            'C-2.2': 'Science', 'C-2.3': 'Science', 'C-2.4': 'Science',
            'C-3.2': 'Science', 'C-4.3': 'Science', 'C-7.3': 'Science',
            'C-1.4': 'Social Science', 'C-4.2': 'Social Science', 'C-6.2': 'Social Science',
            'C-6.3': 'Social Science', 'C-6.4': 'Social Science', 'C-7.1': 'Social Science',
            'C-7.2': 'Social Science', 'C-8.2': 'Social Science', 'C-8.3': 'Social Science', 'C-9.1': 'Social Science'
        }
    }
    return mapping.get(stage, {}).get(comp_code, 'Unknown')

def json_to_csv(json_file, csv_file):
    """Convert group JSON to CSV."""
    print(f"Converting {json_file} to {csv_file}...")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    rows = []
    for record in data:
        state = record.get('state', '')
        stage = record.get('stage', '')
        comp_code = extract_competency_code(record.get('competency_code', ''))
        chart_title = record.get('chart_title', '')
        subject = get_subject(stage, comp_code)
        
        for point in record.get('data', []):
            name_obj = point.get('name', {})
            if isinstance(name_obj, dict):
                district = name_obj.get('name', '') or name_obj.get('userOptions', '')
            else:
                district = name_obj
            
            score = point.get('y')
            
            if district and score is not None:
                rows.append({
                    'State': state,
                    'State_Code': '',
                    'District': district,
                    'Stage': stage,
                    'Subject': subject,
                    'Competency_Code': comp_code,
                    'Competency_Description': chart_title,
                    'Score_Percent': round(score, 2)
                })
    
    df = pd.DataFrame(rows)
    
    # Add state codes
    state_codes = {
        'Himachal Pradesh': 'IND02',
        'Punjab': 'IND03',
        'Chandigarh': 'IND04',
        'Uttarakhand': 'IND05',
        'Haryana': 'IND06',
        'NCT of Delhi': 'IND07',
        'Uttar Pradesh': 'IND09',
        'Bihar': 'IND10',
        'Sikkim': 'IND11',
        'Arunachal Pradesh': 'IND12',
        'Nagaland': 'IND13',
        'Manipur': 'IND14',
        'Mizoram': 'IND15',
        'Tripura': 'IND16',
        'Meghalaya': 'IND17',
        'Assam': 'IND18',
        'West Bengal': 'IND19',
        'Odisha': 'IND21',
        'Madhya Pradesh': 'IND23',
        'Gujarat': 'IND24',
        'Maharashtra': 'IND27',
        'Karnataka': 'IND29',
        'Goa': 'IND30',
        'Lakshadweep': 'IND31',
        'Tamil Nadu': 'IND33',
        'Puducherry': 'IND34',
        'Andaman & Nicobar Islands': 'IND35',
        'Telangana': 'IND36',
        'Ladakh': 'IND37',
        'Daman & Diu and Dadra & Nagar Haveli': 'IND38'
    }
    
    df['State_Code'] = df['State'].map(state_codes)
    
    # Sort by State, District, Stage, then Competency
    stage_order = {'Foundational Stage': 1, 'Preparatory Stage': 2, 'Middle Stage': 3}
    df['_stage_order'] = df['Stage'].map(stage_order)
    
    df = df.sort_values(['State', 'District', '_stage_order', 'Competency_Code'])
    df = df.drop('_stage_order', axis=1)
    
    # Save
    df.to_csv(csv_file, index=False)
    
    print(f"✓ Saved {len(df)} rows to {csv_file}")
    print(f"  States: {df['State'].nunique()}")
    print(f"  Districts: {df['District'].nunique()}")
    print(f"  Competencies: {df['Competency_Code'].nunique()}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_group_to_csv.py <group_number>")
        sys.exit(1)
    
    group_num = sys.argv[1]
    json_file = f'group{group_num}_results.json'
    csv_file = f'group{group_num}_data.csv'
    
    json_to_csv(json_file, csv_file)
