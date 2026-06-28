with open('c:/Users/saura/ParseOps/extracted_src_-54c4904_jpFE.jsx.txt', 'r', encoding='utf-8') as f:
    text = f.read()

pos = 417909
start = max(0, pos - 500)
end = min(len(text), pos + 1000)
print(text[start:end].encode('ascii', 'ignore').decode('ascii'))
