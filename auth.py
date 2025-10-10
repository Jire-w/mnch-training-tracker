import streamlit as st
from database import Database

def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"

class Authenticator:
    def __init__(self):
        self.db = Database()
    
    def login(self, username, password):
        """Authenticate user with demo fallback"""
        # Demo credentials for testing
        if username == "demo" and password == "demo123":
            return {
                'id': 1,
                'username': 'demo',
                'full_name': 'Demo Administrator',
                'role': 'admin',
                'region': 'National',
                'email': 'demo@mnch.gov'
            }
        
        if username == "user" and password == "user123":
            return {
                'id': 2,
                'username': 'user',
                'full_name': 'Demo User',
                'role': 'user',
                'region': 'Oromia',
                'email': 'user@mnch.gov'
            }
        
        try:
            query = "SELECT * FROM users WHERE username = %s AND password = %s"
            result = self.db.execute_query(query, (username, password), fetch=True)
            if result is not None and not result.empty:
                return result.iloc[0].to_dict()
            return None
        except Exception as e:
            st.error(f"Login error: {e}")
            return None
    
    def register_user(self, username, password, email, role, full_name, facility, region, woreda, phone_number, zone):
        """Register a new user"""
        try:
            query = """
                INSERT INTO users (username, password, email, role, full_name, facility, region, woreda, phone_number, zone)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            return self.db.execute_query(query, (username, password, email, role, full_name, facility, region, woreda, phone_number, zone))
        except Exception as e:
            st.error(f"Registration error: {e}")
            return False
    
    def register_trainee(self, trainee_data):
        """Register a new trainee"""
        return self.register_user(
            trainee_data['username'],
            trainee_data['password'],
            trainee_data['email'],
            'user',
            f"{trainee_data['first_name']} {trainee_data['fathers_name']} {trainee_data['grand_fathers_name']}",
            trainee_data['health_facility'],
            trainee_data['region'],
            trainee_data['woreda'],
            trainee_data['phone_number'],
            trainee_data.get('zone', '')
        )
