with open(r"c:\Users\saura\ParseOps\frontend\src\App.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Delete lines 13292 to 13383 inclusive (0-indexed: 13291 to 13383)
del lines[13291:13383]

with open(r"c:\Users\saura\ParseOps\frontend\src\App.jsx", "w", encoding="utf-8") as f:
    f.writelines(lines)
print("Lines deleted successfully.")
