"""Model configuration classes for different providers."""

class ModelsConfig:
    """Configuration classes for different model providers."""
    
    class OpenAI:
        """OpenAI model configurations."""
        LLM_MODELS = {
            "gpt-4o": "gpt-4o",
            "gpt-4o-mini": "gpt-4o-mini"
        }
        
        TTS_MODELS = {
            "gpt-4o-mini-tts": "gpt-4o-mini-tts"
        }
        
        # Available voices for OpenAI TTS
        TTS_VOICES = [
            "alloy", "ash", "ballad", "coral", "echo", 
            "fable", "onyx", "nova", "sage", "shimmer", "verse"
        ]
        
        STT_MODELS = {
            "gpt-4o-mini-transcribe": "gpt-4o-mini-transcribe"
        }
    
    class Groq:
        """Groq model configurations."""
        LLM_MODELS = {
            "meta-llama/llama-4-maverick-17b-128e-instruct": "meta-llama/llama-4-maverick-17b-128e-instruct"
        }
        
        STT_MODELS = {
            "whisper-large-v3-turbo": "whisper-large-v3-turbo"
        }
    
    # class Cartesia:
    #     """Cartesia model configurations."""
    #     TTS_MODELS = {
    #         "sonic-2": "sonic-2"
    #     }
        
    #     # Voice IDs for Cartesia
    #     TTS_VOICES = {
    #         "female_1": "32b3f3c5-7171-46aa-abe7-b598964aa793",
    #         "female_2": "c99d36f3-5ffd-4253-803a-535c1bc9c306",
    #         "male_1": "bf0a246a-8642-498a-9950-80c35e9276b5",
    #         "male_2": "6f84f4b8-58a2-430c-8c79-688dad597532"
    #     }
    
    class Deepgram:
        """Deepgram model configurations."""
        STT_MODELS = {
            "nova-2-general": "nova-2-general",
            "nova-2-meeting": "nova-2-meeting"
        }
