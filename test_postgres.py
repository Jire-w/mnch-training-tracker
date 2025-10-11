import psycopg2
import streamlit as st
import sys

def test_postgres_connection():
    st.title("PostgreSQL Connection Test")
    
    # Common password attempts (try these one by one)
    passwords_to_try = [
        "",  # Empty password
        "password", 
        "postgres",
        "admin",
        "123456"
    ]
    
    for password in passwords_to_try:
        st.write(f"### Trying password: '{password if password else 'empty'}'")
        
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password=password,
                port=5432,
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # List databases
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            databases = [db[0] for db in cursor.fetchall()]
            
            st.success("✅ CONNECTION SUCCESSFUL!")
            st.write(f"**PostgreSQL Version:** {version}")
            st.write(f"**Available Databases:** {databases}")
            
            # Check if our database exists
            if 'mnch_training_tracker' in databases:
                st.success("✅ mnch_training_tracker database exists!")
            else:
                st.warning("❌ mnch_training_tracker database doesn't exist yet")
            
            cursor.close()
            conn.close()
            break  # Stop if successful
            
        except psycopg2.OperationalError as e:
            st.error(f"Connection failed: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    test_postgres_connection()
