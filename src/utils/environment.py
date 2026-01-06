"""Environment variable management for the voice pipeline agent."""

import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger("voice-agent")

def load_environment():
    """Load environment variables from .env files.
    
    First tries to load from .env.local, falls back to .env if available.
    
    Returns:
        bool: True if environment variables were loaded, False otherwise
    """
    try:
        # Try to load from .env.local first
        if os.path.exists(".env.local"):
            load_dotenv(dotenv_path=".env.local")
            logger.info("Environment variables loaded from .env.local")
            return True
        # Fall back to .env
        elif os.path.exists(".env"):
            load_dotenv(dotenv_path=".env")
            logger.info("Environment variables loaded from .env")
            return True
        else:
            logger.warning("No .env or .env.local file found")
            return False
    except Exception as e:
        logger.warning(f"Failed to load environment variables: {e}")
        return False

def get_env_var(key, default=None):
    """Get an environment variable with optional default value.
    
    Args:
        key: The environment variable key
        default: Default value if the key is not found
        
    Returns:
        The environment variable value or the default
    """
    value = os.environ.get(key, default)
    if value is None:
        logger.warning(f"Environment variable {key} not found")
    return value
