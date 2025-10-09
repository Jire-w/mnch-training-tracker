import psycopg2

def update_user_roles():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mnch_training_tracker',
            user='postgres',
            password='MnchTraining2024!',
            port='5432'
        )
        cursor = conn.cursor()
        
        print("Updating user roles...")
        
        # Update existing users: change 'trainer', 'supervisor', 'trainee' to 'user'
        cursor.execute("""
            UPDATE users 
            SET role = 'user' 
            WHERE role IN ('trainer', 'supervisor', 'trainee')
        """)
        
        # Update role check constraint
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
        print("✅ User roles updated successfully!")
        print("Now only two roles: 'admin' and 'user'")
        
    except Exception as e:
        print(f"❌ Error updating user roles: {e}")

if __name__ == "__main__":
    update_user_roles()