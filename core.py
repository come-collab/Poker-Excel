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
