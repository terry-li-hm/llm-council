"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    enable_thinking: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds
        enable_thinking: Whether to enable extended thinking mode

    Returns:
        Response dict with 'content', optional 'reasoning_details', and optional 'thinking'
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    # Add reasoning parameters for models that support it
    # OpenRouter uses a unified "reasoning" parameter for thinking/reasoning models
    if enable_thinking:
        # Models that support the reasoning parameter with effort control
        # Note: x-ai/grok-4 has internal reasoning but it's not exposed/tunable
        reasoning_models = {
            "openai/gpt-5.1",
            "google/gemini-3-pro-preview",
            "anthropic/claude-opus-4.5",
            "google/gemini-2.5-pro",
            "google/gemini-2.5-flash-preview",
            "deepseek/deepseek-r1",
        }

        if model in reasoning_models:
            payload["reasoning"] = {"effort": "high"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            result = {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details'),
            }

            # Extract thinking content if present (Anthropic format)
            if 'thinking' in message:
                result['thinking'] = message['thinking']

            return result

    except httpx.HTTPStatusError as e:
        print(f"Error querying model {model}: {e}")
        print(f"Response body: {e.response.text}")
        return None
    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    enable_thinking: bool = False
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model
        enable_thinking: Whether to enable extended thinking mode

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    # Increase timeout when thinking is enabled (reasoning takes longer)
    timeout = 300.0 if enable_thinking else 120.0

    # Create tasks for all models
    tasks = [
        query_model(model, messages, timeout=timeout, enable_thinking=enable_thinking)
        for model in models
    ]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
