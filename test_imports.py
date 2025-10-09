try:
    import streamlit
    import psycopg2
    import pandas
    import plotly
    from dotenv import load_dotenv
    import streamlit_authenticator
    import qrcode
    from reportlab.pdfgen import canvas
    from PIL import Image
    
    print("All imports successful!")
except ImportError as e:
    print(f"Import error: {e}")