"""Tests for pricing utilities."""

from unittest.mock import patch

from sniffly.utils.pricing import (
    DEFAULT_CLAUDE_PRICING,
    VERTEX_AI_PRICING,
    calculate_cost,
    get_dynamic_pricing,
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
        for _model, pricing in VERTEX_AI_PRICING.items():
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


class TestProviderPricing:
    """Test provider-specific pricing."""

    @patch("sniffly.utils.pricing.Config")
    def test_get_dynamic_pricing_anthropic(self, mock_config):
        """Test getting Anthropic pricing."""
        mock_config_instance = mock_config.return_value
        mock_config_instance.get.return_value = "anthropic"

        # Reset cache
        import sniffly.utils.pricing as pricing_module
        pricing_module._dynamic_pricing_cache = None

        pricing = get_dynamic_pricing()
        assert pricing is not None
        assert isinstance(pricing, dict)

    @patch("sniffly.utils.pricing.Config")
    def test_get_dynamic_pricing_vertex_ai(self, mock_config):
        """Test getting Vertex AI pricing."""
        mock_config_instance = mock_config.return_value
        mock_config_instance.get.return_value = "vertex_ai"

        # Reset cache
        import sniffly.utils.pricing as pricing_module
        pricing_module._dynamic_pricing_cache = None

        pricing = get_dynamic_pricing()
        assert pricing == VERTEX_AI_PRICING

    @patch("sniffly.utils.pricing.Config")
    def test_calculate_cost_with_vertex_ai_regional(self, mock_config):
        """Test cost calculation with Vertex AI regional pricing (10% premium)."""
        mock_config_instance = mock_config.return_value
        mock_config_instance.get.return_value = "vertex_ai_regional"

        # Reset cache
        import sniffly.utils.pricing as pricing_module
        pricing_module._dynamic_pricing_cache = None

        tokens = {
            "input": 1_000_000,
            "output": 1_000_000,
            "cache_creation": 0,
            "cache_read": 0,
        }

        costs = calculate_cost(tokens, "claude-3-5-sonnet-20241022")

        # Base Vertex pricing: $3 input, $15 output
        # With 10% regional premium: $3.30 input, $16.50 output
        expected_input = 3.0 * 1.10
        expected_output = 15.0 * 1.10

        assert abs(costs["input_cost"] - expected_input) < 0.01
        assert abs(costs["output_cost"] - expected_output) < 0.01
        assert abs(costs["total_cost"] - (expected_input + expected_output)) < 0.01
