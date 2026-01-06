"""Logging configuration for the voice pipeline agent."""

import logging

def setup_logger():
    """Configure logging for the voice pipeline agent.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s %(name)s - %(message)s',
    )
    
    # Get logger instance
    logger = logging.getLogger("voice-agent")
    
    return logger
