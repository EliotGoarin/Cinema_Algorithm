-- ---------------------------------
-- Création de la base de test
-- ---------------------------------
DROP DATABASE IF EXISTS movies;
CREATE DATABASE movies;
USE movies;

-- ---------------------------------
-- Table des réalisateurs
-- ---------------------------------
DROP TABLE IF EXISTS directors;
CREATE TABLE directors (
    tmdb_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    film_tmdb_id INT -- pour lier au film si besoin
);

-- Insérer 10 réalisateurs
INSERT INTO directors (tmdb_id, name, film_tmdb_id) VALUES
(1, 'Christopher Nolan', 101),
(2, 'Quentin Tarantino', 102),
(3, 'Steven Spielberg', 103),
(4, 'James Cameron', 104),
(5, 'Martin Scorsese', 105),
(6, 'Ridley Scott', 106),
(7, 'Peter Jackson', 107),
(8, 'Clint Eastwood', 108),
(9, 'Tim Burton', 109);

-- ---------------------------------
-- Table des films
-- ---------------------------------
DROP TABLE IF EXISTS film;
CREATE TABLE film (
    tmdb_id INT PRIMARY KEY,
    title VARCHAR(300),
    director_id INT,
    FOREIGN KEY (director_id) REFERENCES directors(tmdb_id)
);

-- Insérer 10 films correspondant aux réalisateurs
INSERT INTO film (tmdb_id, title, director_id) VALUES
(101, 'Inception', 1),
(102, 'Pulp Fiction', 2),
(103, 'Jurassic Park', 3),
(104, 'Avatar', 4),
(105, 'The Irishman', 5),
(106, 'Gladiator', 6),
(107, 'The Lord of the Rings', 7),
(108, 'Gran Torino', 8),
(109, 'Edward Scissorhands', 9),
(110, 'Oppenheimer', 1);

-- ---------------------------------
-- Vérification
-- ---------------------------------
SELECT * FROM directors;
SELECT * FROM film;
