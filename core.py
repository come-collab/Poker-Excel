# core.py
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import streamlit as st
import hashlib
import json

class User:
    def __init__(self, username: str, is_admin: bool = False):
        self.username = username
        self.is_admin = is_admin
        self.is_authenticated = False
    
    def authenticate(self, password: str) -> bool:
        # Simple password hashing - in production use proper password hashing
        users = json.load(open('users.json'))
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if (self.username in users and 
            users[self.username]['password'] == hashed_password and 
            users[self.username]['is_admin'] == self.is_admin):
            self.is_authenticated = True
            return True
        return False

class ExcelManager:
    def __init__(self, main_file: str, tournament_file: str):
        self.main_file = Path(main_file)
        self.tournament_file = Path(tournament_file)
        
    def load_main_data(self) -> pd.DataFrame:
        return pd.read_excel(self.main_file)
    
    def load_tournament_data(self) -> pd.DataFrame:
        return pd.read_excel(self.tournament_file)
    
    def save_main_data(self, df: pd.DataFrame) -> None:
        self.backup_files()
        df.to_excel(self.main_file, index=False)
    
    def save_tournament_data(self, df: pd.DataFrame) -> None:
        self.backup_files()
        df.to_excel(self.tournament_file, index=False)
    
    def backup_files(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        for file in [self.main_file, self.tournament_file]:
            if file.exists():
                backup_name = backup_dir / f"{file.stem}_{timestamp}{file.suffix}"
                pd.read_excel(file).to_excel(backup_name, index=False)
class Tournament:
    def __init__(self, name: str, num_players: int, participants: list, bounties: list, 
                 stack_size: int, comment: str):
        self.name = name
        self.num_players = num_players
        self.participants = participants
        self.bounties = bounties
        self.stack_size = stack_size
        self.comment = comment
        self.date_created = datetime.now()
        self.history = []
        
    def add_history_entry(self, action: str, details: str) -> None:
        """Add an entry to tournament history"""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        })
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'num_players': self.num_players,
            'participants': self.participants,
            'bounties': self.bounties,
            'stack_size': self.stack_size,
            'comment': self.comment,
            'date_created': self.date_created.isoformat(),
            'history': self.history
        }
class TournamentManager:
    def __init__(self, tournaments_file: str = 'tournaments.json'):
        self.tournaments_file = Path(tournaments_file)
        self.tournaments = self.load_tournaments()
    
    def load_tournaments(self) -> Dict:
        """Load tournaments from JSON file"""
        if self.tournaments_file.exists():
            try:
                with open(self.tournaments_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def save_tournaments(self) -> None:
        """Save tournaments to JSON file"""
        with open(self.tournaments_file, 'w') as f:
            json.dump(self.tournaments, f, indent=4)
    
    def get_tournaments(self) -> Dict:
        """Get all tournaments"""
        return self.tournaments
    
    def get_tournament(self, name: str) -> Optional[Dict]:
        """Get specific tournament by name"""
        return self.tournaments.get(name)
    
    def create_tournament_excel(self, tournament_name: str, num_players: int) -> None:
        """Create initial tournament Excel file with required columns"""
        df = pd.DataFrame(columns=['Rank', 'Player', 'Elimination Time', 'Eliminated By'])
        df['Rank'] = range(num_players, 0, -1)  # Reverse order for eliminations
        excel_path = f"tournament_{tournament_name}.xlsx"
        df.to_excel(excel_path, index=False)
    
    def create_tournament(self, name: str, num_players: int, participants: list, 
                         bounties: list, stack_size: int, comment: str) -> None:
        """Create a new tournament"""
        if name in self.tournaments:
            raise ValueError(f"Tournament {name} already exists")
        
        tournament_data = {
            'name': name,
            'num_players': num_players,
            'participants': participants,
            'bounties': bounties,
            'stack_size': stack_size,
            'comment': comment,
            'date_created': datetime.now().isoformat(),
            'history': []
        }
        
        self.tournaments[name] = tournament_data
        self.save_tournaments()
        
        # Create initial tournament Excel file
        self.create_tournament_excel(name, num_players)
    
    def update_tournament_history(self, name: str, action: str, details: str) -> None:
        """Update tournament history"""
        if name not in self.tournaments:
            raise ValueError(f"Tournament {name} not found")
            
        if 'history' not in self.tournaments[name]:
            self.tournaments[name]['history'] = []
            
        self.tournaments[name]['history'].append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        })
        self.save_tournaments()
    
    def update_tournament_elimination(self, tournament_name: str, player: str, 
                                    elimination_time: str, eliminated_by: str) -> None:
        """Update tournament Excel with elimination information"""
        excel_path = f"tournament_{tournament_name}.xlsx"
        
        try:
            df = pd.read_excel(excel_path)
            
            # Find the first empty row (based on Player column) and update it
            empty_row = df['Player'].isna()
            if empty_row.any():
                idx = empty_row.idxmax()
                df.loc[idx, 'Player'] = player
                df.loc[idx, 'Elimination Time'] = elimination_time
                df.loc[idx, 'Eliminated By'] = eliminated_by
                
                # Save updates
                df.to_excel(excel_path, index=False)
            else:
                raise ValueError("No empty slots available for elimination")
                
        except Exception as e:
            raise Exception(f"Error updating tournament elimination: {str(e)}")