"""Main entry point for the voice pipeline agent application."""

import logging
import os
import sys
import signal

from livekit.agents import (
    JobProcess,
    JobContext,
    AgentServer,
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

# Load environment variables FIRST before creating AgentServer
load_environment()

# Create AgentServer with proper initialization timeout
# The server will automatically pick up LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET from environment
server = AgentServer(
    initialize_process_timeout=120.0,  # Increased from 60 to 120 seconds for model loading
    num_idle_processes=1,  # Keep 1 idle process ready
)

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

async def entrypoint(ctx: JobContext):
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
        logger.error(f"Error in entry point: {e}", exc_info=True)
        # Ensure we exit gracefully
        return

# Register the prewarm and entrypoint functions
server.setup_fnc = prewarm

@server.rtc_session()
async def rtc_entrypoint(ctx: JobContext):
    await entrypoint(ctx)

if __name__ == "__main__":
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Environment already loaded at module level
        
        # Start health check server for Kubernetes probes (if enabled)
        if os.environ.get("ENABLE_HEALTH_SERVER", "true").lower() == "true":
            run_health_server_background()
            logger.info("Health check server started for Kubernetes probes")
        
        # Run the application using the new AgentServer API
        cli.run_app(server)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Application startup failed: {e}", exc_info=True)
        sys.exit(1)
