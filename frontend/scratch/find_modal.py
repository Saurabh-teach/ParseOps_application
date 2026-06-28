with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'className="modal' in l:
        print(''.join(lines[i-2:i+5]))
        break
