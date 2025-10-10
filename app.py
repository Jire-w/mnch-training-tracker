import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import io

# Set page config first
st.set_page_config(
    page_title="MNCH Training Tracker",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize with error handling
try:
    from auth import initialize_session_state
    initialize_session_state()
except Exception as e:
    st.error(f"Initialization error: {e}")
    # Set basic session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"

# Import other components with error handling
try:
    from auth import Authenticator
    from database import Database, get_trainings, get_users_by_role, add_training, update_user
    from certificate_generator import CertificateGenerator, generate_certificate_id
    from location_data import location_data
    
    auth = Authenticator()
    cert_gen = CertificateGenerator()
    
    # Test database connection
    db_test = Database()
    if db_test.conn is None:
        st.warning("🔧 Demo Mode: Running without database connection. Use demo credentials: username: 'demo', password: 'demo123'")
    
except ImportError as e:
    st.error(f"Missing component: {e}")
    st.info("The app will run in limited mode. Some features may not work.")
except Exception as e:
    st.warning(f"Component initialization issue: {e}")

# Your existing functions continue here...
def login_page():
    st.title("🏥 MNCH Training Tracker")
    
    # Create tabs for Login and Sign Up
    tab1, tab2 = st.tabs(["🔐 Login", "👤 Sign Up"])
    
    with tab1:
        st.subheader("Existing User Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                    return
                    
                user = auth.login(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.current_page = "dashboard"
                    st.success(f"Welcome back {user['full_name']}!")
                    st.rerun()
                else:
                    st.error("Login failed. Please check your credentials.")
                    st.info("💡 Demo credentials: username: 'demo', password: 'demo123'")
    
    with tab2:
        st.subheader("New User Registration")
        st.info("Create a new account to access the MNCH Training Tracker")
        
        with st.form("signup_form", clear_on_submit=True):
            st.markdown("### Account Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input("Full Name*", placeholder="Enter your full name")
                email = st.text_input("Email Address*", placeholder="example@email.com")
                phone_number = st.text_input("Phone Number*", placeholder="+251XXXXXXXXX")
                
                # Region selection for signup
                regions = location_data.get_regions()
                region = st.selectbox("Region*", [""] + regions, key="signup_region")
                
            with col2:
                # Zone selection (depends on region)
                zones = location_data.get_zones_by_region(region) if region else []
                zone = st.selectbox("Zone*", [""] + zones, key="signup_zone")
                
                # Woreda selection (depends on zone)
                woredas = location_data.get_woredas_by_zone(region, zone) if region and zone else []
                woreda = st.selectbox("Woreda*", [""] + woredas, key="signup_woreda")
                
                username = st.text_input("Username*", placeholder="Choose a username")
                password = st.text_input("Password*", type="password", placeholder="Create a password")
                confirm_password = st.text_input("Confirm Password*", type="password", placeholder="Confirm your password")
            
            st.markdown("**Required fields**")
            
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                # Validation
                required_fields = [full_name, email, phone_number, region, zone, woreda, username, password]
                
                if not all(required_fields):
                    st.error("Please fill all required fields (*)")
                    return
                
                if len(password) < 6:
                    st.error("Password must be at least 6 characters long")
                    return
                
                if password != confirm_password:
                    st.error("Passwords do not match!")
                    return
                
                # Check if username already exists
                db = Database()
                existing_user = db.execute_query(
                    "SELECT username FROM users WHERE username = %s", 
                    (username,), fetch=True
                )
                
                if existing_user is not None and not existing_user.empty:
                    st.error("Username already exists. Please choose a different username.")
                    return
                
                # Check if email already exists
                existing_email = db.execute_query(
                    "SELECT email FROM users WHERE email = %s", 
                    (email,), fetch=True
                )
                
                if existing_email is not None and not existing_email.empty:
                    st.error("Email address already exists. Please use a different email.")
                    return
                
                # Register user as 'user' role (not admin)
                if auth.register_user(username, password, email, 'user', full_name, None, region, woreda, phone_number, zone):
                    st.success("🎉 Account created successfully!")
                    st.info("You can now login with your username and password.")
                    
                    # Auto-login after successful registration
                    user = auth.login(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.current_page = "dashboard"
                        st.rerun()
                else:
                    st.error("Error creating account. Please try again.")

# ... Continue with the rest of your existing functions (training_management, trainee_registration_form, etc.)
# Make sure to copy all your existing functions below this line

def training_management():
    """Manage trainings - Create, view, and manage training programs"""
    st.subheader("📚 Training Management")
    
    tab1, tab2 = st.tabs(["Create Training", "View Trainings"])
    
    with tab1:
        st.markdown("### Create New Training")
        
        with st.form("create_training"):
            col1, col2 = st.columns(2)
            
            with col1:
                training_title = st.text_input("Training Title*", placeholder="e.g., Basic MNCH Care")
                training_type = st.selectbox(
                    "Training Type*",
                    ["", "A", "B", "C", "D", "E", "F", "G"]
                )
                training_venue = st.text_input("Training Venue*", placeholder="e.g., Adama Hospital")
                
            with col2:
                training_start_date = st.date_input("Start Date*", value=datetime.now().date())
                training_end_date = st.date_input("End Date*", value=datetime.now().date() + timedelta(days=7))
                training_duration = st.text_input("Duration*", placeholder="e.g., 5 days")
            
            training_description = st.text_area("Training Description", placeholder="Brief description of the training content...")
            
            if st.form_submit_button("Create Training"):
                if not all([training_title, training_type, training_venue, training_duration]):
                    st.error("Please fill all required fields (*)")
                    return
                
                if training_start_date > training_end_date:
                    st.error("End date must be after start date!")
                    return
                
                # Create training
                if add_training(training_title, training_type, training_start_date, training_end_date, training_venue, training_duration, training_description):
                    st.success("✅ Training created successfully!")
                    # Clear dashboard cache to refresh data
                    if 'dashboard_data' in st.session_state:
                        del st.session_state.dashboard_data
                else:
                    st.error("Error creating training. Please try again.")
    
    with tab2:
        st.markdown("### Available Trainings")
        
        trainings_df = get_trainings()
        
        if trainings_df is not None and not trainings_df.empty:
            st.dataframe(trainings_df, use_container_width=True)
        else:
            st.info("No trainings available. Please create trainings first.")

# ... Copy all your other existing functions here (trainee_registration_form, certificate_management, etc.)

def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        # For now, just show a simple dashboard
        st.title("MNCH Training Tracker")
        st.success(f"Welcome, {st.session_state.user['full_name']}!")
        st.info("The app is working! Full functionality will be available once the database is configured.")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()

if __name__ == "__main__":
    main()
