import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def create_tables():
    conn = None
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'postgres'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
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
        
        # Now connect to the specific database and create tables
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database='mnch_training_tracker',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        # Create users table (updated with additional fields for trainees)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'user')),
                full_name VARCHAR(100) NOT NULL,
                first_name VARCHAR(50),
                fathers_name VARCHAR(50),
                grand_fathers_name VARCHAR(50),
                sex VARCHAR(10),
                facility VARCHAR(100),
                region VARCHAR(50),
                zone VARCHAR(50),
                woreda VARCHAR(50),
                phone_number VARCHAR(20),
                place_of_work_type VARCHAR(50),
                professional_background VARCHAR(50),
                training_start_date DATE,
                training_end_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create trainings table WITHOUT the check constraint initially
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trainings (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                training_type VARCHAR(50) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                venue VARCHAR(255) NOT NULL,
                duration VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create training_participants table (junction table for many-to-many relationship)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_participants (
                id SERIAL PRIMARY KEY,
                training_id INTEGER REFERENCES trainings(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                attendance_status VARCHAR(20) DEFAULT 'registered' CHECK (attendance_status IN ('registered', 'attended', 'completed', 'absent')),
                certificate_issued BOOLEAN DEFAULT FALSE,
                registered_date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(training_id, user_id)
            )
        """)
        
        # Create certificates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id SERIAL PRIMARY KEY,
                certificate_id VARCHAR(100) UNIQUE NOT NULL,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                training_id INTEGER REFERENCES trainings(id) ON DELETE CASCADE,
                issue_date DATE NOT NULL,
                training_venue VARCHAR(255) NOT NULL,
                training_duration VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES users(id)
            )
        """)
        
        # Update existing tables if they have old schema
        update_existing_tables(cursor)
        
        # Fix any existing constraints
        fix_constraints(cursor)
        
        # Create indexes for better performance
        create_indexes(cursor)
        
        # Commit the changes
        conn.commit()
        print("All tables created/updated successfully!")
        
        # Create default admin user if doesn't exist
        create_default_admin(conn)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

def update_existing_tables(cursor):
    """Update existing tables to have the correct schema"""
    try:
        # Check and update trainings table
        cursor.execute("""
            DO $$ 
            BEGIN 
                -- Add duration column if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='trainings' AND column_name='duration') THEN
                    ALTER TABLE trainings ADD COLUMN duration VARCHAR(100);
                END IF;
                
                -- Add description column if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='trainings' AND column_name='description') THEN
                    ALTER TABLE trainings ADD COLUMN description TEXT;
                END IF;
                
                -- Add venue column if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='trainings' AND column_name='venue') THEN
                    ALTER TABLE trainings ADD COLUMN venue VARCHAR(255);
                END IF;
                
            END $$;
        """)
        
        # Check and update users table with additional trainee fields
        cursor.execute("""
            DO $$ 
            BEGIN 
                -- Add trainee-specific columns if they don't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='users' AND column_name='first_name') THEN
                    ALTER TABLE users ADD COLUMN first_name VARCHAR(50);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='users' AND column_name='fathers_name') THEN
                    ALTER TABLE users ADD COLUMN fathers_name VARCHAR(50);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='users' AND column_name='grand_fathers_name') THEN
                    ALTER TABLE users ADD COLUMN grand_fathers_name VARCHAR(50);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='users' AND column_name='sex') THEN
                    ALTER TABLE users ADD COLUMN sex VARCHAR(10);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='users' AND column_name='zone') THEN
                    ALTER TABLE users ADD COLUMN zone VARCHAR(50);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='users' AND column_name='phone_number') THEN
                    ALTER TABLE users ADD COLUMN phone_number VARCHAR(20);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='users' AND column_name='place_of_work_type') THEN
                    ALTER TABLE users ADD COLUMN place_of_work_type VARCHAR(50);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='users' AND column_name='professional_background') THEN
                    ALTER TABLE users ADD COLUMN professional_background VARCHAR(50);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='users' AND column_name='training_start_date') THEN
                    ALTER TABLE users ADD COLUMN training_start_date DATE;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='users' AND column_name='training_end_date') THEN
                    ALTER TABLE users ADD COLUMN training_end_date DATE;
                END IF;
                
            END $$;
        """)
        
        print("Existing tables updated with missing columns!")
        
    except Exception as e:
        print(f"Error updating tables: {e}")

def fix_constraints(cursor):
    """Fix any problematic constraints on the trainings table"""
    try:
        # First, drop any existing check constraints on training_type
        cursor.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'trainings' 
            AND constraint_type = 'CHECK'
            AND constraint_name LIKE '%training_type%'
        """)
        
        constraints = cursor.fetchall()
        for constraint in constraints:
            constraint_name = constraint[0]
            cursor.execute(f"ALTER TABLE trainings DROP CONSTRAINT IF EXISTS {constraint_name}")
            print(f"Dropped constraint: {constraint_name}")
        
        # Now add a proper check constraint that allows A-K training types
        cursor.execute("""
            ALTER TABLE trainings 
            ADD CONSTRAINT trainings_training_type_check 
            CHECK (training_type IN ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K'))
        """)
        
        print("Training type constraint fixed successfully!")
        
    except Exception as e:
        print(f"Error fixing constraints: {e}")
        # If adding constraint fails, it's okay - we'll work without it
        print("Continuing without training_type constraint...")

def create_indexes(cursor):
    """Create indexes for better performance"""
    try:
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            "CREATE INDEX IF NOT EXISTS idx_users_region ON users(region)",
            "CREATE INDEX IF NOT EXISTS idx_trainings_type ON trainings(training_type)",
            "CREATE INDEX IF NOT EXISTS idx_trainings_dates ON trainings(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_training_participants_training ON training_participants(training_id)",
            "CREATE INDEX IF NOT EXISTS idx_training_participants_user ON training_participants(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_certificates_cert_id ON certificates(certificate_id)",
            "CREATE INDEX IF NOT EXISTS idx_certificates_user ON certificates(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_certificates_training ON certificates(training_id)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print("Indexes created successfully!")
        
    except Exception as e:
        print(f"Error creating indexes: {e}")

def create_default_admin(conn):
    """Create a default admin user if no users exist"""
    try:
        cursor = conn.cursor()
        
        # Check if any users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Create default admin user
            cursor.execute("""
                INSERT INTO users (username, password, email, role, full_name, region)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                'admin',
                'admin123',  # You should hash this password in production
                'admin@mnch.gov',
                'admin',
                'System Administrator',
                'National'
            ))
            conn.commit()
            print("Default admin user created:")
            print("Username: admin")
            print("Password: admin123")
            print("Please change the password after first login!")
        else:
            print("Users already exist in the database.")
            
    except Exception as e:
        print(f"Error creating default admin: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()

def check_table_schema():
    """Check the current table schema for debugging"""
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database='mnch_training_tracker',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        # Check trainings table columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'trainings' 
            ORDER BY ordinal_position
        """)
        trainings_columns = cursor.fetchall()
        
        print("Trainings table columns:")
        for col in trainings_columns:
            print(f"  {col[0]} ({col[1]}) - Nullable: {col[2]}")
            
        # Check constraints
        cursor.execute("""
            SELECT constraint_name, constraint_type 
            FROM information_schema.table_constraints 
            WHERE table_name = 'trainings'
        """)
        constraints = cursor.fetchall()
        
        print("\nTrainings table constraints:")
        for constraint in constraints:
            print(f"  {constraint[0]} ({constraint[1]})")
            
    except Exception as e:
        print(f"Error checking schema: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_tables()
    print("\n" + "="*50)
    print("Schema check:")
    print("="*50)
    check_table_schema()