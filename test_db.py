from database import Database

def test_connection():
    db = Database()
    
    # Test query
    result = db.execute_query("SELECT version()", fetch=True)
    if result is not None:
        print("Database connection successful!")
        print(f"PostgreSQL version: {result.iloc[0,0]}")
    else:
        print("Database connection failed!")

if __name__ == "__main__":
    test_connection()