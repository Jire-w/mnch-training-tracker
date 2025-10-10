import psycopg2
import pandas as pd
import streamlit as st
import os
import time
from contextlib import contextmanager

class Database:
    def __init__(self):
        self.conn = None
        # Don't connect immediately, connect when needed
    
    def get_connection_config(self):
        """Get database connection configuration from Streamlit secrets or environment variables"""
        try:
            # Try Streamlit secrets first (for cloud deployment)
            if hasattr(st, 'secrets'):
                # Check for different secret formats
                if 'postgres' in st.secrets:
                    # Format 1: Using [postgres] section
                    config = {
                        'host': st.secrets.postgres.get('host', 'localhost'),
                        'database': st.secrets.postgres.get('database', 'mnch_training_tracker'),
                        'user': st.secrets.postgres.get('user', 'postgres'),
                        'password': st.secrets.postgres.get('password', ''),
                        'port': st.secrets.postgres.get('port', 5432)
                    }
                elif 'DATABASE_URL' in st.secrets:
                    # Format 2: Using DATABASE_URL
                    config = self._parse_database_url(st.secrets.DATABASE_URL)
                else:
                    # Format 3: Individual secrets
                    config = {
                        'host': st.secrets.get('DB_HOST', 'localhost'),
                        'database': st.secrets.get('DB_NAME', 'mnch_training_tracker'),
                        'user': st.secrets.get('DB_USER', 'postgres'),
                        'password': st.secrets.get('DB_PASSWORD', ''),
                        'port': st.secrets.get('DB_PORT', 5432)
                    }
            else:
                # Local development - use environment variables
                config = {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'database': os.getenv('DB_NAME', 'mnch_training_tracker'),
                    'user': os.getenv('DB_USER', 'postgres'),
                    'password': os.getenv('DB_PASSWORD', ''),
                    'port': int(os.getenv('DB_PORT', 5432))
                }
            
            # Validate configuration
            if not all([config['host'], config['database'], config['user']]):
                st.error("Missing required database configuration")
                return None
                
            return config
            
        except Exception as e:
            st.error(f"Error getting database configuration: {e}")
            return None
    
    def _parse_database_url(self, database_url):
        """Parse DATABASE_URL format (common in cloud providers)"""
        try:
            # Handle both postgres:// and postgresql://
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
    
    def connect(self, max_retries=3, retry_delay=2):
        """Connect to database with retry logic"""
        for attempt in range(max_retries):
            try:
                db_config = self.get_connection_config()
                if not db_config:
                    st.error("Could not get database configuration")
                    return False
                
                self.conn = psycopg2.connect(**db_config)
                st.success("✅ Database connected successfully!")
                return True
                
            except psycopg2.OperationalError as e:
                if attempt < max_retries - 1:
                    st.warning(f"Connection attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    st.error(f"Database connection failed after {max_retries} attempts: {e}")
                    st.info("""
                    **Troubleshooting steps:**
                    1. Make sure PostgreSQL is running: `sudo service postgresql start` (Linux) or start PostgreSQL service (Windows)
                    2. Check if the database exists: `psql -U postgres -c "CREATE DATABASE mnch_training_tracker;"`
                    3. Verify your connection settings
                    4. Ensure PostgreSQL is accepting connections on port 5432
                    """)
                    return False
            except Exception as e:
                st.error(f"Unexpected connection error: {e}")
                return False
    
    def is_connected(self):
        """Check if connection is active"""
        try:
            if self.conn and not self.conn.closed:
                # Test connection with a simple query
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return True
            return False
        except:
            return False
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        if not self.is_connected():
            if not self.connect():
                raise Exception("Failed to connect to database")
        
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute query with proper error handling"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or ())
                
                if fetch:
                    if query.strip().upper().startswith('SELECT'):
                        # For SELECT queries, return DataFrame
                        columns = [desc[0] for desc in cursor.description]
                        data = cursor.fetchall()
                        if data:
                            return pd.DataFrame(data, columns=columns)
                        else:
                            return pd.DataFrame(columns=columns)
                    else:
                        # For other queries with RETURNING clause
                        result = cursor.fetchone()
                        return result
                else:
                    # For INSERT/UPDATE/DELETE without RETURNING
                    return True
                    
        except Exception as e:
            st.error(f"Query execution error: {e}")
            st.error(f"Query: {query}")
            st.error(f"Params: {params}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()

# Utility functions with better error handling
def get_trainings():
    try:
        db = Database()
        query = """
        SELECT id, title, training_type, start_date, end_date, venue, duration, description, created_at
        FROM trainings 
        ORDER BY start_date DESC
        """
        result = db.execute_query(query, fetch=True)
        return result if result is not None else pd.DataFrame()
    except Exception as e:
        st.error(f"Error getting trainings: {e}")
        return pd.DataFrame()

def get_users_by_role(role=None):
    try:
        db = Database()
        if role:
            query = "SELECT * FROM users WHERE role = %s ORDER BY full_name"
            result = db.execute_query(query, (role,), fetch=True)
        else:
            query = "SELECT * FROM users ORDER BY full_name"
            result = db.execute_query(query, fetch=True)
        return result if result is not None else pd.DataFrame()
    except Exception as e:
        st.error(f"Error getting users: {e}")
        return pd.DataFrame()

def add_training(title, training_type, start_date, end_date, venue, duration, description=None):
    try:
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
        
        if result and len(result) > 0:
            return result[0]  # Return the ID
        return False
    except Exception as e:
        st.error(f"Error adding training: {e}")
        return False

def update_user(user_id, update_data):
    try:
        db = Database()
        set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
        values = list(update_data.values())
        values.append(user_id)
        
        query = f"UPDATE users SET {set_clause} WHERE id = %s"
        return db.execute_query(query, values)
    except Exception as e:
        st.error(f"Error updating user: {e}")
        return False
