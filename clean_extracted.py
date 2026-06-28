with open('c:/Users/saura/ParseOps/extracted_src_-54c4904_jpFE.jsx.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Clean up Chat Edit prefix and suffix
prefix = "Chat Edit: '"
if text.startswith(prefix):
    text = text[len(prefix):]

if text.endswith("'"):
    text = text[:-1]

# Save as App_recovered_actual.jsx
with open('c:/Users/saura/ParseOps/frontend/src/App_recovered_actual.jsx', 'w', encoding='utf-8') as out_f:
    out_f.write(text)

print("Saved cleaned file to App_recovered_actual.jsx")
