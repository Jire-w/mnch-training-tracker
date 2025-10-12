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

# Initialize session state and components
@st.cache_resource
def initialize_app():
    """Initialize app components with caching"""
    initialize_session_state()
    auth = Authenticator()
    cert_gen = CertificateGenerator()
    return auth, cert_gen

auth, cert_gen = initialize_app()

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
                    
                user = auth.login(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.current_page = "dashboard"
                    st.success(f"Welcome back {user['full_name']}!")
                    st.rerun()
                else:
                    st.error("Login failed. Please check your credentials.")
    
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
                if not handle_registration(full_name, email, phone_number, region, zone, woreda, username, password, confirm_password):
                    return
                
                # Auto-login after successful registration
                user = auth.login(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.current_page = "dashboard"
                    st.rerun()

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

def view_trainings():
    """Display available trainings and statistics"""
    st.markdown("### Available Trainings")
    
    trainings_df = get_trainings()
    
    if trainings_df is not None and not trainings_df.empty:
        st.dataframe(trainings_df, width='stretch')
        
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

def trainee_registration_form():
    """Form for registering new trainees"""
    st.subheader("👥 Trainee Registration Form")
    
    # Initialize form state
    initialize_registration_state()
    
    if st.session_state.registration_success:
        show_registration_success()
        return
    
    # Initialize form data from session state or empty
    form_data = st.session_state.form_data
    
    with st.form("trainee_registration"):
        render_personal_info_section(form_data)
        render_location_section()
        render_work_info_section(form_data)
        render_training_info_section(form_data)
        
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

def show_registration_success():
    """Show success message after registration"""
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

def render_personal_info_section(form_data):
    """Render personal information section of the form"""
    st.markdown("### Personal Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.text_input("First Name*", 
                     placeholder="Enter first name",
                     value=form_data.get('first_name', ''),
                     key="first_name")
    with col2:
        st.text_input("Father's Name*", 
                     placeholder="Enter father's name",
                     value=form_data.get('fathers_name', ''),
                     key="fathers_name")
    with col3:
        st.text_input("Grand Father's Name*", 
                     placeholder="Enter grand father's name",
                     value=form_data.get('grand_fathers_name', ''),
                     key="grand_fathers_name")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox("Sex*", 
                    ["", "Male", "Female"], 
                    index=0 if not form_data.get('sex') else ["Male", "Female"].index(form_data.get('sex')) + 1,
                    key="sex")
    with col2:
        st.text_input("Email Address", 
                     placeholder="example@email.com",
                     value=form_data.get('email', ''),
                     key="email")
    with col3:
        st.text_input("Phone Number*", 
                     placeholder="+251XXXXXXXXX",
                     value=form_data.get('phone_number', ''),
                     key="phone_number")

def render_location_section():
    """Render location information section"""
    st.markdown("### Location Information")
    
    # Get regions
    regions = location_data.get_regions()
    
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
        zones = location_data.get_zones_by_region(selected_region) if selected_region else []
        
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
        woredas = location_data.get_woredas_by_zone(selected_region, selected_zone) if selected_region and selected_zone else []
        
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
    
    st.text_input("Health Facility*", 
                 placeholder="e.g., Adama Hospital",
                 value=st.session_state.form_data.get('health_facility', ''),
                 key="health_facility")

def render_work_info_section(form_data):
    """Render work information section"""
    st.markdown("### Work Information")
    col1, col2 = st.columns(2)
    with col1:
        place_of_work_options = ["", "Health Center", "Hospital", "Health Post", "EPSS", "EFDA", "Others"]
        st.selectbox(
            "Place of Work*", 
            place_of_work_options,
            index=place_of_work_options.index(form_data.get('place_of_work_type', '')),
            key="place_of_work_type"
        )
    with col2:
        professional_options = ["", "Nurse", "Health Officer", "Midwife", "Pharmacist", 
                              "Laboratory Technologist", "HITD", "Environmental", "Others"]
        st.selectbox(
            "Professional Background*",
            professional_options,
            index=professional_options.index(form_data.get('professional_background', '')),
            key="professional_background"
        )

def render_training_info_section(form_data):
    """Render training information section"""
    st.markdown("### Training Information")
    col1, col2 = st.columns(2)
    with col1:
        # Training Type Selection (A, B, C, D, E, F, G)
        training_type_options = ["", "A", "B", "C", "D", "E", "F", "G"]
        st.selectbox(
            "Training Type*",
            training_type_options,
            index=training_type_options.index(form_data.get('training_type', '')),
            key="training_type"
        )
        
    with col2:
        # Use today's date if no date in form_data
        default_date = form_data.get('registration_date')
        if default_date:
            default_date = datetime.strptime(default_date, '%Y-%m-%d').date() if isinstance(default_date, str) else default_date
        else:
            default_date = datetime.now().date()
        st.date_input("Registration Date*", value=default_date, key="registration_date")
    
    col1, col2 = st.columns(2)
    with col1:
        # Use today's date if no date in form_data
        default_start = form_data.get('training_start_date')
        if default_start:
            default_start = datetime.strptime(default_start, '%Y-%m-%d').date() if isinstance(default_start, str) else default_start
        else:
            default_start = datetime.now().date()
        st.date_input("Training Period - From*", value=default_start, key="training_start_date")
    with col2:
        # Use today + 7 days if no date in form_data
        default_end = form_data.get('training_end_date')
        if default_end:
            default_end = datetime.strptime(default_end, '%Y-%m-%d').date() if isinstance(default_end, str) else default_end
        else:
            default_end = (datetime.now() + timedelta(days=7)).date()
        st.date_input("Training Period - To*", value=default_end, key="training_end_date")

def clear_registration_form():
    """Clear registration form data"""
    st.session_state.form_data = {}
    st.session_state.selected_region = ''
    st.session_state.selected_zone = ''
    st.session_state.selected_woreda = ''

def handle_trainee_registration():
    """Handle trainee registration form submission"""
    # Save current form data to session state
    current_form_data = {
        'first_name': st.session_state.first_name,
        'fathers_name': st.session_state.fathers_name,
        'grand_fathers_name': st.session_state.grand_fathers_name,
        'sex': st.session_state.sex,
        'email': st.session_state.email,
        'phone_number': st.session_state.phone_number,
        'region': st.session_state.selected_region,
        'zone': st.session_state.selected_zone,
        'woreda': st.session_state.selected_woreda,
        'health_facility': st.session_state.health_facility,
        'place_of_work_type': st.session_state.place_of_work_type,
        'professional_background': st.session_state.professional_background,
        'training_type': st.session_state.training_type,
        'registration_date': st.session_state.registration_date.strftime('%Y-%m-%d'),
        'training_start_date': st.session_state.training_start_date.strftime('%Y-%m-%d'),
        'training_end_date': st.session_state.training_end_date.strftime('%Y-%m-%d')
    }
    st.session_state.form_data = current_form_data
    
    # Validation
    required_fields = [
        st.session_state.first_name, st.session_state.fathers_name, st.session_state.grand_fathers_name,
        st.session_state.sex, st.session_state.phone_number, st.session_state.selected_region,
        st.session_state.health_facility, st.session_state.place_of_work_type,
        st.session_state.professional_background, st.session_state.training_type
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
    
    if st.session_state.training_start_date > st.session_state.training_end_date:
        st.error("Training end date must be after start date!")
        return
    
    # Generate unique username
    username = f"trainee.{st.session_state.first_name.lower()}.{random.randint(1000,9999)}"
    password = "trainee123"  # Default password
    
    # Prepare form data for registration
    registration_form_data = {
        'first_name': st.session_state.first_name,
        'fathers_name': st.session_state.fathers_name,
        'grand_fathers_name': st.session_state.grand_fathers_name,
        'sex': st.session_state.sex,
        'email': st.session_state.email if st.session_state.email else f"{username}@mnch.gov",
        'phone_number': st.session_state.phone_number,
        'region': st.session_state.selected_region,
        'zone': st.session_state.selected_zone,
        'woreda': st.session_state.selected_woreda,
        'health_facility': st.session_state.health_facility,
        'place_of_work_type': st.session_state.place_of_work_type,
        'professional_background': st.session_state.professional_background,
        'training_type': st.session_state.training_type,
        'training_date': st.session_state.registration_date,
        'training_start_date': st.session_state.training_start_date,
        'training_end_date': st.session_state.training_end_date,
        'username': username,
        'password': password
    }
    
    if auth.register_trainee(registration_form_data):
        st.session_state.registration_success = True
        st.session_state.registered_trainee = {
            'name': f"{st.session_state.first_name} {st.session_state.fathers_name} {st.session_state.grand_fathers_name}",
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

def certificate_management():
    """Manage certificate generation and viewing"""
    st.subheader("📜 Certificate Management")
    
    tab1, tab2 = st.tabs(["Generate Certificate", "View Certificates"])
    
    with tab1:
        generate_certificate_tab()
    
    with tab2:
        view_certificates_tab()

def generate_certificate_tab():
    """Tab for generating new certificates"""
    st.markdown("### Generate New Certificate")
    
    # Get users and trainings for selection
    db = Database()
    users_df = db.execute_query("""
        SELECT id, first_name, fathers_name, grand_fathers_name, full_name, region, facility
        FROM users 
        WHERE role = 'user'
        ORDER BY first_name
    """, fetch=True)
    
    trainings_df = get_trainings()
    
    # Check if we have both trainees and trainings
    if users_df is None or users_df.empty:
        st.error("❌ No trainees registered yet. Please register trainees first.")
        st.info("Go to 'Register Trainee' page to add trainees.")
        return
        
    if trainings_df is None or trainings_df.empty:
        st.error("❌ No trainings created yet. Please create trainings first.")
        st.info("Go to 'Training Management' page to create trainings.")
        return
    
    if users_df is not None and not users_df.empty and trainings_df is not None and not trainings_df.empty:
        with st.form("generate_certificate"):
            col1, col2 = st.columns(2)
            
            with col1:
                selected_user = st.selectbox(
                    "Select Trainee*",
                    options=users_df['id'].tolist(),
                    format_func=lambda x: f"{users_df[users_df['id'] == x].iloc[0]['first_name']} {users_df[users_df['id'] == x].iloc[0]['fathers_name']} {users_df[users_df['id'] == x].iloc[0]['grand_fathers_name']} - {users_df[users_df['id'] == x].iloc[0]['region']}"
                )
                
                # Auto-fill facility from selected user
                if selected_user:
                    user_info = users_df[users_df['id'] == selected_user].iloc[0]
                    default_facility = user_info['facility']
                else:
                    default_facility = ""
                
                selected_training = st.selectbox(
                    "Select Training*",
                    options=trainings_df['id'].tolist(),
                    format_func=lambda x: f"{trainings_df[trainings_df['id'] == x].iloc[0]['title']} ({trainings_df[trainings_df['id'] == x].iloc[0]['start_date']})"
                )
            
            with col2:
                completion_date = st.date_input("Completion Date*", value=datetime.now().date())
                training_venue = st.text_input("Training Venue*", 
                                             placeholder="e.g., Adama Hospital",
                                             value=default_facility)
                training_duration = st.text_input("Training Duration*", 
                                                placeholder="e.g., 5 days",
                                                value="5 days")
            
            if st.form_submit_button("Generate Certificate"):
                generate_certificate(selected_user, selected_training, completion_date, training_venue, training_duration, users_df, trainings_df)
    else:
        st.info("No trainees or trainings available. Please register trainees and create trainings first.")
        
        if users_df is None or users_df.empty:
            st.error("❌ No trainees registered yet. Please register trainees first.")
        if trainings_df is None or trainings_df.empty:
            st.error("❌ No trainings created yet. Please create trainings first.")

def generate_certificate(selected_user, selected_training, completion_date, training_venue, training_duration, users_df, trainings_df):
    """Generate certificate for selected trainee and training"""
    # Get user and training details
    user_info = users_df[users_df['id'] == selected_user].iloc[0]
    training_info = trainings_df[trainings_df['id'] == selected_training].iloc[0]
    
    participant_name = f"{user_info['first_name']} {user_info['fathers_name']} {user_info['grand_fathers_name']}"
    training_title = training_info['title']
    
    # Generate certificate ID
    certificate_id = generate_certificate_id(selected_user, selected_training)
    
    # Generate PDF certificate
    pdf_buffer = cert_gen.generate_certificate(
        participant_name, 
        training_title, 
        completion_date.strftime("%Y-%m-%d"),
        certificate_id,
        training_venue,
        training_duration
    )
    
    # Save certificate record
    if cert_gen.create_certificate_record(selected_user, selected_training, certificate_id):
        st.success("✅ Certificate generated successfully!")
        
        # Download button
        st.download_button(
            label="📥 Download Certificate",
            data=pdf_buffer,
            file_name=f"certificate_{certificate_id}.pdf",
            mime="application/pdf"
        )
        
        # Show certificate details
        st.info(f"""
        **Certificate Details:**
        - **Certificate ID:** {certificate_id}
        - **Trainee:** {participant_name}
        - **Training:** {training_title}
        - **Issue Date:** {completion_date.strftime('%Y-%m-%d')}
        - **Venue:** {training_venue}
        """)
    else:
        st.error("Error saving certificate record.")

def view_certificates_tab():
    """Tab for viewing and verifying certificates"""
    st.markdown("### Issued Certificates")
    
    certificates_df = cert_gen.get_certificates()
    
    if certificates_df is not None and not certificates_df.empty:
        st.dataframe(certificates_df[['certificate_id', 'full_name', 'training_title', 'training_type', 'issue_date']], width='stretch')
        
        # Certificate search and filter
        st.markdown("#### Search Certificate")
        col1, col2 = st.columns(2)
        with col1:
            search_cert_id = st.text_input("Enter Certificate ID")
        with col2:
            if st.button("Verify Certificate"):
                if search_cert_id:
                    verify_certificate(search_cert_id)
    else:
        st.info("No certificates issued yet.")

def verify_certificate(certificate_id):
    """Verify certificate validity"""
    db = Database()
    verify_result = db.execute_query(
        "SELECT c.*, u.full_name, t.title FROM certificates c JOIN users u ON c.user_id = u.id JOIN trainings t ON c.training_id = t.id WHERE c.certificate_id = %s",
        (certificate_id,), fetch=True
    )
    if verify_result is not None and not verify_result.empty:
        st.success("✅ Certificate is valid!")
        cert_info = verify_result.iloc[0]
        st.write(f"**Name:** {cert_info['full_name']}")
        st.write(f"**Training:** {cert_info['title']}")
        st.write(f"**Issue Date:** {cert_info['issue_date']}")
    else:
        st.error("❌ Certificate not found or invalid!")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_dashboard_stats(time_filter='all'):
    """Get dashboard statistics with time filtering and caching"""
    db = Database()
    
    # Base queries
    base_user_query = "SELECT COUNT(*) as count FROM users WHERE role = 'user'"
    base_cert_query = "SELECT COUNT(*) as count FROM certificates"
    base_training_query = "SELECT COUNT(*) as count FROM trainings"
    
    # Add time filters
    time_conditions = get_time_conditions(time_filter)
    date_condition = time_conditions['date']
    cert_date_condition = time_conditions['cert_date']
    training_date_condition = time_conditions['training_date']
    
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

def get_time_conditions(time_filter):
    """Get SQL conditions for time filtering"""
    if time_filter == 'today':
        return {
            'date': " AND created_at::date = CURRENT_DATE",
            'cert_date': " AND issue_date = CURRENT_DATE",
            'training_date': " AND created_at::date = CURRENT_DATE"
        }
    elif time_filter == 'week':
        return {
            'date': " AND created_at >= CURRENT_DATE - INTERVAL '7 days'",
            'cert_date': " AND issue_date >= CURRENT_DATE - INTERVAL '7 days'",
            'training_date': " AND created_at >= CURRENT_DATE - INTERVAL '7 days'"
        }
    elif time_filter == 'month':
        return {
            'date': " AND created_at >= CURRENT_DATE - INTERVAL '30 days'",
            'cert_date': " AND issue_date >= CURRENT_DATE - INTERVAL '30 days'",
            'training_date': " AND created_at >= CURRENT_DATE - INTERVAL '30 days'"
        }
    elif time_filter == 'year':
        return {
            'date': " AND created_at >= CURRENT_DATE - INTERVAL '365 days'",
            'cert_date': " AND issue_date >= CURRENT_DATE - INTERVAL '365 days'",
            'training_date': " AND created_at >= CURRENT_DATE - INTERVAL '365 days'"
        }
    else:
        return {
            'date': "",
            'cert_date': "",
            'training_date': ""
        }

def export_trainees_to_excel(region_filter=None):
    """Export trainees data to Excel"""
    db = Database()
    
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

def admin_dashboard():
    """Admin dashboard with comprehensive statistics"""
    st.subheader("Admin Dashboard")
    
    # Time filter and export button
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        time_filter = st.selectbox(
            "Filter by Time Period",
            ["all", "today", "week", "month", "year"],
            format_func=lambda x: {
                "all": "All Time",
                "today": "Today",
                "week": "Last 7 Days",
                "month": "Last 30 Days",
                "year": "Last Year"
            }[x]
        )
    
    with col6:
        st.write("")  # Spacer
        st.write("")  # Spacer
        if st.button("📊 Export All Trainees to Excel"):
            excel_data = export_trainees_to_excel()
            if excel_data:
                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_data,
                    file_name=f"all_trainees_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("No trainees data to export")
    
    # Get statistics
    stats = get_dashboard_stats(time_filter)
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Total Trainees Registered", stats['total_trainees'])
    col2.metric("Certificates Issued", stats['total_certificates'])
    col3.metric("Total Trainings", stats['total_trainings'])
    
    # Charts
    render_dashboard_charts(stats)
    
    # Recent activity
    render_recent_activity()

def render_dashboard_charts(stats):
    """Render dashboard charts"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Training Types Distribution")
        if stats['training_types'] is not None and not stats['training_types'].empty:
            fig = px.pie(
                stats['training_types'], 
                values='count', 
                names='training_type',
                title='Distribution of Training Types'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No training data available")
    
    with col2:
        st.subheader("Monthly Registration Trend")
        if stats['monthly_trend'] is not None and not stats['monthly_trend'].empty:
            fig = px.line(
                stats['monthly_trend'],
                x='month',
                y='registrations',
                title='Trainee Registrations Over Time'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No registration data available")

def render_recent_activity():
    """Render recent activity section"""
    st.subheader("Recent Activity")
    
    db = Database()
    recent_trainees = db.execute_query("""
        SELECT first_name, fathers_name, grand_fathers_name, region, created_at 
        FROM users 
        WHERE role = 'user'
        ORDER BY created_at DESC 
        LIMIT 10
    """, fetch=True)
    
    recent_certificates = db.execute_query("""
        SELECT c.certificate_id, u.full_name, t.title, c.issue_date
        FROM certificates c
        JOIN users u ON c.user_id = u.id
        JOIN trainings t ON c.training_id = t.id
        ORDER BY c.issue_date DESC 
        LIMIT 10
    """, fetch=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Recent Trainee Registrations**")
        if recent_trainees is not None and not recent_trainees.empty:
            st.dataframe(recent_trainees, width='stretch')
        else:
            st.info("No recent trainee registrations")
    
    with col2:
        st.write("**Recent Certificates Issued**")
        if recent_certificates is not None and not recent_certificates.empty:
            st.dataframe(recent_certificates, width='stretch')
        else:
            st.info("No recent certificates issued")

def user_dashboard():
    """User-specific dashboard"""
    st.subheader("User Dashboard")
    
    # Time filter and export button
    user_region = st.session_state.user.get('region', '')
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        time_filter = st.selectbox(
            "Filter by Time Period",
            ["all", "today", "week", "month", "year"],
            format_func=lambda x: {
                "all": "All Time",
                "today": "Today",
                "week": "Last 7 Days",
                "month": "Last 30 Days",
                "year": "Last Year"
            }[x]
        )
    
    with col6:
        st.write("")  # Spacer
        st.write("")  # Spacer
        if st.button("📊 Export Regional Trainees to Excel"):
            excel_data = export_trainees_to_excel(user_region)
            if excel_data:
                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_data,
                    file_name=f"trainees_{user_region}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("No trainees data to export for your region")
    
    # Get statistics for current user's region
    render_user_dashboard_stats(user_region, time_filter)

def render_user_dashboard_stats(user_region, time_filter):
    """Render user dashboard statistics"""
    db = Database()
    
    # Base queries with region filter
    base_user_query = f"SELECT COUNT(*) as count FROM users WHERE role = 'user' AND region = '{user_region}'"
    base_cert_query = f"""
        SELECT COUNT(*) as count 
        FROM certificates c 
        JOIN users u ON c.user_id = u.id 
        WHERE u.region = '{user_region}'
    """
    
    # Add time filters
    time_conditions = get_time_conditions(time_filter)
    date_condition = time_conditions['date']
    cert_date_condition = time_conditions['cert_date']
    
    # Execute queries
    total_trainees = db.execute_query(base_user_query + date_condition, fetch=True)
    total_certificates = db.execute_query(base_cert_query + cert_date_condition, fetch=True)
    
    # Get training type distribution for region
    training_types = db.execute_query(f"""
        SELECT t.training_type, COUNT(*) as count 
        FROM trainings t
        JOIN training_participants tp ON t.id = tp.training_id
        JOIN users u ON tp.user_id = u.id
        WHERE u.region = '{user_region}'
        GROUP BY t.training_type
    """, fetch=True)
    
    # Display metrics
    col1, col2 = st.columns(2)
    
    total_trainees_count = total_trainees.iloc[0, 0] if total_trainees is not None and not total_trainees.empty else 0
    total_certificates_count = total_certificates.iloc[0, 0] if total_certificates is not None and not total_certificates.empty else 0
    
    col1.metric("Trainees Registered", total_trainees_count)
    col2.metric("Certificates Issued", total_certificates_count)
    
    # Training types chart
    st.subheader(f"Training Types in {user_region}")
    if training_types is not None and not training_types.empty:
        fig = px.pie(
            training_types, 
            values='count', 
            names='training_type',
            title=f'Training Types in {user_region}'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No training data available for your region")
    
    # Recent trainees in region
    st.subheader(f"Recent Trainees in {user_region}")
    recent_trainees = db.execute_query(f"""
        SELECT first_name, fathers_name, grand_fathers_name, zone, woreda, facility, created_at 
        FROM users 
        WHERE role = 'user' AND region = '{user_region}'
        ORDER BY created_at DESC 
        LIMIT 10
    """, fetch=True)
    
    if recent_trainees is not None and not recent_trainees.empty:
        st.dataframe(recent_trainees, width='stretch')
    else:
        st.info("No recent trainee registrations in your region")

def dashboard():
    """Main dashboard with navigation"""
    st.markdown('<div style="font-size: 2.5rem; color: #2E86AB; text-align: center; margin-bottom: 2rem;">🏥 MNCH Training Tracker</div>', unsafe_allow_html=True)
    
    # User info sidebar
    with st.sidebar:
        render_sidebar()
    
    # Page routing
    handle_page_routing()

def render_sidebar():
    """Render sidebar navigation"""
    st.write(f"**Welcome, {st.session_state.user['full_name']}**")
    st.write(f"**Role:** {st.session_state.user['role'].title()}")
    st.write(f"**Region:** {st.session_state.user.get('region', 'N/A')}")
    
    # Navigation
    st.markdown("---")
    st.subheader("Navigation")
    
    user_role = st.session_state.user['role']
    
    if st.button("🏠 Dashboard"):
        st.session_state.current_page = "dashboard"
        # Clear any cached data to force refresh
        if 'dashboard_data' in st.session_state:
            del st.session_state.dashboard_data
        st.rerun()
        
    if st.button("👥 Register Trainee"):
        st.session_state.current_page = "register_trainee"
        st.rerun()
        
    if st.button("📚 Training Management"):
        st.session_state.current_page = "training_management"
        st.rerun()
        
    if st.button("📜 Certificates"):
        st.session_state.current_page = "certificates"
        st.rerun()
    
    if user_role == 'admin':
        if st.button("📊 Reports"):
            st.session_state.current_page = "reports"
            st.rerun()
    
    st.markdown("---")
    if st.button("🚪 Logout"):
        logout_user()

def logout_user():
    """Handle user logout"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.current_page = "dashboard"
    # Clear all cached data
    for key in list(st.session_state.keys()):
        if key not in ['_rerun', '_last_script_run_hash']:
            del st.session_state[key]
    st.rerun()

def handle_page_routing():
    """Handle page routing based on current page"""
    user_role = st.session_state.user['role']
    
    if st.session_state.current_page == "register_trainee":
        trainee_registration_form()
    
    elif st.session_state.current_page == "training_management":
        training_management()
    
    elif st.session_state.current_page == "certificates":
        certificate_management()
    
    elif st.session_state.current_page == "reports":
        if user_role == 'admin':
            admin_dashboard()
        else:
            st.error("You don't have permission to access this page.")
    
    elif st.session_state.current_page == "dashboard":
        if user_role == 'admin':
            admin_dashboard()
        else:
            user_dashboard()

def main():
    """Main application entry point"""
    if not st.session_state.authenticated:
        login_page()
    else:
        dashboard()

if __name__ == "__main__":
    main()
