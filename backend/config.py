"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers
COUNCIL_MODELS = [
    "openai/gpt-5.1",
    "google/gemini-3-pro-preview",
    "anthropic/claude-opus-4.5",
    "x-ai/grok-4",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "google/gemini-3-pro-preview"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# Thinking mode configuration
# Extended thinking helps models reason more carefully before responding
THINKING_CONFIG = {
    "enabled": True,
    "stages": {
        "stage1": False,  # Keep Stage 1 fast for diverse initial responses
        "stage2": True,   # Enable for careful peer evaluation
        "stage3": True,   # Enable for thoughtful chairman synthesis
    },
    "budget_tokens": 10000,  # Token budget for thinking (where supported)
}
