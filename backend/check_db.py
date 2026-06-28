import sqlite3
import uuid

conn = sqlite3.connect('c:/Users/saura/ParseOps/backend/db.sqlite3')
c = conn.cursor()

# Get the user id for the email
c.execute("SELECT id FROM user_table WHERE email='bhangalesaurabh20+mem505@gmail.com'")
row = c.fetchone()
if not row:
    print("User not found in DB")
else:
    user_id = row[0]
    # Check working schedule
    c.execute("SELECT work_start_time, work_end_time FROM user_working_schedule WHERE user_id=?", (user_id,))
    schedule = c.fetchone()
    if not schedule:
        print(f"Schedule missing for user_id {user_id}")
    else:
        print(f"Schedule found! Start: {schedule[0]}, End: {schedule[1]}")

conn.close()
