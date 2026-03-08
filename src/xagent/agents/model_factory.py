# -*- coding: utf-8 -*-
"""Factory for creating chat models and formatters.

This module provides a unified factory for creating chat model instances
and their corresponding formatters based on configuration.
"""

import os
from typing import Optional, Tuple

from agentscope.formatter import OpenAIChatFormatter
from agentscope.model import OpenAIChatModel


def create_model_and_formatter(provider_type: str = "openai") -> Tuple[OpenAIChatModel, OpenAIChatFormatter]:
    """Factory method to create model and formatter instances.

    This method creates a chat model and its corresponding formatter based on provider type.

    Args:
        provider_type: Provider type (openai, claude, gemini)

    Returns:
        Tuple of (model_instance, formatter_instance)
    """
    # Get configuration from environment based on provider type
    if provider_type == "openai":
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", None)
        
        # Create model instance
        model = OpenAIChatModel(
            model_name,
            api_key=api_key,
            stream=True,
            client_kwargs={"base_url": base_url} if base_url else {}
        )
        
        # Create formatter instance
        formatter = OpenAIChatFormatter()
    elif provider_type == "claude":
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")
        
        # Create model instance (using OpenAIChatModel with Claude API)
        model = OpenAIChatModel(
            model_name,
            api_key=api_key,
            stream=True,
            client_kwargs={"base_url": base_url}
        )
        
        # Create formatter instance
        formatter = OpenAIChatFormatter()
    elif provider_type == "gemini":
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")
        api_key = os.getenv("GEMINI_API_KEY", "")
        base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1")
        
        # Create model instance (using OpenAIChatModel with Gemini API)
        model = OpenAIChatModel(
            model_name,
            api_key=api_key,
            stream=True,
            client_kwargs={"base_url": base_url}
        )
        
        # Create formatter instance
        formatter = OpenAIChatFormatter()
    else:
        # Default to OpenAI
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", None)
        
        # Create model instance
        model = OpenAIChatModel(
            model_name,
            api_key=api_key,
            stream=True,
            client_kwargs={"base_url": base_url} if base_url else {}
        )
        
        # Create formatter instance
        formatter = OpenAIChatFormatter()
    
    return model, formatter


__all__ = [
    "create_model_and_formatter",
]