import psycopg2

def verify_database_constraints():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mnch_training_tracker',
            user='postgres',
            password='MnchTraining2024!',
            port='5432'
        )
        cursor = conn.cursor()
        
        print("Checking database constraints...")
        
        # Check the current role constraint
        cursor.execute("""
            SELECT constraint_name, constraint_type, check_clause 
            FROM information_schema.check_constraints 
            WHERE constraint_name LIKE '%role%'
        """)
        
        constraints = cursor.fetchall()
        print("Current role constraints:")
        for constraint in constraints:
            print(f"  - {constraint}")
        
        # Update the constraint if needed
        cursor.execute("""
            ALTER TABLE users 
            DROP CONSTRAINT IF EXISTS users_role_check
        """)
        
        cursor.execute("""
            ALTER TABLE users 
            ADD CONSTRAINT users_role_check 
            CHECK (role IN ('admin', 'user'))
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database constraints verified and updated!")
        
    except Exception as e:
        print(f"❌ Error verifying constraints: {e}")

if __name__ == "__main__":
    verify_database_constraints()