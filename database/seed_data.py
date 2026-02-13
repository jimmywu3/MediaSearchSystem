import mysql.connector
import requests
import time
import os
from dotenv import load_dotenv

# load credentials from .env file
load_dotenv()

# configuration
API_KEY = os.getenv("TMDB_API_KEY")
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME")
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def seed_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # get Genre List from TMDb
    genre_url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={API_KEY}"
    genres_data = requests.get(genre_url).json().get('genres', [])

    # insert genres into DB
    for g in genres_data:
        cursor.execute("INSERT IGNORE INTO Genres (genre_name) VALUES (%s)", (g['name'],))
    conn.commit()

    # fetch movies for the genres
    for genre in genres_data:
        print(f"Populating genre: {genre['name']}...")
        discover_url = f"https://api.themoviedb.org/3/discover/movie"
        params = {"api_key": API_KEY, "with_genres": genre['id'], "sort_by": "popularity.desc"}
        # 15 movies
        movies = requests.get(discover_url, params=params).json().get('results', [])[:15]

        for m in movies:
            # insert Title
            m_id = m['id']
            avg_rating = m.get('vote_average', 0.0)

            detail_url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={API_KEY}&append_to_response=credits"
            detail_data = requests.get(detail_url).json()

            # runtime 
            runtime = detail_data.get('runtime', 0)
            # credits to use for Director and Actors
            credits = requests.get(f"https://api.themoviedb.org/3/movie/{m_id}/credits?api_key={API_KEY}").json()
            
            director = next((mem['name'] for mem in credits.get('crew', []) if mem['job'] == 'Director'), "Unknown")
            
            sql_title = """INSERT IGNORE INTO Titles 
                           (title_id, title, release_year, runtime, director, overview, type, avg_rating) 
                           VALUES (%s, %s, %s, %s, %s, %s, 'Movie', %s)"""
            year = m.get('release_date', '0000')[:4]
            cursor.execute(sql_title, (
                m_id, m['title'], 
                year, runtime, 
                director, 
                m.get('overview', ''), 
                avg_rating
            ))

            # link Title to Genre
            cursor.execute("SELECT genre_id FROM Genres WHERE genre_name = %s", (genre['name'],))
            g_id = cursor.fetchone()[0]
            cursor.execute("INSERT IGNORE INTO Title_Genres (title_id, genre_id) VALUES (%s, %s)", (m_id, g_id))

            # Insert and Link Top 5 Actors
            for actor_name in [cast['name'] for cast in credits.get('cast', [])][:5]:
                # insert actor if they don't exist
                cursor.execute("INSERT IGNORE INTO Actors (actor_name) VALUES (%s)", (actor_name,))
                # get the actor_id
                cursor.execute("SELECT actor_id FROM Actors WHERE actor_name = %s", (actor_name,))
                a_id = cursor.fetchone()[0]
                # link to movie
                cursor.execute("INSERT IGNORE INTO Title_Actors (title_id, actor_id) VALUES (%s, %s)", (m_id, a_id))
            
            conn.commit()
            print(f"  - Saved: {m['title']}")
            time.sleep(0.1)

    cursor.close()
    conn.close()
    print("Database seeding complete!")

if __name__ == "__main__":
    seed_database()