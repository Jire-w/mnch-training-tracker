import psycopg2
import pandas as pd
import streamlit as st
import os
import urllib.parse
from contextlib import contextmanager

class Database:
    def __init__(self):
        self.conn = None
    
    def get_connection_config(self):
        """Get database connection configuration for cloud deployment"""
        try:
            # Try Streamlit secrets first (for cloud deployment)
            if hasattr(st, 'secrets'):
                # Check for different secret formats
                if 'postgres' in st.secrets:
                    config = {
                        'host': st.secrets.postgres.get('host', ''),
                        'database': st.secrets.postgres.get('database', ''),
                        'user': st.secrets.postgres.get('user', ''),
                        'password': st.secrets.postgres.get('password', ''),
                        'port': st.secrets.postgres.get('port', 5432)
                    }
                    # Validate that we have the essential connection details
                    if config['host'] and config['database'] and config['user']:
                        st.success("✅ Using cloud database configuration")
                        return config
                
                # Check for DATABASE_URL (common in cloud platforms)
                elif 'DATABASE_URL' in st.secrets:
                    return self._parse_database_url(st.secrets.DATABASE_URL)
                
                # Check for individual environment variables
                else:
                    config = {
                        'host': st.secrets.get('DB_HOST', ''),
                        'database': st.secrets.get('DB_NAME', ''),
                        'user': st.secrets.get('DB_USER', ''),
                        'password': st.secrets.get('DB_PASSWORD', ''),
                        'port': st.secrets.get('DB_PORT', 5432)
                    }
                    if config['host'] and config['database'] and config['user']:
                        return config
            
            # Fallback to environment variables (for local development)
            config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'database': os.getenv('DB_NAME', 'mnch_training_tracker'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
                'port': int(os.getenv('DB_PORT', 5432))
            }
            
            # If we have a cloud database URL, use it
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                return self._parse_database_url(database_url)
                
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
            result = urllib.parse.urlparse(database_url)
            
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
        """Connect to database with detailed error reporting"""
        try:
            db_config = self.get_connection_config()
            if not db_config:
                st.error("""
                ❌ Database configuration not found!
                
                For local development, create a `.env` file with:
                ```
                DB_HOST=localhost
                DB_NAME=mnch_training_tracker
                DB_USER=postgres
                DB_PASSWORD=your_password
                DB_PORT=5432
                ```
                
                For cloud deployment, add your database credentials to Streamlit Cloud secrets.
                """)
                return False
            
            # Test connection
            self.conn = psycopg2.connect(**db_config)
            st.success("✅ Connected to database successfully!")
            return True
            
        except psycopg2.OperationalError as e:
            st.error(f"❌ Database connection failed: {e}")
            st.info("""
            **To fix this:**
            
            1. **For Cloud Deployment:**
               - Set up a cloud database (Supabase, ElephantSQL, or Render)
               - Add your database credentials to Streamlit Cloud secrets
               
            2. **For Local Development:**
               - Make sure PostgreSQL is running
               - Check your connection settings in the .env file
               
            **Recommended Cloud Databases (Free Tier):**
            - Supabase (https://supabase.com)
            - ElephantSQL (https://elephantsql.com)
            - Render (https://render.com)
            """)
            return False
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            return False
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute query with error handling"""
        try:
            if self.conn is None or self.conn.closed:
                if not self.connect():
                    return None
            
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())
            
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
            if self.conn:
                self.conn.rollback()
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

# Utility functions with better error handling
def get_trainings():
    """Get all trainings from the database"""
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
    """Get users by role"""
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
        st.error(f"Error getting users by role: {e}")
        return pd.DataFrame()

def add_training(title, training_type, start_date, end_date, venue, duration, description=None):
    """Add a new training to the database"""
    try:
        db = Database()
        
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
            return result[0]
        return False
        
    except Exception as e:
        st.error(f"Error adding training: {e}")
        return False

def update_user(user_id, update_data):
    """Update user information"""
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
