import psycopg2
import hashlib

def create_test_users():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mnch_training_tracker',
            user='postgres',
            password='MnchTraining2024!',
            port='5432'
        )
        cursor = conn.cursor()
        
        test_users = [
            {
                'username': 'user1',
                'password': 'user123',
                'email': 'user1@region.gov',
                'role': 'user',
                'full_name': 'Test User One',
                'region': 'Oromia',
                'zone': 'East Shewa',
                'phone_number': '+251911111111'
            },
            {
                'username': 'user2', 
                'password': 'user123',
                'email': 'user2@region.gov',
                'role': 'user',
                'full_name': 'Test User Two',
                'region': 'Amhara',
                'zone': 'North Gondar',
                'phone_number': '+251922222222'
            }
        ]
        
        for user_data in test_users:
            hashed_password = hashlib.sha256(user_data['password'].encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO users (username, password, email, role, full_name, region, zone, phone_number, contact_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_data['username'],
                hashed_password,
                user_data['email'],
                user_data['role'],
                user_data['full_name'],
                user_data['region'],
                user_data['zone'],
                user_data['phone_number'],
                user_data['phone_number']
            ))
            print(f"✅ Created user: {user_data['username']}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 Test users created successfully!")
        print("You can now login with:")
        for user in test_users:
            print(f"   Username: {user['username']} | Password: {user['password']} | Region: {user['region']}")
        
    except Exception as e:
        print(f"❌ Error creating test users: {e}")

if __name__ == "__main__":
    create_test_users()