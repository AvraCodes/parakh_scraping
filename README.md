# PARAKH Data Scraping Project

## Successfully Working Code

### Main Scraper: `scrape_groups.py`
This is the script that successfully scraped all 28+ states from the PARAKH dashboard.

**Key features:**
- Uses Playwright to interact with Angular dashboard
- Finds custom AngularJS competency dropdowns
- Extracts Highcharts data for each competency
- Collects district-level performance scores
- Outputs JSON files with raw data

**Usage:**
```bash
python scrape_groups.py <group_number>
```

**Method:**
1. Navigates to PARAKH dashboard for each state and stage
2. Finds custom dropdown elements (`.custom-dropdown-list`)
3. Iterates through competency options
4. Extracts Highcharts series data with district names and scores
5. Saves to `group{X}_results.json`

### Data Conversion: `convert_group_to_csv.py`
Converts JSON results to properly formatted CSV files.

**Features:**
- Maps competency codes to subjects
- Adds state codes
- Sorts by State → District → Stage → Competency
- Outputs `group{X}_data.csv`

**Usage:**
```bash
python convert_group_to_csv.py <group_number>
```

### Combining Data: `combine_all_csvs.py`
Merges all group CSVs with existing data into one master file.

**Output:** `parakh_competency_data_all.csv`

### Batch Processing: `scrape_all_groups.sh`
Bash script that runs all 6 groups sequentially and combines them.

**Usage:**
```bash
bash scrape_all_groups.sh
```

## Final Data Files

### CSV Files (Keep These)
- `parakh_competency_data.csv` - Original 6 states (13,026 rows)
- `group1_data.csv` through `group6_data.csv` - New 28 states (53,609 rows)
- `parakh_competency_data_all.csv` - Combined all states

### JSON Files (Keep These)
- `all_results_complete.json` - Original scraped data for 6 states
- `group1_results.json` through `group6_results.json` - New scraped data

## CSV Format

```
State,State_Code,District,Stage,Subject,Competency_Code,Competency_Description,Score_Percent
```

**Sorting:** State → District → Stage (Foundational → Preparatory → Middle) → Competency Code

## Data Summary

**Original 6 states:** Andhra Pradesh, Chhattisgarh, Jammu & Kashmir, Jharkhand, Kerala, Rajasthan

**New 28 states in 6 groups:**
- Group 1: Himachal Pradesh, Punjab, Chandigarh, Uttarakhand, Haryana
- Group 2: NCT of Delhi, Uttar Pradesh, Bihar, Sikkim, Arunachal Pradesh  
- Group 3: Nagaland, Manipur, Mizoram, Tripura, Meghalaya
- Group 4: Assam, West Bengal, Odisha, Madhya Pradesh, Gujarat
- Group 5: Maharashtra, Karnataka, Goa, Lakshadweep, Tamil Nadu
- Group 6: Puducherry, Andaman & Nicobar, Telangana, Ladakh, Daman & Diu

**Total:** 34 states/UTs, 66,635 rows of competency data

## Archived Files

Experimental and non-working files moved to `archive/` folder.
