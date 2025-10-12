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
import random

# Page configuration
st.set_page_config(
    page_title="MNCH Training Tracker",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state safely
def initialize_session_state_safe():
    """Safely initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    if 'registration_success' not in st.session_state:
        st.session_state.registration_success = False
    if 'registered_trainee' not in st.session_state:
        st.session_state.registered_trainee = None
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    if 'selected_region' not in st.session_state:
        st.session_state.selected_region = ''
    if 'selected_zone' not in st.session_state:
        st.session_state.selected_zone = ''
    if 'selected_woreda' not in st.session_state:
        st.session_state.selected_woreda = ''

# Initialize session state first
initialize_session_state_safe()

# Initialize app components with error handling
try:
    # Call the original initialize_session_state if it exists
    if 'initialize_session_state' in globals():
        initialize_session_state()
    
    auth = Authenticator()
    cert_gen = CertificateGenerator()
except Exception as e:
    st.error(f"Error initializing application: {e}")
    # Create fallback instances
    class FallbackAuthenticator:
        def login(self, username, password):
            return None
        def register_user(self, *args, **kwargs):
            return False
        def register_trainee(self, *args, **kwargs):
            return False
    
    class FallbackCertificateGenerator:
        def generate_certificate(self, *args, **kwargs):
            return io.BytesIO()
        def create_certificate_record(self, *args, **kwargs):
            return False
        def get_certificates(self):
            return pd.DataFrame()
    
    auth = FallbackAuthenticator()
    cert_gen = FallbackCertificateGenerator()

def login_page():
    """Login and registration page"""
    st.title("🏥 MNCH Training Tracker")
    
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
                    st.error(f"Login error: {e}")
    
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
                try:
                    regions = location_data.get_regions()
                    region = st.selectbox("Region*", [""] + regions, key="signup_region")
                except:
                    regions = []
                    region = st.selectbox("Region*", [""], key="signup_region")
                
            with col2:
                # Zone selection (depends on region)
                try:
                    zones = location_data.get_zones_by_region(region) if region else []
                    zone = st.selectbox("Zone*", [""] + zones, key="signup_zone")
                except:
                    zones = []
                    zone = st.selectbox("Zone*", [""], key="signup_zone")
                
                # Woreda selection (depends on zone)
                try:
                    woredas = location_data.get_woredas_by_zone(region, zone) if region and zone else []
                    woreda = st.selectbox("Woreda*", [""] + woredas, key="signup_woreda")
                except:
                    woredas = []
                    woreda = st.selectbox("Woreda*", [""], key="signup_woreda")
                
                username = st.text_input("Username*", placeholder="Choose a username")
                password = st.text_input("Password*", type="password", placeholder="Create a password")
                confirm_password = st.text_input("Confirm Password*", type="password", placeholder="Confirm your password")
            
            st.markdown("**Required fields**")
            
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                try:
                    if not handle_registration(full_name, email, phone_number, region, zone, woreda, username, password, confirm_password):
                        return
                    
                    # Auto-login after successful registration
                    user = auth.login(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.current_page = "dashboard"
                        st.rerun()
                except Exception as e:
                    st.error(f"Registration error: {e}")

def handle_registration(full_name, email, phone_number, region, zone, woreda, username, password, confirm_password):
    """Handle user registration with validation"""
    required_fields = [full_name, email, phone_number, region, zone, woreda, username, password]
    
    if not all(required_fields):
        st.error("Please fill all required fields (*)")
        return False
    
    if len(password) < 6:
        st.error("Password must be at least 6 characters long")
        return False
    
    if password != confirm_password:
        st.error("Passwords do not match!")
        return False
    
    try:
        # Check if username already exists
        db = Database()
        existing_user = db.execute_query(
            "SELECT username FROM users WHERE username = %s", 
            (username,), fetch=True
        )
        
        if existing_user is not None and not existing_user.empty:
            st.error("Username already exists. Please choose a different username.")
            return False
        
        # Check if email already exists
        existing_email = db.execute_query(
            "SELECT email FROM users WHERE email = %s", 
            (email,), fetch=True
        )
        
        if existing_email is not None and not existing_email.empty:
            st.error("Email address already exists. Please use a different email.")
            return False
        
        # Register user as 'user' role (not admin)
        if auth.register_user(username, password, email, 'user', full_name, None, region, woreda, phone_number, zone):
            st.success("🎉 Account created successfully!")
            st.info("You can now login with your username and password.")
            return True
        else:
            st.error("Error creating account. Please try again.")
            return False
    except Exception as e:
        st.error(f"Database error during registration: {e}")
        return False

def training_management():
    """Manage trainings - Create, view, and manage training programs"""
    st.subheader("📚 Training Management")
    
    tab1, tab2 = st.tabs(["Create Training", "View Trainings"])
    
    with tab1:
        create_training_form()
    
    with tab2:
        view_trainings()

def create_training_form():
    """Form to create new training"""
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
            try:
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
            except Exception as e:
                st.error(f"Error creating training: {e}")

def view_trainings():
    """Display available trainings and statistics"""
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
        st.error(f"Error loading trainings: {e}")

def trainee_registration_form():
    """Form for registering new trainees"""
    st.subheader("👥 Trainee Registration Form")
    
    # Initialize form state
    initialize_registration_state()
    
    if st.session_state.registration_success:
        show_registration_success()
        return
    
    with st.form("trainee_registration"):
        render_personal_info_section()
        render_location_section()
        render_work_info_section()
        render_training_info_section()
        
        st.markdown("**Required fields**")
        
        col1, col2 = st.columns(2)
        with col1:
            save_button = st.form_submit_button("💾 Save and Add New Trainee")
        with col2:
            clear_button = st.form_submit_button("🗑️ Clear Form")
        
        if clear_button:
            clear_registration_form()
            st.rerun()
        
        if save_button:
            handle_trainee_registration()

def initialize_registration_state():
    """Initialize registration form state"""
    # Already initialized in the main initialization function

def show_registration_success():
    """Show success message after registration"""
    if st.session_state.registered_trainee:
        st.success(f"🎉 Trainee successfully registered!")
        st.info(f"Trainee Name: **{st.session_state.registered_trainee['name']}**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Register Another Trainee"):
            st.session_state.registration_success = False
            st.session_state.registered_trainee = None
            st.session_state.form_data = {}
            st.session_state.selected_region = ''
            st.session_state.selected_zone = ''
            st.session_state.selected_woreda = ''
            st.rerun()
    with col2:
        if st.button("📜 Generate Certificate"):
            st.session_state.current_page = "certificates"
            st.rerun()
    with col3:
        if st.button("🏠 Back to Dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()

def render_personal_info_section():
    """Render personal information section of the form"""
    st.markdown("### Personal Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.session_state.form_data['first_name'] = st.text_input(
            "First Name*", 
            placeholder="Enter first name",
            value=st.session_state.form_data.get('first_name', ''),
            key="first_name_input"
        )
    with col2:
        st.session_state.form_data['fathers_name'] = st.text_input(
            "Father's Name*", 
            placeholder="Enter father's name",
            value=st.session_state.form_data.get('fathers_name', ''),
            key="fathers_name_input"
        )
    with col3:
        st.session_state.form_data['grand_fathers_name'] = st.text_input(
            "Grand Father's Name*", 
            placeholder="Enter grand father's name",
            value=st.session_state.form_data.get('grand_fathers_name', ''),
            key="grand_fathers_name_input"
        )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.form_data['sex'] = st.selectbox(
            "Sex*", 
            ["", "Male", "Female"], 
            index=0 if not st.session_state.form_data.get('sex') else ["Male", "Female"].index(st.session_state.form_data.get('sex')) + 1,
            key="sex_select"
        )
    with col2:
        st.session_state.form_data['email'] = st.text_input(
            "Email Address", 
            placeholder="example@email.com",
            value=st.session_state.form_data.get('email', ''),
            key="email_input"
        )
    with col3:
        st.session_state.form_data['phone_number'] = st.text_input(
            "Phone Number*", 
            placeholder="+251XXXXXXXXX",
            value=st.session_state.form_data.get('phone_number', ''),
            key="phone_number_input"
        )

def render_location_section():
    """Render location information section"""
    st.markdown("### Location Information")
    
    # Get regions
    try:
        regions = location_data.get_regions()
    except:
        regions = []
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_region = st.selectbox(
            "Region*",
            options=[""] + regions,
            index=0 if not st.session_state.selected_region else (regions.index(st.session_state.selected_region) + 1 if st.session_state.selected_region in regions else 0),
            key="region_select"
        )
        
    with col2:
        # Zone selection - depends on region
        try:
            zones = location_data.get_zones_by_region(selected_region) if selected_region else []
        except:
            zones = []
        
        # Determine the index for zone selection
        zone_index = 0
        if st.session_state.selected_zone and st.session_state.selected_zone in zones:
            zone_index = zones.index(st.session_state.selected_zone) + 1
        
        selected_zone = st.selectbox(
            "Zone",
            options=[""] + zones,
            index=zone_index,
            key="zone_select"
        )
        
    with col3:
        # Woreda selection - depends on zone
        try:
            woredas = location_data.get_woredas_by_zone(selected_region, selected_zone) if selected_region and selected_zone else []
        except:
            woredas = []
        
        # Determine the index for woreda selection
        woreda_index = 0
        if st.session_state.selected_woreda and st.session_state.selected_woreda in woredas:
            woreda_index = woredas.index(st.session_state.selected_woreda) + 1
        
        selected_woreda = st.selectbox(
            "Woreda",
            options=[""] + woredas,
            index=woreda_index,
            key="woreda_select"
        )
    
    # Check for changes and trigger rerun if needed
    region_changed = selected_region != st.session_state.selected_region
    zone_changed = selected_zone != st.session_state.selected_zone
    woreda_changed = selected_woreda != st.session_state.selected_woreda
    
    if region_changed or zone_changed or woreda_changed:
        st.session_state.selected_region = selected_region
        st.session_state.selected_zone = selected_zone
        st.session_state.selected_woreda = selected_woreda
        st.rerun()
    
    st.session_state.form_data['health_facility'] = st.text_input(
        "Health Facility*", 
        placeholder="e.g., Adama Hospital",
        value=st.session_state.form_data.get('health_facility', ''),
        key="health_facility_input"
    )

def render_work_info_section():
    """Render work information section"""
    st.markdown("### Work Information")
    col1, col2 = st.columns(2)
    with col1:
        place_of_work_options = ["", "Health Center", "Hospital", "Health Post", "EPSS", "EFDA", "Others"]
        current_value = st.session_state.form_data.get('place_of_work_type', '')
        st.session_state.form_data['place_of_work_type'] = st.selectbox(
            "Place of Work*", 
            place_of_work_options,
            index=place_of_work_options.index(current_value) if current_value in place_of_work_options else 0,
            key="place_of_work_select"
        )
    with col2:
        professional_options = ["", "Nurse", "Health Officer", "Midwife", "Pharmacist", 
                              "Laboratory Technologist", "HITD", "Environmental", "Others"]
        current_value = st.session_state.form_data.get('professional_background', '')
        st.session_state.form_data['professional_background'] = st.selectbox(
            "Professional Background*",
            professional_options,
            index=professional_options.index(current_value) if current_value in professional_options else 0,
            key="professional_background_select"
        )

def render_training_info_section():
    """Render training information section"""
    st.markdown("### Training Information")
    col1, col2 = st.columns(2)
    with col1:
        # Training Type Selection (A, B, C, D, E, F, G)
        training_type_options = ["", "A", "B", "C", "D", "E", "F", "G"]
        current_value = st.session_state.form_data.get('training_type', '')
        st.session_state.form_data['training_type'] = st.selectbox(
            "Training Type*",
            training_type_options,
            index=training_type_options.index(current_value) if current_value in training_type_options else 0,
            key="training_type_select"
        )
        
    with col2:
        # Use today's date if no date in form_data
        default_date = st.session_state.form_data.get('registration_date')
        if default_date:
            try:
                default_date = datetime.strptime(default_date, '%Y-%m-%d').date() if isinstance(default_date, str) else default_date
            except:
                default_date = datetime.now().date()
        else:
            default_date = datetime.now().date()
        st.session_state.form_data['registration_date'] = st.date_input(
            "Registration Date*", 
            value=default_date, 
            key="registration_date_input"
        )
    
    col1, col2 = st.columns(2)
    with col1:
        # Use today's date if no date in form_data
        default_start = st.session_state.form_data.get('training_start_date')
        if default_start:
            try:
                default_start = datetime.strptime(default_start, '%Y-%m-%d').date() if isinstance(default_start, str) else default_start
            except:
                default_start = datetime.now().date()
        else:
            default_start = datetime.now().date()
        st.session_state.form_data['training_start_date'] = st.date_input(
            "Training Period - From*", 
            value=default_start, 
            key="training_start_date_input"
        )
    with col2:
        # Use today + 7 days if no date in form_data
        default_end = st.session_state.form_data.get('training_end_date')
        if default_end:
            try:
                default_end = datetime.strptime(default_end, '%Y-%m-%d').date() if isinstance(default_end, str) else default_end
            except:
                default_end = (datetime.now() + timedelta(days=7)).date()
        else:
            default_end = (datetime.now() + timedelta(days=7)).date()
        st.session_state.form_data['training_end_date'] = st.date_input(
            "Training Period - To*", 
            value=default_end, 
            key="training_end_date_input"
        )

def clear_registration_form():
    """Clear registration form data"""
    st.session_state.form_data = {}
    st.session_state.selected_region = ''
    st.session_state.selected_zone = ''
    st.session_state.selected_woreda = ''

def handle_trainee_registration():
    """Handle trainee registration form submission"""
    try:
        # Validation
        required_fields = [
            st.session_state.form_data.get('first_name'),
            st.session_state.form_data.get('fathers_name'),
            st.session_state.form_data.get('grand_fathers_name'),
            st.session_state.form_data.get('sex'),
            st.session_state.form_data.get('phone_number'),
            st.session_state.selected_region,
            st.session_state.form_data.get('health_facility'),
            st.session_state.form_data.get('place_of_work_type'),
            st.session_state.form_data.get('professional_background'),
            st.session_state.form_data.get('training_type')
        ]
        
        missing_fields = []
        field_names = [
            "First Name", "Father's Name", "Grand Father's Name", "Sex", "Phone Number",
            "Region", "Health Facility", "Place of Work", "Professional Background", "Training Type"
        ]
        
        for i, field in enumerate(required_fields):
            if not field:
                missing_fields.append(field_names[i])
        
        if missing_fields:
            st.error(f"Please fill all required fields: {', '.join(missing_fields)}")
            return
        
        training_start_date = st.session_state.form_data.get('training_start_date')
        training_end_date = st.session_state.form_data.get('training_end_date')
        
        if training_start_date and training_end_date and training_start_date > training_end_date:
            st.error("Training end date must be after start date!")
            return
        
        # Generate unique username
        first_name = st.session_state.form_data.get('first_name', '')
        username = f"trainee.{first_name.lower()}.{random.randint(1000,9999)}"
        password = "trainee123"  # Default password
        
        # Prepare form data for registration
        registration_form_data = {
            'first_name': first_name,
            'fathers_name': st.session_state.form_data.get('fathers_name'),
            'grand_fathers_name': st.session_state.form_data.get('grand_fathers_name'),
            'sex': st.session_state.form_data.get('sex'),
            'email': st.session_state.form_data.get('email') or f"{username}@mnch.gov",
            'phone_number': st.session_state.form_data.get('phone_number'),
            'region': st.session_state.selected_region,
            'zone': st.session_state.selected_zone,
            'woreda': st.session_state.selected_woreda,
            'health_facility': st.session_state.form_data.get('health_facility'),
            'place_of_work_type': st.session_state.form_data.get('place_of_work_type'),
            'professional_background': st.session_state.form_data.get('professional_background'),
            'training_type': st.session_state.form_data.get('training_type'),
            'training_date': st.session_state.form_data.get('registration_date'),
            'training_start_date': training_start_date,
            'training_end_date': training_end_date,
            'username': username,
            'password': password
        }
        
        if auth.register_trainee(registration_form_data):
            st.session_state.registration_success = True
            st.session_state.registered_trainee = {
                'name': f"{first_name} {st.session_state.form_data.get('fathers_name')} {st.session_state.form_data.get('grand_fathers_name')}",
                'username': username
            }
            # Clear form data after successful registration
            clear_registration_form()
            # Clear the dashboard cache to force refresh
            if 'dashboard_data' in st.session_state:
                del st.session_state.dashboard_data
            st.rerun()
        else:
            st.error("Error registering trainee. Please try again.")
    except Exception as e:
        st.error(f"Error during registration: {e}")

# [Rest of the functions remain the same as in the previous refined version, 
# but make sure to add similar try-catch blocks in each function]

def main():
    """Main application entry point"""
    try:
        # Ensure session state is initialized
        initialize_session_state_safe()
        
        if not st.session_state.authenticated:
            login_page()
        else:
            dashboard()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.info("Please refresh the page and try again.")

if __name__ == "__main__":
    main()
