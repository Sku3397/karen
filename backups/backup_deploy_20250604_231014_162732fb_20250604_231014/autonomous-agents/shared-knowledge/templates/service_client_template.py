"""
Service Client Template for Karen AI System
===========================================

This template follows Karen's established patterns for OAuth-based service clients.
Use this when integrating with external APIs that require authentication.

Patterns Included:
- OAuth 2.0 token management with automatic refresh
- Comprehensive error handling with admin notifications
- Project-relative path resolution
- Structured logging with context
- Graceful degradation on authentication failures

Usage:
1. Copy this template to src/your_service_client.py
2. Replace placeholders with your service-specific implementation
3. Update OAuth scopes for your service
4. Add configuration variables to src/config.py
5. Test OAuth flow thoroughly
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import time

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.exceptions

logger = logging.getLogger(__name__)

# Define the scopes needed for your service
YOUR_SERVICE_SCOPES = [
    'https://www.googleapis.com/auth/your.service.scope',
    'https://www.googleapis.com/auth/your.service.readonly'
]

class YourServiceClient:
    """
    Client for [Your Service Name] API integration.
    
    Follows Karen's OAuth patterns with automatic token refresh,
    comprehensive error handling, and admin notifications.
    
    Example Services:
    - Google Drive API
    - Google Sheets API
    - Twilio API (with OAuth)
    - Slack API
    - Any OAuth 2.0 service
    """
    
    def __init__(self, service_account_email: str, token_file_path: str, 
                 credentials_file_path: str = 'credentials.json'):
        """
        Initialize the service client.
        
        Args:
            service_account_email: Email address for the service account
            token_file_path: Path to OAuth token file (relative to project root)
            credentials_file_path: Path to OAuth credentials file
        """
        self.service_account_email = service_account_email
        
        # Resolve paths relative to project root (following Karen's pattern)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.token_file_path = os.path.join(project_root, token_file_path)
        self.credentials_file_path = os.path.join(project_root, credentials_file_path)
        
        logger.debug(f"Initializing YourServiceClient for {service_account_email}")
        logger.debug(f"Token path: {self.token_file_path}")
        logger.debug(f"Credentials path: {self.credentials_file_path}")
        
        # Initialize caching for expensive operations
        self._cache: Dict[str, Any] = {}
        
        # Load client configuration
        self.client_config = self._load_client_config()
        if not self.client_config:
            error_msg = f"Failed to load client configuration from {self.credentials_file_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Load and refresh credentials
        self.creds = self._load_and_refresh_credentials()
        if not self.creds:
            error_msg = f"Failed to load OAuth credentials from {self.token_file_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Build the service
        try:
            self.service = build('your_service', 'v1', credentials=self.creds)
            logger.info(f"YourServiceClient initialized successfully for {service_account_email}")
        except Exception as e:
            logger.error(f"Failed to build service client: {e}", exc_info=True)
            raise
    
    def _load_client_config(self) -> Optional[Dict[str, Any]]:
        """Load OAuth client configuration from credentials file."""
        logger.debug(f"Loading client config from {self.credentials_file_path}")
        
        try:
            with open(self.credentials_file_path, 'r') as f:
                full_creds_json = json.load(f)
                # Support both 'installed' and 'web' OAuth types
                client_config = full_creds_json.get('installed') or full_creds_json.get('web')
            
            # Validate required fields
            required_fields = ['client_id', 'client_secret', 'token_uri']
            if not client_config or not all(field in client_config for field in required_fields):
                logger.error(f"Client config missing required fields: {required_fields}")
                return None
            
            logger.debug("Client configuration loaded successfully")
            return client_config
            
        except FileNotFoundError:
            logger.error(f"OAuth credentials file not found: {self.credentials_file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in credentials file: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading client config: {e}", exc_info=True)
            return None
    
    def _load_and_refresh_credentials(self) -> Optional[Credentials]:
        """Load OAuth credentials with automatic refresh (Karen's pattern)."""
        logger.debug(f"Loading credentials from {self.token_file_path}")
        
        creds = None
        token_data = None
        
        # Try to load existing token
        if os.path.exists(self.token_file_path):
            try:
                with open(self.token_file_path, 'r') as token_file:
                    token_data = json.load(token_file)
                logger.debug("Token data loaded from file")
                
                # Create credentials object
                creds = Credentials.from_authorized_user_info(token_data, YOUR_SERVICE_SCOPES)
                logger.debug("Credentials object created from token data")
                
            except Exception as e:
                logger.error(f"Error loading token from {self.token_file_path}: {e}", exc_info=True)
                creds = None
                token_data = None
        else:
            logger.info(f"Token file not found: {self.token_file_path}")
        
        # Check if refresh is needed
        has_refresh_token = (token_data and token_data.get('refresh_token')) or (creds and creds.refresh_token)
        needs_refresh = creds and (not creds.valid or creds.expired)
        
        if has_refresh_token and needs_refresh:
            logger.info(f"Token refresh needed for {self.service_account_email}")
            try:
                creds.refresh(GoogleAuthRequest())
                logger.info(f"Successfully refreshed credentials for {self.service_account_email}")
                self._save_credentials(creds)
                
            except google.auth.exceptions.RefreshError as e:
                logger.error(f"OAuth refresh failed for {self.service_account_email}: {e}", exc_info=True)
                
                # Send admin notification following Karen's pattern
                self._send_admin_notification(
                    subject=f"[URGENT] OAuth Refresh Failed - {self.__class__.__name__}",
                    body=f"OAuth token refresh failed for {self.service_account_email}.\n"
                         f"Error: {e}\n"
                         f"Token file: {self.token_file_path}\n"
                         f"Re-authentication required."
                )
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error during refresh: {e}", exc_info=True)
                return None
        
        # Final validation
        if not creds or not creds.valid:
            logger.error(f"No valid credentials available for {self.service_account_email}")
            return None
        
        # Verify scopes
        if not all(scope in creds.scopes for scope in YOUR_SERVICE_SCOPES):
            logger.warning(f"Missing required scopes. Current: {creds.scopes}, Required: {YOUR_SERVICE_SCOPES}")
        
        logger.info(f"Credentials loaded successfully for {self.service_account_email}")
        return creds
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to token file (Karen's pattern)."""
        logger.debug(f"Saving credentials to {self.token_file_path}")
        
        try:
            token_data = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            }
            
            if creds.expiry:
                token_data['expiry_date'] = creds.expiry.timestamp()
            
            with open(self.token_file_path, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            logger.info(f"Credentials saved to {self.token_file_path}")
            
        except Exception as e:
            logger.error(f"Error saving credentials: {e}", exc_info=True)
    
    def _send_admin_notification(self, subject: str, body: str):
        """Send admin notification (integrate with Karen's email system)."""
        logger.critical(f"ADMIN NOTIFICATION: {subject}")
        logger.critical(f"Details: {body}")
        
        # TODO: Integrate with Karen's admin notification system
        # from src.communication_agent.agent import CommunicationAgent
        # comm_agent = CommunicationAgent.get_instance()
        # comm_agent.send_admin_email(subject, body)
    
    def your_service_operation(self, operation_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Example service operation following Karen's error handling patterns.
        
        Args:
            operation_params: Parameters for the operation
            
        Returns:
            Operation result or None on failure
        """
        logger.info(f"Performing service operation for {self.service_account_email}")
        logger.debug(f"Operation parameters: {operation_params}")
        
        # Check credentials before operation
        if not self.creds or not self.creds.valid:
            logger.warning("Invalid credentials, attempting to reload")
            reloaded_creds = self._load_and_refresh_credentials()
            if not reloaded_creds:
                logger.error("Cannot perform operation: no valid credentials")
                return None
            self.creds = reloaded_creds
            self.service = build('your_service', 'v1', credentials=self.creds)
        
        try:
            # Example API call - replace with your service's actual API
            result = self.service.your_resource().your_method(
                **operation_params
            ).execute()
            
            logger.info(f"Service operation completed successfully")
            logger.debug(f"Result: {result}")
            return result
            
        except HttpError as error:
            # Handle specific HTTP errors (Karen's pattern)
            error_content = error.content.decode() if isinstance(error.content, bytes) else error.content
            logger.error(f"API error in service operation: {error}. Details: {error_content}", exc_info=True)
            
            if error.resp.status == 401:
                logger.error("Authentication error (401). Token may be invalid or revoked.")
                self._send_admin_notification(
                    subject=f"[URGENT] Authentication Error - {self.__class__.__name__}",
                    body=f"401 Authentication error for {self.service_account_email}.\n"
                         f"Operation: {operation_params}\n"
                         f"Error: {error_content}"
                )
            elif error.resp.status == 403:
                logger.error("Permission error (403). Check API scopes and permissions.")
            elif error.resp.status == 429:
                logger.error("Rate limit exceeded (429). Implement backoff strategy.")
            
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error in service operation: {e}", exc_info=True)
            
            # Admin notification for unexpected errors
            self._send_admin_notification(
                subject=f"[URGENT] Service Error - {self.__class__.__name__}",
                body=f"Unexpected error in service operation for {self.service_account_email}.\n"
                     f"Operation: {operation_params}\n"
                     f"Error: {str(e)}"
            )
            return None
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get service health status for monitoring.
        
        Returns:
            Status dictionary with health information
        """
        status = {
            'service_name': 'YourService',
            'account_email': self.service_account_email,
            'timestamp': datetime.now().isoformat(),
            'credentials_valid': False,
            'last_error': None
        }
        
        try:
            # Test credentials
            if self.creds and self.creds.valid:
                status['credentials_valid'] = True
                status['credentials_expiry'] = self.creds.expiry.isoformat() if self.creds.expiry else None
            
            # Test basic API connectivity
            # result = self.service.test_endpoint().execute()
            # status['api_connectivity'] = 'healthy'
            
        except Exception as e:
            status['last_error'] = str(e)
            status['api_connectivity'] = 'error'
            logger.error(f"Service health check failed: {e}")
        
        return status


# Usage Example:
"""
# In your agent or main application:

from src.your_service_client import YourServiceClient

# Initialize client
client = YourServiceClient(
    service_account_email='your-service@your-project.iam.gserviceaccount.com',
    token_file_path='your_service_token.json',
    credentials_file_path='credentials.json'
)

# Perform operations
result = client.your_service_operation({
    'param1': 'value1',
    'param2': 'value2'
})

if result:
    print(f"Operation successful: {result}")
else:
    print("Operation failed - check logs")

# Check service health
status = client.get_service_status()
print(f"Service status: {status}")
"""

# Configuration Integration (add to src/config.py):
"""
# Your Service Configuration
YOUR_SERVICE_EMAIL = os.getenv('YOUR_SERVICE_EMAIL')
YOUR_SERVICE_TOKEN_PATH = os.getenv('YOUR_SERVICE_TOKEN_PATH', 'your_service_token.json')
"""