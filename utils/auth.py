import sqlite3
import bcrypt
import json
import secrets

DB_FILE = "users.db"

def log_event(event_type: str, email: str, details: str = ""):
    """Writes a security or system event to the logs table."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # SQLite automatically generates the current UTC timestamp
    c.execute('''
        INSERT INTO logs (event_type, user_email, details) 
        VALUES (?, ?, ?)
    ''', (event_type, email.lower(), details))
    conn.commit()
    conn.close()

def init_db():
    """Initializes the SQLite database and safely upgrades existing tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            portfolio TEXT,
            favourites TEXT
        )
    ''')
    
    # Create the new logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            user_email TEXT,
            details TEXT
        )
    ''')
    
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    if "reset_token" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
        
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(email: str, password: str, is_admin: bool = False) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('SELECT email FROM users WHERE email = ?', (email.lower(),))
    if c.fetchone():
        conn.close()
        log_event("REGISTER_FAILED", email, "Email already exists")
        return False
        
    hashed_pw = hash_password(password)
    empty_portfolio = json.dumps([])
    empty_favs = json.dumps(["AAPL", "BTC-USD", "GC=F"])
    
    c.execute('''
        INSERT INTO users (email, password, is_admin, portfolio, favourites, reset_token)
        VALUES (?, ?, ?, ?, ?, NULL)
    ''', (email.lower(), hashed_pw, 1 if is_admin else 0, empty_portfolio, empty_favs))
    
    conn.commit()
    conn.close()
    
    log_event("REGISTER_SUCCESS", email, "New user account created")
    return True

def authenticate_user(email: str, password: str) -> dict:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT email, password, is_admin FROM users WHERE email = ?', (email.lower(),))
    user = c.fetchone()
    conn.close()
    
    if user and verify_password(password, user[1]):
        log_event("LOGIN_SUCCESS", email)
        return {"email": user[0], "is_admin": bool(user[2])}
        
    log_event("LOGIN_FAILED", email, "Invalid credentials or user not found")
    return None

def get_user_data(email: str) -> dict:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT portfolio, favourites FROM users WHERE email = ?', (email.lower(),))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "portfolio": json.loads(row[0]) if row[0] else [],
            "favourites": json.loads(row[1]) if row[1] else []
        }
    return None

def update_user_data(email: str, portfolio: list, favourites: list):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE users 
        SET portfolio = ?, favourites = ? 
        WHERE email = ?
    ''', (json.dumps(portfolio), json.dumps(favourites), email.lower()))
    conn.commit()
    conn.close()

def generate_reset_token(email: str) -> str:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE email = ?', (email.lower(),))
    if not c.fetchone():
        conn.close()
        log_event("RECOVERY_FAILED", email, "Requested token for unknown email")
        return None
        
    token = secrets.token_hex(4)
    c.execute('UPDATE users SET reset_token = ? WHERE email = ?', (token, email.lower()))
    conn.commit()
    conn.close()
    
    log_event("RECOVERY_TOKEN_GENERATED", email)
    return token

def reset_password(email: str, token: str, new_password: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT reset_token FROM users WHERE email = ?', (email.lower(),))
    row = c.fetchone()
    
    if row and row[0] and row[0] == token.strip():
        hashed_pw = hash_password(new_password)
        c.execute('UPDATE users SET password = ?, reset_token = NULL WHERE email = ?', (hashed_pw, email.lower()))
        conn.commit()
        conn.close()
        log_event("PASSWORD_RESET_SUCCESS", email)
        return True
        
    conn.close()
    log_event("PASSWORD_RESET_FAILED", email, "Invalid or expired token submitted")
    return False