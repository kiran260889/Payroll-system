import psycopg2
import bcrypt
import configparser

# Load database config
config = configparser.ConfigParser()
config.read("config.ini")

def get_db_connection():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            dbname=config["database"]["dbname"],
            user=config["database"]["user"],
            password=config["database"]["password"],
            host=config["database"]["host"],
            port=config["database"]["port"]
        )
        print("Debug: Database connection successful")  # Debugging step
        return conn
    except Exception as e:
        print(f"Debug: Database connection failed: {e}")
        return None

def check_password(input_password, stored_hash):
    """Verify input password against stored hash"""
    try:
        is_valid = bcrypt.checkpw(input_password.encode(), stored_hash.encode())
        print(f"🔍 Debug: Password check result: {is_valid}")  # Debugging step
        return is_valid
    except Exception as e:
        print(f" Debug: Password check error: {e}")
        return False

def get_user_designation(user_id):
    """Retrieve the designation (role) of a user from the database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT designation FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return user[0] if user else None

def authenticate_user(user_id, password):
    """Authenticate user by User ID and password"""
    #print(f" Debug: Authenticating User ID {user_id}")  # Debugging step

    conn = get_db_connection()
    if conn is None:
        print("Debug: No database connection.")
        return None, None

    cur = conn.cursor()

    try:
        cur.execute("SELECT password_hash, designation FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()

        if user:
            #print(" Debug: User found in database")  # Debugging step
            stored_hash = user[0]
            if check_password(password, stored_hash):
             #   print("Debug: Password verified")  # Debugging step
                cur.close()
                conn.close()
                return user_id, user[1]  # Return user_id and designation
         

    except Exception as e:
        print(f"Debug: Error fetching user data: {e}")

    cur.close()
    conn.close()
    return None, None
