import re
import zlib

def simple_pdf_text(path):
    with open(path, 'rb') as f:
        data = f.read()

    text_parts = []
    # Find FlateDecode streams
    for match in re.finditer(b'stream[\r\n]+', data):
        start = match.end()
        end = data.find(b'endstream', start)
        if end == -1:
            continue
        raw_stream = data[start:end].rstrip(b'\r\n')
        try:
            decomp = zlib.decompress(raw_stream)
        except Exception:
            continue
        
        # Scan for string literals in decomp
        # Look for sequences like (Hello world) Tj or [(Hello) -10 (world)] TJ
        # Simple extraction: find all ASCII strings in parentheses
        in_paren = False
        current = []
        for b in decomp:
            if b == ord('(') and not in_paren:
                in_paren = True
                current = []
            elif b == ord(')') and in_paren:
                in_paren = False
                s = bytes(current).decode('latin1', errors='ignore')
                if len(s.strip()) > 1:
                    text_parts.append(s.strip())
            elif in_paren:
                current.append(b)
                if len(current) > 500: # prevent runaway
                    in_paren = False

    return '\n'.join(text_parts)

out_text = simple_pdf_text('Docs/Energy_Consumption_Prediction_Project_Report_Final.pdf')
with open('Docs/report_extracted_summary.txt', 'w', encoding='utf-8') as f:
    f.write(out_text[:100000])

print(f"Extracted {len(out_text)} characters.")
print("Preview:\n", out_text[:1500])

