import sqlite3

def create_chat_history_db():
    # Connect to SQLite database (it will create the database file if it doesn't exist)
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()

    # Create the table if it doesn't exist (add the 'username' column)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,  
        user_message TEXT NOT NULL,
        bot_response TEXT NOT NULL,
        timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
    )
    ''')

    conn.commit()
    conn.close()
    print("Chat history database and table created/modified successfully.")

# Call the function to create the database and table
if __name__ == "__main__":
    create_chat_history_db()
