import psycopg2
import pandas as pd

def view_all_users():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mnch_training_tracker',
            user='postgres',
            password='MnchTraining2024!',
            port='5432'
        )
        
        query = "SELECT id, username, email, role, full_name, region, created_at FROM users ORDER BY created_at DESC"
        users_df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        print("📋 Current Users in Database:")
        print("=" * 80)
        if not users_df.empty:
            print(users_df.to_string(index=False))
        else:
            print("No users found in database.")
        
        return users_df
        
    except Exception as e:
        print(f"❌ Error viewing users: {e}")

if __name__ == "__main__":
    view_all_users()