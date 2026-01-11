#!/usr/bin/env python3
"""
Combine all group CSVs into the main parakh_competency_data.csv
"""
import pandas as pd
import sys

def combine_csvs():
    """Combine existing CSV with new group CSVs."""
    
    # Load existing data
    main_df = pd.read_csv('parakh_competency_data.csv')
    print(f"Existing data: {len(main_df)} rows, {main_df['State'].nunique()} states")
    
    # Find all group CSVs
    import glob
    group_files = sorted(glob.glob('group*_data.csv'))
    
    if not group_files:
        print("No group CSV files found!")
        return
    
    print(f"\nFound {len(group_files)} group files:")
    for f in group_files:
        print(f"  {f}")
    
    # Combine all data
    all_dfs = [main_df]
    
    for group_file in group_files:
        df = pd.read_csv(group_file)
        print(f"\n{group_file}: {len(df)} rows, {df['State'].nunique()} states")
        all_dfs.append(df)
    
    # Concatenate
    combined = pd.concat(all_dfs, ignore_index=True)
    
    # Remove duplicates (keep last version)
    combined = combined.drop_duplicates(
        subset=['State', 'District', 'Stage', 'Competency_Code'],
        keep='last'
    )
    
    # Sort by State, District, Stage, then Competency
    stage_order = {'Foundational Stage': 1, 'Preparatory Stage': 2, 'Middle Stage': 3}
    combined['_stage_order'] = combined['Stage'].map(stage_order)
    
    combined = combined.sort_values(['State', 'District', '_stage_order', 'Competency_Code'])
    combined = combined.drop('_stage_order', axis=1)
    
    # Save
    combined.to_csv('parakh_competency_data_all.csv', index=False)
    
    print(f"\n{'='*60}")
    print(f"✓ Combined CSV saved: parakh_competency_data_all.csv")
    print(f"  Total rows: {len(combined):,}")
    print(f"  Total states: {combined['State'].nunique()}")
    print(f"  Total districts: {combined['District'].nunique()}")
    print(f"  Total competencies: {combined['Competency_Code'].nunique()}")
    print(f"\nStates included:")
    for state in sorted(combined['State'].unique()):
        count = len(combined[combined['State'] == state])
        districts = combined[combined['State'] == state]['District'].nunique()
        print(f"  {state}: {districts} districts, {count:,} rows")
    print(f"{'='*60}")

if __name__ == "__main__":
    combine_csvs()
