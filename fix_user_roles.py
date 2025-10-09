import psycopg2

def fix_user_roles():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mnch_training_tracker',
            user='postgres',
            password='MnchTraining2024!',
            port='5432'
        )
        cursor = conn.cursor()
        
        print("Fixing user roles...")
        
        # Update any 'trainee' roles to 'user'
        cursor.execute("UPDATE users SET role = 'user' WHERE role = 'trainee'")
        
        # Count how many were updated
        updated_count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Fixed {updated_count} user roles from 'trainee' to 'user'")
        
    except Exception as e:
        print(f"❌ Error fixing user roles: {e}")

if __name__ == "__main__":
    fix_user_roles()