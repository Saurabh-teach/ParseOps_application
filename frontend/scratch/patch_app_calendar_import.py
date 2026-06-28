import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the specific import line to inject WorkspaceCalendar
target = "import React, { useState, useEffect, useRef } from 'react';"
replacement = "import React, { useState, useEffect, useRef } from 'react';\nimport WorkspaceCalendar from './components/CalendarView';"

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx patched to import WorkspaceCalendar")
