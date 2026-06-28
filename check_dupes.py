with open('c:/Users/saura/ParseOps/frontend/src/App_recovered_actual.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

target = "const [activeTabState, setActiveTabState] = useState"
count = text.count(target)
print(f"Keyword '{target}' appears {count} times.")

# Let's find positions
pos = 0
for idx in range(count):
    pos = text.find(target, pos)
    print(f"  Occurrence {idx+1} at char position {pos}")
    pos += len(target)
