with open('c:/Users/saura/ParseOps/frontend/src/App_cleaned_no_empty.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove the duplicate/broken lines (0-indexed 521 to 530, which correspond to lines 522 to 531)
# Wait, let's check what lines we are deleting to be absolutely sure:
del_lines = lines[521:531]
print("Deleting lines:")
for l in del_lines:
    print(f"  {l.strip()}")

del lines[521:531]

# Strip trailing comments from the last lines
if lines[-1].strip() == '"develope this all"':
    print("Stripping trailing comment:", lines[-1].strip())
    lines.pop()

# Write to c:/Users/saura/ParseOps/frontend/src/App.jsx
with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as out_f:
    out_f.writelines(lines)

print("Saved to App.jsx")
