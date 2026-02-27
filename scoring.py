def update_scores(connection, user_id, title_id, liked):
    delta = 1 if liked else -0.5
    cursor = connection.cursor()

    # Record watch
    cursor.execute("""
        INSERT INTO UserWatchHistory (user_id, title_id, liked)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE liked = VALUES(liked)
    """, (user_id, title_id, liked))

    # Get actors
    cursor.execute("""
        SELECT actor_id FROM TitleActors WHERE title_id = %s
    """, (title_id,))
    actors = cursor.fetchall()

    for (actor_id,) in actors:
        cursor.execute("""
            INSERT INTO UserActorScores (user_id, actor_id, score)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE score = score + %s
        """, (user_id, actor_id, delta, delta))

    connection.commit()