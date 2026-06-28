"""Count braces in App.jsx to find the mismatch."""
path = r'c:\Users\saura\ParseOps\frontend\src\App.jsx'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

opens = 0
closes = 0
for i, line in enumerate(lines, 1):
    opens += line.count('{')
    closes += line.count('}')

print(f"Total opens: {opens}, Total closes: {closes}, Diff: {opens - closes}")

# Find where braces go negative or show large imbalance
depth = 0
for i, line in enumerate(lines, 1):
    depth += line.count('{') - line.count('}')
    if depth < 0:
        print(f"  Brace depth went NEGATIVE at line {i}: depth={depth}")
        print(f"    Content: {line.rstrip()}")
        break

# Also look for duplicate useState declarations that shouldn't be there
dupes_to_check = [
    'pendingExtensionCount',
    'isExtensionRequestsModalOpen', 
    'isScheduleModalOpen',
    'comments, setComments',
    'newCommentText',
    'feedbackModalConfig',
    'submissionModalConfig',
    'submissionForm',
    'submissionFile',
    'extensionModalConfig',
]
for dupe in dupes_to_check:
    occurrences = []
    for i, line in enumerate(lines, 1):
        if dupe in line and 'useState' in line:
            occurrences.append(i)
    if len(occurrences) > 1:
        print(f"  DUPLICATE useState for '{dupe}' at lines: {occurrences}")
