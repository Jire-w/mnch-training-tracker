import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from auth import Authenticator, initialize_session_state
from database import Database, get_trainings, get_users_by_role, add_training, update_user
from certificate_generator import CertificateGenerator, generate_certificate_id
import io
from location_data import location_data
import time

# Page configuration
st.set_page_config(
    page_title="MNCH Training Tracker",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize with error handling
try:
    initialize_session_state()
    auth = Authenticator()
    cert_gen = CertificateGenerator()
except Exception as e:
    st.error(f"Initialization error: {str(e)}")
    st.stop()

def get_db_with_retry(max_retries=3, delay=2):
    """Get database connection with retry logic"""
    for attempt in range(max_retries):
        try:
            db = Database()
            # Test connection
            test_result = db.execute_query("SELECT 1", fetch=True)
            if test_result is not None:
                return db
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"Database connection attempt {attempt + 1} failed. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                st.error(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
                return None
    return None

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
                    
                try:
                    user = auth.login(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.current_page = "dashboard"
                        st.success(f"Welcome back {user['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Login failed. Please check your credentials.")
                except Exception as e:
                    st.error(f"Login error: {str(e)}")
    
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
                
                try:
                    # Check if username already exists
                    db = get_db_with_retry()
                    if db is None:
                        st.error("Database connection failed. Please try again.")
                        return
                        
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
                        
                except Exception as e:
                    st.error(f"Registration error: {str(e)}")

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
                
                try:
                    # Create training
                    if add_training(training_title, training_type, training_start_date, training_end_date, training_venue, training_duration, training_description):
                        st.success("✅ Training created successfully!")
                        # Clear dashboard cache to refresh data
                        if 'dashboard_data' in st.session_state:
                            del st.session_state.dashboard_data
                    else:
                        st.error("Error creating training. Please try again.")
                except Exception as e:
                    st.error(f"Error creating training: {str(e)}")
    
    with tab2:
        st.markdown("### Available Trainings")
        
        try:
            trainings_df = get_trainings()
            
            if trainings_df is not None and not trainings_df.empty:
                st.dataframe(trainings_df, use_container_width=True)
                
                # Training statistics
                st.markdown("#### Training Statistics")
                col1, col2, col3 = st.columns(3)
                
                total_trainings = len(trainings_df)
                ongoing_trainings = len(trainings_df[
                    (trainings_df['start_date'] <= pd.Timestamp.now()) & 
                    (trainings_df['end_date'] >= pd.Timestamp.now())
                ])
                upcoming_trainings = len(trainings_df[trainings_df['start_date'] > pd.Timestamp.now()])
                
                col1.metric("Total Trainings", total_trainings)
                col2.metric("Ongoing Trainings", ongoing_trainings)
                col3.metric("Upcoming Trainings", upcoming_trainings)
            else:
                st.info("No trainings available. Please create trainings first.")
        except Exception as e:
            st.error(f"Error loading trainings: {str(e)}")

# ... (other functions like trainee_registration_form, certificate_management would follow the same pattern with error handling)

def get_dashboard_stats(time_filter='all'):
    """Get dashboard statistics with time filtering"""
    db = get_db_with_retry()
    if db is None:
        return {
            'total_trainees': 0,
            'total_certificates': 0,
            'total_trainings': 0,
            'training_types': None,
            'monthly_trend': None
        }
    
    try:
        # Base queries
        base_user_query = "SELECT COUNT(*) as count FROM users WHERE role = 'user'"
        base_cert_query = "SELECT COUNT(*) as count FROM certificates"
        base_training_query = "SELECT COUNT(*) as count FROM trainings"
        
        # Add time filters
        if time_filter == 'today':
            date_condition = " AND created_at::date = CURRENT_DATE"
            cert_date_condition = " AND issue_date = CURRENT_DATE"
            training_date_condition = " AND created_at::date = CURRENT_DATE"
        elif time_filter == 'week':
            date_condition = " AND created_at >= CURRENT_DATE - INTERVAL '7 days'"
            cert_date_condition = " AND issue_date >= CURRENT_DATE - INTERVAL '7 days'"
            training_date_condition = " AND created_at >= CURRENT_DATE - INTERVAL '7 days'"
        elif time_filter == 'month':
            date_condition = " AND created_at >= CURRENT_DATE - INTERVAL '30 days'"
            cert_date_condition = " AND issue_date >= CURRENT_DATE - INTERVAL '30 days'"
            training_date_condition = " AND created_at >= CURRENT_DATE - INTERVAL '30 days'"
        elif time_filter == 'year':
            date_condition = " AND created_at >= CURRENT_DATE - INTERVAL '365 days'"
            cert_date_condition = " AND issue_date >= CURRENT_DATE - INTERVAL '365 days'"
            training_date_condition = " AND created_at >= CURRENT_DATE - INTERVAL '365 days'"
        else:
            date_condition = ""
            cert_date_condition = ""
            training_date_condition = ""
        
        # Execute queries
        total_trainees = db.execute_query(base_user_query + date_condition, fetch=True)
        total_certificates = db.execute_query(base_cert_query + cert_date_condition, fetch=True)
        total_trainings = db.execute_query(base_training_query + training_date_condition, fetch=True)
        
        # Get training type distribution
        training_types = db.execute_query("""
            SELECT training_type, COUNT(*) as count 
            FROM trainings 
            GROUP BY training_type
        """, fetch=True)
        
        # Get monthly registration trend
        monthly_trend = db.execute_query("""
            SELECT DATE_TRUNC('month', created_at) as month, 
                   COUNT(*) as registrations
            FROM users 
            WHERE role = 'user'
            GROUP BY month 
            ORDER BY month
        """, fetch=True)
        
        return {
            'total_trainees': total_trainees.iloc[0, 0] if total_trainees is not None and not total_trainees.empty else 0,
            'total_certificates': total_certificates.iloc[0, 0] if total_certificates is not None and not total_certificates.empty else 0,
            'total_trainings': total_trainings.iloc[0, 0] if total_trainings is not None and not total_trainings.empty else 0,
            'training_types': training_types,
            'monthly_trend': monthly_trend
        }
    except Exception as e:
        st.error(f"Error getting dashboard stats: {str(e)}")
        return {
            'total_trainees': 0,
            'total_certificates': 0,
            'total_trainings': 0,
            'training_types': None,
            'monthly_trend': None
        }

def export_trainees_to_excel(region_filter=None):
    """Export trainees data to Excel"""
    db = get_db_with_retry()
    if db is None:
        return None
    
    try:
        if region_filter:
            query = """
                SELECT 
                    first_name, fathers_name, grand_fathers_name, sex, email, phone_number,
                    region, zone, woreda, facility as health_facility,
                    place_of_work_type, professional_background,
                    training_start_date, training_end_date, created_at as registration_date
                FROM users 
                WHERE role = 'user' AND region = %s
                ORDER BY created_at DESC
            """
            trainees_df = db.execute_query(query, (region_filter,), fetch=True)
        else:
            query = """
                SELECT 
                    first_name, fathers_name, grand_fathers_name, sex, email, phone_number,
                    region, zone, woreda, facility as health_facility,
                    place_of_work_type, professional_background,
                    training_start_date, training_end_date, created_at as registration_date
                FROM users 
                WHERE role = 'user'
                ORDER BY created_at DESC
            """
            trainees_df = db.execute_query(query, fetch=True)
        
        if trainees_df is not None and not trainees_df.empty:
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                trainees_df.to_excel(writer, sheet_name='Trainees', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Trainees']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            output.seek(0)
            return output
        return None
    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")
        return None

# ... (rest of your functions like admin_dashboard, user_dashboard, dashboard, main)

def main():
    try:
        if not st.session_state.authenticated:
            login_page()
        else:
            dashboard()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page and try again.")

if __name__ == "__main__":
    main()
