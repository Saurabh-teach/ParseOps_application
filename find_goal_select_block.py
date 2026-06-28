with open('c:/Users/saura/ParseOps/extracted_src_-54c4904_jpFE.jsx.txt', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'updateOrgTask\(selectedOrg\.slug,\s*activeTask\.id,\s*\{\s*goal:', text)]
for idx, pos in enumerate(matches):
    print(f"Occurrence {idx+1} at char {pos}:")
    print(text[pos-100:pos+300].strip())
    print("-" * 40)
