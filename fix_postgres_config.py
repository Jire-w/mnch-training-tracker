import os
import subprocess
import streamlit as st

def main():
    st.title("PostgreSQL Configuration Fix")
    
    postgresql_conf_path = r"C:\Program Files\PostgreSQL\17\data\postgresql.conf"
    pg_hba_conf_path = r"C:\Program Files\PostgreSQL\17\data\pg_hba.conf"
    
    st.write("### Current Configuration Files:")
    st.write(f"**postgresql.conf**: {postgresql_conf_path}")
    st.write(f"**pg_hba.conf**: {pg_hba_conf_path}")
    
    # Step 1: Check current postgresql.conf
    st.write("### Step 1: Checking postgresql.conf")
    try:
        with open(postgresql_conf_path, 'r') as f:
            postgresql_content = f.read()
        
        if "listen_addresses = '*'" in postgresql_content:
            st.success("✅ listen_addresses is already set to '*'")
        else:
            st.error("❌ listen_addresses is NOT set to '*'")
            
        if "port = 5432" in postgresql_content:
            st.success("✅ Port is set to 5432")
        else:
            st.error("❌ Port is not set to 5432")
            
    except Exception as e:
        st.error(f"Error reading postgresql.conf: {e}")
    
    # Step 2: Check current pg_hba.conf
    st.write("### Step 2: Checking pg_hba.conf")
    try:
        with open(pg_hba_conf_path, 'r') as f:
            pg_hba_content = f.read()
        
        st.text_area("Current pg_hba.conf content:", pg_hba_content, height=200)
        
        if "127.0.0.1/32" in pg_hba_content:
            st.success("✅ IPv4 local connection rules exist")
        else:
            st.error("❌ Missing IPv4 local connection rules")
            
    except Exception as e:
        st.error(f"Error reading pg_hba.conf: {e}")
    
    # Step 3: Fix configuration
    st.write("### Step 3: Fix Configuration")
    
    if st.button("🛠️ Fix PostgreSQL Configuration"):
        try:
            # Fix postgresql.conf
            with open(postgresql_conf_path, 'r') as f:
                postgresql_content = f.read()
            
            # Replace listen_addresses
            if "listen_addresses = 'localhost'" in postgresql_content:
                postgresql_content = postgresql_content.replace("listen_addresses = 'localhost'", "listen_addresses = '*'")
            elif "#listen_addresses = 'localhost'" in postgresql_content:
                postgresql_content = postgresql_content.replace("#listen_addresses = 'localhost'", "listen_addresses = '*'")
            elif "listen_addresses = '*'" not in postgresql_content:
                # Add it if it doesn't exist
                postgresql_content += "\nlisten_addresses = '*'"
            
            # Ensure port is set
            if "port = 5432" not in postgresql_content:
                postgresql_content += "\nport = 5432"
            
            with open(postgresql_conf_path, 'w') as f:
                f.write(postgresql_content)
            
            st.success("✅ Fixed postgresql.conf")
            
            # Fix pg_hba.conf
            with open(pg_hba_conf_path, 'r') as f:
                pg_hba_content = f.read()
            
            # Add connection rules if they don't exist
            needed_rules = """
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
host    all             all             0.0.0.0/0               md5

# IPv6 local connections:
host    all             all             ::1/128                 md5
"""
            
            if "127.0.0.1/32" not in pg_hba_content:
                pg_hba_content += needed_rules
                with open(pg_hba_conf_path, 'w') as f:
                    f.write(pg_hba_content)
                st.success("✅ Added connection rules to pg_hba.conf")
            else:
                st.info("ℹ️ Connection rules already exist in pg_hba.conf")
            
            # Step 4: Restart PostgreSQL
            st.write("### Step 4: Restart PostgreSQL Service")
            
            try:
                # Stop service
                result = subprocess.run([
                    'net', 'stop', 'postgresql-x64-17'
                ], capture_output=True, text=True, shell=True)
                
                if "service was stopped" in result.stdout or "The requested service has already been stopped" in result.stderr:
                    st.info("✅ PostgreSQL service stopped")
                else:
                    st.warning(f"Stop message: {result.stderr}")
                
                # Start service
                result = subprocess.run([
                    'net', 'start', 'postgresql-x64-17'
                ], capture_output=True, text=True, shell=True)
                
                if "service was started" in result.stdout:
                    st.success("✅ PostgreSQL service started successfully!")
                else:
                    st.error(f"Start error: {result.stderr}")
                
            except Exception as e:
                st.error(f"Error restarting service: {e}")
            
            # Step 5: Test connection
            st.write("### Step 5: Test Connection")
            
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host="localhost",
                    database="postgres",
                    user="postgres",
                    password="",
                    port=5432,
                    connect_timeout=10
                )
                
                st.success("🎉 SUCCESS! PostgreSQL is now accepting connections!")
                
                # Create our database
                conn.autocommit = True
                cursor = conn.cursor()
                
                # Check if database exists
                cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
                databases = [db[0] for db in cursor.fetchall()]
                
                if 'mnch_training_tracker' not in databases:
                    cursor.execute("CREATE DATABASE mnch_training_tracker;")
                    st.success("✅ Created mnch_training_tracker database!")
                else:
                    st.info("ℹ️ mnch_training_tracker database already exists")
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                st.error(f"❌ Connection test failed: {e}")
                st.info("We may need to check the PostgreSQL logs for more details.")
                
        except Exception as e:
            st.error(f"❌ Error during configuration: {e}")
    
    # Show PostgreSQL logs for debugging
    st.write("### PostgreSQL Logs (for debugging)")
    log_dir = r"C:\Program Files\PostgreSQL\17\data\log"
    if os.path.exists(log_dir):
        log_files = os.listdir(log_dir)
        if log_files:
            latest_log = os.path.join(log_dir, sorted(log_files)[-1])
            try:
                with open(latest_log, 'r') as f:
                    log_content = f.read()
                st.text_area("Latest log file content:", log_content[-2000:], height=200)
            except:
                st.info("Could not read log file")
        else:
            st.info("No log files found")
    else:
        st.info("Log directory not found")

if __name__ == "__main__":
    main()
