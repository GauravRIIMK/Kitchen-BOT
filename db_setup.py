import sqlite3


# Connect to (or create) the database file
con = sqlite3.connect("kitchen_reports.db")
cur = con.cursor()

# Create the responsibilities table (kitchen -> user mapping)
cur.execute('''
    CREATE TABLE IF NOT EXISTS responsibilities (
        kitchen_name TEXT NOT NULL,
        slack_user_id TEXT NOT NULL,
        PRIMARY KEY (kitchen_name, slack_user_id)
    )
''')

# Create the submissions table
cur.execute('''
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        kitchen_name TEXT NOT NULL,
        image_url TEXT,
        report_text TEXT,
        submission_ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# --- PRE-POPULATE DATA (EXAMPLE) ---
# Add the people responsible for each kitchen here
# To get a user's Slack ID, click their profile -> More -> Copy member ID
responsibilities_data = [
    ('Main Canteen', 'U012ABCDEFG'),
    ('North Block', 'U034HIJKLMN'),
    ('West Wing Cafe', 'U012ABCDEFG'), # A user can be responsible for multiple kitchens
]

cur.executemany("INSERT OR IGNORE INTO responsibilities VALUES (?, ?)", responsibilities_data)

# Commit changes and close the connection
con.commit()
con.close()

print("Database initialized successfully.")


