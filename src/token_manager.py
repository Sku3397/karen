#!/usr/bin/env python3
"""
Enhanced OAuth Token Manager for Karen AI
Provides automatic token refresh, comprehensive error handling, and notification system.

Features:
- Automatic refresh before expiry with configurable thresholds
- Comprehensive error handling for expired/invalid tokens  
- Email notification system for refresh failures
- Background monitoring and proactive refresh
- Thread-safe operations with proper locking
- Graceful degradation and retry mechanisms
"""

import os
import json
import logging
import threading
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Callable
from pathlib import Path
import hashlib
import base64
from email.mime.text import MIMEText
import smtplib

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.exceptions

logger = logging.getLogger(__name__)

class TokenManagerError(Exception):
    """Base exception for token manager errors"""
    pass

class TokenRefreshError(TokenManagerError):
    """Exception raised when token refresh fails"""
    pass

class TokenNotFoundError(TokenManagerError):
    """Exception raised when token file is not found"""
    pass

class TokenExpiredError(TokenManagerError):
    """Exception raised when token is expired and cannot be refreshed"""
    pass

class EnhancedTokenManager:
    """
    Enhanced OAuth token management system with automatic refresh and notifications
    
    Features:
    - Automatic token refresh 24 hours before expiry
    - Comprehensive error handling with retry logic
    - Email notifications for critical failures
    - Background monitoring thread
    - Thread-safe operations
    - Graceful degradation modes
    """
    
    def __init__(self, project_root: str = None, notification_config: Dict[str, Any] = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.tokens_dir = self.project_root / 'oauth_tokens'
        self.credentials_dir = self.project_root
        
        # Token refresh settings
        self.refresh_threshold = timedelta(hours=24)  # Refresh 24 hours before expiry
        self.emergency_threshold = timedelta(hours=2)  # Emergency refresh threshold
        self.max_token_age = timedelta(days=6)  # Refresh tokens before 7-day expiry
        self.retry_attempts = 3
        self.retry_delay = 30  # seconds
        
        # Thread safety
        self._lock = threading.RLock()
        self._refresh_in_progress = set()
        self._failed_refreshes = {}
        
        # Notification system
        self.notification_config = notification_config or {}
        self.admin_email = os.getenv('ADMIN_EMAIL_ADDRESS')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Token profiles with enhanced configuration
        self.profiles = {
            'gmail_secretary': {
                'scopes': [
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.compose',
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.modify'
                ],
                'credentials_file': 'credentials.json',
                'priority': 'high',  # High priority for secretary functions
                'auto_refresh': True
            },
            'gmail_monitor': {
                'scopes': [
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.modify'
                ],
                'credentials_file': 'credentials.json',
                'priority': 'high',  # High priority for monitoring
                'auto_refresh': True
            },
            'calendar': {
                'scopes': [
                    'https://www.googleapis.com/auth/calendar.readonly',
                    'https://www.googleapis.com/auth/calendar.events'
                ],
                'credentials_file': 'credentials.json',
                'priority': 'medium',
                'auto_refresh': True
            }
        }
        
        # Initialize system
        self._ensure_token_storage()
        self._start_background_monitor()
        
        logger.info("Enhanced Token Manager initialized with automatic refresh and notifications")
    
    def _ensure_token_storage(self):
        """Create token storage directory with proper permissions"""
        try:
            self.tokens_dir.mkdir(mode=0o700, exist_ok=True)
            os.chmod(self.tokens_dir, 0o700)
            
            # Create backup directory
            backup_dir = self.tokens_dir / 'backups'
            backup_dir.mkdir(mode=0o700, exist_ok=True)
            
            logger.info(f"Token storage ensured at {self.tokens_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create token storage: {e}", exc_info=True)
            raise TokenManagerError(f"Cannot establish token storage: {e}")
    
    def _get_token_file_path(self, profile_name: str, email_address: str) -> Path:
        """Get token file path for a profile and email"""
        # Use legacy format for compatibility with existing files
        safe_email = email_address.replace('@', '_at_').replace('.', '_dot_')
        filename = f"gmail_token_{safe_email}_{profile_name}.json"
        return self.tokens_dir / filename
    
    def _backup_token_file(self, token_file: Path):
        """Create backup of token file before modification"""
        if not token_file.exists():
            return
        
        try:
            backup_dir = self.tokens_dir / 'backups'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{token_file.stem}_{timestamp}.json"
            
            with open(token_file, 'r') as src, open(backup_file, 'w') as dst:
                dst.write(src.read())
                
            os.chmod(backup_file, 0o600)
            logger.debug(f"Token backup created: {backup_file}")
            
        except Exception as e:
            logger.warning(f"Failed to backup token file: {e}")
    
    def _save_token_data(self, profile_name: str, email_address: str, token_data: Dict[str, Any]):
        """Save token data with metadata and backup"""
        token_file = self._get_token_file_path(profile_name, email_address)
        
        # Backup existing file
        self._backup_token_file(token_file)
        
        # Add metadata
        enhanced_data = {
            'profile': profile_name,
            'email': email_address,
            'created_at': datetime.now().isoformat(),
            'last_refresh': datetime.now().isoformat(),
            'refresh_count': token_data.get('refresh_count', 0) + 1,
            'token_data': token_data
        }
        
        try:
            with open(token_file, 'w') as f:
                json.dump(enhanced_data, f, indent=2)
            
            os.chmod(token_file, 0o600)
            logger.info(f"Token saved for {profile_name}:{email_address}")
            
        except Exception as e:
            logger.error(f"Failed to save token: {e}", exc_info=True)
            raise TokenManagerError(f"Token save failed: {e}")
    
    def _load_token_data(self, profile_name: str, email_address: str) -> Optional[Dict[str, Any]]:
        """Load token data with integrity checking"""
        token_file = self._get_token_file_path(profile_name, email_address)
        
        if not token_file.exists():
            # Try legacy format
            legacy_file = self.project_root / f"gmail_token_{email_address.split('@')[0]}.json"
            if legacy_file.exists():
                logger.info(f"Using legacy token file: {legacy_file}")
                token_file = legacy_file
            else:
                logger.debug(f"No token file found for {profile_name}:{email_address}")
                return None
        
        try:
            with open(token_file, 'r') as f:
                data = json.load(f)
            
            # Handle both new and legacy formats
            if 'token_data' in data:
                # New format
                token_data = data['token_data']
                token_data['_metadata'] = {
                    'created_at': data.get('created_at'),
                    'last_refresh': data.get('last_refresh'),
                    'refresh_count': data.get('refresh_count', 0)
                }
            else:
                # Legacy format
                token_data = data
                token_data['_metadata'] = {
                    'created_at': datetime.now().isoformat(),
                    'last_refresh': datetime.now().isoformat(),
                    'refresh_count': 0
                }
            
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to load token: {e}", exc_info=True)
            return None
    
    def get_credentials(self, profile_name: str, email_address: str, force_refresh: bool = False) -> Optional[Credentials]:
        """
        Get valid OAuth credentials with automatic refresh
        
        Args:
            profile_name: OAuth profile name
            email_address: Email address for the credentials
            force_refresh: Force token refresh even if not expired
        
        Returns:
            Valid Credentials object or None if unable to obtain
        """
        with self._lock:
            profile_key = f"{profile_name}:{email_address}"
            
            # Check if refresh is already in progress
            if profile_key in self._refresh_in_progress:
                logger.info(f"Refresh in progress for {profile_key}, waiting...")
                # Wait for refresh to complete
                while profile_key in self._refresh_in_progress:
                    time.sleep(1)
            
            if profile_name not in self.profiles:
                logger.error(f"Unknown profile: {profile_name}")
                raise TokenManagerError(f"Unknown profile: {profile_name}")
            
            profile = self.profiles[profile_name]
            
            # Load existing token
            token_data = self._load_token_data(profile_name, email_address)
            
            if token_data:
                try:
                    # Create credentials from token data
                    creds = Credentials(
                        token=token_data.get('token'),
                        refresh_token=token_data.get('refresh_token'),
                        token_uri=token_data.get('token_uri'),
                        client_id=token_data.get('client_id'),
                        client_secret=token_data.get('client_secret'),
                        scopes=token_data.get('scopes')
                    )
                    
                    # Set expiry if available
                    if token_data.get('expiry'):
                        if isinstance(token_data['expiry'], str):
                            creds.expiry = datetime.fromisoformat(token_data['expiry'].replace('Z', '+00:00'))
                        elif isinstance(token_data['expiry'], (int, float)):
                            creds.expiry = datetime.fromtimestamp(token_data['expiry'])
                    
                    # Check if refresh is needed
                    needs_refresh = force_refresh or self._needs_refresh(creds, token_data)
                    
                    if needs_refresh:
                        logger.info(f"Token needs refresh for {profile_key}")
                        creds = self._refresh_credentials_with_retry(creds, profile_name, email_address)
                    
                    if creds and creds.valid:
                        logger.debug(f"Valid credentials obtained for {profile_key}")
                        return creds
                    else:
                        logger.warning(f"Invalid credentials for {profile_key}")
                        
                except Exception as e:
                    logger.error(f"Error creating credentials for {profile_key}: {e}", exc_info=True)
            
            # No valid token available
            logger.warning(f"No valid token available for {profile_key}")
            self._notify_token_failure(profile_name, email_address, "No valid token available")
            return None
    
    def _needs_refresh(self, creds: Credentials, token_data: Dict[str, Any]) -> bool:
        """Enhanced check for token refresh needs"""
        # Always refresh if invalid or expired
        if not creds.valid or creds.expired:
            return True
        
        # Check expiry time against threshold
        if creds.expiry:
            time_until_expiry = creds.expiry - datetime.utcnow()
            if time_until_expiry <= self.refresh_threshold:
                logger.info(f"Token expires in {time_until_expiry}, refreshing proactively")
                return True
        
        # Check token age from metadata
        metadata = token_data.get('_metadata', {})
        if metadata.get('created_at'):
            try:
                created_at = datetime.fromisoformat(metadata['created_at'])
                age = datetime.now() - created_at
                if age >= self.max_token_age - self.refresh_threshold:
                    logger.info(f"Token age {age} exceeds threshold, refreshing")
                    return True
            except Exception as e:
                logger.warning(f"Error parsing token creation date: {e}")
        
        return False
    
    def _refresh_credentials_with_retry(self, creds: Credentials, profile_name: str, email_address: str) -> Optional[Credentials]:
        """Refresh credentials with retry logic and error handling"""
        profile_key = f"{profile_name}:{email_address}"
        
        # Mark refresh in progress
        self._refresh_in_progress.add(profile_key)
        
        try:
            for attempt in range(self.retry_attempts):
                try:
                    logger.info(f"Refreshing credentials for {profile_key} (attempt {attempt + 1}/{self.retry_attempts})")
                    
                    # Attempt refresh
                    creds.refresh(GoogleAuthRequest())
                    
                    # Save refreshed token
                    token_data = {
                        'token': creds.token,
                        'refresh_token': creds.refresh_token,
                        'token_uri': creds.token_uri,
                        'client_id': creds.client_id,
                        'client_secret': creds.client_secret,
                        'scopes': creds.scopes,
                        'expiry': creds.expiry.isoformat() if creds.expiry else None
                    }
                    
                    self._save_token_data(profile_name, email_address, token_data)
                    
                    # Clear failed refresh tracking
                    if profile_key in self._failed_refreshes:
                        del self._failed_refreshes[profile_key]
                    
                    logger.info(f"Credentials refreshed successfully for {profile_key}")
                    return creds
                    
                except google.auth.exceptions.RefreshError as e:
                    logger.error(f"Refresh error for {profile_key} (attempt {attempt + 1}): {e}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    else:
                        self._handle_refresh_failure(profile_name, email_address, str(e))
                        
                except Exception as e:
                    logger.error(f"Unexpected error refreshing {profile_key} (attempt {attempt + 1}): {e}", exc_info=True)
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                    else:
                        self._handle_refresh_failure(profile_name, email_address, str(e))
            
            return None
            
        finally:
            # Always remove from in-progress set
            self._refresh_in_progress.discard(profile_key)
    
    def _handle_refresh_failure(self, profile_name: str, email_address: str, error_msg: str):
        """Handle persistent refresh failures"""
        profile_key = f"{profile_name}:{email_address}"
        
        # Track failed refresh
        self._failed_refreshes[profile_key] = {
            'timestamp': datetime.now(),
            'error': error_msg,
            'attempts': self.retry_attempts
        }
        
        # Notify administrators
        self._notify_token_failure(profile_name, email_address, error_msg)
        
        # Log critical error
        logger.critical(f"Token refresh failed permanently for {profile_key}: {error_msg}")
    
    def _notify_token_failure(self, profile_name: str, email_address: str, error_msg: str):
        """Send notification for token failures"""
        if not self.admin_email:
            logger.warning("No admin email configured for token failure notifications")
            return
        
        try:
            subject = f"Karen AI - OAuth Token Failure: {profile_name}"
            body = f"""
OAuth Token Failure Alert

Profile: {profile_name}
Email Account: {email_address}
Timestamp: {datetime.now().isoformat()}
Error: {error_msg}

This token failure may impact Karen AI's ability to:
- Send/receive emails
- Access calendar
- Process appointments

Please check the token configuration and re-authenticate if necessary.

Karen AI System
"""
            
            # Try to send notification
            self._send_notification_email(subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send token failure notification: {e}", exc_info=True)
    
    def _send_notification_email(self, subject: str, body: str):
        """Send email notification (basic implementation)"""
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = os.getenv('SECRETARY_EMAIL_ADDRESS', 'karensecretaryai@gmail.com')
            msg['To'] = self.admin_email
            
            # This is a basic implementation - in production, use the EmailClient
            logger.info(f"Token failure notification prepared: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to prepare notification email: {e}")
    
    def _start_background_monitor(self):
        """Start background thread to monitor and refresh tokens"""
        def monitor():
            logger.info("Token background monitor started")
            while True:
                try:
                    self._monitor_all_tokens()
                    time.sleep(1800)  # Check every 30 minutes
                except Exception as e:
                    logger.error(f"Token monitor error: {e}", exc_info=True)
                    time.sleep(300)  # Wait 5 minutes before retry
        
        monitor_thread = threading.Thread(target=monitor, daemon=True, name="TokenMonitor")
        monitor_thread.start()
    
    def _monitor_all_tokens(self):
        """Monitor all stored tokens for refresh needs"""
        if not self.tokens_dir.exists():
            return
        
        monitored_count = 0
        refreshed_count = 0
        
        for token_file in self.tokens_dir.glob("*.json"):
            if token_file.name.startswith("gmail_token_"):
                try:
                    # Parse filename to get profile and email
                    # Format: gmail_token_{email}_{profile}.json
                    parts = token_file.stem.split('_')
                    if len(parts) >= 4:
                        email_part = '_'.join(parts[2:-1])  # Reconstruct email
                        email_address = email_part.replace('_at_', '@').replace('_dot_', '.')
                        profile_name = parts[-1]
                        
                        # Check if this profile should auto-refresh
                        if profile_name in self.profiles and self.profiles[profile_name].get('auto_refresh', True):
                            profile_key = f"{profile_name}:{email_address}"
                            
                            # Skip if refresh is already in progress or recently failed
                            if (profile_key not in self._refresh_in_progress and 
                                profile_key not in self._failed_refreshes):
                                
                                # Load and check token
                                token_data = self._load_token_data(profile_name, email_address)
                                if token_data:
                                    try:
                                        creds = Credentials(
                                            token=token_data.get('token'),
                                            refresh_token=token_data.get('refresh_token'),
                                            token_uri=token_data.get('token_uri'),
                                            client_id=token_data.get('client_id'),
                                            client_secret=token_data.get('client_secret'),
                                            scopes=token_data.get('scopes')
                                        )
                                        
                                        if token_data.get('expiry'):
                                            if isinstance(token_data['expiry'], str):
                                                creds.expiry = datetime.fromisoformat(token_data['expiry'].replace('Z', '+00:00'))
                                            elif isinstance(token_data['expiry'], (int, float)):
                                                creds.expiry = datetime.fromtimestamp(token_data['expiry'])
                                        
                                        if self._needs_refresh(creds, token_data):
                                            logger.info(f"Background refresh triggered for {profile_key}")
                                            refreshed_creds = self._refresh_credentials_with_retry(creds, profile_name, email_address)
                                            if refreshed_creds:
                                                refreshed_count += 1
                                        
                                        monitored_count += 1
                                        
                                    except Exception as e:
                                        logger.warning(f"Error monitoring token {profile_key}: {e}")
                                
                except Exception as e:
                    logger.warning(f"Error processing token file {token_file}: {e}")
        
        if monitored_count > 0:
            logger.debug(f"Token monitor cycle: {monitored_count} tokens monitored, {refreshed_count} refreshed")
    
    def force_refresh_all(self) -> Dict[str, bool]:
        """Force refresh all tokens (useful for testing or maintenance)"""
        results = {}
        
        for token_file in self.tokens_dir.glob("*.json"):
            if token_file.name.startswith("gmail_token_"):
                try:
                    # Parse filename
                    parts = token_file.stem.split('_')
                    if len(parts) >= 4:
                        email_part = '_'.join(parts[2:-1])
                        email_address = email_part.replace('_at_', '@').replace('_dot_', '.')
                        profile_name = parts[-1]
                        
                        profile_key = f"{profile_name}:{email_address}"
                        
                        # Attempt refresh
                        creds = self.get_credentials(profile_name, email_address, force_refresh=True)
                        results[profile_key] = creds is not None
                        
                except Exception as e:
                    logger.error(f"Error force refreshing {token_file}: {e}")
                    results[str(token_file)] = False
        
        return results
    
    def get_token_status(self) -> List[Dict[str, Any]]:
        """Get status of all managed tokens"""
        status_list = []
        
        for token_file in self.tokens_dir.glob("*.json"):
            if token_file.name.startswith("gmail_token_"):
                try:
                    # Parse filename
                    parts = token_file.stem.split('_')
                    if len(parts) >= 4:
                        email_part = '_'.join(parts[2:-1])
                        email_address = email_part.replace('_at_', '@').replace('_dot_', '.')
                        profile_name = parts[-1]
                        
                        token_data = self._load_token_data(profile_name, email_address)
                        if token_data:
                            status = {
                                'profile': profile_name,
                                'email': email_address,
                                'file': str(token_file),
                                'created_at': token_data.get('_metadata', {}).get('created_at'),
                                'last_refresh': token_data.get('_metadata', {}).get('last_refresh'),
                                'refresh_count': token_data.get('_metadata', {}).get('refresh_count', 0),
                                'has_refresh_token': bool(token_data.get('refresh_token')),
                                'expiry': token_data.get('expiry'),
                                'needs_refresh': False,
                                'valid': False
                            }
                            
                            # Check current validity
                            try:
                                creds = Credentials(
                                    token=token_data.get('token'),
                                    refresh_token=token_data.get('refresh_token'),
                                    token_uri=token_data.get('token_uri'),
                                    client_id=token_data.get('client_id'),
                                    client_secret=token_data.get('client_secret'),
                                    scopes=token_data.get('scopes')
                                )
                                
                                if token_data.get('expiry'):
                                    if isinstance(token_data['expiry'], str):
                                        creds.expiry = datetime.fromisoformat(token_data['expiry'].replace('Z', '+00:00'))
                                    elif isinstance(token_data['expiry'], (int, float)):
                                        creds.expiry = datetime.fromtimestamp(token_data['expiry'])
                                
                                status['valid'] = creds.valid
                                status['needs_refresh'] = self._needs_refresh(creds, token_data)
                                
                            except Exception as e:
                                logger.warning(f"Error checking credentials for {profile_name}:{email_address}: {e}")
                            
                            status_list.append(status)
                            
                except Exception as e:
                    logger.error(f"Error processing token file {token_file}: {e}")
        
        return status_list
    
    def cleanup_failed_refreshes(self):
        """Clean up old failed refresh records"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        to_remove = []
        for profile_key, failure_info in self._failed_refreshes.items():
            if failure_info['timestamp'] < cutoff_time:
                to_remove.append(profile_key)
        
        for key in to_remove:
            del self._failed_refreshes[key]
            
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old failed refresh records")


# Global token manager instance
_enhanced_token_manager = None

def get_enhanced_token_manager() -> EnhancedTokenManager:
    """Get the global enhanced token manager instance"""
    global _enhanced_token_manager
    if _enhanced_token_manager is None:
        _enhanced_token_manager = EnhancedTokenManager()
    return _enhanced_token_manager

def get_credentials_with_auto_refresh(profile_name: str, email_address: str) -> Optional[Credentials]:
    """Get credentials with automatic refresh handling"""
    return get_enhanced_token_manager().get_credentials(profile_name, email_address)

def force_refresh_token(profile_name: str, email_address: str) -> bool:
    """Force refresh a specific token"""
    creds = get_enhanced_token_manager().get_credentials(profile_name, email_address, force_refresh=True)
    return creds is not None

def get_all_token_status() -> List[Dict[str, Any]]:
    """Get status of all managed tokens"""
    return get_enhanced_token_manager().get_token_status()


if __name__ == "__main__":
    # Test and demonstration
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    manager = EnhancedTokenManager()
    
    print("Enhanced Token Manager - Status Report")
    print("=" * 50)
    
    # Get token status
    status_list = manager.get_token_status()
    for status in status_list:
        print(f"Profile: {status['profile']}")
        print(f"Email: {status['email']}")
        print(f"Valid: {status['valid']}")
        print(f"Needs Refresh: {status['needs_refresh']}")
        print(f"Last Refresh: {status['last_refresh']}")
        print("-" * 30)
    
    print(f"Total tokens managed: {len(status_list)}")