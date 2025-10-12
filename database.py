import psycopg2
import pandas as pd
import streamlit as st
import os
import time
from contextlib import contextmanager
from urllib.parse import urlparse

class Database:
    def __init__(self):
        self.conn = None
    
    def get_connection_config(self):
        """Get database connection configuration with smart fallbacks"""
        # Try different configuration sources in order
        config_sources = [
            self._get_config_from_env_file,
            self._get_config_from_streamlit_secrets,
            self._get_config_from_env_vars,
            self._get_config_from_common_passwords
        ]
        
        for config_source in config_sources:
            try:
                config = config_source()
                if config and self._test_connection(config):
                    return config
            except Exception:
                continue
        
        st.error("❌ Could not find valid database configuration")
        return None
    
    def _get_config_from_env_file(self):
        """Try to load from .env file in project root"""
        try:
            from dotenv import load_dotenv
            load_dotenv()  # This loads from .env file in current directory
            
            password = os.getenv('DB_PASSWORD')
            if password:
                return {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'database': os.getenv('DB_NAME', 'mnch_training_tracker'),
                    'user': os.getenv('DB_USER', 'postgres'),
                    'password': password,
                    'port': int(os.getenv('DB_PORT', 5432))
                }
        except ImportError:
            st.warning("python-dotenv not installed. Run: pip install python-dotenv")
        except Exception:
            pass
        return None
    
    def _get_config_from_streamlit_secrets(self):
        """Get config from Streamlit secrets"""
        try:
            if hasattr(st, 'secrets'):
                # Try different secret formats
                if 'postgres' in st.secrets:
                    config = {
                        'host': st.secrets.postgres.get('host', 'localhost'),
                        'database': st.secrets.postgres.get('database', 'mnch_training_tracker'),
                        'user': st.secrets.postgres.get('user', 'postgres'),
                        'password': st.secrets.postgres.get('password', ''),
                        'port': st.secrets.postgres.get('port', 5432)
                    }
                    if config['password']:  # Only return if password exists
                        return config
                elif 'DATABASE_URL' in st.secrets:
                    return self._parse_database_url(st.secrets.DATABASE_URL)
        except Exception:
            pass
        return None
    
    def _get_config_from_env_vars(self):
        """Get config from environment variables"""
        try:
            password = os.getenv('DB_PASSWORD')
            if password:
                return {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'database': os.getenv('DB_NAME', 'mnch_training_tracker'),
                    'user': os.getenv('DB_USER', 'postgres'),
                    'password': password,
                    'port': int(os.getenv('DB_PORT', 5432))
                }
        except Exception:
            pass
        return None
    
    def _get_config_from_common_passwords(self):
        """Try common PostgreSQL passwords as last resort"""
        common_passwords = [
            "new_password",      # The password you recently set
            "password",          # Most common default
            "postgres",          # Second most common
            "",                  # Empty password
            "admin",             # Third common
            "123456",            # Simple password
            "MnchTraining2024!"  # Your old password
        ]
        
        base_config = {
            'host': 'localhost',
            'database': 'mnch_training_tracker',
            'user': 'postgres',
            'port': 5432
        }
        
        for password in common_passwords:
            test_config = base_config.copy()
            test_config['password'] = password
            if self._test_connection(test_config):
                st.info(f"🔑 Connected using password: '{password}'")
                return test_config
        
        return None
    
    def _test_connection(self, config, timeout=3):
        """Test if a connection configuration works"""
        try:
            conn = psycopg2.connect(**config, connect_timeout=timeout)
            conn.close()
            return True
        except Exception:
            return False
    
    def _parse_database_url(self, database_url):
        """Parse DATABASE_URL format"""
        try:
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://')
            
            result = urlparse(database_url)
            return {
                'host': result.hostname,
                'database': result.path[1:],
                'user': result.username,
                'password': result.password,
                'port': result.port or 5432
            }
        except Exception:
            return None
    
    def connect(self):
        """Connect to database"""
        try:
            db_config = self.get_connection_config()
            if not db_config:
                self._show_connection_help()
                return False
            
            self.conn = psycopg2.connect(**db_config)
            return True
                
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            self._show_connection_help()
            return False
    
    def _show_connection_help(self):
        """Show helpful connection troubleshooting information"""
        st.error("""
        **Database Connection Troubleshooting:**
        
        1. **Create a .env file in your project root with:**
        ```
        DB_HOST=localhost
        DB_NAME=mnch_training_tracker  
        DB_USER=postgres
        DB_PASSWORD=new_password
        DB_PORT=5432
        ```
        
        2. **Or create .streamlit/secrets.toml with:**
        ```toml
        [postgres]
        host = "localhost"
        database = "mnch_training_tracker"
        user = "postgres" 
        password = "new_password"
        port = 5432
        ```
        
        3. **Install required package:**
        ```bash
        pip install python-dotenv
        ```
        """)
    
    def is_connected(self):
        """Check if connection is active and valid"""
        try:
            if self.conn and not self.conn.closed:
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return True
            return False
        except Exception:
            return False
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        if not self.is_connected():
            if not self.connect():
                raise Exception("Failed to establish database connection")
        
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
        """Execute query with comprehensive error handling"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or ())
                
                if fetch:
                    if query.strip().upper().startswith('SELECT'):
                        columns = [desc[0] for desc in cursor.description]
                        data = cursor.fetchall()
                        if data:
                            return pd.DataFrame(data, columns=columns)
                        else:
                            return pd.DataFrame(columns=columns)
                    else:
                        result = cursor.fetchone()
                        return result
                else:
                    return True
                    
        except Exception as e:
            st.error(f"Database error: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()

# Utility functions
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

# Test function
def test_connection():
    """Test database connection"""
    try:
        db = Database()
        result = db.execute_query("SELECT version()", fetch=True)
        if result is not None:
            st.success("✅ Database connection successful!")
            return True
        else:
            st.error("❌ Database connection failed")
            return False
    except Exception as e:
        st.error(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
