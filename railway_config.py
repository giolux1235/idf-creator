"""
Railway deployment configuration
"""

import os

# Railway environment variables
RAILWAY_ENVIRONMENT = os.getenv('RAILWAY_ENVIRONMENT')

# Get port from Railway or default
PORT = int(os.getenv('PORT', 5000))

# API keys (set in Railway dashboard)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Database URL if needed (Railway provides this)
DATABASE_URL = os.getenv('DATABASE_URL')

def get_config():
    """Get configuration for deployment"""
    return {
        'debug': False,  # Never debug in production
        'host': '0.0.0.0',  # Listen on all interfaces
        'port': PORT,
        'environment': RAILWAY_ENVIRONMENT or 'production'
    }

