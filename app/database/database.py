import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

def connect():
    try:        
        connection=mysql.connector.connect(
            host = os.getenv("MYSQL_HOST"),
            port = int(os.getenv("MYSQL_PORT",3306)),
            user = os.getenv("MYSQL_USER"),
            password = os.getenv("MYSQL_PASSWORD"),
            database = os.getenv("MYSQL_DB")
        )
        
        if connection.is_connected():
            print("Successfully connected to MySQL database")
            return connection
        
    except Error as e:
        print("MySQL connection error:")
        raise e