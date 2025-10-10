import streamlit as st
import hashlib
from database import Database

class Authenticator:
    def __init__(self):
        self.db = Database()
    
    def hash_password(self, password):
        """Simple password hashing"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, hashed):
        return self.hash_password(password) == hashed
    
    def login(self, username, password):
        query = "SELECT * FROM users WHERE username = %s"
        user_df = self.db.execute_query(query, (username,), fetch=True)
        
        if user_df is None:
            st.error("Database connection error. Please check your database setup.")
            return None
            
        if not user_df.empty:
            user = user_df.iloc[0]
            if self.verify_password(password, user['password']):
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'full_name': user['full_name'],
                    'region': user['region'],
                    'facility': user['facility']
                }
            else:
                st.error("Invalid password")
        else:
            st.error("User not found")
        return None
    
    def register_trainee(self, form_data):
        """Register a new trainee with all the required fields"""
        hashed_password = self.hash_password(form_data['password'])
        
        query = """
        INSERT INTO users (
            username, password, email, role, full_name, 
            first_name, fathers_name, grand_fathers_name, sex,
            region, zone, woreda, facility,
            place_of_work_type, professional_background,
            training_start_date, training_end_date,
            phone_number, contact_number, gender
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        # Build full name from components
        full_name = f"{form_data['first_name']} {form_data['fathers_name']} {form_data['grand_fathers_name']}"
        
        params = (
            form_data['username'],
            hashed_password,
            form_data['email'],
            'user',  # Changed from 'trainee' to 'user' to match database constraint
            full_name,
            form_data['first_name'],
            form_data['fathers_name'],
            form_data['grand_fathers_name'],
            form_data['sex'],
            form_data['region'],
            form_data['zone'],
            form_data['woreda'],
            form_data['health_facility'],
            form_data['place_of_work_type'],
            form_data['professional_background'],
            form_data['training_start_date'],
            form_data['training_end_date'],
            form_data['phone_number'],
            form_data['phone_number'],
            form_data['sex']
        )
        
        return self.db.execute_query(query, params)
    
    def register_user(self, username, password, email, role, full_name, facility=None, region=None, woreda=None, contact_number=None, gender=None):
        """Original register method for backward compatibility"""
        hashed_password = self.hash_password(password)
        
        query = """
        INSERT INTO users (username, password, email, role, full_name, facility, region, woreda, contact_number, gender)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute_query(query, (username, hashed_password, email, role, full_name, facility, region, woreda, contact_number, gender))

def initialize_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
        def login(self, username, password):
    # Demo credentials for testing
    if username == "demo" and password == "demo123":
        return {
            'id': 1,
            'username': 'demo',
            'full_name': 'Demo User',
            'role': 'admin',
            'region': 'Demo Region'
        }
    
    try:
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        result = self.db.execute_query(query, (username, password), fetch=True)
        if result is not None and not result.empty:
            return result.iloc[0].to_dict()
        return None
    except:
        return None
