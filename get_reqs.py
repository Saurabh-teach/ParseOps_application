import subprocess
import codecs

try:
    result = subprocess.run([r"d:\test_applications\myenv\Scripts\pip.exe", "freeze"], capture_output=True, text=True, encoding='utf-8')
    reqs = result.stdout
except Exception as e:
    reqs = str(e)

with codecs.open(r"d:\test_applications\backend\requirements.txt", "w", "utf-8") as f:
    f.write(reqs)

with codecs.open(r"d:\test_applications\frontend\requirements.txt", "w", "utf-8") as f:
    f.write(reqs)
