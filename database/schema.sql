-- 1. create the DB
CREATE DATABASE IF NOT EXISTS movie_search_system;
USE movie_search_system;

-- 2. Titles Table (the core movie/show data)
CREATE TABLE IF NOT EXISTS Titles (
    title_id INT PRIMARY KEY,         -- use TMDb ID as primary key
    title VARCHAR(255) NOT NULL,
    release_year INT,
    runtime INT,
    director VARCHAR(255),
    type ENUM('Movie', 'Series') DEFAULT 'Movie',
    overview TEXT,
    avg_rating DECIMAL(3, 1) DEFAULT 0.0,
    poster_path VARCHAR(255),
    -- full-text index to allow searching on title and description using words
    FULLTEXT(title, overview)
);

-- 3. Genres table
CREATE TABLE IF NOT EXISTS Genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name VARCHAR(100) UNIQUE NOT NULL
);

-- 4. Junction table: Titles and Genres
CREATE TABLE IF NOT EXISTS Title_Genres (
    title_id INT,
    genre_id INT,
    PRIMARY KEY (title_id, genre_id),
    FOREIGN KEY (title_id) REFERENCES Titles(title_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES Genres(genre_id) ON DELETE CASCADE
);

-- 5. Actors table
CREATE TABLE IF NOT EXISTS Actors (
    actor_id INT AUTO_INCREMENT PRIMARY KEY,
    actor_name VARCHAR(255) UNIQUE NOT NULL,
    FULLTEXT(actor_name)
);

-- 6. Junction table: Titles and Actors
CREATE TABLE IF NOT EXISTS Title_Actors (
    title_id INT,
    actor_id INT,
    PRIMARY KEY (title_id, actor_id),
    FOREIGN KEY (title_id) REFERENCES Titles(title_id) ON DELETE CASCADE,
    FOREIGN KEY (actor_id) REFERENCES Actors(actor_id) ON DELETE CASCADE
);


-- 7. User table 
CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 8. Directors table
CREATE TABLE IF NOT EXISTS Directors (
    director_id INT AUTO_INCREMENT PRIMARY KEY,
    director_name VARCHAR(255) UNIQUE NOT NULL,
    FULLTEXT(director_name)
);

-- 5. Junction Table: Titles and Directors
CREATE TABLE IF NOT EXISTS Title_Directors (
    title_id INT,
    director_id INT,
    PRIMARY KEY (title_id, director_id),
    FOREIGN KEY (title_id) REFERENCES Titles(title_id) ON DELETE CASCADE,
    FOREIGN KEY (director_id) REFERENCES Directors(director_id) ON DELETE CASCADE
);



-- 9. Movie Ratings for movies watched by users
CREATE TABLE IF NOT EXISTS User_Ratings (
    user_id INT,
    title_id INT,
    rating DECIMAL(3,1) NOT NULL CHECK (rating BETWEEN 1.0 AND 10.0), -- score of 1-10
    time_watched TIMESTAMP DEFAULT NULL, 
    rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, title_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (title_id) REFERENCES Titles(title_id) ON DELETE CASCADE
);


-- 10. Junction table: User's top 3 actors
CREATE TABLE IF NOT EXISTS UserTopActors (
    user_id INT NOT NULL,
    actor_id INT NOT NULL,
    rank_position TINYINT NOT NULL,

    PRIMARY KEY (user_id, rank_position),

    FOREIGN KEY (user_id)
        REFERENCES Users(user_id)
        ON DELETE CASCADE,

    FOREIGN KEY (actor_id)
        REFERENCES Actors(actor_id)
        ON DELETE CASCADE,

    UNIQUE (user_id, actor_id),

    CHECK (rank_position BETWEEN 1 AND 3)
);

-- 11. Junction table: User's top 3 directors
CREATE TABLE IF NOT EXISTS UserTopDirectors (
    user_id INT NOT NULL,
    director_id INT NOT NULL,
    rank_position TINYINT NOT NULL,

    PRIMARY KEY (user_id, rank_position),

    FOREIGN KEY (user_id)
        REFERENCES Users(user_id)
        ON DELETE CASCADE,

    FOREIGN KEY (director_id)
        REFERENCES Directors(director_id)
        ON DELETE CASCADE,

    UNIQUE (user_id, director_id),

    CHECK (rank_position BETWEEN 1 AND 3)
);
-- 12. Junction table: User's top 3 genres
CREATE TABLE IF NOT EXISTS UserTopGenres (
    user_id INT NOT NULL,
    genre_id INT NOT NULL,
    rank_position TINYINT NOT NULL,

    PRIMARY KEY (user_id, rank_position),

    FOREIGN KEY (user_id)
        REFERENCES Users(user_id)
        ON DELETE CASCADE,

    FOREIGN KEY (genre_id)
        REFERENCES Genres(genre_id)
        ON DELETE CASCADE,

    UNIQUE (user_id, genre_id),

    CHECK (rank_position BETWEEN 1 AND 3)
);

-- 13. Junction table: User's top 3 movies
CREATE TABLE IF NOT EXISTS UserTopTitles (
    user_id INT NOT NULL,
    title_id INT NOT NULL,
    rank_position TINYINT NOT NULL,

    PRIMARY KEY (user_id, rank_position),

    FOREIGN KEY (user_id)
        REFERENCES Users(user_id)
        ON DELETE CASCADE,

    FOREIGN KEY (title_id)
        REFERENCES Titles(title_id)
        ON DELETE CASCADE,

    UNIQUE (user_id, title_id),

    CHECK (rank_position BETWEEN 1 AND 3)
);




