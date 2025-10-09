import streamlit as st
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import io
import os
from datetime import datetime
from database import Database

class CertificateGenerator:
    def __init__(self):
        self.db = Database()
    
    def generate_certificate(self, participant_name, training_title, completion_date, certificate_id, training_venue, training_duration):
        """Generate PDF certificate with QR code"""
        buffer = io.BytesIO()
        
        # Create PDF
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Add decorative border
        c.setStrokeColorRGB(0.2, 0.4, 0.6)  # Blue color
        c.setLineWidth(3)
        c.rect(20*mm, 20*mm, width-40*mm, height-40*mm)
        
        # Add header
        c.setFillColorRGB(0.2, 0.4, 0.6)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(width/2, height-80, "CERTIFICATE OF COMPLETION")
        
        # Add decorative line
        c.setLineWidth(2)
        c.line(50*mm, height-100, width-50*mm, height-100)
        
        # Add main text
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height-150, "This is to certify that")
        
        # Participant name
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(width/2, height-200, participant_name.upper())
        
        # Completion text
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height-250, "has successfully completed the training program")
        
        # Training title
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height-290, f"'{training_title}'")
        
        # Training details
        c.setFont("Helvetica", 14)
        c.drawCentredString(width/2, height-330, f"Venue: {training_venue}")
        c.drawCentredString(width/2, height-360, f"Duration: {training_duration}")
        c.drawCentredString(width/2, height-390, f"Completed on: {completion_date}")
        
        # Certificate ID
        c.drawCentredString(width/2, height-430, f"Certificate ID: {certificate_id}")
        
        # Generate and add QR code
        try:
            qr = qrcode.QRCode(version=1, box_size=4, border=2)
            qr_data = f"Certificate ID: {certificate_id}\nName: {participant_name}\nTraining: {training_title}\nDate: {completion_date}"
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = io.BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # Add QR code to PDF
            qr_image = ImageReader(qr_buffer)
            c.drawImage(qr_image, width/2-50, 80, width=100, height=100)
            
            # QR code label
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, 60, "Scan to verify certificate")
            
        except Exception as e:
            st.error(f"Error generating QR code: {e}")
        
        # Footer
        c.setFont("Helvetica-Oblique", 12)
        c.drawCentredString(width/2, 30, "MNCH Training Tracker - Ministry of Health")
        
        c.save()
        buffer.seek(0)
            
        return buffer

    def create_certificate_record(self, user_id, training_id, certificate_id):
        """Create certificate record in database"""
        try:
            query = """
            INSERT INTO certificates (certificate_id, training_id, user_id, issue_date)
            VALUES (%s, %s, %s, CURRENT_DATE)
            """
            result = self.db.execute_query(query, (certificate_id, training_id, user_id))
            return result
        except Exception as e:
            st.error(f"Error creating certificate record: {e}")
            return False

    def get_certificates(self):
        """Get all certificates with user and training info"""
        try:
            query = """
            SELECT c.*, u.full_name, u.first_name, u.fathers_name, u.grand_fathers_name, 
                   t.title as training_title, t.start_date, t.end_date, t.venue, t.training_type
            FROM certificates c
            JOIN users u ON c.user_id = u.id
            JOIN trainings t ON c.training_id = t.id
            ORDER BY c.issue_date DESC
            """
            return self.db.execute_query(query, fetch=True)
        except Exception as e:
            st.error(f"Error fetching certificates: {e}")
            return None

def generate_certificate_id(user_id, training_id):
    """Generate unique certificate ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    return f"MNCH-{training_id:03d}-{user_id:03d}-{timestamp}"