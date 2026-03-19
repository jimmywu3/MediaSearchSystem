from flask import Flask, jsonify, send_from_directory, request
import mysql.connector
import os
from dotenv import load_dotenv
import random
import time
from datetime import datetime
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from recomendation import get_recommended_movies

load_dotenv()

# Cache for highly-rated movies
cached_high_rated_movies = []
cache_timestamp = 0
CACHE_DURATION = 300  # Refresh cache every 5 minutes
RATING_THRESHOLD = 7.5  # Movies with rating >= 7.5 are considered "highly-rated"

API_KEY = os.getenv("TMDB_API_KEY")
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME")
}

def get_current_hour():
    """
    Returns the current hour, or a debug override if set via query parameter.
    Debug override is passed via query parameter: ?debug_hour=15
    """
    debug_hour = request.args.get('debug_hour')
    if debug_hour is not None:
        try:
            hour = int(debug_hour)
            if 0 <= hour <= 23:
                print(f"DEBUG: Using override hour {hour}")
                return hour
        except ValueError:
            pass
    return datetime.now().hour

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def refresh_high_rated_cache():
    """Fetch and cache all movies with rating >= RATING_THRESHOLD"""
    global cached_high_rated_movies, cache_timestamp
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT title_id, title, release_year, runtime, director, overview, avg_rating, poster_path
        FROM Titles
        WHERE avg_rating >= %s
        ORDER BY avg_rating DESC
    """, (RATING_THRESHOLD,))
    cached_high_rated_movies = cursor.fetchall()
    cursor.close()
    conn.close()
    cache_timestamp = time.time()

app = Flask(__name__, static_folder="../", static_url_path="")

@app.route("/api/recommended")
def recommended():
    """
    Recommends highly-rated movies based on genres the user watches within ±2 hours of current time.
    Falls back to all highly-rated movies if user hasn't watched anything in that time window.
    Returns: { movies: [...], genre_names: "...", current_hour: ... }
    """
    demo_user_name = "Main"
    
    # Get current hour (0-23) - check for debug override
    current_hour = get_current_hour()
    
    # Calculate hour range: ±2 hours with wrapping (e.g., 23, 0, 1, 2, 3 for hour 1)
    hour_range = 2
    hours_in_range = []
    for i in range(-hour_range, hour_range + 1):
        hours_in_range.append((current_hour + i) % 24)
    
    hours_str = ",".join(map(str, hours_in_range))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get user_id
    cursor.execute("SELECT user_id FROM Users WHERE user_name = %s LIMIT 1", (demo_user_name,))
    user_row = cursor.fetchone()
    if not user_row:
        cursor.close()
        conn.close()
        return jsonify({"movies": [], "genre_names": "", "current_hour": current_hour})
    user_id = user_row["user_id"]
    
    # Get genres from movies the user watched within ±2 hours of current_hour
    # Pick the genre that appears most frequently
    cursor.execute(f"""
        SELECT g.genre_id, g.genre_name, COUNT(*) as watch_count
        FROM User_Ratings ur
        JOIN Title_Genres tg ON ur.title_id = tg.title_id
        JOIN Genres g ON tg.genre_id = g.genre_id
        WHERE ur.user_id = %s
        AND HOUR(ur.time_watched) IN ({hours_str})
        GROUP BY g.genre_id, g.genre_name
        ORDER BY watch_count DESC
        LIMIT 1
    """, (user_id,))
    genre_row = cursor.fetchone()
    
    if genre_row:
        genre_ids = [genre_row["genre_id"]]
        genre_names = [genre_row["genre_name"]]
    else:
        genre_ids = []
        genre_names = []
    
    genre_names_str = ", ".join(genre_names) if genre_names else "No genre data"
    
    print(f"DEBUG /recommended: Current hour: {current_hour}, Hour range: {hours_in_range}, Most watched genre: {genre_names}")
    
    # If user has watched movies in this time range, recommend from those genres
    if genre_ids:
        genre_ids_str = ",".join(map(str, genre_ids))
        cursor.execute(f"""
            SELECT DISTINCT t.title_id, t.title, t.release_year, t.runtime, t.director, t.overview, t.avg_rating, t.poster_path
            FROM Titles t
            JOIN Title_Genres tg ON t.title_id = tg.title_id
            WHERE tg.genre_id IN ({genre_ids_str})
            AND t.avg_rating >= %s
            ORDER BY t.avg_rating DESC
        """, (RATING_THRESHOLD,))
        rows = cursor.fetchall()
        print(f"DEBUG /recommended: Found {len(rows)} movies in hour-based genres")
    else:
        # Fallback: recommend all highly-rated movies
        genre_names_str = "Popular"
        print(f"DEBUG /recommended: No watch history in hour range {hours_in_range}, using all highly-rated")
        cursor.execute("""
            SELECT title_id, title, release_year, runtime, director, overview, avg_rating, poster_path
            FROM Titles
            WHERE avg_rating >= %s
            ORDER BY avg_rating DESC
        """, (RATING_THRESHOLD,))
        rows = cursor.fetchall()
        print(f"DEBUG /recommended: Found {len(rows)} highly-rated movies")
    
    cursor.close()
    conn.close()
    
    if not rows:
        return jsonify({"movies": [], "genre_names": genre_names_str, "current_hour": current_hour})
    

    # Return up to 10 random movies so refresh shows different ones
    selected = random.sample(rows, min(10, len(rows)))
    print(f"DEBUG /recommended: Selected {len(selected)} movies: {[m['title'] for m in selected]}")
    return jsonify({"movies": selected, "genre_names": genre_names_str, "current_hour": current_hour})


@app.route("/api/recommended/scoring")
def recommended_by_scoring():
    """
    Personalized recommendations using a scoring engine based on:
    - User's top actors
    - User's top directors
    - User's top genres
    - Movie ratings
    Returns up to 10 random movies from the recommendation list.
    """
    demo_user_name = "Main"
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get user_id
    cursor.execute("SELECT user_id FROM Users WHERE user_name = %s LIMIT 1", (demo_user_name,))
    user_row = cursor.fetchone()
    cursor.close()
    
    if not user_row:
        conn.close()
        return jsonify([])
    
    user_id = user_row["user_id"]
    
    # Get personalized recommendations using the scoring engine
    results = get_recommended_movies(conn, user_id, limit=50)
    
    conn.close()
    
    if not results:
        print(f"DEBUG /recommended/scoring: No recommendations found for user {user_id}")
        return jsonify([])
    
    print(f"DEBUG /recommended/scoring: Found {len(results)} scored recommendations")
    print(f"DEBUG /recommended/scoring: Top recommendations: {[r['title'] for r in results[:3]]}")
    
    # Return up to 10 random from the scored list so refresh shows different ones
    selected = random.sample(results, min(10, len(results)))
    
    # Convert to JSON-serializable format (remove match_score to keep response clean)
    response = [
        {
            "title_id": r["title_id"],
            "title": r["title"],
            "release_year": r["release_year"],
            "runtime": r["runtime"],
            "director": r["director"],
            "overview": r["overview"],
            "avg_rating": r["avg_rating"],
            "poster_path": r["poster_path"],
        }
        for r in selected
    ]
    
    print(f"DEBUG /recommended/scoring: Selected {len(response)} movies: {[m['title'] for m in response]}")
    return jsonify(response)


@app.route("/api/recommended/genre")
def recommended_by_genre():
    """
    Pick a random movie from user's watch history and recommend movies 
    with the same primary genre.
    Returns: { movies: [...], genre_name: "...", movie_name: "..." }
    """
    demo_user_name = "Main"
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get user_id
    cursor.execute("SELECT user_id FROM Users WHERE user_name = %s LIMIT 1", (demo_user_name,))
    user_row = cursor.fetchone()
    if not user_row:
        cursor.close()
        conn.close()
        return jsonify({"movies": [], "genre_name": "", "movie_name": ""})
    user_id = user_row["user_id"]
    
    # Get a random movie from user's watch history
    cursor.execute("""
        SELECT title_id, title FROM User_Ratings
        JOIN Titles USING (title_id)
        WHERE user_id = %s
        ORDER BY RAND()
        LIMIT 1
    """, (user_id,))
    random_watch = cursor.fetchone()
    if not random_watch:
        cursor.close()
        conn.close()
        return jsonify({"movies": [], "genre_name": "", "movie_name": ""})
    random_title_id = random_watch["title_id"]
    movie_name = random_watch["title"]
    
    # Get the primary genre (first genre) of that movie
    cursor.execute("""
        SELECT genre_id, g.genre_name FROM Title_Genres
        JOIN Genres g USING (genre_id)
        WHERE title_id = %s
        LIMIT 1
    """, (random_title_id,))
    genre_row = cursor.fetchone()
    if not genre_row:
        cursor.close()
        conn.close()
        return jsonify({"movies": [], "genre_name": "", "movie_name": movie_name})
    genre_id = genre_row["genre_id"]
    genre_name = genre_row["genre_name"]
    
    # Recommend movies with that genre (excluding watched titles)
    cursor.execute("""
        SELECT DISTINCT t.title_id, t.title, t.release_year, t.runtime, t.director, t.overview, t.avg_rating, t.poster_path
        FROM Titles t
        JOIN Title_Genres tg ON t.title_id = tg.title_id
        WHERE tg.genre_id = %s
        AND t.title_id NOT IN (
            SELECT title_id FROM User_Ratings WHERE user_id = %s
        )
        ORDER BY t.avg_rating DESC
        LIMIT 10
    """, (genre_id, user_id))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({"movies": rows, "genre_name": genre_name, "movie_name": movie_name})


@app.route("/api/search")
def search_titles():
    query = (request.args.get("q") or "").strip()
    if len(query) < 2:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT title_id, title
        FROM Titles
        WHERE title LIKE %s
        ORDER BY title
        LIMIT 15
        """,
        (f"%{query}%",),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)


@app.route("/api/rate", methods=["POST"])
def rate_title():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    title_id = payload.get("title_id")
    rating = payload.get("rating")
    time_watched = (payload.get("time_watched") or "").strip()

    if not title and not title_id:
        return jsonify({"error": "Missing movie title"}), 400

    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid rating"}), 400

    # This example app uses a fixed demo user. Replace with real auth.
    demo_user_name = "Main"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM Users WHERE user_name = %s LIMIT 1", (demo_user_name,))
    user_row = cursor.fetchone()
    if user_row:
        user_id = user_row[0]
    else:
        cursor.execute(
            "INSERT INTO Users (user_name, email, password) VALUES (%s, %s, %s)",
            (demo_user_name, "main@test.com", "cs125"),
        )
        user_id = cursor.lastrowid

    if title_id:
        try:
            title_id = int(title_id)
        except (TypeError, ValueError):
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid title_id"}), 400

        cursor.execute("SELECT title_id FROM Titles WHERE title_id = %s LIMIT 1", (title_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({"error": "Movie not found"}), 404
    else:
        cursor.execute("SELECT title_id FROM Titles WHERE title = %s LIMIT 1", (title,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({"error": "Movie not found"}), 404
        title_id = row[0]

    if time_watched:
        # Store as TIME (hour:minute[:second])
        cursor.execute(
            """
            INSERT INTO User_Ratings (user_id, title_id, rating, time_watched)
            VALUES (%s, %s, %s, CAST(%s AS TIME))
            ON DUPLICATE KEY UPDATE rating = VALUES(rating), time_watched = VALUES(time_watched)
            """,
            (user_id, title_id, rating, time_watched),
        )
    else:
        cursor.execute(
            """
            INSERT INTO User_Ratings (user_id, title_id, rating)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE rating = VALUES(rating)
            """,
            (user_id, title_id, rating),
        )

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/history")
def watch_history():
    # In a real app this would be tied to the authenticated user.
    demo_user_name = "Main"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT user_id FROM Users WHERE user_name = %s LIMIT 1", (demo_user_name,))
    user_row = cursor.fetchone()
    if not user_row:
        # no history if user doesn't exist yet
        return jsonify([])
    user_id = user_row["user_id"]
    cursor.execute(
        """
        SELECT ur.title_id, t.title, ur.rating, TIME_FORMAT(ur.time_watched, '%H:%i') AS watched_at
        FROM User_Ratings ur
        JOIN Titles t ON ur.title_id = t.title_id
        WHERE ur.user_id = %s
        ORDER BY ur.time_watched DESC, ur.rated_at DESC
        LIMIT 100
        """,
        (user_id,),
    )
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
    app.run(host=host, port=5001, debug=debug)