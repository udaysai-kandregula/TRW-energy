import re
import zlib

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as f:
        content = f.read()
    
    # Find all streams
    streams = re.findall(b'stream[\r\n]+(.*?)[\r\n]+endstream', content, re.DOTALL)
    text_chunks = []
    
    for s in streams:
        try:
            decompressed = zlib.decompress(s)
        except Exception:
            decompressed = s
            
        # Look for BT ... ET text blocks or Tj / TJ operators
        # Extract strings inside parentheses ( ... ) Tj
        matches = re.findall(rb'\((.*?)\)\s*T[jJ]', decompressed)
        for m in matches:
            try:
                text_chunks.append(m.decode('latin1'))
            except Exception:
                pass
                
        # Also look for [ (str1) ... (str2) ] TJ
        array_matches = re.findall(rb'\[(.*?)\]\s*TJ', decompressed)
        for arr in array_matches:
            inner_strs = re.findall(rb'\((.*?)\)', arr)
            text_chunks.append(''.join(s.decode('latin1', errors='ignore') for s in inner_strs))
            
    return '\n'.join(text_chunks)

text = extract_text_from_pdf('Docs/Energy_Consumption_Prediction_Project_Report_Final.pdf')
print("Total extracted characters:", len(text))
with open('Docs/extracted_report_text.txt', 'w', encoding='utf-8') as out:
    out.write(text)

print("First 1000 characters:")
print(text[:1000])

