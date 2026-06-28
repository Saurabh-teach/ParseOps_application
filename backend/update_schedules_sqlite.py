import sqlite3

def main():
    conn = sqlite3.connect('c:/Users/saura/ParseOps/backend/db.sqlite3')
    c = conn.cursor()
    c.execute("UPDATE user_working_schedule SET work_end_time = '19:00:00' WHERE work_end_time = '18:00:00'")
    conn.commit()
    print(f"Updated {c.rowcount} rows")
    conn.close()

if __name__ == '__main__':
    main()
