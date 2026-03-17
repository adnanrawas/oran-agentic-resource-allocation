import os

class APIProvider:
    def openrouter(self):
        return os.getenv('OPENROUTER_API_KEY')
    
    def openai(self):
        return os.getenv('OPENAI_API_KEY')
    
    def anthropic(self):
        return os.getenv('ANTHROPIC_API_KEY')
    
    def google(self):
        return os.getenv('GOOGLE_API_KEY')
    
