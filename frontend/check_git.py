import subprocess

try:
    # Check if there is any git ref
    res = subprocess.run(["git", "log", "-n", "1"], capture_output=True, text=True, cwd="c:\\Users\\saura\\ParseOps\\frontend")
    print("Git log output:")
    print(res.stdout)
    print(res.stderr)
    
    # Check git status
    res_status = subprocess.run(["git", "status"], capture_output=True, text=True, cwd="c:\\Users\\saura\\ParseOps\\frontend")
    print("Git status output:")
    print(res_status.stdout)
except Exception as e:
    print(f"Error running git: {e}")
