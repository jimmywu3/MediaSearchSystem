def get_top_actors(connection, user_id):
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT a.actor_name, uas.score
        FROM UserActorScores uas
        JOIN Actors a ON a.actor_id = uas.actor_id
        WHERE uas.user_id = %s
        ORDER BY uas.score DESC
        LIMIT 3
    """, (user_id,))

    return cursor.fetchall()