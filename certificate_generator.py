import os
import io
from fpdf import FPDF
from datetime import datetime
import streamlit as st

# Make QR code optional
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

class CertificateGenerator:
    def __init__(self):
        # Import Database here to avoid circular imports
        from database import Database
        self.db = Database()
    
    def generate_certificate(self, participant_name, training_title, completion_date, certificate_id, venue, duration):
        pdf = FPDF()
        pdf.add_page()
        
        # Set up certificate design
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(200, 20, "CERTIFICATE OF COMPLETION", ln=True, align='C')
        pdf.ln(20)
        
        pdf.set_font("Arial", '', 16)
        pdf.cell(200, 10, f"This is to certify that", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(200, 10, participant_name, ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", '', 16)
        pdf.cell(200, 10, f"has successfully completed the training", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(200, 10, training_title, ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", '', 14)
        pdf.cell(200, 10, f"Completed on: {completion_date}", ln=True, align='C')
        pdf.cell(200, 10, f"Venue: {venue}", ln=True, align='C')
        pdf.cell(200, 10, f"Duration: {duration}", ln=True, align='C')
        pdf.ln(15)
        
        pdf.cell(200, 10, f"Certificate ID: {certificate_id}", ln=True, align='C')
        
        # Only add QR code if available
        if QRCODE_AVAILABLE:
            try:
                self._add_qr_code(pdf, certificate_id)
            except Exception as e:
                # Silently fail for QR code - it's optional
                pass
        
        # Save to buffer
        pdf_buffer = io.BytesIO()
        pdf_output = pdf.output(dest='S').encode('latin1')
        pdf_buffer.write(pdf_output)
        pdf_buffer.seek(0)
        
        return pdf_buffer
    
    def _add_qr_code(self, pdf, certificate_id):
        """Add QR code to certificate (only if qrcode is available)"""
        if not QRCODE_AVAILABLE:
            return
            
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,
            border=2,
        )
        qr.add_data(f"Certificate ID: {certificate_id}")
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to temporary file
        qr_temp_path = f"/tmp/qr_{certificate_id}.png"
        qr_img.save(qr_temp_path)
        
        # Add QR code to PDF
        pdf.image(qr_temp_path, x=80, y=200, w=50)
        
        # Clean up temporary file
        if os.path.exists(qr_temp_path):
            os.remove(qr_temp_path)
    
    def create_certificate_record(self, user_id, training_id, certificate_id):
        """Save certificate record to database"""
        try:
            query = """
                INSERT INTO certificates (certificate_id, user_id, training_id, issue_date, training_venue, training_duration)
                VALUES (%s, %s, %s, CURRENT_DATE, %s, %s)
            """
            # Use default values for venue and duration
            return self.db.execute_query(query, (certificate_id, user_id, training_id, "Training Venue", "5 days"))
        except Exception as e:
            st.error(f"Error creating certificate record: {e}")
            return False
    
    def get_certificates(self):
        """Get all certificates from database"""
        try:
            query = """
                SELECT c.certificate_id, u.full_name, t.title as training_title, 
                       t.training_type, c.issue_date
                FROM certificates c
                JOIN users u ON c.user_id = u.id
                JOIN trainings t ON c.training_id = t.id
                ORDER BY c.issue_date DESC
            """
            return self.db.execute_query(query, fetch=True)
        except Exception as e:
            st.error(f"Error getting certificates: {e}")
            return None

def generate_certificate_id(user_id, training_id):
    """Generate a unique certificate ID"""
    import hashlib
    from datetime import datetime
    
    # Create a unique string
    unique_string = f"{user_id}_{training_id}_{datetime.now().timestamp()}"
    
    # Generate hash
    hash_object = hashlib.md5(unique_string.encode())
    return f"CERT_{hash_object.hexdigest()[:12].upper()}"
