# app.py
import streamlit as st
from core import User, ExcelManager , Tournament , TournamentManager
import json
import hashlib
from typing import Dict
import pandas as pd
import io
from pathlib import Path
import datetime


def load_users() -> Dict:
    """Load users from JSON file"""
    with open('users.json', 'r') as f:
        return json.load(f)

def save_users(users: Dict) -> None:
    """Save users to JSON file"""
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

def load_tournament_data():
    """Load tournament data from Excel/CSV file"""
    try:
        excel_manager = ExcelManager("main_data.xlsx", "tournament_data.xlsx")
        if Path("tournament_data.xlsx").exists():
            return pd.read_excel("tournament_data.xlsx")
        elif Path("tournament_data.csv").exists():
            return pd.read_csv("tournament_data.csv")
        return None
    except Exception as e:
        st.error(f"Error loading tournament data: {str(e)}")
        return None

def format_tournament_data(df):
    """Format the tournament data display"""
    if df is None:
        return None
        
    # Select and rename columns in the desired order
    columns_mapping = {
        'Classement': 'Classement',
        'Joueurs': 'Joueurs',
        'Pts Classement': 'Pts Classement',
        'Bonus Kills': 'Bonus Kills',
        'Total des Pts': 'Total des Pts',
        'Moyenne': 'Moyenne',
        'Nb de Kill': 'Nb de Kill'
    }
    
    # Select only the columns we want in the specified order
    df = df[list(columns_mapping.keys())]
    
    # Apply formatting
    df = df.rename(columns=columns_mapping)
    
    # Format numeric columns
    numeric_columns = ['Pts Classement', 'Bonus Kills', 'Total des Pts', 'Nb de Kill']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: int(x) if x == int(x) else round(x, 1))
    
    # Format Moyenne column separately (always show 2 decimal places)
    if 'Moyenne' in df.columns:
        df['Moyenne'] = df['Moyenne'].round(2)
    
    # Style the dataframe with specific number formatting
    return df.style.apply(lambda x: ['background-color: #FFD700' if i == 0 
                                   else 'background-color: #C0C0C0' if i == 1 
                                   else 'background-color: #CD7F32' if i == 2
                                   else '' for i in range(len(x))], axis=0)\
                  .format({
                      'Classement': '{:.0f}',
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
    
    tab1, tab2, tab3, tab4 = st.tabs(["User Management", "General Ranking", "Tournament Management", "Active Tournament"])
    
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
        st.subheader("General Ranking Management")
        
        # Display current general ranking data
        df = load_tournament_data()
        if df is not None:
            st.markdown("### Current General Ranking")
            formatted_df = format_tournament_data(df)
            st.dataframe(formatted_df, use_container_width=True)
        else:
            st.warning("No general ranking data available")
        
        # File upload section for general ranking
        st.markdown("### Update General Ranking")
        uploaded_file = st.file_uploader("Choose a general ranking file", type=['xlsx', 'xls', 'csv'], key="general_ranking")
        
        if uploaded_file is not None:
            try:
                # Read the file based on its type
                file_extension = uploaded_file.name.split('.')[-1].lower()
                if file_extension in ['xlsx', 'xls']:
                    df = pd.read_excel(uploaded_file)
                elif file_extension == 'csv':
                    df = pd.read_csv(uploaded_file)
                
                # Preview the uploaded data
                st.markdown("### Preview of New General Ranking Data")
                formatted_preview = format_tournament_data(df)
                st.dataframe(formatted_preview, use_container_width=True)
                
                # Add update button
                if st.button("Update General Ranking"):
                    excel_manager = ExcelManager("main_data.xlsx", "tournament_data.xlsx")
                    excel_manager.save_tournament_data(df)
                    st.success("General ranking updated successfully!")
                    st.rerun()
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.error("Please ensure your file has the required columns")
    
    with tab3:
        st.subheader("Tournament Management")
        
        st.markdown("### Create New Tournament")

        # Put the number input and update button outside the form
        tournament_name = st.text_input("Tournament Name", key="tournament_name")
        col1, col2 = st.columns([2,1])
        with col1:
            num_players = st.number_input("Number of Players", min_value=2, value=8, key="num_players")

        with st.form("create_tournament"):
            # Basic tournament info
            stack_size = st.number_input("Starting Stack Size", min_value=100, value=10000, step=100)
            
            # Earnings section
            st.markdown("#### Tournament Earnings")
            earnings = {}
            col1, col2 = st.columns(2)
            
            with col1:
                earnings[1] = st.number_input("1st Place Earnings (€)", min_value=0, value=0, step=10)
                earnings[2] = st.number_input("2nd Place Earnings (€)", min_value=0, value=0, step=10)
                earnings[3] = st.number_input("3rd Place Earnings (€)", min_value=0, value=0, step=10)
            
            with col2:
                earnings[4] = st.number_input("4th Place Earnings (€)", min_value=0, value=0, step=10)
                earnings[5] = st.number_input("5th Place Earnings (€)", min_value=0, value=0, step=10)
                earnings[6] = st.number_input("6th Place Earnings (€)", min_value=0, value=0, step=10)
            
            total_earnings = sum(earnings.values())
            st.write(f"Total Prize Pool: €{total_earnings:,}")
            
            # Participants and Bounties section
            st.markdown("#### Participants & Bounties")
            
            # Initialize lists for participants and bounties
            participants = [""] * num_players
            bounties = []
            
            # Create a table-like layout with st.columns
            st.markdown("Enter participant names and check the box for players with bounties:")
            
            # Headers
            col1, col2, col3, col4 = st.columns([0.4, 0.1, 0.4, 0.1])
            with col1:
                st.markdown("**Player Name**")
            with col2:
                st.markdown("**Bounty**")
            with col3:
                st.markdown("**Player Name**")
            with col4:
                st.markdown("**Bounty**")
            
            # Create rows for participant inputs
            for i in range(0, num_players, 2):
                col1, col2, col3, col4 = st.columns([0.4, 0.1, 0.4, 0.1])
                
                # First participant in row
                with col1:
                    participants[i] = st.text_input("", key=f"participant_{i}", 
                                                placeholder=f"Participant {i+1}")
                with col2:
                    if st.checkbox("", key=f"bounty_{i}") and participants[i]:
                        bounties.append(participants[i])
                
                # Second participant in row (if exists)
                if i + 1 < num_players:
                    with col3:
                        participants[i+1] = st.text_input("", key=f"participant_{i+1}", 
                                                        placeholder=f"Participant {i+2}")
                    with col4:
                        if st.checkbox("", key=f"bounty_{i+1}") and participants[i+1]:
                            bounties.append(participants[i+1])
            
            # Comment section
            comment = st.text_area("Tournament Comments", height=100)
            
            # Remove empty strings from participants list before submission
            participants = [p for p in participants if p]
            
            submit_button = st.form_submit_button("Create Tournament")
            
            if submit_button:
                if len(participants) != num_players:
                    st.error("Please enter all participant names")
                elif len(set(participants)) != len(participants):
                    st.error("Duplicate participants found")
                elif not tournament_name:
                    st.error("Please enter a tournament name")
                elif total_earnings <= 0:
                    st.error("Please enter tournament earnings")
                else:
                    try:
                        tournament_manager = TournamentManager()
                        tournament = tournament_manager.create_tournament(
                            name=tournament_name,
                            num_players=num_players,
                            participants=participants,
                            bounties=bounties,
                            stack_size=stack_size,
                            comment=comment,
                            earnings=earnings
                        )
                        st.success(f"Tournament {tournament_name} created successfully!")
                        
                        # Clear session state after successful creation
                        for key in list(st.session_state.keys()):
                            if key.startswith('participant_') or key.startswith('bounty_'):
                                del st.session_state[key]
                        st.rerun()
                            
                    except ValueError as e:
                        st.error(str(e))
            
        # List existing tournaments
        st.markdown("### Existing Tournaments")
        tournament_manager = TournamentManager()
        tournaments = tournament_manager.get_tournaments()
        
        if tournaments:
            for name, data in tournaments.items():
                with st.expander(f"Tournament: {name}"):
                    # Basic tournament info
                    st.write(f"Number of Players: {data['num_players']}")
                    st.write(f"Starting Stack: {data['stack_size']:,}")
                    st.write(f"Created: {data['date_created']}")
                    
                    # Display earnings
                    st.markdown("#### Prize Pool")
                    earnings = data.get('earnings', {})
                    if earnings:
                        for place, amount in earnings.items():
                            if amount > 0:
                                st.write(f"{place}{'st' if place == 1 else 'nd' if place == 2 else 'rd' if place == 3 else 'th'} Place: €{amount:,}")
                        st.write(f"Total Prize Pool: €{sum(earnings.values()):,}")
                    
                    # Participants and Bounties
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### Participants")
                        for participant in data['participants']:
                            has_bounty = participant in data['bounties']
                            st.write(f"• {participant} {'🎯' if has_bounty else ''}")
                    
                    # Comment
                    if data['comment']:
                        st.markdown("#### Tournament Comments")
                        st.write(data['comment'])
                    
                    # Tournament history
                    if data['history']:
                        st.markdown("#### Tournament History")
                        for entry in data['history']:
                            st.write(f"{entry['timestamp']}: {entry['action']} - {entry['details']}")
        else:
            st.info("No tournaments created yet")
    with tab4:
        st.subheader("Active Tournament Management")
        
        # Select active tournament
        tournament_manager = TournamentManager()
        tournaments = tournament_manager.load_tournaments()
        tournament_names = list(tournaments.keys())
        
        if tournament_names:
            selected_tournament = st.selectbox("Select Tournament", tournament_names)
            
            if selected_tournament:
                tournament_data = tournaments[selected_tournament]
                
                # Display tournament info
                st.markdown("### Tournament Information")
                st.write(f"Number of Players: {tournament_data['num_players']}")
                st.write(f"Starting Stack: {tournament_data['stack_size']:,}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### Participants")
                    for i, participant in enumerate(tournament_data['participants'], 1):
                        st.write(f"{i}. {participant}")
                
                with col2:
                    st.markdown("#### Bounties")
                    if tournament_data['bounties']:
                        for bounty in tournament_data['bounties']:
                            st.write(f"• {bounty}")
                    else:
                        st.write("No bounties in this tournament")
                
                # Display current tournament eliminations
                st.markdown("### Current Tournament Status")
                try:
                    df = pd.read_excel(f"tournament_{selected_tournament}.xlsx")
                    st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading tournament data: {str(e)}")
                
                # Form for recording eliminations
                st.markdown("### Record Elimination")
                with st.form("elimination_form"):
                    # Get currently eliminated players
                    try:
                        eliminated_players = set(df['Player'].dropna().values)
                    except:
                        eliminated_players = set()
                    
                    # Create list of remaining players (not yet eliminated)
                    remaining_players = [p for p in tournament_data['participants'] 
                                      if p not in eliminated_players]
                    
                    # Only show remaining players in elimination dropdown
                    eliminated_player = st.selectbox(
                        "Eliminated Player",
                        remaining_players if remaining_players else ["No players available"],
                        key="eliminated_player"
                    )
                    
                    # Time selection with current time as default
                    current_time = datetime.datetime.now().time()
                    elimination_time = st.time_input(
                        "Elimination Time",
                        value=current_time,
                        key="elimination_time"
                    )
                    
                    # Killer selection (from all players including eliminated)
                    # But mark eliminated players with "(Eliminated)" suffix
                    killer_options = [
                        f"{p}{' (Eliminated)' if p in eliminated_players else ''}"
                        for p in tournament_data['participants']
                    ]
                    killer_display = st.selectbox(
                        "Eliminated By",
                        killer_options,
                        key="killer"
                    )
                    # Remove "(Eliminated)" suffix for database storage
                    killer = killer_display.split(" (Eliminated)")[0]
                    
                    submit_button = st.form_submit_button("Record Elimination")
                    
                    if submit_button and eliminated_player != "No players available":
                        try:
                            tournament_manager.update_tournament_elimination(
                                selected_tournament,
                                eliminated_player,
                                elimination_time.strftime("%H:%M"),
                                killer
                            )
                            
                            # Log the elimination in tournament history
                            tournament_manager.update_tournament_history(
                                selected_tournament,
                                "Elimination",
                                f"{eliminated_player} eliminated by {killer} at {elimination_time.strftime('%H:%M')}"
                            )
                            
                            st.success(f"Recorded elimination of {eliminated_player}")
                            # Clear the form selections
                            if 'eliminated_player' in st.session_state:
                                del st.session_state.eliminated_player
                            if 'killer' in st.session_state:
                                del st.session_state.killer
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error recording elimination: {str(e)}")
                            
                # Display remaining players count
                st.info(f"Remaining players: {len(remaining_players)}")
                
        else:
            st.warning("No tournaments available. Please create a tournament first.")

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
