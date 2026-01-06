# Voice Pipeline Agent - Python

This project implements a voice agent with multiple persona options (assistant, friend, girlfriend, boyfriend), each with configurable models for natural language processing, text-to-speech, and speech-to-text conversion.

## Project Structure

The codebase has been restructured into a production-ready format with the following organization:

```
voice-pipeline-agent-python/
├── main.py                 # Main entry point for the application
├── src/                    # Source code directory
│   ├── agents/             # Agent implementations
│   │   └── agent.py        # Voice Pipeline Agent runner
│   ├── config/             # Configuration settings
│   │   └── agent_configs.py # Agent personality configurations
│   ├── models/             # Model implementations
│   │   ├── model_config.py # Model providers and configurations
│   │   └── model_factory.py # Factory methods for model creation
│   └── utils/              # Utility functions
│       ├── environment.py  # Environment variable management
│       └── logger.py       # Logging configuration
├── requirements.txt        # Project dependencies
├── Dockerfile              # Docker configuration for deployment
└── docker-compose.yml      # Docker Compose configuration
```

## Features

- **Multiple Agent Personalities**: Choose between assistant, friend, girlfriend, or boyfriend personas
- **Configurable Models**: Each agent can use different LLM, TTS, and STT models
- **Model Provider Support**: Works with OpenAI, Groq, Cartesia, and Deepgram
- **Voice Activity Detection**: Uses Silero VAD model for better speech detection
- **Noise Cancellation**: Optional background noise removal

## Setup and Installation

### Local Development

1. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your API keys and configuration
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

## Agent Configuration

The agent configurations are defined in `src/config/agent_configs.py`. You can modify existing agent types or add new ones by following the same structure.

Each agent configuration includes:
- System prompt defining the agent's personality
- Greeting message
- Description
- Avatar URL
- Model configurations for LLM, TTS, and STT

Example:
```python
"assistant": {
    "prompt": "You are a voice assistant created by M0...",
    "greeting": "Hey, how can I help you today?",
    "description": "A helpful voice assistant for everyday tasks",
    "avatar": "https://source.unsplash.com/random/400x400/?robot,assistant",
    "models": {
        "llm": { ... },
        "tts": { ... },
        "stt": { ... }
    }
}
```

## Advanced Customization

### Adding New Model Providers

To add support for a new model provider:

1. Add the provider's configuration to `src/models/model_config.py`
2. Implement the provider in the factory methods in `src/models/model_factory.py`
3. Update agent configurations in `src/config/agent_configs.py` to use the new provider

### Adding New Agent Types

To create a new agent personality:

1. Add a new entry to the `AGENT_CONFIGS` dictionary in `src/config/agent_configs.py`
2. Follow the structure of existing agent configurations

## Prerequisites

- Docker and Docker Compose installed on your production server
- API keys for the services used by the application (OpenAI, Groq, Cartesia, Deepgram)
- LiveKit server URL and credentials

## Setup

1. **Create Environment File**

   Copy the example environment file and add your credentials:

   ```bash
   cp .env.local.example .env.local
   ```

   Then edit `.env.local` to add your actual API keys and configuration.

2. **Build and Deploy with Docker Compose**

   ```bash
   # close the docker:running
   sudo docker-compose down --volumes
   
   # Build the Docker image
   docker-compose build

   # Start the application in detached mode
   docker-compose up -d
   ```

3. **Check Logs**

   ```bash
   docker-compose logs -f
   ```

## Scaling

To deploy multiple instances of the application, you can modify the `docker-compose.yml` file to add more services or use Docker Swarm or Kubernetes for orchestration.

## Maintenance

- **Restart the Service**:
  ```bash
  docker-compose restart
  ```

- **Update the Application**:
  ```bash
  git pull  # Get latest code
  docker-compose down
  docker-compose build
  docker-compose up -d
  ```

- **View Logs**:
  ```bash
  docker-compose logs -f
  ```

## Troubleshooting

- Check the container logs for errors: `docker-compose logs`
- Verify that all required environment variables are set in `.env.local`
- Check if the container has network access to external services (OpenAI, Groq, etc.)
- Ensure your LiveKit server is accessible from the Docker container
