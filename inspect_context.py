with open('c:/Users/saura/ParseOps/frontend/src/App_recovered_actual.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

pos = 417909
start = pos - 200
end = pos + 400
print("Context:")
print(text[start:end].encode('ascii', 'ignore').decode('ascii'))
