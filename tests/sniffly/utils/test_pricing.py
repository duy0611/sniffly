"""Tests for pricing utilities."""

import pytest
from sniffly.utils.pricing import (
    DEFAULT_CLAUDE_PRICING,
    VERTEX_AI_PRICING,
    get_model_pricing,
)


class TestVertexAIPricing:
    """Test Vertex AI pricing data."""

    def test_vertex_ai_pricing_exists(self):
        """Test that VERTEX_AI_PRICING constant exists."""
        assert VERTEX_AI_PRICING is not None
        assert isinstance(VERTEX_AI_PRICING, dict)

    def test_vertex_ai_has_same_models_as_anthropic(self):
        """Test that Vertex AI pricing covers same models as Anthropic."""
        anthropic_models = set(DEFAULT_CLAUDE_PRICING.keys())
        vertex_models = set(VERTEX_AI_PRICING.keys())
        assert anthropic_models == vertex_models

    def test_vertex_ai_pricing_structure(self):
        """Test that Vertex AI pricing has correct structure."""
        for model, pricing in VERTEX_AI_PRICING.items():
            assert "input_cost_per_token" in pricing
            assert "output_cost_per_token" in pricing
            assert "cache_creation_cost_per_token" in pricing
            assert "cache_read_cost_per_token" in pricing
            assert all(isinstance(v, float) for v in pricing.values())

    def test_vertex_ai_pricing_matches_anthropic(self):
        """Test that Vertex AI global pricing matches Anthropic pricing."""
        # For global endpoints, pricing should be identical
        for model in DEFAULT_CLAUDE_PRICING:
            anthropic = DEFAULT_CLAUDE_PRICING[model]
            vertex = VERTEX_AI_PRICING[model]
            assert anthropic["input_cost_per_token"] == vertex["input_cost_per_token"]
            assert anthropic["output_cost_per_token"] == vertex["output_cost_per_token"]
            assert anthropic["cache_creation_cost_per_token"] == vertex["cache_creation_cost_per_token"]
            assert anthropic["cache_read_cost_per_token"] == vertex["cache_read_cost_per_token"]

    def test_vertex_ai_sonnet_pricing_accuracy(self):
        """Test that Vertex AI Sonnet 3.5 pricing matches documented values."""
        sonnet = VERTEX_AI_PRICING["claude-3-5-sonnet-20241022"]
        assert sonnet["input_cost_per_token"] == 3.0 / 1_000_000
        assert sonnet["output_cost_per_token"] == 15.0 / 1_000_000
        assert sonnet["cache_creation_cost_per_token"] == 3.75 / 1_000_000
        assert sonnet["cache_read_cost_per_token"] == 0.30 / 1_000_000
