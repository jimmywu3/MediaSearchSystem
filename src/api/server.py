from flask import Flask, jsonify, send_from_directory
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME")
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

app = Flask(__name__, static_folder="../", static_url_path="")

@app.route("/api/recommended")
def recommended():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT title_id, title, release_year, runtime, director, overview, avg_rating
        FROM Titles
        ORDER BY RAND()
        LIMIT 10
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug)