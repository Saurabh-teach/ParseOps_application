with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_button2 = '<button type="submit" className="btn-primary" style={{ width: \'auto\', padding: \'0.4rem 1.25rem\', fontSize: \'0.75rem\' }}>'
new_button2 = '<button type="submit" disabled={loading} className="btn-primary" style={{ width: \'auto\', padding: \'0.4rem 1.25rem\', fontSize: \'0.75rem\' }}>'

content = content.replace(old_button2, new_button2)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
