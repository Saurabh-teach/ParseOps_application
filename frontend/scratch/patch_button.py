with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_button = '<button type="submit" className="btn-primary" style={{ width: \'auto\', padding: \'0.6rem 1.5rem\' }}>Create Task</button>'
new_button = '<button type="submit" disabled={loading} className="btn-primary" style={{ width: \'auto\', padding: \'0.6rem 1.5rem\' }}>{loading ? \'Creating...\' : \'Create Task\'}</button>'

content = content.replace(old_button, new_button)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
