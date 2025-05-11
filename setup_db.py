import sqlite3

# Connect to SQLite database (it will create the file if it doesn't exist)
conn = sqlite3.connect('chat_history.db')  # This will create a file named 'chat_history.db'
cursor = conn.cursor()

# Create a table for storing chat history
cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_message TEXT,
        bot_response TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Commit and close the connection
conn.commit()
conn.close()

print("Database and table created successfully.")
