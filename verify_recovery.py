with open('c:/Users/saura/ParseOps/frontend/src/App_cleaned_no_empty.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Let's remove lines 522 to 530 (0-indexed: 521 to 529)
del lines[521:530]

# Now let's calculate the brace depth
opens = 0
closes = 0
negative_depth_line = -1
depth = 0

for i, line in enumerate(lines, 1):
    opens += line.count('{')
    closes += line.count('}')
    depth += line.count('{') - line.count('}')
    if depth < 0 and negative_depth_line == -1:
        negative_depth_line = i

print(f"After deletion: Opens: {opens}, Closes: {closes}, Diff: {opens - closes}")
if negative_depth_line != -1:
    print(f"First negative depth at line {negative_depth_line}: {lines[negative_depth_line-1].strip()}")
else:
    print("No negative depth found!")
