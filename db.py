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
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None  # Return None if connection fails

def check_password(input_password, stored_hash):
    """Verify input password against stored bcrypt hash"""
    if not input_password or not stored_hash:
        print("No password provided or stored hash is missing.")
        return False  # Prevent login if input password or stored hash is empty

    try:
        valid = bcrypt.checkpw(input_password.encode(), stored_hash.encode())  # Validate password
        if valid:
            print("Password verification successful.")
        else:
            print("Password does not match.")
        return valid
    except Exception as e:
        print(f"Password validation error: {e}")
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
        return None, None, None  # Return three values to match unpacking in CLI

    cur = conn.cursor()

    try:
        cur.execute("SELECT password_hash, designation, password_reset_required FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()

        if user:
            stored_hash, designation, password_reset_required = user
            if check_password(password, stored_hash):  
                cur.close()
                conn.close()
                return user_id, designation, password_reset_required  # Return user_id, role, and reset flag

    except Exception:
        pass  # Suppress errors for security reasons

    cur.close()
    conn.close()
    return None, None, None  # Ensure three values are returned
