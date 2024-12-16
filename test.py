import psycopg2

conn = psycopg2.connect(database="baza",
                        host="localhost",
                        user="postgres",
                        password="admin",
                        port="5432")

cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
print(cursor.fetchall())
