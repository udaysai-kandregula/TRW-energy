import json

with open('Coding/Final_TRW (1).ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("Inspecting outputs across cells...")
for i, cell in enumerate(nb['cells']):
    outputs = cell.get('outputs', [])
    if outputs:
        print(f"\n--- Cell {i} Outputs ({len(outputs)}) ---")
        for out in outputs:
            out_type = out.get('output_type')
            if out_type == 'stream':
                text = ''.join(out.get('text', []))
                print(f"[stream] {text[:300]}...")
            elif out_type in ('execute_result', 'display_data'):
                data = out.get('data', {})
                if 'text/plain' in data:
                    print(f"[{out_type} text] {''.join(data['text/plain'])[:300]}...")
                if 'text/html' in data:
                    print(f"[{out_type} html] length: {len(''.join(data['text/html']))}")
                if 'image/png' in data:
                    print(f"[{out_type} image/png] exists!")

