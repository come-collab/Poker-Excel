# app.py
import streamlit as st
from core import User, ExcelManager
import json
import hashlib
from typing import Dict
import pandas as pd
import io

def load_users() -> Dict:
    """Load users from JSON file"""
    with open('users.json', 'r') as f:
        return json.load(f)

def save_users(users: Dict) -> None:
    """Save users to JSON file"""
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

def load_tournament_data():
    """Load tournament data from Excel file"""
    try:
        excel_manager = ExcelManager("main_data.xlsx", "tournament_data.xlsx")
        return pd.read_excel("tournament_data.xlsx")
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"Error loading tournament data: {str(e)}")
        return None

def format_tournament_data(df):
    """Format the tournament data display"""
    if df is None:
        return None
        
    # Rename columns to match the French names
    column_mapping = {
        'Classement': 'Classement',
        'Joueurs': 'Joueurs',
        'Pts Classement': 'Pts Classement',
        'Bonus Kills': 'Bonus Kills',
        'Total des Pts': 'Total des Pts',
        'Moyenne': 'Moyenne',
        'Nb de Kill': 'Nb de Kill'
    }
    
    # Apply formatting
    df = df.rename(columns=column_mapping)
    
    # Format numeric columns
    numeric_columns = ['Pts Classement', 'Bonus Kills', 'Total des Pts', 'Nb de Kill']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: int(x) if x == int(x) else round(x, 1))
    
    # Format Moyenne column separately (always show 2 decimal places)
    if 'Moyenne' in df.columns:
        df['Moyenne'] = df['Moyenne'].round(2)
    
    # Style the dataframe
    return df.style.apply(lambda x: ['background-color: #FFD700' if i == 0 
                                   else 'background-color: #C0C0C0' if i == 1 
                                   else 'background-color: #CD7F32' if i == 2
                                   else '' for i in range(len(x))], axis=0)\
                  .format({
                      'Pts Classement': '{:.1f}',
                      'Bonus Kills': '{:.0f}',
                      'Total des Pts': '{:.1f}',
                      'Moyenne': '{:.2f}',
                      'Nb de Kill': '{:.0f}'
                  })

def display_tournament_data():
    """Display tournament data in a formatted table"""
    df = load_tournament_data()
    if df is not None:
        st.markdown("### Current Tournament Standings")
        formatted_df = format_tournament_data(df)
        st.dataframe(formatted_df, use_container_width=True)
    else:
        st.warning("No tournament data available")

def init_session_state():
    """Initialize session state variables if they don't exist"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

def login_page():
    """Display the login interface"""
    st.title("Poker Tournament Manager")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            users = load_users()
            
            if username in users and not users[username].get('suspended', False):
                is_admin = users[username]['is_admin']
                user = User(username, is_admin)
                
                if user.authenticate(password):
                    st.session_state.user = user
                    st.session_state.authenticated = True
                    st.success(f"Successfully logged in")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            else:
                if username in users and users[username].get('suspended', False):
                    st.error("This account has been suspended. Please contact an administrator.")
                else:
                    st.error("Invalid credentials")

def admin_view():
    """Display the admin interface"""
    st.title(f"Welcome Admin: {st.session_state.user.username}")
    
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.authenticated = False
        st.rerun()
    
    st.header("Admin Dashboard")
    
    tab1, tab2 = st.tabs(["User Management", "Tournament Management"])
    
    with tab1:
        st.subheader("User Management")
        
        # Create new user section
        st.markdown("### Create New User")
        with st.form("create_user"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            is_admin = st.checkbox("Admin Privileges")
            
            submit_button = st.form_submit_button("Create User")
            
            if submit_button:
                users = load_users()
                if new_username in users:
                    st.error("Username already exists!")
                elif not new_username or not new_password:
                    st.error("Username and password are required!")
                else:
                    users[new_username] = {
                        "password": hashlib.sha256(new_password.encode()).hexdigest(),
                        "is_admin": is_admin,
                        "suspended": False
                    }
                    save_users(users)
                    st.success(f"User {new_username} created successfully!")
        
        # User management section
        st.markdown("### Manage Existing Users")
        users = load_users()
        
        for username, user_data in users.items():
            if username != st.session_state.user.username:  # Prevent self-modification
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"Username: {username}")
                    st.write(f"Role: {'Admin' if user_data['is_admin'] else 'User'}")
                    st.write(f"Status: {'Suspended' if user_data.get('suspended', False) else 'Active'}")
                
                with col2:
                    if st.button(
                        "Suspend" if not user_data.get('suspended', False) else "Reactivate",
                        key=f"suspend_{username}"
                    ):
                        users[username]['suspended'] = not users[username].get('suspended', False)
                        save_users(users)
                        st.rerun()
                
                with col3:
                    if st.button("Delete", key=f"delete_{username}"):
                        del users[username]
                        save_users(users)
                        st.rerun()
                
                st.divider()
    
    with tab2:
        st.subheader("Tournament Management")
        
        # Display current tournament data
        display_tournament_data()
        
        # File upload section
        st.markdown("### Update Tournament Data")
        uploaded_file = st.file_uploader("Choose a tournament Excel file", type=['xlsx', 'xls'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                
                # Preview the uploaded data
                st.markdown("### Preview of New Data")
                formatted_preview = format_tournament_data(df)
                st.dataframe(formatted_preview, use_container_width=True)
                
                # Add update button
                if st.button("Update Tournament Data"):
                    excel_manager = ExcelManager("main_data.xlsx", "tournament_data.xlsx")
                    excel_manager.save_tournament_data(df)
                    st.success("Tournament data updated successfully!")
                    st.rerun()  # Refresh to show new data
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

def user_view():
    """Display the regular user interface"""
    st.title(f"Welcome {st.session_state.user.username}")
    
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.authenticated = False
        st.rerun()
    
    # Display tournament data for users
    display_tournament_data()
    
    # Add auto-refresh button
    if st.button("Refresh Data"):
        st.rerun()

def main():
    init_session_state()
    
    st.set_page_config(
        page_title="Poker Tournament Manager",
        page_icon="🎰",
        layout="wide"
    )
    
    if not st.session_state.authenticated:
        login_page()
    else:
        if st.session_state.user.is_admin:
            admin_view()
        else:
            user_view()

if __name__ == "__main__":
    main()
