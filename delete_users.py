import psycopg2

def delete_all_users_except_admin():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mnch_training_tracker',
            user='postgres',
            password='MnchTraining2024!',
            port='5432'
        )
        cursor = conn.cursor()
        
        print("Deleting all users except admin...")
        
        # Delete all users except admin
        cursor.execute("DELETE FROM users WHERE username != 'admin'")
        
        # Reset sequences if needed
        cursor.execute("""
            SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users))
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ {deleted_count} users deleted successfully!")
        print("✅ Only admin user remains.")
        print("   Username: admin")
        print("   Password: admin123")
        
    except Exception as e:
        print(f"❌ Error deleting users: {e}")

if __name__ == "__main__":
    confirm = input("This will DELETE ALL USERS except admin. Type 'YES' to continue: ")
    if confirm == 'YES':
        delete_all_users_except_admin()
    else:
        print("Operation cancelled.")