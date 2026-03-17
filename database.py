import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="wellness_tracker",
        user="postgres",
        password="2006",
        port="5432"
    )