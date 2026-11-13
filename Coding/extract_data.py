import json
import re

with open('Coding/Final_TRW (1).ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

project_data = {}

# Let's extract metadata, test metrics, validation metrics, feature importances, etc.
for i, cell in enumerate(nb['cells']):
    source = ''.join(cell.get('source', []))
    outputs = cell.get('outputs', [])
    for out in outputs:
        # Check stream outputs
        if out.get('output_type') == 'stream':
            text = ''.join(out.get('text', []))
            if 'SAVED MODEL FILES' in text:
                project_data['saved_models_info'] = text
            if 'Cleaned shape:' in text:
                project_data['cleaned_shape_info'] = text
            if 'Time interval counts:' in text:
                project_data['time_interval_info'] = text
        
        # Check text/plain or execute_result
        data = out.get('data', {})
        plain = ''.join(data.get('text/plain', []))
        html = ''.join(data.get('text/html', []))
        
        if 'Accuracy' in plain and 'Macro F1' in plain:
            project_data[f'metrics_cell_{i}'] = {
                'plain': plain,
                'html': html
            }
        if 'Global_active_power' in plain and 'Importance' in plain:
            project_data[f'importance_cell_{i}'] = {
                'plain': plain,
                'html': html
            }
        if 'setting' in plain and 'best_model' in plain:
            project_data['metadata'] = {
                'plain': plain,
                'html': html
            }

with open('frontend_assets/extracted_data.json', 'w', encoding='utf-8') as f:
    json.dump(project_data, f, indent=2)

print("Exported project_data keys:", list(project_data.keys()))
for k in project_data:
    if 'metrics' in k or 'metadata' in k or 'importance' in k:
        print(f"\n--- {k} ---")
        print(project_data[k].get('plain', '')[:400])

