"""
Template for creating new API clients following EmailClient patterns
Replace TODO items with your specific implementation
"""
import os
import json
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

# For Google APIs
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
import google.auth.exceptions

logger = logging.getLogger(__name__)

# Define project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Define required scopes for your service
TODO_SCOPES = [
    # TODO: Add your required OAuth scopes
    # 'https://www.googleapis.com/auth/TODO.readonly',
    # 'https://www.googleapis.com/auth/TODO.modify'
]

class TODOClient:
    """Client for TODO service following EmailClient patterns"""
    
    def __init__(self, 
                 account_identifier: str,
                 token_file_path: str,
                 credentials_file_path: Optional[str] = None):
        """
        Initialize TODO client with OAuth credentials
        
        Args:
            account_identifier: Account identifier (e.g., email, user ID)
            token_file_path: Path to OAuth token JSON file
            credentials_file_path: Path to OAuth credentials JSON (client ID/secret)
        """
        self.account_identifier = account_identifier
        self.token_file_path = os.path.join(PROJECT_ROOT, token_file_path)
        self.credentials_file_path = credentials_file_path or os.path.join(PROJECT_ROOT, 'credentials.json')
        
        logger.debug(f"Initializing TODOClient for {account_identifier} using token {self.token_file_path}")
        
        # Initialize cache
        self._cache: Dict[str, Any] = {}
        self._label_cache: Dict[str, Optional[str]] = {}  # For label/tag caching
        
        # Load client configuration
        self.client_config = self._load_client_config()
        if not self.client_config:
            logger.error(f"Failed to load client config from {self.credentials_file_path}")
            raise ValueError(f"Failed to load client configuration")
        
        # Load and refresh credentials
        self.creds = self._load_and_refresh_credentials()
        if not self.creds:
            logger.error(f"Failed to load credentials from {self.token_file_path}")
            raise ValueError(f"Failed to load or refresh OAuth credentials")
        
        # Build service client
        try:
            # TODO: Replace with your service name and version
            # self.service = build('TODO_service', 'v1', credentials=self.creds)
            pass
        except Exception as e:
            logger.error(f"Failed to build service client: {e}", exc_info=True)
            raise
        
        logger.info(f"TODOClient for {account_identifier} initialized successfully")
    
    def _load_client_config(self) -> Optional[Dict[str, Any]]:
        """Load OAuth client configuration"""
        logger.debug(f"Loading client config from {self.credentials_file_path}")
        
        try:
            with open(self.credentials_file_path, 'r') as f:
                full_creds = json.load(f)
                client_config = full_creds.get('installed') or full_creds.get('web')
            
            required_fields = ['client_id', 'client_secret', 'token_uri']
            if not all(client_config.get(field) for field in required_fields):
                logger.error(f"Missing required fields in credentials.json: {required_fields}")
                return None
            
            logger.debug("Client config loaded successfully")
            return client_config
            
        except FileNotFoundError:
            logger.error(f"Credentials file not found: {self.credentials_file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in credentials file: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading client config: {e}", exc_info=True)
            return None
    
    def _load_and_refresh_credentials(self) -> Optional[Credentials]:
        """Load and refresh OAuth credentials following EmailClient pattern"""
        logger.debug(f"Loading credentials from {self.token_file_path}")
        
        creds = None
        token_data = None
        
        # Try to load existing token
        if os.path.exists(self.token_file_path):
            try:
                with open(self.token_file_path, 'r') as token_file:
                    token_data = json.load(token_file)
                logger.debug("Token file loaded successfully")
                
                # Create credentials object
                creds = Credentials.from_authorized_user_info(token_data, TODO_SCOPES)
                logger.debug("Credentials object created from token data")
                
            except Exception as e:
                logger.error(f"Error loading token from {self.token_file_path}: {e}", exc_info=True)
                creds = None
        
        # Check if refresh is needed
        if creds and not creds.valid:
            if creds.expired and creds.refresh_token:
                logger.info("Token expired, attempting refresh...")
                try:
                    creds.refresh(GoogleAuthRequest())
                    logger.info("Token refreshed successfully")
                    self._save_credentials(creds)
                except google.auth.exceptions.RefreshError as e:
                    logger.error(f"Failed to refresh token: {e}", exc_info=True)
                    self._log_oauth_error_details(e)
                    creds = None
                except Exception as e:
                    logger.error(f"Unexpected error during token refresh: {e}", exc_info=True)
                    creds = None
        
        # Final validation
        if not creds or not creds.valid:
            logger.error(f"No valid credentials available. Re-authentication required.")
            # TODO: Implement re-authentication flow if needed
            return None
        
        logger.debug("Credentials loaded and validated successfully")
        return creds
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to token file"""
        logger.debug(f"Saving credentials to {self.token_file_path}")
        
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
            logger.debug(f"Token expiry: {creds.expiry.isoformat()}")
        
        try:
            with open(self.token_file_path, 'w') as f:
                json.dump(token_data, f, indent=2)
            logger.info("Credentials saved successfully")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}", exc_info=True)
    
    def _log_oauth_error_details(self, error: google.auth.exceptions.RefreshError):
        """Log detailed OAuth error information"""
        if hasattr(error, 'response') and hasattr(error.response, 'data'):
            try:
                error_details = json.loads(error.response.data.decode())
                logger.error(f"OAuth Error Details: {error_details}")
            except Exception:
                logger.error("Could not parse OAuth error details")
    
    def fetch_items(self, 
                    query: Optional[str] = None,
                    max_results: int = 10,
                    last_n_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch items from the service
        
        Args:
            query: Query string for filtering
            max_results: Maximum number of results
            last_n_days: Fetch items from last N days
            
        Returns:
            List of item dictionaries
        """
        logger.debug(f"Fetching items with query='{query}', max_results={max_results}, last_n_days={last_n_days}")
        
        if not self.creds or not self.creds.valid:
            logger.warning("Invalid credentials, attempting refresh...")
            self.creds = self._load_and_refresh_credentials()
            if not self.creds:
                logger.error("Cannot fetch items: invalid credentials")
                return []
        
        try:
            # Build query parameters
            params = {
                'maxResults': max_results
            }
            
            if query:
                params['q'] = query
            
            if last_n_days:
                # Calculate date filter
                after_date = (datetime.now() - timedelta(days=last_n_days)).isoformat()
                params['updatedMin'] = after_date
            
            # TODO: Replace with actual API call
            # response = self.service.items().list(**params).execute()
            # items = response.get('items', [])
            
            items = []  # Placeholder
            
            logger.info(f"Fetched {len(items)} items")
            
            # Process items
            processed_items = []
            for item in items:
                processed_item = self._process_item(item)
                processed_items.append(processed_item)
            
            return processed_items
            
        except HttpError as error:
            self._handle_http_error(error, "fetch_items")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in fetch_items: {e}", exc_info=True)
            return []
    
    def create_item(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new item"""
        logger.debug(f"Creating item: {item_data}")
        
        if not self.creds or not self.creds.valid:
            logger.error("Cannot create item: invalid credentials")
            return None
        
        try:
            # TODO: Replace with actual API call
            # result = self.service.items().create(body=item_data).execute()
            result = None  # Placeholder
            
            if result:
                logger.info(f"Successfully created item: {result.get('id')}")
            
            return result
            
        except HttpError as error:
            self._handle_http_error(error, "create_item")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in create_item: {e}", exc_info=True)
            return None
    
    def update_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing item"""
        logger.debug(f"Updating item {item_id} with: {updates}")
        
        if not self.creds or not self.creds.valid:
            logger.error("Cannot update item: invalid credentials")
            return False
        
        try:
            # TODO: Replace with actual API call
            # self.service.items().update(itemId=item_id, body=updates).execute()
            
            logger.info(f"Successfully updated item {item_id}")
            return True
            
        except HttpError as error:
            self._handle_http_error(error, "update_item")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in update_item: {e}", exc_info=True)
            return False
    
    def _process_item(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw API item into standardized format"""
        processed = {
            'id': raw_item.get('id'),
            'created_at': raw_item.get('createdDate'),
            'updated_at': raw_item.get('updatedDate'),
            # TODO: Add your specific field mappings
        }
        
        # Extract nested data if needed
        if metadata := raw_item.get('metadata'):
            processed['metadata'] = self._process_metadata(metadata)
        
        return processed
    
    def _process_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process nested metadata"""
        return {
            # TODO: Add metadata processing
        }
    
    def _handle_http_error(self, error: HttpError, operation: str):
        """Handle HTTP errors with detailed logging"""
        error_content = error.content.decode() if isinstance(error.content, bytes) else error.content
        logger.error(f"HTTP error in {operation}: {error}. Details: {error_content}", exc_info=True)
        
        if error.resp.status == 401:
            logger.error("Authentication error (401). Token may be invalid or revoked.")
        elif error.resp.status == 403:
            logger.error("Permission error (403). Check API scopes and quotas.")
        elif error.resp.status == 429:
            logger.error("Rate limit exceeded (429). Consider implementing backoff.")
        elif error.resp.status >= 500:
            logger.error(f"Server error ({error.resp.status}). Service may be temporarily unavailable.")
    
    def get_cached_or_fetch(self, cache_key: str, fetch_func, *args, **kwargs) -> Any:
        """Get from cache or fetch using provided function"""
        if cache_key in self._cache:
            logger.debug(f"Cache hit for key: {cache_key}")
            return self._cache[cache_key]
        
        logger.debug(f"Cache miss for key: {cache_key}, fetching...")
        value = fetch_func(*args, **kwargs)
        
        if value is not None:
            self._cache[cache_key] = value
            logger.debug(f"Cached value for key: {cache_key}")
        
        return value
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        self._label_cache.clear()
        logger.info("Cache cleared")

# Example usage following Karen's patterns
if __name__ == "__main__":
    # This section would typically be in a setup script
    client = TODOClient(
        account_identifier="user@example.com",
        token_file_path="todo_token.json",
        credentials_file_path="credentials.json"
    )
    
    # Fetch recent items
    items = client.fetch_items(last_n_days=7, max_results=20)
    
    # Create new item
    new_item = client.create_item({
        'title': 'Test Item',
        'description': 'Created by TODOClient template'
    })
    
    # Update item
    if new_item:
        client.update_item(new_item['id'], {'status': 'completed'})