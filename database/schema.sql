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


-- 7. Users table
CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(255) UNIQUE NOT NULL,
    FULLTEXT(user_name)
);

-- 5. Directors table
CREATE TABLE IF NOT EXISTS Directors (
    director_id INT AUTO_INCREMENT PRIMARY KEY,
    director_name VARCHAR(255) UNIQUE NOT NULL,
    FULLTEXT(director_name)
);

-- 5. Junction User preference table
CREATE TABLE IF NOT EXISTS Actors (
    actor_id INT AUTO_INCREMENT PRIMARY KEY,
    actor_name VARCHAR(255) UNIQUE NOT NULL,
    FULLTEXT(actor_name)
);


