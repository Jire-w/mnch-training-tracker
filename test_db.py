import psycopg2
import streamlit as st

def test_connection():
    st.title("Database Connection Test")
    
    # Test different connection scenarios
    test_cases = [
        {
            "name": "Basic connection to default database",
            "config": {
                "host": "localhost",
                "database": "postgres",  # Try default postgres database first
                "user": "postgres",
                "password": "",  # Try empty password first
                "port": 5432
            }
        },
        {
            "name": "Connection to mnch_training_tracker",
            "config": {
                "host": "localhost",
                "database": "mnch_training_tracker",
                "user": "postgres",
                "password": "",
                "port": 5432
            }
        }
    ]
    
    for test in test_cases:
        st.write(f"### Testing: {test['name']}")
        try:
            conn = psycopg2.connect(**test['config'])
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            # List databases
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            databases = cursor.fetchall()
            
            st.success("✅ Connection successful!")
            st.write(f"PostgreSQL Version: {version[0]}")
            st.write("Available databases:")
            for db in databases:
                st.write(f"- {db[0]}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
