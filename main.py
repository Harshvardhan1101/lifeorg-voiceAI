"""Main entry point for the voice pipeline agent application."""

import logging
import os
import sys

from livekit.agents import (
    JobProcess,
    WorkerOptions,
    cli,
)
from livekit.plugins import silero

# Import application modules
from src.agents.agent import VoicePipelineAgentRunner
from src.utils.logger import setup_logger
from src.utils.environment import load_environment
from healthcheck import run_health_server_background

# Set up logger
logger = setup_logger()

def prewarm(proc: JobProcess):
    """Prewarm function to load models and resources before handling requests.
    
    Args:
        proc: Job process instance to store prewarmed models
    """
    try:
        # Load environment variables
        load_environment()
        
        # Initialize VAD model
        proc.userdata["vad"] = silero.VAD.load()
        logger.info("VAD model prewarmed successfully")
        
        # Initialize noise suppressor (optional)
        proc.userdata["noise_suppressor"] = True
        logger.info("Noise suppressor enabled")
    except Exception as e:
        logger.error(f"Failed to prewarm models: {e}")
        # Initialize empty userdata dict to avoid errors
        proc.userdata["vad"] = None
        proc.userdata["noise_suppressor"] = False

async def entrypoint(ctx):
    """Main entry point for the voice pipeline agent.
    
    Args:
        ctx: Job context from LiveKit
    """
    try:
        # Create agent runner with prewarmed models
        agent_runner = VoicePipelineAgentRunner(
            vad=ctx.proc.userdata.get("vad"),
            noise_suppressor=ctx.proc.userdata.get("noise_suppressor")
        )
        
        # Run the agent
        await agent_runner.run(ctx)
    except Exception as e:
        logger.error(f"Error in entry point: {e}")
        # Ensure we exit gracefully
        return

if __name__ == "__main__":
    try:
        # Load environment variables
        load_environment()
        
        # Start health check server for Kubernetes probes (if enabled)
        if os.environ.get("ENABLE_HEALTH_SERVER", "true").lower() == "true":
            run_health_server_background()
            logger.info("Health check server started for Kubernetes probes")
        
        # Run the application with increased initialization timeout
        cli.run_app(
            WorkerOptions(
                prewarm_fnc=prewarm,
                entrypoint_fnc=entrypoint,
              #   initialize_process_timeout=60.0,  # Increase timeout for model loading
            )
        )
    except Exception as e:
        logger.critical(f"Application startup failed: {e}")
        sys.exit(1)
