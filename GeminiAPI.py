import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiAPIClient:
    def __init__(self):
        # Load environment variables from the root directory
        root_dir = Path(__file__).parent.parent
        env_path = root_dir / '.env'
        load_dotenv(env_path)
        self.api_key = self._get_api_key()
        self._initialize_api()
        
    def _get_api_key(self) -> Optional[str]:
        """Get the Gemini API key from environment variables."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("Gemini API key not found in environment variables")
            return None
        return api_key
    
    def _initialize_api(self) -> None:
        """Initialize the Gemini API with the API key."""
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                logger.info("Gemini API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {str(e)}")
    
    def verify_api_key(self) -> bool:
        """Verify that the API key is properly set up."""
        if not self.api_key:
            logger.error("API key is not configured")
            return False
        return True
    
    def generate_content(self, prompt: str, model: str = "gemini-2.0-flash") -> Optional[str]:
        """Generate content using the Gemini API."""
        if not self.verify_api_key():
            return None
            
        try:
            model = genai.GenerativeModel(model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return None
    
    def analyze_code(self, code: str, analysis_type: str = "review") -> Optional[Dict[str, Any]]:
        """Analyze code using the Gemini API."""
        if not self.verify_api_key():
            return None
            
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            # Create a structured prompt based on analysis type
            if analysis_type == "review":
                prompt = f"Please review this code and provide feedback on:\n1. Code quality\n2. Potential issues\n3. Best practices\n4. Security concerns\n\nCode:\n{code}"
            elif analysis_type == "optimization":
                prompt = f"Please analyze this code for optimization opportunities:\n1. Performance improvements\n2. Memory usage\n3. Algorithm efficiency\n\nCode:\n{code}"
            else:
                prompt = f"Please analyze this code:\n{code}"
            
            response = model.generate_content(prompt)
            return {
                "analysis_type": analysis_type,
                "response": response.text,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    client = GeminiAPIClient()
    if client.verify_api_key():
        print("✅ Gemini API key is properly configured")
        
        # Test content generation
        response = client.generate_content("Explain how AI works")
        if response:
            print("\n📝 Generated Response:")
            print(response)
            
        # Test code analysis
        test_code = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
        """
        analysis = client.analyze_code(test_code, "review")
        if analysis:
            print("\n🔍 Code Analysis:")
            print(analysis["response"])
    else:
        print("❌ Gemini API key is not properly configured") 