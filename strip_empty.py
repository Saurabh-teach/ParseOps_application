with open('c:/Users/saura/ParseOps/frontend/src/App_recovered_actual.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

non_empty_lines = [line for line in lines if line.strip() != '']

print(f"Total lines: {len(lines)}")
print(f"Non-empty lines: {len(non_empty_lines)}")

# Save to App_cleaned_no_empty.jsx
with open('c:/Users/saura/ParseOps/frontend/src/App_cleaned_no_empty.jsx', 'w', encoding='utf-8') as out_f:
    out_f.writelines(non_empty_lines)

print("Saved non-empty lines.")
