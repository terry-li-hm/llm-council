"""Pytest configuration and fixtures for LLM Council tests."""

import os

# Set dummy API key before any imports that require it
# This must happen before backend.config is imported
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_for_unit_tests")
