"""
db_connector.py
This module provides functions to interact with the MySQL database.
It handles user creation, retrieval, updating, and deletion.
"""

import os
import sys
import pymysql
from pypika import Query, Table, Parameter
from datetime import datetime

# Database Configuration
# Username and password are NOT stored in code. They come from:
#   - command line arguments (sys.argv) - Jenkins / local / docker compose, or
#   - environment variables DB_USER / DB_PASSWORD - Kubernetes Secret 'db-secret'
# Host and port come from environment variables DB_HOST / DB_PORT
# (docker compose: DB_HOST=mysql, Kubernetes: ConfigMap 'db-config').
# Defaults = local MySQL.
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = "devops_db"
DB_USER = None
DB_PASSWORD = None

def set_credentials(user, password):
    """
    Sets the database username and password used by get_connection().
    """
    global DB_USER, DB_PASSWORD
    DB_USER = user
    DB_PASSWORD = password

def init_from_argv():
    """
    Sets the DB username and password.
    1. From the command line (sys.argv[1] and sys.argv[2]) if given.
    2. Otherwise from the environment variables DB_USER / DB_PASSWORD
       (in Kubernetes these are injected from the Secret 'db-secret').
    Exits with a usage message if neither is available.
    """
    if len(sys.argv) >= 3:
        set_credentials(sys.argv[1], sys.argv[2])
    elif os.getenv("DB_USER") and os.getenv("DB_PASSWORD"):
        set_credentials(os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))
    else:
        print(f"Usage: python {sys.argv[0]} <db_user> <db_password>\n"
              f"   or: set the environment variables DB_USER and DB_PASSWORD")
        sys.exit(1)

def get_connection():
    """
    Establishes and returns a connection to the MySQL database.
    """
    if DB_USER is None or DB_PASSWORD is None:
        raise RuntimeError("DB credentials not set. Call set_credentials() or init_from_argv() first.")
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def setup_database():
    """
    Creates the 'users' and 'config' tables if they do not exist.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Create users table with DATETIME (Extra 3)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT PRIMARY KEY,
                    user_name VARCHAR(50) NOT NULL,
                    creation_date DATETIME NOT NULL
                )
            ''')
            
            # Create config table (Extra 4)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    api_url VARCHAR(255) NOT NULL,
                    test_user_name VARCHAR(50) NOT NULL
                )
            ''')
            
            # Insert default config if table is empty
            cursor.execute("SELECT COUNT(*) as count FROM config")
            result = cursor.fetchone()
            if result['count'] == 0:
                cursor.execute('''
                    INSERT INTO config (api_url, test_user_name) 
                    VALUES ('http://127.0.0.1:5000/users', 'test_user')
                ''')
    finally:
        connection.close()

def insert_user(user_id, user_name):
    """
    Inserts a new user into the database using PyPika and prepared statements.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            users = Table('users')
            # Using PyPika to build the parameterized query (Extra 6 & Extra 2)
            query = Query.into(users).columns('user_id', 'user_name', 'creation_date').insert(Parameter('%s'), Parameter('%s'), Parameter('%s'))
            
            # Current datetime
            creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Executing prepared statement to prevent SQL injection
            cursor.execute(query.get_sql(quote_char=None), (user_id, user_name, creation_date))
    finally:
        connection.close()

def get_user(user_id):
    """
    Retrieves a user's name by their ID. Returns None if not found.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            users = Table('users')
            query = Query.from_(users).select('user_name').where(users.user_id == user_id)
            cursor.execute(query.get_sql(quote_char=None))
            result = cursor.fetchone()
            return result['user_name'] if result else None
    finally:
        connection.close()

def get_free_id():
    """
    Helper function to find an unused ID in case of collisions (Extra 5).
    Returns the max ID + 1.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT MAX(user_id) as max_id FROM users")
            result = cursor.fetchone()
            return (result['max_id'] or 0) + 1
    finally:
        connection.close()

def update_user(user_id, new_user_name):
    """
    Updates an existing user's name. Returns True if updated, False if user doesn't exist.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            users = Table('users')
            query = Query.update(users).set(users.user_name, Parameter('%s')).where(users.user_id == Parameter('%s'))
            affected_rows = cursor.execute(query.get_sql(quote_char=None), (new_user_name, user_id))
            return affected_rows > 0
    finally:
        connection.close()

def delete_user(user_id):
    """
    Deletes a user by ID. Returns True if deleted, False if user didn't exist.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            users = Table('users')
            query = Query.from_(users).delete().where(users.user_id == user_id)
            affected_rows = cursor.execute(query.get_sql(quote_char=None))
            return affected_rows > 0
    finally:
        connection.close()

def get_config():
    """
    Retrieves the testing configuration from the database.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            config = Table('config')
            query = Query.from_(config).select('*').limit(1)
            cursor.execute(query.get_sql(quote_char=None))
            return cursor.fetchone()
    finally:
        connection.close()

if __name__ == '__main__':
    init_from_argv()
    setup_database()
    print("Database tables initialized successfully.")
