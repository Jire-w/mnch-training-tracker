import psycopg2
import hashlib

def setup_database():
    try:
        # First connect to default postgres database to create our database
        conn = psycopg2.connect(
            host='localhost',
            database='postgres',
            user='postgres',
            password='MnchTraining2024!',  # Your password here
            port='5432'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'mnch_training_tracker'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute('CREATE DATABASE mnch_training_tracker')
            print("Database 'mnch_training_tracker' created successfully!")
        else:
            print("Database 'mnch_training_tracker' already exists!")
        
        cursor.close()
        conn.close()
        
        # Now connect to our database and create tables
        conn = psycopg2.connect(
            host='localhost',
            database='mnch_training_tracker',
            user='postgres',
            password='MnchTraining2024!',  # Your password here
            port='5432'
        )
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'trainer', 'trainee', 'supervisor')),
                full_name VARCHAR(100) NOT NULL,
                facility VARCHAR(100),
                region VARCHAR(50),
                woreda VARCHAR(50),
                contact_number VARCHAR(20),
                gender VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create other tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trainings (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                training_type VARCHAR(50) NOT NULL CHECK (training_type IN ('EPI', 'Cold Chain', 'Data', 'Clinical', 'Community', 'Other')),
                objectives TEXT,
                description TEXT,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                venue VARCHAR(200),
                max_participants INTEGER,
                trainer_id INTEGER REFERENCES users(id),
                status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'ongoing', 'completed', 'cancelled')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create admin user if doesn't exist
        hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
        
        cursor.execute("SELECT 1 FROM users WHERE username = 'admin'")
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            cursor.execute("""
                INSERT INTO users (username, password, email, role, full_name, facility, region)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('admin', hashed_password, 'admin@mnch.gov', 'admin', 'System Administrator', 'MOH', 'National'))
            print("Admin user created: username='admin', password='admin123'")
        else:
            print("Admin user already exists")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Error during database setup: {e}")

if __name__ == "__main__":
    setup_database()