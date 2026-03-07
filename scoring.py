from db import get_connection


def update_scores(connection, user_id, title_id, rating):
    """
    Called after a user rates a movie.
    - Records the rating in User_Ratings
    - Updates the user's top 3 actors, directors, genres, and titles
      based on their all-time average ratings.
    rating: float between 1.0 and 10.0
    """
    cursor = connection.cursor()

    # 1. Record the rating
    cursor.execute("""
        INSERT INTO User_Ratings (user_id, title_id, rating)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE rating = VALUES(rating), rated_at = CURRENT_TIMESTAMP
    """, (user_id, title_id, rating))

    # 2. Update top 3 actors
    cursor.execute("""
        SELECT a.actor_id, AVG(ur.rating) AS avg_score
        FROM User_Ratings ur
        JOIN Title_Actors ta ON ta.title_id = ur.title_id
        JOIN Actors a ON a.actor_id = ta.actor_id
        WHERE ur.user_id = %s
        GROUP BY a.actor_id
        ORDER BY avg_score DESC
        LIMIT 3
    """, (user_id,))
    top_actors = cursor.fetchall()

    cursor.execute("DELETE FROM UserTopActors WHERE user_id = %s", (user_id,))
    for rank, (actor_id, _) in enumerate(top_actors, start=1):
        cursor.execute("""
            INSERT INTO UserTopActors (user_id, actor_id, rank_position)
            VALUES (%s, %s, %s)
        """, (user_id, actor_id, rank))

    # 3. Update top 3 directors
    cursor.execute("""
        SELECT t.director, AVG(ur.rating) AS avg_score
        FROM User_Ratings ur
        JOIN Titles t ON t.title_id = ur.title_id
        WHERE ur.user_id = %s AND t.director IS NOT NULL
        GROUP BY t.director
        ORDER BY avg_score DESC
        LIMIT 3
    """, (user_id,))
    top_directors = cursor.fetchall()

    cursor.execute("DELETE FROM UserTopDirectors WHERE user_id = %s", (user_id,))
    for rank, (director_name, _) in enumerate(top_directors, start=1):
        cursor.execute("""
            INSERT INTO Directors (director_name)
            VALUES (%s)
            ON DUPLICATE KEY UPDATE director_id = LAST_INSERT_ID(director_id)
        """, (director_name,))
        director_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO UserTopDirectors (user_id, director_id, rank_position)
            VALUES (%s, %s, %s)
        """, (user_id, director_id, rank))

    # 4. Update top 3 genres
    cursor.execute("""
        SELECT g.genre_id, AVG(ur.rating) AS avg_score
        FROM User_Ratings ur
        JOIN Title_Genres tg ON tg.title_id = ur.title_id
        JOIN Genres g ON g.genre_id = tg.genre_id
        WHERE ur.user_id = %s
        GROUP BY g.genre_id
        ORDER BY avg_score DESC
        LIMIT 3
    """, (user_id,))
    top_genres = cursor.fetchall()

    cursor.execute("DELETE FROM UserTopGenres WHERE user_id = %s", (user_id,))
    for rank, (genre_id, _) in enumerate(top_genres, start=1):
        cursor.execute("""
            INSERT INTO UserTopGenres (user_id, genre_id, rank_position)
            VALUES (%s, %s, %s)
        """, (user_id, genre_id, rank))

    # 5. Update top 3 titles
    cursor.execute("""
        SELECT title_id, rating
        FROM User_Ratings
        WHERE user_id = %s
        ORDER BY rating DESC
        LIMIT 3
    """, (user_id,))
    top_titles = cursor.fetchall()

    cursor.execute("DELETE FROM UserTopTitles WHERE user_id = %s", (user_id,))
    for rank, (top_title_id, _) in enumerate(top_titles, start=1):
        cursor.execute("""
            INSERT INTO UserTopTitles (user_id, title_id, rank_position)
            VALUES (%s, %s, %s)
        """, (user_id, top_title_id, rank))

    connection.commit()
    cursor.close()