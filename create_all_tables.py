import psycopg2
import streamlit as st

def create_simple_tables():
    try:
        # Connect to your database
        conn = psycopg2.connect(
            host="localhost",
            database="mnch_training_tracker",
            user="postgres",
            password="password",
            port=5432
        )
        cursor = conn.cursor()
        
        # Create users table (simplified)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                role VARCHAR(20) DEFAULT 'user',
                full_name VARCHAR(100),
                first_name VARCHAR(50),
                fathers_name VARCHAR(50),
                grand_fathers_name VARCHAR(50),
                sex VARCHAR(10),
                phone_number VARCHAR(20),
                region VARCHAR(100),
                zone VARCHAR(100),
                woreda VARCHAR(100),
                facility VARCHAR(100),
                place_of_work_type VARCHAR(100),
                professional_background VARCHAR(100),
                training_type VARCHAR(10),
                training_start_date DATE,
                training_end_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create trainings table (simplified)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trainings (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                training_type VARCHAR(10),
                start_date DATE,
                end_date DATE,
                venue VARCHAR(100),
                duration VARCHAR(50),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create certificates table (simplified)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certificates (
                id SERIAL PRIMARY KEY,
                certificate_id VARCHAR(100) UNIQUE NOT NULL,
                user_id INTEGER REFERENCES users(id),
                training_id INTEGER REFERENCES trainings(id),
                issue_date DATE,
                training_venue VARCHAR(100),
                training_duration VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ All tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    create_simple_tables()
