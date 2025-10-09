import psycopg2

def reset_database():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mnch_training_tracker',
            user='postgres',
            password='MnchTraining2024!',
            port='5432'
        )
        cursor = conn.cursor()
        
        print("Resetting database...")
        
        # Drop all tables in correct order (due to foreign key constraints)
        cursor.execute("DROP TABLE IF EXISTS certificates CASCADE")
        cursor.execute("DROP TABLE IF EXISTS training_participants CASCADE")
        cursor.execute("DROP TABLE IF EXISTS attendance CASCADE")
        cursor.execute("DROP TABLE IF EXISTS feedback CASCADE")
        cursor.execute("DROP TABLE IF EXISTS trainings CASCADE")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE")
        
        print("✅ All tables dropped successfully!")
        
        # Recreate tables
        print("Recreating tables...")
        
        # Users table
        cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'user')),
                full_name VARCHAR(100) NOT NULL,
                facility VARCHAR(100),
                region VARCHAR(50),
                woreda VARCHAR(50),
                contact_number VARCHAR(20),
                gender VARCHAR(10),
                first_name VARCHAR(100),
                fathers_name VARCHAR(100),
                grand_fathers_name VARCHAR(100),
                sex VARCHAR(10),
                zone VARCHAR(50),
                place_of_work_type VARCHAR(50),
                professional_background VARCHAR(100),
                training_start_date DATE,
                training_end_date DATE,
                phone_number VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trainings table
        cursor.execute("""
            CREATE TABLE trainings (
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
        
        # Training participants table
        cursor.execute("""
            CREATE TABLE training_participants (
                id SERIAL PRIMARY KEY,
                training_id INTEGER REFERENCES trainings(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                attendance_status VARCHAR(20) DEFAULT 'registered' CHECK (attendance_status IN ('registered', 'attended', 'absent')),
                certificate_issued BOOLEAN DEFAULT FALSE,
                certificate_id VARCHAR(100) UNIQUE,
                evaluation_score INTEGER,
                feedback TEXT,
                UNIQUE(training_id, user_id)
            )
        """)
        
        # Certificates table
        cursor.execute("""
            CREATE TABLE certificates (
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
        
        # Create admin user
        import hashlib
        hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, password, email, role, full_name, facility, region)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('admin', hashed_password, 'admin@mnch.gov', 'admin', 'System Administrator', 'MOH', 'National'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database reset successfully!")
        print("✅ All tables recreated!")
        print("✅ Admin user created:")
        print("   Username: admin")
        print("   Password: admin123")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")

if __name__ == "__main__":
    confirm = input("This will DELETE ALL DATA and recreate the database. Type 'YES' to continue: ")
    if confirm == 'YES':
        reset_database()
    else:
        print("Operation cancelled.")