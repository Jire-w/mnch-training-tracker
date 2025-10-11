import os
import re
import streamlit as st
import subprocess

def find_postgresql_dir():
    """Find PostgreSQL data directory"""
    possible_paths = [
        r"C:\Program Files\PostgreSQL\17\data",
        r"C:\PostgreSQL\17\data", 
        r"C:\Program Files\PostgreSQL\16\data",
        r"C:\PostgreSQL\16\data"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            st.success(f"✅ Found PostgreSQL data directory: {path}")
            return path
    
    st.error("❌ Could not find PostgreSQL data directory")
    return None

def fix_postgresql_conf(data_dir):
    """Fix postgresql.conf file"""
    conf_path = os.path.join(data_dir, "postgresql.conf")
    
    if not os.path.exists(conf_path):
        st.error(f"❌ postgresql.conf not found at {conf_path}")
        return False
    
    try:
        with open(conf_path, 'r') as f:
            content = f.read()
        
        # Replace listen_addresses
        content = re.sub(r'#?listen_addresses\s*=\s*.*', "listen_addresses = '*'", content)
        
        # Ensure port is 5432
        content = re.sub(r'#?port\s*=\s*.*', "port = 5432", content)
        
        with open(conf_path, 'w') as f:
            f.write(content)
        
        st.success("✅ Fixed postgresql.conf")
        return True
        
    except Exception as e:
        st.error(f"❌ Error fixing postgresql.conf: {e}")
        return False

def fix_pg_hba_conf(data_dir):
    """Fix pg_hba.conf file"""
    hba_path = os.path.join(data_dir, "pg_hba.conf")
    
    if not os.path.exists(hba_path):
        st.error(f"❌ pg_hba.conf not found at {hba_path}")
        return False
    
    try:
        # Read existing content
        with open(hba_path, 'r') as f:
            content = f.read()
        
        # Add our connection rules if they don't exist
        new_rules = """
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
host    all             all             0.0.0.0/0               md5

# IPv6 local connections:
host    all             all             ::1/128                 md5
"""
        
        if "127.0.0.1/32" not in content:
            content += new_rules
            with open(hba_path, 'w') as f:
                f.write(content)
            st.success("✅ Added connection rules to pg_hba.conf")
        else:
            st.info("ℹ️  Connection rules already exist in pg_hba.conf")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error fixing pg_hba.conf: {e}")
        return False

def restart_postgresql():
    """Restart PostgreSQL service"""
    try:
        st.info("🔄 Restarting PostgreSQL service...")
        
        # Stop service
        result = subprocess.run([
            'net', 'stop', 'postgresql-x64-17'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            st.warning(f"Service stop message: {result.stderr}")
        
        # Start service  
        result = subprocess.run([
            'net', 'start', 'postgresql-x64-17'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            st.success("✅ PostgreSQL service restarted successfully!")
            return True
        else:
            st.error(f"❌ Failed to restart service: {result.stderr}")
            return False
            
    except Exception as e:
        st.error(f"❌ Error restarting service: {e}")
        return False

def main():
    st.title("🔧 PostgreSQL Configuration Fix")
    
    st.warning("""
    **This script will:**
    1. Find your PostgreSQL data directory
    2. Fix postgresql.conf to allow connections  
    3. Fix pg_hba.conf to allow authentication
    4. Restart PostgreSQL service
    """)
    
    if st.button("🚀 Fix PostgreSQL Configuration"):
        with st.spinner("Working..."):
            # Step 1: Find data directory
            data_dir = find_postgresql_dir()
            if not data_dir:
                return
            
            # Step 2: Fix configuration files
            if not fix_postgresql_conf(data_dir):
                return
                
            if not fix_pg_hba_conf(data_dir):
                return
            
            # Step 3: Restart service
            if restart_postgresql():
                st.success("🎉 Configuration fixed! PostgreSQL should now accept connections.")
                
                # Test connection
                st.info("🧪 Testing connection...")
                try:
                    import psycopg2
                    conn = psycopg2.connect(
                        host="localhost",
                        database="postgres",
                        user="postgres", 
                        password="",
                        port=5432
                    )
                    st.success("✅ Connection test successful!")
                    conn.close()
                except Exception as e:
                    st.error(f"❌ Connection test failed: {e}")

if __name__ == "__main__":
    main()
