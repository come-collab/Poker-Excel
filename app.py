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
from PIL import Image



# Load player names from data.csv at the start
def get_club_members():
    try:
        df = pd.read_csv('data.csv')
        return df['Joueurs'].tolist()
    except Exception as e:
        st.error(f"Error loading club members: {str(e)}")
        return []

def display_logo():
    """Display the logo at the top of the page"""
    try:
        logo = Image.open("logo_bdf.png")
        # Calculate one-third of the page width
        page_width = 1000  # Typical page width in pixels
        logo_width = page_width // 6  # Divide by 6 to account for the column layout
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo, width=logo_width)
    except FileNotFoundError:
        st.error("Logo file 'logo_bdf.png' not found. Please ensure it's in the application directory.")



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
        st.markdown("### Classement actuel : ")
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
    display_logo()
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
    display_logo()
    st.title(f"Bienvenue Didier: {st.session_state.user.username}")
    
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.authenticated = False
        st.rerun()
    
    st.header("Tableau de bord Administrateur")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Gestion des utilisateurs", "Classement général ", "Gestion des tournois", "Tournois en cours"])
    
    with tab1:
        st.subheader("Gestion des utilisateurs")
        
        # Create new user section
        st.markdown("### Créer un utilisateur")
        with st.form("create_user"):
            new_username = st.text_input("Nouvel utilisateur")
            new_password = st.text_input("Nouveau mot de passe", type="password")
            is_admin = st.checkbox("Privilèges Administrateur")
            
            submit_button = st.form_submit_button("Création Utilisateur")
            
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
        st.markdown("### Gestion des utilisateurs existants")
        users = load_users()
        
        for username, user_data in users.items():
            if username != st.session_state.user.username:  # Prevent self-modification
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"Utilisateur: {username}")
                    st.write(f"Role: {'Admin' if user_data['is_admin'] else 'User'}")
                    st.write(f"Status: {'Suspendu' if user_data.get('suspended', False) else 'Active'}")
                
                with col2:
                    if st.button(
                        "Suspendre" if not user_data.get('suspended', False) else "Ré Activer",
                        key=f"suspend_{username}"
                    ):
                        users[username]['suspended'] = not users[username].get('suspended', False)
                        save_users(users)
                        st.rerun()
                
                with col3:
                    if st.button("Supprimer", key=f"delete_{username}"):
                        del users[username]
                        save_users(users)
                        st.rerun()
                
                st.divider()
    
    with tab2:
        st.subheader("Gestion du classement géneral")
        
        # Display current general ranking data
        df = load_tournament_data()
        if df is not None:
            st.markdown("### Classement actuel")
            formatted_df = format_tournament_data(df)
            st.dataframe(formatted_df, use_container_width=True)
        else:
            st.warning("Pas de classement actuel")
        
        # File upload section for general ranking
        st.markdown("### Mettre à jour le classement général")
        uploaded_file = st.file_uploader("Choisir un fichier de classement général", type=['xlsx', 'xls', 'csv'], key="general_ranking")
        
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
        st.subheader("Gestion d'un tournois")
        
        st.markdown("### Créer un nouveau tournoi")

        # Tournament name and player count
        tournament_name = st.text_input("Nom du tournoi", key="tournament_name")
        col1, col2 = st.columns([2,1])
        with col1:
            num_players = st.number_input("Nombre de joueurs", min_value=2, value=8, key="num_players")

        with st.form("create_tournament"):
            # Basic tournament info
            stack_size = st.number_input("Stack de départ", min_value=100, value=10000, step=100)
            
            # Earnings section
            st.markdown("#### Gains Tournoi")
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
            
            club_members = get_club_members()
            
            # Initialize lists for participants and bounties
            participants = [""] * num_players
            bounties = []
            
            # Create headers for the table
            col1, col2, col3, col4 = st.columns([0.4, 0.1, 0.4, 0.1])
            with col1:
                st.markdown("**Nom du joueur**")
            with col2:
                st.markdown("**Bounty**")
            with col3:
                st.markdown("**Nom du joueur**")
            with col4:
                st.markdown("**Bounty**")
            
            # Create rows for participant inputs
            for i in range(0, num_players, 2):
                col1, col2, col3, col4 = st.columns([0.4, 0.1, 0.4, 0.1])
                
                # First participant in row
                with col1:
                    participants[i] = st.selectbox("", 
                                                options=[""] + club_members,
                                                key=f"participant_{i}",
                                                placeholder=f"Participant {i+1}")
                with col2:
                    if participants[i] and st.checkbox("", key=f"bounty_{i}"):
                        bounties.append(participants[i])
                
                # Second participant in row (if exists)
                if i + 1 < num_players:
                    with col3:
                        participants[i+1] = st.selectbox("", 
                                                    options=[""] + club_members,
                                                    key=f"participant_{i+1}",
                                                    placeholder=f"Participant {i+2}")
                    with col4:
                        if participants[i+1] and st.checkbox("", key=f"bounty_{i+1}"):
                            bounties.append(participants[i+1])
            
            # Comment section
            comment = st.text_area("Commentaire tournois", height=100)
            
            # Remove empty strings from participants list before submission
            participants = [p for p in participants if p]
            
            submit_button = st.form_submit_button("Créer un tournoi")
            
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
                        tournament_manager.create_tournament(
                            name=tournament_name,
                            num_players=num_players,
                            participants=participants,
                            bounties=bounties,
                            stack_size=stack_size,
                            comment=comment,
                            earnings=earnings
                        )
                        st.success(f"Tournoi {tournament_name} créé avec succès")
                        
                        # Clear session state after successful creation
                        for key in list(st.session_state.keys()):
                            if key.startswith('participant_') or key.startswith('bounty_'):
                                del st.session_state[key]
                        st.rerun()
                            
                    except ValueError as e:
                        st.error(str(e))
            
        # List existing tournaments
        st.markdown("### Tournois existants : ")
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
        
        st.subheader("Gestion du tournoi en cours")
        
        # Select active tournament
        tournament_manager = TournamentManager()
        tournaments = tournament_manager.load_tournaments()
        tournament_names = list(tournaments.keys())
        
        if tournament_names:
            selected_tournament = st.selectbox("Choisir un tournoi ", tournament_names)
            
            if selected_tournament:
                # Get tournament data
                tournament_data = tournaments[selected_tournament]
                
                # Display tournament info
                st.markdown("### Information tournois ")
                st.write(f"Nombres de joueurs: {tournament_data['num_players']}")
                st.write(f"Stack de départ: {tournament_data['stack_size']:,}")
                
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
                        st.write("Pas de bounties pour ce tournoi ")
                
                # Display current tournament eliminations
                st.markdown("### Statut du tournoi en cours")
                try:
                    df = pd.read_excel(f"tournament_{selected_tournament}.xlsx")
                    st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Erreur lors de la création du tournoi: {str(e)}")
                    df = pd.DataFrame()  # Create empty DataFrame if file doesn't exist
                
                # Form for recording eliminations
                st.markdown("### Eliminations")
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
                        "Joueur éliminé",
                        remaining_players if remaining_players else ["No players available"],
                        key="eliminated_player"
                    )
                    
                    # Create two columns for hour and minute inputs
                    time_col1, time_col2 = st.columns(2)
                    
                    # Current time as default values
                    current_time = datetime.datetime.now().time()
                    
                    with time_col1:
                        hour = st.number_input(
                            "Hour",
                            min_value=0,
                            max_value=23,
                            value=current_time.hour,
                            key="elimination_hour"
                        )
                    
                    with time_col2:
                        minute = st.number_input(
                            "Minute",
                            min_value=0,
                            max_value=59,
                            value=current_time.minute,
                            key="elimination_minute"
                        )
                    
                    # Combine hour and minute into a time object
                    elimination_time = datetime.time(hour=int(hour), minute=int(minute))
                    
                    # Killer selection (from all players including eliminated)
                    killer_options = [
                        f"{p}{' (Eliminated)' if p in eliminated_players else ''}"
                        for p in tournament_data['participants']
                    ]
                    killer_display = st.selectbox(
                        "Eliminé par : ",
                        killer_options,
                        key="killer"
                    )
                    # Remove "(Eliminated)" suffix for database storage
                    killer = killer_display.split(" (Eliminated)")[0]
                    
                    submit_button = st.form_submit_button("Enregistrement élimination")
                    
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
                            
                            st.success(f"Elimination enregistré de : {eliminated_player}")
                            # Clear the form selections
                            if 'eliminated_player' in st.session_state:
                                del st.session_state.eliminated_player
                            if 'killer' in st.session_state:
                                del st.session_state.killer
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error recording elimination: {str(e)}")
                            
                # Display remaining players count
                st.info(f"Joueurs restants : {len(remaining_players)}")
                
        else:
            st.warning("Pas de tournoi en cours. Créer un tournoi en premier lieu")

def user_view():
    """Display the regular user interface"""
    display_logo()
    st.title(f"Bienvenue : {st.session_state.user.username}")
    
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.authenticated = False
        st.rerun()
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Classement géneral", "Tournois en cours"])
    
    with tab1:
        st.header("Classement géneral BDF : ")
        display_tournament_data()
    
    with tab2:
        st.header("Information sur la bdf en cours : ")
        
        # Get available tournaments
        tournament_manager = TournamentManager()
        tournaments = tournament_manager.load_tournaments()
        tournament_names = list(tournaments.keys())
        
        if tournament_names:
            # Tournament selection
            selected_tournament = st.selectbox(
                "Select Tournament to View",
                tournament_names,
                key="user_tournament_select"
            )
            
            if selected_tournament:
                # Get tournament data
                tournament_data = tournaments[selected_tournament]
                
                # Display tournament info in columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.subheader("Tournament Details")
                    st.write(f"Players: {tournament_data['num_players']}")
                    st.write(f"Starting Stack: {tournament_data['stack_size']:,}")
                    
                with col2:
                    st.subheader("Prize Pool")
                    earnings = tournament_data.get('earnings', {})
                    if earnings:
                        total_prize = sum(earnings.values())
                        st.write(f"Total Prize Pool: €{total_prize:,}")
                        for place, amount in earnings.items():
                            if amount > 0:
                                suffix = 'st' if place == 1 else 'nd' if place == 2 else 'rd' if place == 3 else 'th'
                                st.write(f"{place}{suffix} Place: €{amount:,}")
                
                with col3:
                    st.subheader("Bounties")
                    if tournament_data['bounties']:
                        for bounty in tournament_data['bounties']:
                            st.write(f"🎯 {bounty}")
                    else:
                        st.write("No bounties in this tournament")
                
                # Display current tournament status
                st.subheader("Current Tournament Progress")
                try:
                    df = pd.read_excel(f"tournament_{selected_tournament}.xlsx")
                    
                    # Calculate remaining players
                    eliminated_players = set(df['Player'].dropna().values)
                    remaining_players = [p for p in tournament_data['participants'] 
                                      if p not in eliminated_players]
                    
                    # Display remaining players
                    st.info(f"Remaining Players ({len(remaining_players)}): {', '.join(remaining_players)}")
                    
                    # Format and display elimination table
                    if not df.empty:
                        df = df.fillna('')
                        styled_df = df.style.apply(lambda x: ['background-color: #FFD700' if i == 0 
                                                            else 'background-color: #C0C0C0' if i == 1 
                                                            else 'background-color: #CD7F32' if i == 2
                                                            else '' for i in range(len(x))], axis=0)
                        st.dataframe(styled_df, use_container_width=True)
                    
                except Exception as e:
                    st.error("Unable to load tournament data. The tournament might not have started yet.")
                
                # Add auto-refresh button
                if st.button("Refresh Tournament Data", key="refresh_tournament"):
                    st.rerun()
        else:
            st.info("Pas de tournois en cours.")
    
    # Add general refresh button at the bottom
    if st.button("Rafraichir les données"):
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
