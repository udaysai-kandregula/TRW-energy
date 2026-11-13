import json

with open('frontend_assets/extracted_data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

for k in ['metrics_cell_40', 'metrics_cell_41', 'metadata', 'importance_cell_44', 'importance_cell_45']:
    if k in d:
        print(f"=== {k} ===")
        print(d[k]['plain'])

