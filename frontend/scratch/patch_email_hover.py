with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_str = """              {/* User email chip + role badge */}

              <div className="header-user-chip">

                <span className="header-user-email">{sessionStorage.getItem('email')}</span>

              </div>"""

new_str = """              {/* User email chip + role badge */}

              <div className="header-user-chip" title={sessionStorage.getItem('email')}>

                <span className="header-user-email">{sessionStorage.getItem('email')}</span>

              </div>"""

content = content.replace(old_str, new_str)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
