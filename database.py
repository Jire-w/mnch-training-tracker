import psycopg2
import pandas as pd
import streamlit as st
import os

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
    
    def get_connection_config(self):
        """Get database connection configuration from Streamlit secrets or environment variables"""
        try:
            # Try Streamlit secrets first (for cloud deployment)
            if hasattr(st, 'secrets'):
                # Check for different secret formats
                if 'postgres' in st.secrets:
                    # Format 1: Using [postgres] section
                    return {
                        'host': st.secrets.postgres.host,
                        'database': st.secrets.postgres.database,
                        'user': st.secrets.postgres.user,
                        'password': st.secrets.postgres.password,
                        'port': st.secrets.postgres.port
                    }
                elif 'DATABASE_URL' in st.secrets:
                    # Format 2: Using DATABASE_URL
                    return self._parse_database_url(st.secrets.DATABASE_URL)
                else:
                    # Format 3: Individual secrets
                    return {
                        'host': st.secrets.get('DB_HOST', 'localhost'),
                        'database': st.secrets.get('DB_NAME', 'mnch_training_tracker'),
                        'user': st.secrets.get('DB_USER', 'postgres'),
                        'password': st.secrets.get('DB_PASSWORD', ''),
                        'port': st.secrets.get('DB_PORT', '5432')
                    }
            else:
                # Local development - use environment variables
                return {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'database': os.getenv('DB_NAME', 'mnch_training_tracker'),
                    'user': os.getenv('DB_USER', 'postgres'),
                    'password': os.getenv('DB_PASSWORD', ''),
                    'port': os.getenv('DB_PORT', '5432')
                }
        except Exception as e:
            st.error(f"Error getting database configuration: {e}")
            return None
    
    def _parse_database_url(self, database_url):
        """Parse DATABASE_URL format (common in cloud providers)"""
        try:
            # Remove postgres:// prefix if present
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://')
            
            # Parse the URL
            from urllib.parse import urlparse
            result = urlparse(database_url)
            
            return {
                'host': result.hostname,
                'database': result.path[1:],  # Remove leading slash
                'user': result.username,
                'password': result.password,
                'port': result.port or 5432
            }
        except Exception as e:
            st.error(f"Error parsing DATABASE_URL: {e}")
            return None
    
    def connect(self):
        try:
            db_config = self.get_connection_config()
            if not db_config:
                st.error("Could not get database configuration")
                return False
            
            self.conn = psycopg2.connect(**db_config)
            return True
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            st.info("""
            **To fix this:**
            1. Set up a cloud database (ElephantSQL, Render, or Supabase)
            2. Add your database credentials to Streamlit Cloud secrets
            3. Run create_all_tables.py to create the database tables
            """)
            return False
    
    def execute_query(self, query, params=None, fetch=False):
        try:
            if self.conn is None or self.conn.closed:
                if not self.connect():
                    return None
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            
            if fetch:
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    return pd.DataFrame(result, columns=columns)
                else:
                    result = cursor.fetchone()
                    return result
            else:
                self.conn.commit()
                return True
                
        except Exception as e:
            st.error(f"Query execution error: {e}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def close(self):
        if self.conn:
            self.conn.close()

# Utility functions
def get_trainings():
    db = Database()
    query = """
    SELECT id, title, training_type, start_date, end_date, venue, duration, description, created_at
    FROM trainings 
    ORDER BY start_date DESC
    """
    return db.execute_query(query, fetch=True)

def get_users_by_role(role=None):
    db = Database()
    if role:
        query = "SELECT * FROM users WHERE role = %s ORDER BY full_name"
        return db.execute_query(query, (role,), fetch=True)
    else:
        query = "SELECT * FROM users ORDER BY full_name"
        return db.execute_query(query, fetch=True)

def add_training(title, training_type, start_date, end_date, venue, duration, description=None):
    db = Database()
    
    # Convert dates to string format for SQL
    start_date_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
    end_date_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
    
    query = """
        INSERT INTO trainings (title, training_type, start_date, end_date, venue, duration, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    
    result = db.execute_query(
        query, 
        (title, training_type, start_date_str, end_date_str, venue, duration, description),
        fetch=True
    )
    
    # Handle the result which is a tuple (id,) from RETURNING clause
    if result is not None and isinstance(result, tuple) and len(result) > 0:
        return result[0]  # Return the ID
    return False

def update_user(user_id, update_data):
    db = Database()
    set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
    values = list(update_data.values())
    values.append(user_id)
    
    query = f"UPDATE users SET {set_clause} WHERE id = %s"
    return db.execute_query(query, values)
