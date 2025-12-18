import json

with open('/Users/avra/paragh/all_results.json', 'r') as f:
    data = json.load(f)

# Check chart titles for competency descriptions
for result in data:
    if result['state'] == 'Rajasthan' and result['stage'] == 'Middle Stage':
        print(f"Found: {result['state']} - {result['stage']}")
        for chart in result.get('charts', []):
            title = chart.get('title', '')
            if title.startswith('C-'):
                print(f'Title: {title[:80]}')
        break
