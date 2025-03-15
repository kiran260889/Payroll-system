import psycopg2
import bcrypt
import configparser

# Load database config
config = configparser.ConfigParser()
config.read("config.ini")

def get_db_connection():
    """Connect to PostgreSQL database"""
    try:
        return psycopg2.connect(
            dbname=config["database"]["dbname"],
            user=config["database"]["user"],
            password=config["database"]["password"],
            host=config["database"]["host"],
            port=config["database"]["port"]
        )
    except Exception:
        return None  # Return None if connection fails

def check_password(input_password, stored_hash):
    """Verify input password against stored hash"""
    try:
        return bcrypt.checkpw(input_password.encode(), stored_hash.encode())
    except Exception:
        return False  # Return False if password verification fails

def get_user_designation(user_id):
    """Retrieve the designation (role) of a user from the database"""
    conn = get_db_connection()
    if not conn:
        return None

    cur = conn.cursor()
    cur.execute("SELECT designation FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return user[0] if user else None

def authenticate_user(user_id, password):
    """Authenticate user by verifying User ID and password"""
    conn = get_db_connection()
    if not conn:
        return None, None

    cur = conn.cursor()

    try:
        cur.execute("SELECT password_hash, designation FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()

        if user:
            stored_hash, designation = user
            if check_password(password, stored_hash):  
                cur.close()
                conn.close()
                return user_id, designation  #  Return user_id if password is correct

    except Exception:
        pass  # Suppress errors for security reasons

    cur.close()
    conn.close()
    return None, None  # Return None if authentication fails
