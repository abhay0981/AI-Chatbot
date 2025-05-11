from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from chatbot_logic import get_response  # Assuming this is where your chatbot logic resides

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Dummy users
users = {
    "admin": "admin123",
    "user1": "pass123"
}

# Connect to SQLite database and retrieve chat history for the logged-in user
def get_chat_history(username):
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()

    cursor.execute("SELECT user_message, bot_response, timestamp FROM chat_history WHERE username = ? ORDER BY timestamp DESC", (username,))
    rows = cursor.fetchall()

    conn.close()
    return [{"user_message": row[0], "bot_response": row[1], "timestamp": row[2]} for row in rows]

# Insert chat history into the database
def insert_chat_history(username, user_message, bot_response):
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()

    cursor.execute("INSERT INTO chat_history (username, user_message, bot_response) VALUES (?, ?, ?)",
                   (username, user_message, bot_response))

    conn.commit()
    conn.close()

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("chat"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username] == password:
            session["username"] = username
            session["context"] = None
            return redirect(url_for("chat"))
        else:
            error = "Invalid username or password"
    return render_template("login.html", error=error)

@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect(url_for("login"))

    # Get chat history for the logged-in user
    chat_history = get_chat_history(session["username"])

    return render_template("index.html", username=session["username"], chat_history=chat_history)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/get")
def get_bot_response():
    if "username" not in session:
        return "Session expired. Please log in again."

    user_text = request.args.get("msg")
    previous_context = session.get("context")

    response, new_context = get_response(user_text, previous_context)

    # Save user message and bot response to the database
    insert_chat_history(session["username"], user_text, response)

    session["context"] = new_context
    return response

if __name__ == "__main__":
    app.run(debug=True)
