-- Utilise ta base
USE movies;

-- Films : ajoute poster_path + last_tmdb_sync (si non présents)
CREATE TABLE IF NOT EXISTS film (
  tmdb_id       INT                NOT NULL,
  title         VARCHAR(255)       NOT NULL,
  release_year  SMALLINT UNSIGNED  NULL,
  poster_path   VARCHAR(255)       NULL,      -- ex: /abc123.jpg (path TMDb)
  last_tmdb_sync DATETIME          NULL,
  PRIMARY KEY (tmdb_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Réalisateurs (une ligne par film/réalisateur)
CREATE TABLE IF NOT EXISTS directors (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  film_tmdb_id  INT           NOT NULL,
  name          VARCHAR(255)  NOT NULL,
  KEY idx_directors_film (film_tmdb_id),
  CONSTRAINT fk_directors_film
    FOREIGN KEY (film_tmdb_id) REFERENCES film (tmdb_id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Genres (ids TMDb)
CREATE TABLE IF NOT EXISTS genre (
  id    INT           NOT NULL,
  name  VARCHAR(100)  NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Jointure film <-> genre
CREATE TABLE IF NOT EXISTS film_genre (
  film_id   INT NOT NULL,
  genre_id  INT NOT NULL,
  PRIMARY KEY (film_id, genre_id),
  KEY idx_filmgenre_genre (genre_id),
  CONSTRAINT fk_filmgenre_film
    FOREIGN KEY (film_id) REFERENCES film (tmdb_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_filmgenre_genre
    FOREIGN KEY (genre_id) REFERENCES genre (id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Nettoyage (optionnel mais recommandé) : purger les vieux enregistrements "non-TMDb"
-- -> si tu avais des ids 101,102... issus d'anciens tests
DELETE FROM film WHERE tmdb_id < 1000;
