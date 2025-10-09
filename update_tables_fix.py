import psycopg2

def fix_users_table_columns():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mnch_training_tracker',
            user='postgres',
            password='MnchTraining2024!',
            port='5432'
        )
        cursor = conn.cursor()
        
        print("Checking and fixing users table columns...")
        
        # Check if columns exist and add them if they don't
        columns_to_check = [
            ('first_name', 'VARCHAR(100)'),
            ('fathers_name', 'VARCHAR(100)'),
            ('grand_fathers_name', 'VARCHAR(100)'),
            ('sex', 'VARCHAR(10)'),
            ('zone', 'VARCHAR(50)'),
            ('place_of_work_type', 'VARCHAR(50)'),
            ('professional_background', 'VARCHAR(100)'),
            ('training_start_date', 'DATE'),
            ('training_end_date', 'DATE'),
            ('phone_number', 'VARCHAR(20)')
        ]
        
        for column_name, column_type in columns_to_check:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name=%s
            """, (column_name,))
            
            if not cursor.fetchone():
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                print(f"✓ Added column: {column_name}")
            else:
                print(f"✓ Column already exists: {column_name}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Users table columns fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing table columns: {e}")

if __name__ == "__main__":
    fix_users_table_columns()