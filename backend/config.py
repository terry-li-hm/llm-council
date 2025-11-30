"""Configuration for the LLM Council."""

import os
import logging
from dotenv import load_dotenv, find_dotenv

# Load .env file, override=True ensures .env takes precedence over shell environment
load_dotenv(find_dotenv(), override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Validate required configuration on startup
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable is required")

# CORS origins (comma-separated list)
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

# Council members - list of OpenRouter model identifiers
COUNCIL_MODELS = [
    "openai/gpt-5.1",
    "google/gemini-3-pro-preview",
    "anthropic/claude-opus-4.5",
    "x-ai/grok-4",
    "moonshotai/kimi-k2-thinking",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "google/gemini-3-pro-preview"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# System prompts for different roles
# Set to None or empty string to disable system prompts
SYSTEM_PROMPTS = {
    # System prompt for council members (Stage 1 and Stage 2)
    "council": "",
    # System prompt for the chairman (Stage 3 and follow-ups)
    "chairman": "Use continuous paragraphs rather than structured notes. Avoid headings or bullet points unless the user explicitly requests a list, step-by-step guide, or pros-and-cons comparison. When in doubt, use simple prose and clearly explain ideas in a few concise, straightforward paragraphs.",
}

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
