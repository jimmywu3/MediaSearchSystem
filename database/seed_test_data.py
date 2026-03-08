import mysql.connector
import random
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME")
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def generate_random_time(hour_choices):
    # generates a random time string based on a list of specific hours
    hour = random.choice(hour_choices)
    minute = random.randint(0, 59)
    return f"{int(hour):02d}:{minute:02d}:00"

# Primary Test User Creation
def seed_primary_user(cursor):
    print("Creating Primary Test User ...")
    
    # Create the user
    cursor.execute("INSERT INTO Users (user_name, email, password) VALUES (%s, %s, %s)", 
                   ("Main", "main@test.com", "cs125"))
    primary_id = cursor.lastrowid

    # Horror Watcher (Late Night: 9 PM - 2 AM)
    cursor.execute("""
        SELECT t.title_id FROM Titles t 
        JOIN Title_Genres tg ON t.title_id = tg.title_id 
        JOIN Genres g ON tg.genre_id = g.genre_id 
        WHERE g.genre_name = 'Horror' LIMIT 7""")
    horror_ids = [row[0] for row in cursor.fetchall()]

    night_hours = [21, 22, 23, 0, 1]
    for m_id in horror_ids:
        watch_time = generate_random_time(night_hours)
        cursor.execute("""
            INSERT INTO User_Ratings (user_id, title_id, rating, time_watched) 
            VALUES (%s, %s, %s, CAST(%s AS TIME))""", (primary_id, m_id, random.uniform(8.0, 10.0), watch_time))

    # Variety of movies (15 movies, various genres, random times)
    cursor.execute("""
        SELECT t.title_id FROM Titles t 
        JOIN Title_Genres tg ON t.title_id = tg.title_id 
        JOIN Genres g ON tg.genre_id = g.genre_id 
        WHERE g.genre_name != 'Horror' LIMIT 15""")
    various_ids = [row[0] for row in cursor.fetchall()]

    day_hours = list(range(8, 20)) # 8 AM to 8 PM
    for m_id in various_ids:
        watch_time = generate_random_time(day_hours)
        cursor.execute("""
            INSERT INTO User_Ratings (user_id, title_id, rating, time_watched) 
            VALUES (%s, %s, %s, CAST(%s AS TIME))""", (primary_id, m_id, random.uniform(5.0, 8.5), watch_time))

    return primary_id, horror_ids, various_ids

# 10 Fake Users (with personas)
def seed_persona_users(cursor, shared_horror, shared_various):
    print("Creating 10 Persona Users...")

    all_main_watched = shared_horror + shared_various
    watched_ids_str = ", ".join(map(str, all_main_watched))
    
    # Standardized names to match the IF/ELIF logic below
    personas = [
        ("Horror_Fan", 3),    
        ("Action_Fan", 3),    
        ("Genre_Neutral", 2),  
        ("Outlier", 2)         
    ]

    for p_name, count in personas:
        for i in range(count):
            username = f"{p_name}_{i+1}"
            cursor.execute("INSERT INTO Users (user_name, email, password) VALUES (%s, %s, %s)", 
                           (username, f"{username}@test.com", "pass123"))
            u_id = cursor.lastrowid
            
            # TRACKER: Keep track of IDs this specific user has rated to avoid duplicates
            rated_titles = set()

            if p_name == "Horror_Fan":
                # Shares 5 of your horror picks with high ratings
                for m_id in random.sample(shared_horror, 5):
                    cursor.execute("INSERT INTO User_Ratings (user_id, title_id, rating) VALUES (%s, %s, %s)",
                                   (u_id, m_id, random.uniform(8.5, 10.0)))
                    rated_titles.add(m_id)
                    
                # 4 individual Horror likes (not in Primary User's list)
                cursor.execute("""
                    SELECT t.title_id FROM Titles t JOIN Title_Genres tg ON t.title_id = tg.title_id 
                    JOIN Genres g ON tg.genre_id = g.genre_id 
                    WHERE g.genre_name = 'Horror' AND t.title_id NOT IN (%s) LIMIT 4""" % watched_ids_str)
                for m_id in [r[0] for r in cursor.fetchall()]:
                    cursor.execute("INSERT INTO User_Ratings (user_id, title_id, rating) VALUES (%s, %s, %s)", (u_id, m_id, random.uniform(8.5, 10.0)))
                    rated_titles.add(m_id)
            
            elif p_name == "Action_Fan":
                # Shares 5 of your "various" picks
                for m_id in random.sample(shared_various, 5):
                    cursor.execute("INSERT INTO User_Ratings (user_id, title_id, rating) VALUES (%s, %s, %s)",
                                   (u_id, m_id, random.uniform(7.0, 9.0)))
                    rated_titles.add(m_id)
                    
                # 4 individual Action likes
                cursor.execute("""
                    SELECT t.title_id FROM Titles t JOIN Title_Genres tg ON t.title_id = tg.title_id 
                    JOIN Genres g ON tg.genre_id = g.genre_id 
                    WHERE g.genre_name = 'Action' AND t.title_id NOT IN (%s) LIMIT 4""" % watched_ids_str)
                for m_id in [r[0] for r in cursor.fetchall()]:
                    cursor.execute("INSERT INTO User_Ratings (user_id, title_id, rating) VALUES (%s, %s, %s)", (u_id, m_id, random.uniform(8.5, 10.0)))
                    rated_titles.add(m_id)
            
            elif p_name == "Genre_Neutral":
                # Shared (2 horror, 2 various)
                for m_id in (shared_horror[:2] + shared_various[:2]):
                    cursor.execute("INSERT INTO User_Ratings (user_id, title_id, rating) VALUES (%s, %s, %s)", (u_id, m_id, random.uniform(6.0, 8.0)))
                    rated_titles.add(m_id)
                # Individual (8 movies from any genre NOT watched by main user)
                cursor.execute(f"SELECT title_id FROM Titles WHERE title_id NOT IN ({watched_ids_str}) ORDER BY RAND() LIMIT 8")
                for m_id in [r[0] for r in cursor.fetchall()]:
                    cursor.execute("INSERT INTO User_Ratings (user_id, title_id, rating) VALUES (%s, %s, %s)", (u_id, m_id, random.uniform(5.0, 10.0)))
                    rated_titles.add(m_id)
            
            # Outliers: 10 random movies not in shared lists
            elif p_name == "Outlier":
                cursor.execute(f"SELECT title_id FROM Titles WHERE title_id NOT IN ({watched_ids_str}) ORDER BY RAND() LIMIT 10")
                for m_id in [r[0] for r in cursor.fetchall()]:
                    cursor.execute("INSERT INTO User_Ratings (user_id, title_id, rating) VALUES (%s, %s, %s)", (u_id, m_id, random.uniform(4.0, 10.0)))
                    rated_titles.add(m_id)

            # 3 random "filler" movies for everyone
            if rated_titles:
                exclude_str = ", ".join(map(str, rated_titles))
                cursor.execute(f"SELECT title_id FROM Titles WHERE title_id NOT IN ({exclude_str}) ORDER BY RAND() LIMIT 3")
                for m_id in [r[0] for r in cursor.fetchall()]:
                    cursor.execute("INSERT IGNORE INTO User_Ratings (user_id, title_id, rating) VALUES (%s, %s, %s)", (u_id, m_id, random.uniform(4.0, 7.0)))

# 4. Main Execution
def main():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create Primary User
        p_id, horror_list, various_list = seed_primary_user(cursor)
        
        # Create 10 Fake Persona Users
        seed_persona_users(cursor, horror_list, various_list)

        conn.commit()
        print("\nSuccess: All test users and ratings have been seeded.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()