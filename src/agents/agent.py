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
    MetricsCollectedEvent,
)
from livekit.plugins import silero, openai, deepgram, groq

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
            
            # Create LLM instance based on provider
            if llm_config["provider"] == "groq":
                llm_instance = groq.LLM(
                    model=llm_config["model"],
                    temperature=llm_config.get("temperature", 0.7),
                )
            elif llm_config["provider"] == "openai":
                llm_instance = openai.LLM(
                    model=llm_config["model"],
                    temperature=llm_config.get("temperature", 0.7),
                )
            else:
                # Fallback to string format
                llm_instance = f"{llm_config['provider']}/{llm_config['model']}"
            
            # Create STT instance
            if stt_config["provider"] == "deepgram":
                stt_instance = deepgram.STT(model=stt_config["model"])
            else:
                stt_instance = f"{stt_config['provider']}/{stt_config['model']}"
            
            # For TTS, handle OpenAI special case with instructions
            if tts_config["provider"] == "openai":
                tts_instance = openai.TTS(
                    model=tts_config["model"],
                    voice=tts_config["voice"],
                    instructions=tts_config.get("instructions"),
                )
            else:
                tts_instance = f"{tts_config['provider']}/{tts_config['model']}:{tts_config['voice']}"
            
            # Create agent session
            session = AgentSession(
                vad=self.vad or silero.VAD.load(),
                stt=stt_instance,
                llm=llm_instance,
                tts=tts_instance,
                allow_interruptions=True,
                min_interruption_duration=0.5,
            )
            
            # Set up usage metrics collection
            usage_collector = metrics.UsageCollector()

            @session.on("metrics_collected")
            def on_metrics_collected(ev: MetricsCollectedEvent):
                # Collect metrics for usage summary
                usage_collector.collect(ev.metrics)
            
            # Log aggregated summary of usage metrics generated by usage collector
            async def log_usage():
                try:
                    summary = usage_collector.get_summary()
                    logger.info(f"Usage Summary: {summary}")
                    logger.info(f"UserId: {userId}")

                    # Convert UsageSummary to dict for JSON serialization
                    # Try multiple methods in order of preference
                    summary_dict = None
                    if hasattr(summary, "model_dump"):
                        # Pydantic v2 method
                        summary_dict = summary.model_dump()
                    elif hasattr(summary, "dict"):
                        # Pydantic v1 method
                        summary_dict = summary.dict()
                    elif hasattr(summary, "to_dict"):
                        summary_dict = summary.to_dict()
                    elif hasattr(summary, "__dict__"):
                        summary_dict = {k: v for k, v in vars(summary).items() if not k.startswith('_')}
                    else:
                        # Last resort: convert to string representation
                        logger.warning("Could not convert UsageSummary to dict, using string representation")
                        summary_dict = {"raw_summary": str(summary)}

                    payment_api_url = get_env_var("PAYMENT_API_URL", "https://your-payment-backend.example.com") + "/ai-agents/ingest-voice-tokens"
                    payload = {
                        "userId": userId,
                        "usage_summary": summary_dict,
                    }
                    
                    logger.info(f"Sending payload to {payment_api_url}: {payload}")
                    
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.post(payment_api_url, json=payload)
                            response.raise_for_status()
                            logger.info(f"✅ Usage summary sent to payment backend successfully: {response.status_code}")
                    except httpx.TimeoutException:
                        logger.warning(f"⚠️ Payment API request timed out - usage data may not be recorded")
                    except httpx.HTTPStatusError as e:
                        logger.warning(f"⚠️ HTTP {e.response.status_code} error sending usage to payment backend: {e.response.text}")
                    except httpx.RequestError as e:
                        logger.warning(f"⚠️ Request error sending usage to payment backend: {e}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to send usage summary to payment backend: {e}")
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
        
        In LiveKit 1.3.x, AgentSession handles disconnect automatically.
        This method is kept for compatibility but does minimal work.
        
        Args:
            ctx: Job context
            
        Returns:
            None
        """
        try:
            # AgentSession automatically handles disconnect in 1.3.x
            # Just wait for the room to signal disconnect
            logger.info(f"Agent session active, disconnect handled automatically by AgentSession")
            
            # Create an event to keep the function running until the session closes
            disconnect_event = asyncio.Event()
            
            @ctx.room.on("disconnected")
            def on_room_disconnected():
                logger.info("Room disconnected")
                disconnect_event.set()
            
            # Wait for disconnect (or let AgentSession handle it)
            try:
                await disconnect_event.wait()
            except asyncio.CancelledError:
                logger.info("Wait for disconnection cancelled")
        except Exception as e:
            logger.error(f"Error in disconnection handler: {e}")
