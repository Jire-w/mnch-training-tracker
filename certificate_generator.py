import os
from fpdf import FPDF
from datetime import datetime
import streamlit as st

# Make QR code optional
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    st.warning("QR code functionality is disabled. Install 'qrcode[pil]' to enable.")

class CertificateGenerator:
    def __init__(self):
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
                st.warning(f"QR code generation failed: {e}")
        
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
    
    # ... rest of your certificate_generator methods remain the same
