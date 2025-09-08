import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Ademolili0806!",
    database="movies"
)
cursor = conn.cursor()

# Lire le fichier schema.sql
with open("src/etl/schema.sql", "r", encoding="utf-8") as f:
    sql_script = f.read()

# Exécuter chaque commande séparément
for statement in sql_script.split(";"):
    if statement.strip():
        cursor.execute(statement)

conn.commit()
cursor.close()
conn.close()
print("Base de données initialisée !")
