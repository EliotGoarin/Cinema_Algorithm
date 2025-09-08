CREATE TABLE director (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tmdb_id INT UNIQUE,
  name VARCHAR(255) NOT NULL
);

CREATE TABLE actor (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tmdb_id INT UNIQUE,
  name VARCHAR(255) NOT NULL
);

CREATE TABLE genre (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tmdb_id INT UNIQUE,
  name VARCHAR(100) NOT NULL
);

CREATE TABLE film (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tmdb_id INT UNIQUE,
  title VARCHAR(300),
  year INT,
  decade VARCHAR(10),
  director_id INT,
  FOREIGN KEY (director_id) REFERENCES director(id)
);

CREATE TABLE film_actor (
  film_id INT,
  actor_id INT,
  cast_order INT,
  PRIMARY KEY (film_id, actor_id),
  FOREIGN KEY (film_id) REFERENCES film(id),
  FOREIGN KEY (actor_id) REFERENCES actor(id)
);

CREATE TABLE film_genre (
  film_id INT,
  genre_id INT,
  PRIMARY KEY (film_id, genre_id),
  FOREIGN KEY (film_id) REFERENCES film(id),
  FOREIGN KEY (genre_id) REFERENCES genre(id)
);

CREATE INDEX idx_film_title ON film(title);
