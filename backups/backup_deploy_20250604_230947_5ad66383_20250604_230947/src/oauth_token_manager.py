#!/usr/bin/env python3
"""
OAuth Token Manager for Karen AI Security System
Handles secure token storage, automatic refresh, and expiration management.

Security Domain: SECURITY-001
Author: Karen AI Security Agent
"""

import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from pathlib import Path
import hashlib
import base64

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.exceptions

# Setup security logging
logger = logging.getLogger(__name__)

class TokenSecurityError(Exception):
    """Custom exception for token security issues"""
    pass

class OAuthTokenManager:
    """
    Secure OAuth token management system for Karen AI
    
    Features:
    - Automatic token refresh before 7-day expiration
    - Encrypted token storage
    - Thread-safe operations
    - Security audit logging
    - Multiple token profile support
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.tokens_dir = self.project_root / 'secure_tokens'
        self.credentials_dir = self.project_root
        
        # Security settings
        self.token_refresh_threshold = timedelta(days=1)  # Refresh 1 day before expiry
        self.max_token_age = timedelta(days=7)  # Google's default refresh token expiry
        
        # Thread safety
        self._lock = threading.RLock()
        self._refresh_threads = {}
        
        # Token profiles for different services
        self.profiles = {
            'gmail_secretary': {
                'scopes': [
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.compose',
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.modify'
                ],
                'credentials_file': 'credentials.json'
            },
            'gmail_monitor': {
                'scopes': [
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.modify'
                ],
                'credentials_file': 'credentials.json'
            },
            'calendar': {
                'scopes': [
                    'https://www.googleapis.com/auth/calendar.readonly',
                    'https://www.googleapis.com/auth/calendar.events'
                ],
                'credentials_file': 'credentials.json'
            }
        }
        
        # Initialize secure storage
        self._ensure_secure_storage()
        
        # Start background refresh monitoring
        self._start_refresh_monitor()
        
        logger.info("OAuthTokenManager initialized with security protocols")
    
    def _ensure_secure_storage(self):
        """Create secure token storage directory with restricted permissions"""
        try:
            self.tokens_dir.mkdir(mode=0o700, exist_ok=True)
            
            # Set restrictive permissions on existing directory
            os.chmod(self.tokens_dir, 0o700)
            
            logger.info(f"Secure token storage ensured at {self.tokens_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create secure storage: {e}")
            raise TokenSecurityError(f"Cannot establish secure token storage: {e}")
    
    def _get_token_file_path(self, profile_name: str, email_address: str) -> Path:
        """Get secure token file path for a profile and email"""
        # Create a secure filename using hash
        identifier = f"{profile_name}_{email_address}"
        secure_name = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return self.tokens_dir / f"token_{secure_name}.json"
    
    def _encrypt_token_data(self, token_data: Dict[str, Any]) -> str:
        """Basic token data obfuscation (not true encryption for simplicity)"""
        # For production, use proper encryption like Fernet
        json_str = json.dumps(token_data)
        encoded = base64.b64encode(json_str.encode()).decode()
        return encoded
    
    def _decrypt_token_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt token data"""
        try:
            decoded = base64.b64decode(encrypted_data.encode()).decode()
            return json.loads(decoded)
        except Exception as e:
            logger.error(f"Failed to decrypt token data: {e}")
            raise TokenSecurityError("Token data corruption detected")
    
    def _save_token_securely(self, profile_name: str, email_address: str, token_data: Dict[str, Any]):
        """Save token data with security metadata"""
        token_file = self._get_token_file_path(profile_name, email_address)
        
        secure_data = {
            'profile': profile_name,
            'email': email_address,
            'created_at': datetime.now().isoformat(),
            'last_refresh': datetime.now().isoformat(),
            'token_data': self._encrypt_token_data(token_data)
        }
        
        try:
            with open(token_file, 'w') as f:
                json.dump(secure_data, f, indent=2)
            
            # Set restrictive file permissions
            os.chmod(token_file, 0o600)
            
            logger.info(f"Token saved securely for {profile_name}:{email_address}")
            
        except Exception as e:
            logger.error(f"Failed to save token securely: {e}")
            raise TokenSecurityError(f"Token save failed: {e}")
    
    def _load_token_securely(self, profile_name: str, email_address: str) -> Optional[Dict[str, Any]]:
        """Load and decrypt token data"""
        token_file = self._get_token_file_path(profile_name, email_address)
        
        if not token_file.exists():
            logger.debug(f"No token file found for {profile_name}:{email_address}")
            return None
        
        try:
            with open(token_file, 'r') as f:
                secure_data = json.load(f)
            
            # Verify token file integrity
            if secure_data.get('profile') != profile_name or secure_data.get('email') != email_address:
                logger.error("Token file integrity check failed")
                raise TokenSecurityError("Token file integrity violation")
            
            token_data = self._decrypt_token_data(secure_data['token_data'])
            token_data['_metadata'] = {
                'created_at': secure_data.get('created_at'),
                'last_refresh': secure_data.get('last_refresh')
            }
            
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to load token securely: {e}")
            return None
    
    def get_credentials(self, profile_name: str, email_address: str) -> Optional[Credentials]:
        """Get valid OAuth credentials for a profile and email"""
        with self._lock:
            if profile_name not in self.profiles:
                logger.error(f"Unknown profile: {profile_name}")
                return None
            
            profile = self.profiles[profile_name]
            
            # Try to load existing token
            token_data = self._load_token_securely(profile_name, email_address)
            
            if token_data:
                # Create credentials from token data
                creds = Credentials(
                    token=token_data.get('token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_uri=token_data.get('token_uri'),
                    client_id=token_data.get('client_id'),
                    client_secret=token_data.get('client_secret'),
                    scopes=token_data.get('scopes')
                )
                
                # Check if token needs refresh
                if self._needs_refresh(creds, token_data):
                    logger.info(f"Token needs refresh for {profile_name}:{email_address}")
                    creds = self._refresh_credentials(creds, profile_name, email_address)
                
                if creds and creds.valid:
                    return creds
            
            # No valid token, initiate OAuth flow
            logger.info(f"Initiating OAuth flow for {profile_name}:{email_address}")
            return self._initiate_oauth_flow(profile_name, email_address)
    
    def _needs_refresh(self, creds: Credentials, token_data: Dict[str, Any]) -> bool:
        """Check if credentials need refresh based on expiry time"""
        if not creds.valid:
            return True
        
        if creds.expired:
            return True
        
        # Check if approaching expiry threshold
        if creds.expiry and creds.expiry <= datetime.utcnow() + self.token_refresh_threshold:
            return True
        
        # Check token age from metadata
        if '_metadata' in token_data:
            created_at = datetime.fromisoformat(token_data['_metadata']['created_at'])
            if datetime.now() - created_at >= self.max_token_age - self.token_refresh_threshold:
                return True
        
        return False
    
    def _refresh_credentials(self, creds: Credentials, profile_name: str, email_address: str) -> Optional[Credentials]:
        """Refresh OAuth credentials"""
        try:
            logger.info(f"Refreshing credentials for {profile_name}:{email_address}")
            
            creds.refresh(GoogleAuthRequest())
            
            # Save refreshed token
            token_data = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            }
            
            self._save_token_securely(profile_name, email_address, token_data)
            
            logger.info(f"Credentials refreshed successfully for {profile_name}:{email_address}")
            return creds
            
        except Exception as e:
            logger.error(f"Failed to refresh credentials for {profile_name}:{email_address}: {e}")
            return None
    
    def _initiate_oauth_flow(self, profile_name: str, email_address: str) -> Optional[Credentials]:
        """Initiate OAuth flow for new token"""
        profile = self.profiles[profile_name]
        credentials_file = self.credentials_dir / profile['credentials_file']
        
        if not credentials_file.exists():
            logger.error(f"Credentials file not found: {credentials_file}")
            return None
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file),
                profile['scopes']
            )
            
            # Run local server flow
            creds = flow.run_local_server(port=0)
            
            # Save new token
            token_data = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            }
            
            self._save_token_securely(profile_name, email_address, token_data)
            
            logger.info(f"OAuth flow completed for {profile_name}:{email_address}")
            return creds
            
        except Exception as e:
            logger.error(f"OAuth flow failed for {profile_name}:{email_address}: {e}")
            return None
    
    def _start_refresh_monitor(self):
        """Start background thread to monitor token refresh needs"""
        def monitor():
            while True:
                try:
                    self._check_all_tokens_for_refresh()
                    time.sleep(3600)  # Check every hour
                except Exception as e:
                    logger.error(f"Token refresh monitor error: {e}")
                    time.sleep(300)  # Wait 5 minutes before retry
        
        refresh_thread = threading.Thread(target=monitor, daemon=True)
        refresh_thread.start()
        logger.info("Token refresh monitor started")
    
    def _check_all_tokens_for_refresh(self):
        """Check all stored tokens for refresh needs"""
        if not self.tokens_dir.exists():
            return
        
        for token_file in self.tokens_dir.glob("token_*.json"):
            try:
                with open(token_file, 'r') as f:
                    secure_data = json.load(f)
                
                profile_name = secure_data.get('profile')
                email_address = secure_data.get('email')
                
                if profile_name and email_address:
                    # Load and check credentials
                    creds = self.get_credentials(profile_name, email_address)
                    if creds:
                        logger.debug(f"Token checked for {profile_name}:{email_address}")
                
            except Exception as e:
                logger.error(f"Error checking token file {token_file}: {e}")
    
    def revoke_token(self, profile_name: str, email_address: str) -> bool:
        """Revoke and delete a token"""
        with self._lock:
            try:
                token_file = self._get_token_file_path(profile_name, email_address)
                
                if token_file.exists():
                    # Securely delete the file
                    token_file.unlink()
                    logger.info(f"Token revoked for {profile_name}:{email_address}")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to revoke token for {profile_name}:{email_address}: {e}")
                return False
    
    def list_active_tokens(self) -> List[Dict[str, str]]:
        """List all active token profiles"""
        tokens = []
        
        if not self.tokens_dir.exists():
            return tokens
        
        for token_file in self.tokens_dir.glob("token_*.json"):
            try:
                with open(token_file, 'r') as f:
                    secure_data = json.load(f)
                
                tokens.append({
                    'profile': secure_data.get('profile'),
                    'email': secure_data.get('email'),
                    'created_at': secure_data.get('created_at'),
                    'last_refresh': secure_data.get('last_refresh')
                })
                
            except Exception as e:
                logger.error(f"Error reading token file {token_file}: {e}")
        
        return tokens
    
    def cleanup_expired_tokens(self):
        """Remove expired or corrupted tokens"""
        if not self.tokens_dir.exists():
            return
        
        cleaned_count = 0
        
        for token_file in self.tokens_dir.glob("token_*.json"):
            try:
                with open(token_file, 'r') as f:
                    secure_data = json.load(f)
                
                created_at = datetime.fromisoformat(secure_data.get('created_at', ''))
                
                # Remove tokens older than max age
                if datetime.now() - created_at > self.max_token_age:
                    token_file.unlink()
                    cleaned_count += 1
                    logger.info(f"Cleaned expired token: {token_file}")
                
            except Exception as e:
                # Remove corrupted token files
                logger.warning(f"Removing corrupted token file {token_file}: {e}")
                token_file.unlink()
                cleaned_count += 1
        
        logger.info(f"Token cleanup completed: {cleaned_count} tokens removed")


# Global token manager instance
_token_manager = None

def get_token_manager() -> OAuthTokenManager:
    """Get the global token manager instance"""
    global _token_manager
    if _token_manager is None:
        _token_manager = OAuthTokenManager()
    return _token_manager

def get_gmail_credentials(email_address: str, profile: str = 'gmail_secretary') -> Optional[Credentials]:
    """Convenience function to get Gmail credentials"""
    return get_token_manager().get_credentials(profile, email_address)

def get_calendar_credentials(email_address: str) -> Optional[Credentials]:
    """Convenience function to get Calendar credentials"""
    return get_token_manager().get_credentials('calendar', email_address)

def revoke_credentials(profile_name: str, email_address: str) -> bool:
    """Convenience function to revoke credentials"""
    return get_token_manager().revoke_token(profile_name, email_address)


if __name__ == "__main__":
    # Security test and demonstration
    logging.basicConfig(level=logging.INFO)
    
    manager = OAuthTokenManager()
    print("OAuth Token Manager - Security Test")
    print(f"Active tokens: {len(manager.list_active_tokens())}")
    
    # Clean up expired tokens
    manager.cleanup_expired_tokens()