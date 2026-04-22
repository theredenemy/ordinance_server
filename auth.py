from functools import wraps

from flask import make_response, request, current_app

from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import os
import secrets
db_file = None 
use_token = False
def get_db():
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn
def init_auth_db(db):
    global db_file
    db_file = db
    with sqlite3.connect(db) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
                        username PRIMARY KEY,
                        password TEXT
                     )
                     """)
        conn.execute("CREATE TABLE IF NOT EXISTS tokens (token TEXT PRIMARY KEY)")
        cursor = conn.cursor()
        cursor.execute('SELECT EXISTS (SELECT 1 FROM users LIMIT 1)')
        not_empty = cursor.fetchone()[0]

        if not not_empty:
            user = input("ENTER USERNAME : ")
            password = input("ENTER PASSWORD : ")
            edit_user(user, password)


def edit_user(username, password):
    db = get_db()
    db.execute("INSERT OR REPLACE INTO users (username, password) VALUES (?, ?)", (username, generate_password_hash(password)))
    db.commit()
def add_ord_key(key):
    db = get_db()
    db.execute("INSERT INTO tokens (token) VALUES (?)", (key,))
    db.commit()
def gen_ord_key():
    key = secrets.token_urlsafe(32)
    return key


def auth_required(f):
    global use_token
    @wraps(f)
    def logon(*args, **kwargs):
        global use_token
        auth = request.authorization
        db = get_db()
        if current_app.debug:
            return f(*args, **kwargs)
        key_header = request.headers.get('X-ORD-KEY')
        if auth and auth.username:
            user = db.execute('SELECT * FROM users WHERE username = ?', (auth.username,)).fetchone()
            if user and check_password_hash(user['password'], auth.password):
                use_token = False
                return f(*args, **kwargs)
            else:
                return make_response("<h1>TO USER YOU DO NOT HAVE PERMISSION TO VIEW THIS DATA PLEASE TRY AGAIN LATER</h1>", 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
        elif key_header:
            ord_key = db.execute('SELECT * FROM tokens WHERE token = ?', (key_header,)).fetchone()
            if ord_key:
               use_token = True
               return f(*args, **kwargs)
            else:
               return make_response("<h1>INVALID KEY</h1>", 401)  
        else:
            return make_response("<h1>TO USER YOU DO NOT HAVE PERMISSION TO VIEW THIS DATA PLEASE TRY AGAIN LATER</h1>", 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    return logon
            
            