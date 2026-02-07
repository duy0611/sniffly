"""
Pricing utilities for calculating Claude API costs.
Uses LiteLLM pricing data with local fallback.
"""

import logging

from ..config import Config

logger = logging.getLogger(__name__)

# Default pricing in USD per token (not per million)
# Based on Anthropic's public pricing
DEFAULT_CLAUDE_PRICING = {
    "claude-opus-4-20250514": {
        "input_cost_per_token": 15.0 / 1_000_000,  # $15 per million
        "output_cost_per_token": 75.0 / 1_000_000,  # $75 per million
        "cache_creation_cost_per_token": 18.75 / 1_000_000,  # $18.75 per million
        "cache_read_cost_per_token": 1.50 / 1_000_000,  # $1.50 per million
    },
    "claude-3-5-sonnet-20241022": {
        "input_cost_per_token": 3.0 / 1_000_000,  # $3 per million
        "output_cost_per_token": 15.0 / 1_000_000,  # $15 per million
        "cache_creation_cost_per_token": 3.75 / 1_000_000,  # $3.75 per million
        "cache_read_cost_per_token": 0.30 / 1_000_000,  # $0.30 per million
    },
    "claude-3-5-haiku-20241022": {
        "input_cost_per_token": 1.0 / 1_000_000,  # $1 per million
        "output_cost_per_token": 5.0 / 1_000_000,  # $5 per million
        "cache_creation_cost_per_token": 1.25 / 1_000_000,  # $1.25 per million
        "cache_read_cost_per_token": 0.10 / 1_000_000,  # $0.10 per million
    },
    "claude-3-opus-20240229": {
        "input_cost_per_token": 15.0 / 1_000_000,  # $15 per million
        "output_cost_per_token": 75.0 / 1_000_000,  # $75 per million
        "cache_creation_cost_per_token": 18.75 / 1_000_000,  # $18.75 per million
        "cache_read_cost_per_token": 1.50 / 1_000_000,  # $1.50 per million
    },
    "claude-3-sonnet-20240229": {
        "input_cost_per_token": 3.0 / 1_000_000,  # $3 per million
        "output_cost_per_token": 15.0 / 1_000_000,  # $15 per million
        "cache_creation_cost_per_token": 3.75 / 1_000_000,  # $3.75 per million
        "cache_read_cost_per_token": 0.30 / 1_000_000,  # $0.30 per million
    },
    "claude-3-haiku-20240307": {
        "input_cost_per_token": 0.25 / 1_000_000,  # $0.25 per million
        "output_cost_per_token": 1.25 / 1_000_000,  # $1.25 per million
        "cache_creation_cost_per_token": 0.30 / 1_000_000,  # $0.30 per million
        "cache_read_cost_per_token": 0.03 / 1_000_000,  # $0.03 per million
    },
}

# Vertex AI pricing (global endpoints)
# Source: https://cloud.google.com/vertex-ai/generative-ai/pricing
# Last updated: 2026-02-05
# Note: Global endpoint pricing matches Anthropic API pricing
# Regional endpoints add 10% premium (applied at calculation time)
VERTEX_AI_PRICING = {
    "claude-opus-4-20250514": {
        "input_cost_per_token": 15.0 / 1_000_000,
        "output_cost_per_token": 75.0 / 1_000_000,
        "cache_creation_cost_per_token": 18.75 / 1_000_000,
        "cache_read_cost_per_token": 1.50 / 1_000_000,
    },
    "claude-3-5-sonnet-20241022": {
        "input_cost_per_token": 3.0 / 1_000_000,
        "output_cost_per_token": 15.0 / 1_000_000,
        "cache_creation_cost_per_token": 3.75 / 1_000_000,
        "cache_read_cost_per_token": 0.30 / 1_000_000,
    },
    "claude-3-5-haiku-20241022": {
        "input_cost_per_token": 1.0 / 1_000_000,
        "output_cost_per_token": 5.0 / 1_000_000,
        "cache_creation_cost_per_token": 1.25 / 1_000_000,
        "cache_read_cost_per_token": 0.10 / 1_000_000,
    },
    "claude-3-opus-20240229": {
        "input_cost_per_token": 15.0 / 1_000_000,
        "output_cost_per_token": 75.0 / 1_000_000,
        "cache_creation_cost_per_token": 18.75 / 1_000_000,
        "cache_read_cost_per_token": 1.50 / 1_000_000,
    },
    "claude-3-sonnet-20240229": {
        "input_cost_per_token": 3.0 / 1_000_000,
        "output_cost_per_token": 15.0 / 1_000_000,
        "cache_creation_cost_per_token": 3.75 / 1_000_000,
        "cache_read_cost_per_token": 0.30 / 1_000_000,
    },
    "claude-3-haiku-20240307": {
        "input_cost_per_token": 0.25 / 1_000_000,
        "output_cost_per_token": 1.25 / 1_000_000,
        "cache_creation_cost_per_token": 0.30 / 1_000_000,
        "cache_read_cost_per_token": 0.03 / 1_000_000,
    },
}

# Cache for dynamic pricing
_dynamic_pricing_cache = None


def get_dynamic_pricing() -> dict[str, dict[str, float]]:
    """Get pricing from service or fallback to defaults."""
    global _dynamic_pricing_cache

    if _dynamic_pricing_cache is None:
        try:
            from ..services.pricing_service import PricingService

            # Get pricing provider from config
            config = Config()
            pricing_provider = config.get("pricing_provider", "anthropic")

            service = PricingService()
            pricing_data = service.get_pricing(provider=pricing_provider)
            _dynamic_pricing_cache = pricing_data.get("pricing", DEFAULT_CLAUDE_PRICING)
        except Exception as e:
            logger.info(f"Error loading dynamic pricing: {e}")
            _dynamic_pricing_cache = DEFAULT_CLAUDE_PRICING

    return _dynamic_pricing_cache


def get_model_pricing(model_name: str) -> dict[str, float] | None:
    """
    Get pricing for a specific model.
    Returns pricing dict or None if model not found.
    """
    # Get dynamic pricing
    pricing_data = get_dynamic_pricing()

    # Direct match
    if model_name in pricing_data:
        return pricing_data[model_name]

    # Try to match by partial name (e.g., "claude-3-5-sonnet" without date)
    for known_model, pricing in pricing_data.items():
        if model_name in known_model or known_model in model_name:
            return pricing

    # Default to Sonnet pricing if model not recognized
    # This is a reasonable default for unknown Claude models
    return pricing_data.get("claude-3-5-sonnet-20241022") or DEFAULT_CLAUDE_PRICING.get("claude-3-5-sonnet-20241022")


def calculate_cost(tokens: dict[str, int], model: str) -> dict[str, float]:
    """
    Calculate cost breakdown for given tokens and model.

    Args:
        tokens: Dict with keys 'input', 'output', 'cache_creation', 'cache_read'
        model: Model name string

    Returns:
        Dict with cost breakdown by token type and total
    """
    pricing = get_model_pricing(model)
    if not pricing:
        return {
            "input_cost": 0.0,
            "output_cost": 0.0,
            "cache_creation_cost": 0.0,
            "cache_read_cost": 0.0,
            "total_cost": 0.0,
        }

    costs = {
        "input_cost": tokens.get("input", 0) * pricing["input_cost_per_token"],
        "output_cost": tokens.get("output", 0) * pricing["output_cost_per_token"],
        "cache_creation_cost": tokens.get("cache_creation", 0) * pricing["cache_creation_cost_per_token"],
        "cache_read_cost": tokens.get("cache_read", 0) * pricing["cache_read_cost_per_token"],
    }

    # Apply 10% regional premium for vertex_ai_regional
    config = Config()
    pricing_provider = config.get("pricing_provider", "anthropic")
    if pricing_provider == "vertex_ai_regional":
        regional_premium = 1.10
        costs["input_cost"] *= regional_premium
        costs["output_cost"] *= regional_premium
        costs["cache_creation_cost"] *= regional_premium
        costs["cache_read_cost"] *= regional_premium

    costs["total_cost"] = sum(costs.values())
    return costs


def format_cost(cost: float) -> str:
    """Format cost for display."""
    if cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"
