import psycopg2
from psycopg2 import sql

# Connect to the default 'postgres' database
conn = psycopg2.connect(
    user="postgres",
    password="iyanupy0007",
    host="localhost",
    port="5432",
    dbname="postgres"   # connect to 'postgres', not an empty string
)

# Enable autocommit so CREATE DATABASE can run
conn.autocommit = True

print("Connection established!")

# Create a cursor to execute queries
cursor = conn.cursor()

# Use SQL module for safety
cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier("neoE_db")))

print("Database created successfully!")

# Close connection
cursor.close()
conn.close()

