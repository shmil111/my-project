import os
from dotenv import load_dotenv
import logging
from typing import Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleAPIClient:
    def __init__(self):
        # Load environment variables from the root directory
        root_dir = Path(__file__).parent.parent
        env_path = root_dir / '.env'
        load_dotenv(env_path)
        self.api_key = self._get_api_key()
        
    def _get_api_key(self) -> Optional[str]:
        """Get the Google API key from environment variables."""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.error("Google API key not found in environment variables")
            return None
        return api_key
    
    def verify_api_key(self) -> bool:
        """Verify that the API key is properly set up."""
        if not self.api_key:
            logger.error("API key is not configured")
            return False
        return True
    
    def get_api_key(self) -> Optional[str]:
        """Get the API key if it exists."""
        return self.api_key

# Example usage
if __name__ == "__main__":
    client = GoogleAPIClient()
    if client.verify_api_key():
        print("Google API key is properly configured")
    else:
        print("Google API key is not properly configured") 