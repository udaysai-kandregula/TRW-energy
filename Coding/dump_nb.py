import json

with open('Coding/Final_TRW (1).ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

with open('Coding/extracted_cells.txt', 'w', encoding='utf-8') as out:
    for i, cell in enumerate(nb['cells']):
        c_type = cell.get('cell_type', '')
        source = ''.join(cell.get('source', []))
        out.write(f"=== Cell {i} [{c_type}] ===\n{source}\n\n")

print(f"Extracted {len(nb['cells'])} cells successfully.")

