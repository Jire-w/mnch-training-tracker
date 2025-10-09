import psycopg2

def create_certificates_table():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mnch_training_tracker',
            user='postgres',
            password='MnchTraining2024!',
            port='5432'
        )
        cursor = conn.cursor()
        
        print("Creating certificates table...")
        
        # Create certificates table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id SERIAL PRIMARY KEY,
                certificate_id VARCHAR(100) UNIQUE NOT NULL,
                training_id INTEGER REFERENCES trainings(id),
                user_id INTEGER REFERENCES users(id),
                issue_date DATE NOT NULL,
                expiry_date DATE,
                qr_code_data TEXT,
                file_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✅ Certificates table created/verified successfully!")
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating certificates table: {e}")

if __name__ == "__main__":
    create_certificates_table()