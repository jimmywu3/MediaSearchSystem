from db import get_connection


def get_top_actors(connection, user_id):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.actor_name, uta.rank_position
        FROM UserTopActors uta
        JOIN Actors a ON a.actor_id = uta.actor_id
        WHERE uta.user_id = %s
        ORDER BY uta.rank_position
    """, (user_id,))
    return cursor.fetchall()


def get_top_directors(connection, user_id):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.director_name, utd.rank_position
        FROM UserTopDirectors utd
        JOIN Directors d ON d.director_id = utd.director_id
        WHERE utd.user_id = %s
        ORDER BY utd.rank_position
    """, (user_id,))
    return cursor.fetchall()


def get_top_genres(connection, user_id):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT g.genre_name, utg.rank_position
        FROM UserTopGenres utg
        JOIN Genres g ON g.genre_id = utg.genre_id
        WHERE utg.user_id = %s
        ORDER BY utg.rank_position
    """, (user_id,))
    return cursor.fetchall()


def get_top_titles(connection, user_id):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.title, utt.rank_position
        FROM UserTopTitles utt
        JOIN Titles t ON t.title_id = utt.title_id
        WHERE utt.user_id = %s
        ORDER BY utt.rank_position
    """, (user_id,))
    return cursor.fetchall()


def get_recommended_movies(connection, user_id, limit=12):
    """
    Scoring:
      - Actor match:    rank 1 = +6, rank 2 = +4, rank 3 = +2
      - Director match: rank 1 = +6, rank 2 = +4, rank 3 = +2
      - Genre match:    rank 1 = +3, rank 2 = +2, rank 3 = +1
      - TMDb avg_rating bonus: up to +2
    """
    cursor = connection.cursor(dictionary=True)

    actor_weights    = {r["actor_name"]:    4 - r["rank_position"] for r in get_top_actors(connection, user_id)}
    director_weights = {r["director_name"]: 4 - r["rank_position"] for r in get_top_directors(connection, user_id)}
    genre_weights    = {r["genre_name"]:    4 - r["rank_position"] for r in get_top_genres(connection, user_id)}

    cursor.execute("SELECT title_id FROM User_Ratings WHERE user_id = %s", (user_id,))
    watched_ids = {r["title_id"] for r in cursor.fetchall()}

    cursor.execute("""
        SELECT
            t.title_id,
            t.title,
            t.release_year,
            t.runtime,
            t.director,
            t.type,
            t.overview,
            t.avg_rating,
            t.poster_path,
            GROUP_CONCAT(DISTINCT a.actor_name SEPARATOR '|') AS actors,
            GROUP_CONCAT(DISTINCT g.genre_name SEPARATOR '|') AS genres
        FROM Titles t
        LEFT JOIN Title_Actors ta ON ta.title_id = t.title_id
        LEFT JOIN Actors a ON a.actor_id = ta.actor_id
        LEFT JOIN Title_Genres tg ON tg.title_id = t.title_id
        LEFT JOIN Genres g ON g.genre_id = tg.genre_id
        GROUP BY t.title_id
    """)
    candidates = cursor.fetchall()
    cursor.close()

    results = []
    for title in candidates:
        if title["title_id"] in watched_ids:
            continue

        score = 0.0

        actors = title["actors"].split("|") if title["actors"] else []
        for actor in actors:
            score += actor_weights.get(actor.strip(), 0) * 2

        if title["director"]:
            score += director_weights.get(title["director"].strip(), 0) * 2

        genres = title["genres"].split("|") if title["genres"] else []
        for genre in genres:
            score += genre_weights.get(genre.strip(), 0)

        score += float(title["avg_rating"] or 0) / 5.0

        if score > 0:
            results.append({
                "title_id":     title["title_id"],
                "title":        title["title"],
                "release_year": title["release_year"],
                "runtime":      title["runtime"],
                "director":     title["director"],
                "type":         title["type"],
                "overview":     title["overview"],
                "avg_rating":   float(title["avg_rating"] or 0),
                "poster_path":  title["poster_path"],
                "genres":       genres,
                "match_score":  round(score, 2),
            })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:limit]