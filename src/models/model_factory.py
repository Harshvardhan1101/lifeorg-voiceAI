"""Factory class for creating different types of models."""

import logging
from livekit.plugins import (
    # cartesia,
    openai,
    deepgram,
)

logger = logging.getLogger("voice-agent")

class ModelFactory:
    """Factory class for creating LLM, TTS, and STT models."""

    @staticmethod
    def get_llm(provider, model, temperature=0.7):
        """Get an LLM instance based on provider and model.
        
        Args:
            provider (str): The provider name (openai, groq, etc.)
            model (str): The model identifier
            temperature (float, optional): Temperature parameter for text generation. Defaults to 0.7.
            
        Returns:
            object: The initialized LLM model instance or None if initialization fails
        """
        try:
            if provider == "openai":
                return openai.LLM(model=model, temperature=temperature)
            elif provider == "groq":
                return openai.llm.LLM.with_groq(model=model, temperature=temperature)
            else:
                # Default to OpenAI
                logger.warning(f"Unknown LLM provider '{provider}', falling back to OpenAI")
                return openai.LLM(model="gpt-4o-mini", temperature=temperature)
        except Exception as e:
            logger.error(f"Failed to initialize {provider} LLM with model {model}: {e}")
            # Fallback to a simpler model
            try:
                return openai.LLM(model="gpt-4o-mini", temperature=temperature)
            except Exception:
                logger.critical("Failed to initialize any LLM model")
                return None
    
    @staticmethod
    def get_tts(provider, model, voice, instructions=None, **kwargs):
        """Get a TTS instance based on provider, model, and voice.
        
        Args:
            provider (str): The provider name (openai, cartesia, etc.)
            model (str): The model identifier
            voice (str): The voice identifier or name
            instructions (str, optional): Voice instructions for TTS. Defaults to None.
            **kwargs: Additional provider-specific parameters
            
        Returns:
            object: The initialized TTS model instance or None if initialization fails
        """
        try:
            if provider == "openai":
                params = {
                    "model": model,
                    "voice": voice,
                }
                if instructions:
                    params["instructions"] = instructions
                
                return openai.tts.TTS(**params)
            
            # elif provider == "cartesia":
            #     # Default emotion settings if not provided
            #     emotion = kwargs.get("emotion", ["curiosity:highest", "positivity:high"])
                
            #     return cartesia.TTS(
            #         model=model,
            #         voice=voice,
            #         emotion=emotion
            #     )
            
            else:
                # Default to OpenAI TTS
                logger.warning(f"Unknown TTS provider '{provider}', falling back to OpenAI")
                return openai.tts.TTS(model="gpt-4o-mini-tts", voice="nova")
        except Exception as e:
            logger.error(f"Failed to initialize {provider} TTS with model {model}: {e}")
            # Fallback to a simpler model
            try:
                return openai.tts.TTS(model="gpt-4o-mini-tts", voice="alloy")
            except Exception as e2:
                logger.critical(f"Failed to initialize any TTS model: {e2}")
                return None
    
    @staticmethod
    def get_stt(provider, model, **kwargs):
        """Get an STT instance based on provider and model.
        
        Args:
            provider (str): The provider name (openai, groq, deepgram, etc.)
            model (str): The model identifier
            **kwargs: Additional provider-specific parameters
            
        Returns:
            object: The initialized STT model instance or None if initialization fails
        """
        try:
            if provider == "openai":
                return openai.stt.STT(model=model, **kwargs)
            
            elif provider == "groq":
                return openai.stt.STT.with_groq(model=model, **kwargs)
            
            elif provider == "deepgram":
                return deepgram.stt.STT(
                    model=model,
                )
            
            else:
                # Default to Deepgram
                logger.warning(f"Unknown STT provider '{provider}', falling back to Deepgram")
                return deepgram.stt.STT(model="nova-3")
        except Exception as e:
            logger.error(f"Failed to initialize {provider} STT with model {model}: {e}")
            # Fallback to a simpler model
            try:
                return deepgram.stt.STT(model="nova-2-general")
            except Exception as e2:
                logger.critical(f"Failed to initialize any STT model: {e2}")
                return None
