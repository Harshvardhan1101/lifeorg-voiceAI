"""Voice Pipeline Agent implementation."""

import logging
import json
import asyncio
import httpx
import random

from livekit.agents import (
    JobContext,
    AutoSubscribe,
    Agent,
    AgentSession,
    llm,
    metrics,
)
from livekit.plugins import silero

from ..config.agent_configs import AGENT_CONFIGS
from ..utils.environment import get_env_var

logger = logging.getLogger("voice-agent")

class VoicePipelineAgentRunner:
    """Runner class for voice pipeline agents with different personalities."""
    
    def __init__(self, vad=None, noise_suppressor=None):
        """Initialize the agent runner.
        
        Args:
            vad: Voice Activity Detection model (deprecated, kept for compatibility)
            noise_suppressor: Noise suppression instance (deprecated)
        """
        self.vad = vad
        self.noise_suppressor = noise_suppressor
    
    async def run(self, ctx: JobContext):
        """Run the voice pipeline agent with the appropriate configuration.
        
        Args:
            ctx: Job context from LiveKit
            
        Returns:
            None
        """
        
        logger.info(f"Connecting to room {ctx.room.name}")
        
        try:
            await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
            logger.info(f"Connected to room {ctx.room.name}")
        except Exception as e:
            logger.error(f"Failed to connect to room: {e}")
            return
        
        try:
            # Wait for the first participant to connect
            participant = await ctx.wait_for_participant()
            logger.info(f"Participant connected: {participant.identity}")
        except Exception as e:
            logger.error(f"Error waiting for participant: {e}")
            return
        
        # Extract agent type from participant metadata
        agent_type, conversationHistory, userId = self._extract_agent_type_from_metadata(participant)

        # Get agent configuration
        agent_config = AGENT_CONFIGS.get(agent_type, AGENT_CONFIGS["SoraAI"])

        initial_prompt = agent_config["prompt"]

        if conversationHistory is not None:
            logger.info(f"Adding conversation history to the prompt")
            if "conversation_history_template" in agent_config:
            # Use custom template if defined
                history_addition = agent_config["conversation_history_template"].format(
                    conversationHistory=conversationHistory
            )
            else:
            # Use default template
                history_addition = f"\n\nPrevious conversation history: {conversationHistory}"
            initial_prompt += history_addition
        
        logger.info(f"Starting voice {agent_type} for participant {participant.identity} with agent type: {agent_type}")

        try:
            # Create custom Agent class with personality
            class CustomAgent(Agent):
                def __init__(self):
                    # Pass instructions directly to Agent constructor
                    super().__init__(instructions=initial_prompt)
                
                async def on_enter(self):
                    """Called when agent becomes active"""
                    # Agent will greet after starting
                    pass
            
            # Initialize AgentSession with model configuration
            llm_config = agent_config["models"]["llm"]
            tts_config = agent_config["models"]["tts"]
            stt_config = agent_config["models"]["stt"]
            
            # Build model strings (provider/model format)
            llm_str = f"{llm_config['provider']}/{llm_config['model']}"
            stt_str = f"{stt_config['provider']}/{stt_config['model']}"
            
            # For TTS, handle OpenAI special case with instructions
            if tts_config["provider"] == "openai":
                from livekit.plugins import openai
                tts_instance = openai.TTS(
                    model=tts_config["model"],
                    voice=tts_config["voice"],
                    instructions=tts_config.get("instructions"),
                )
            else:
                tts_str = f"{tts_config['provider']}/{tts_config['model']}:{tts_config['voice']}"
                tts_instance = tts_str
            
            # Create agent session
            session = AgentSession(
                vad=self.vad or silero.VAD.load(),
                stt=stt_str,
                llm=llm_str,
                tts=tts_instance,
                allow_interruptions=True,
                min_interruption_duration=0.5,
            )
            
            # Set up usage metrics collection
            usage_collector = metrics.UsageCollector()

            @session.on("metrics_collected")
            def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
                metrics.log_metrics(agent_metrics)
                usage_collector.collect(agent_metrics)
            
            # Log aggregated summary of usage metrics generated by usage collector
            async def log_usage():
                try:
                    summary = usage_collector.get_summary()
                    logger.info(f"Usage: ${summary}")
                    logger.info(f"UserId: {userId}")

                    # Convert UsageSummary to dict for JSON serialization
                    if hasattr(summary, "to_dict"):
                        summary_dict = summary.to_dict()
                    elif hasattr(summary, "__dict__"):
                        summary_dict = vars(summary)
                    else:
                        summary_dict = str(summary)  # fallback, but not recommended

                    payment_api_url = get_env_var("PAYMENT_API_URL", "https://your-payment-backend.example.com") + "/ai-agents/ingest-voice-tokens"
                    payload = {
                        "userId": userId,
                        "usage_summary": summary_dict,
                    }
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.post(payment_api_url, json=payload)
                            response.raise_for_status()
                            logger.info(f"Usage summary sent to payment backend: {response.status_code}")
                    except httpx.TimeoutException:
                        logger.warning(f"Payment API request timed out - usage data may not be recorded")
                    except httpx.HTTPError as e:
                        logger.warning(f"HTTP error sending usage to payment backend: {e}")
                    except Exception as e:
                        logger.warning(f"Failed to send usage summary to payment backend: {e}")
                except Exception as e:
                    logger.error(f"Critical error in log_usage shutdown callback: {e}", exc_info=True)
                    # Don't re-raise - we're in a shutdown callback
                    
            # At shutdown, generate and log the summary from the usage collector
            ctx.add_shutdown_callback(log_usage)
            
            # Create and start the agent
            logger.info(f"Starting agent session for {participant.identity}")
            agent_instance = CustomAgent()
            await session.start(agent=agent_instance, room=ctx.room)
            
            # Greet the user with a random greeting for the selected agent type
            try:
                # Select a random greeting from the agent's greetings list
                random_greeting = random.choice(agent_config["greetings"])
                logger.info(f"Sending greeting: {random_greeting}")
                await session.say(random_greeting, allow_interruptions=True)
            except Exception as e:
                logger.error(f"Failed to send greeting: {e}", exc_info=True)
            
            # Wait until disconnected
            await self._wait_for_disconnection(ctx)
            
        except asyncio.CancelledError:
            logger.info(f"Agent task cancelled for {participant.identity}")
            raise
        except Exception as e:
            logger.error(f"Error in agent setup or execution: {e}", exc_info=True)
        finally:
            logger.info(f"Participant {participant.identity} disconnected")
    
    def _extract_agent_type_from_metadata(self, participant):
        """Extract agent type from participant metadata.
        
        Args:
            participant: LiveKit participant object
            
        Returns:
            str: Agent type extracted from metadata or 'SoraAI' as default
        """
        try:
            # Handle metadata whether it's bytes or already a string
            if isinstance(participant.metadata, bytes):
                metadata = participant.metadata.decode('utf-8')
            else:
                metadata = participant.metadata if participant.metadata else '{}'
                
            metadata_json = json.loads(metadata)
            
            agent_type = "SoraAI"
            conversationHistory = None
            userId = "userId"
            logger.info(f"metadata_json {metadata_json}")
            
            if 'agentType' in metadata_json:
                agent_type = metadata_json['agentType']
                logger.info(f"Using agentType from metadata: {agent_type}")
            if 'conversationHistory' in metadata_json:
                conversationHistory = metadata_json['conversationHistory']
                logger.info(f"Using conversationHistory from metadata: {conversationHistory}")
            if 'userId' in metadata_json:
                userId = metadata_json['userId']
                logger.info(f"Using userId from metadata: {userId}")
            
            return agent_type, conversationHistory, userId
            
        except Exception as e:
            logger.error(f"Failed to parse participant metadata: {e}")
            return "SoraAI", None, "userId"
    
    async def _wait_for_disconnection(self, ctx):
        """Wait for all participants to disconnect from the room.
        
        Args:
            ctx: Job context
            
        Returns:
            None
        """
        try:
            # Wait for room to disconnect
            logger.info(f"Waiting for room to disconnect")
            internal_event = asyncio.Event()
            
            # Set up a participant disconnect handler
            @ctx.room.on("participant_disconnected")
            def on_participant_disconnected(participant):
                logger.info(f"Participant {participant.identity} disconnected")
                # Check if all non-agent participants have left
                non_agent_participants = [p for p in ctx.room.participants.values() 
                                        if not p.is_agent]
                if len(non_agent_participants) == 0:
                    logger.info("All participants have disconnected")
                    internal_event.set()
            
            # Wait for the internal event to be set
            await internal_event.wait()
        except Exception as e:
            logger.error(f"Error waiting for disconnection: {e}")
