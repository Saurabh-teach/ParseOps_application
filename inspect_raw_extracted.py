with open('c:/Users/saura/ParseOps/frontend/src/App_cleaned_no_empty.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Lines 3900 to 4100:")
for i in range(3899, min(len(lines), 4050)):
    print(f"Line {i+1}: {lines[i].rstrip()}")
