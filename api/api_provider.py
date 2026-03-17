import os

class APIProvider:
    @staticmethod
    def openrouter():
        return os.getenv('OPENROUTER_API_KEY')
    @staticmethod 
    def openai():
        return os.getenv('OPENAI_API_KEY')
    @staticmethod
    def anthropic():
        return os.getenv('ANTHROPIC_API_KEY')
    
    @staticmethod
    def google():
        return os.getenv('GOOGLE_API_KEY')
    
