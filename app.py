from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import sqlite3
import os
import re

app = Flask(__name__)

DB_FILE = "chat_history.db"

# Initialize DB
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

# Save message to DB
def save_message(role, message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO chat (role, message) VALUES (?, ?)", (role, message))
    conn.commit()
    conn.close()

# Fetch all messages
def get_all_messages():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role, message FROM chat")
    messages = c.fetchall()
    conn.close()
    return messages

# Clear all chat history
def delete_all_messages():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM chat")
    conn.commit()
    conn.close()

def get_ollama_response(prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "deepseek-r1:1.5b",
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        raw = response.json()["response"]
        clean = re.sub(r"<[^>]+>", "", raw).strip()
        return clean
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("prompt", "")
    save_message("user", user_input)
    bot_response = get_ollama_response(user_input)
    save_message("bot", bot_response)
    return jsonify({"response": bot_response})

@app.route("/history")
def history():
    messages = get_all_messages()
    return render_template("history.html", messages=messages)

@app.route("/clear")
def clear():
    delete_all_messages()
    return redirect(url_for("history"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
