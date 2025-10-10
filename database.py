import psycopg2
import pandas as pd
import streamlit as st
import os

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
    
    def connect(self):
        try:
            # Try to get from Streamlit secrets first, then environment variables
            db_config = {
                'host': st.secrets.get('DB_HOST', os.getenv('DB_HOST', 'localhost')),
                'database': st.secrets.get('DB_NAME', os.getenv('DB_NAME', 'mnch_training_tracker')),
                'user': st.secrets.get('DB_USER', os.getenv('DB_USER', 'postgres')),
                'password': st.secrets.get('DB_PASSWORD', os.getenv('DB_PASSWORD', '')),
                'port': st.secrets.get('DB_PORT', os.getenv('DB_PORT', '5432'))
            }
            
            self.conn = psycopg2.connect(**db_config)
            return True
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            return False
    
    # ... rest of your database code remains the same
    
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host='localhost',
                database='mnch_training_tracker',
                user='postgres',
                password='MnchTraining2024!',
                port='5432'
            )
            return True
        except Exception as e:
            st.error(f"Database connection failed: {e}")
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
                    # For SELECT queries, return DataFrame
                    result = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    return pd.DataFrame(result, columns=columns)
                else:
                    # For INSERT...RETURNING, UPDATE, etc., return the raw result
                    result = cursor.fetchone()
                    return result
            else:
                self.conn.commit()
                return True
                
        except Exception as e:
            st.error(f"Query execution error: {e}")
            self.conn.rollback()  # Important: rollback on error
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def close(self):
        if self.conn:
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
        return result
    except Exception as e:
        st.error(f"Error getting trainings: {e}")
        return None

def get_participants(training_id):
    """Get participants for a specific training"""
    try:
        db = Database()
        query = """
        SELECT u.*, tp.attendance_status, tp.certificate_issued
        FROM training_participants tp
        JOIN users u ON tp.user_id = u.id
        WHERE tp.training_id = %s
        """
        return db.execute_query(query, (training_id,), fetch=True)
    except Exception as e:
        st.error(f"Error getting participants: {e}")
        return None

def add_training(title, training_type, start_date, end_date, venue, duration, description=None):
    """Add a new training to the database"""
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
        
        # Handle the result which is a tuple (id,) from RETURNING clause
        if result is not None and isinstance(result, tuple) and len(result) > 0:
            return result[0]  # Return the ID
        return False
        
    except Exception as e:
        st.error(f"Error adding training: {e}")
        return False

def get_users_by_role(role=None):
    """Get users by role"""
    try:
        db = Database()
        if role:
            query = "SELECT * FROM users WHERE role = %s ORDER BY full_name"
            return db.execute_query(query, (role,), fetch=True)
        else:
            query = "SELECT * FROM users ORDER BY full_name"
            return db.execute_query(query, fetch=True)
    except Exception as e:
        st.error(f"Error getting users by role: {e}")
        return None

def add_training_participant(training_id, user_id):
    """Add a participant to a training"""
    try:
        db = Database()
        query = """
        INSERT INTO training_participants (training_id, user_id)
        VALUES (%s, %s)
        ON CONFLICT (training_id, user_id) DO NOTHING
        """
        return db.execute_query(query, (training_id, user_id))
    except Exception as e:
        st.error(f"Error adding training participant: {e}")
        return False

def get_training_by_id(training_id):
    """Get a specific training by ID"""
    try:
        db = Database()
        query = """
        SELECT id, title, training_type, start_date, end_date, venue, duration, description, created_at
        FROM trainings 
        WHERE id = %s
        """
        result = db.execute_query(query, (training_id,), fetch=True)
        if result is not None and not result.empty:
            return result.iloc[0]
        return None
    except Exception as e:
        st.error(f"Error getting training by ID: {e}")
        return None

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
