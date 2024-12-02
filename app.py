import streamlit as st
from core import User, ExcelManager
import json

def init_session_state():
    """Initialize session state variables if they don't exist"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

def login_page():
    """Display the login interface"""
    st.title("Poker Tournament Manager")
    
    # Create columns for centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            # Check if username exists in users.json to determine admin status
            with open('users.json', 'r') as f:
                users = json.load(f)
            
            if username in users:
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
                st.error("Invalid credentials")

def admin_view():
    """Display the admin interface"""
    st.title(f"Welcome Admin: {st.session_state.user.username}")
    
    # Add logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.authenticated = False
        st.rerun()
    
    st.header("Admin Dashboard")
    
    # Create tabs for different admin functionalities
    tab1, tab2 = st.tabs(["User Management", "Tournament Management"])
    
    with tab1:
        st.subheader("User Management")
        # Display current users
        with open('users.json', 'r') as f:
            users = json.load(f)
        st.json(users)
        
    with tab2:
        st.subheader("Tournament Management")
        st.write("Tournament management interface will be implemented here")

def user_view():
    """Display the regular user interface"""
    st.title(f"Welcome User: {st.session_state.user.username}")
    
    # Add logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.authenticated = False
        st.rerun()
    
    st.header("Tournament View")
    st.write("Tournament viewing interface will be implemented here")

def main():
    # Initialize session state
    init_session_state()
    
    # Configure page
    st.set_page_config(
        page_title="Poker Tournament Manager",
        page_icon="🎰",
        layout="wide"
    )
    
    # Display appropriate view based on authentication status
    if not st.session_state.authenticated:
        login_page()
    else:
        if st.session_state.user.is_admin:
            admin_view()
        else:
            user_view()

if __name__ == "__main__":
    main()