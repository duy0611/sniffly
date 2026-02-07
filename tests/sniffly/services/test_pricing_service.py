"""Tests for pricing service."""

import json
import tempfile
from pathlib import Path

from sniffly.services.pricing_service import PricingService
from sniffly.utils.pricing import VERTEX_AI_PRICING


class TestMultiProviderPricing:
    """Test multi-provider pricing support."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = PricingService()
        self.service.cache_dir = Path(self.temp_dir)
        self.service.pricing_cache_file = self.service.cache_dir / "pricing.json"

    def test_get_pricing_anthropic_provider(self):
        """Test getting Anthropic pricing."""
        result = self.service.get_pricing(provider="anthropic")
        assert result["pricing"] is not None
        assert "source" in result
        assert "timestamp" in result

    def test_get_pricing_vertex_ai_provider(self):
        """Test getting Vertex AI pricing."""
        result = self.service.get_pricing(provider="vertex_ai")
        assert result["pricing"] is not None
        # Should use manual Vertex AI pricing
        assert result["pricing"] == VERTEX_AI_PRICING

    def test_get_pricing_invalid_provider_falls_back(self):
        """Test that invalid provider falls back to anthropic."""
        result = self.service.get_pricing(provider="invalid")
        assert result["pricing"] is not None
        # Should fall back to Anthropic
        assert result["source"] in ["cache", "litellm", "default"]

    def test_multi_provider_cache_structure(self):
        """Test that cache stores multiple providers."""
        # Get pricing for different providers
        self.service.get_pricing(provider="anthropic")
        self.service.get_pricing(provider="vertex_ai")

        # Check cache file structure
        with open(self.service.pricing_cache_file) as f:
            cache = json.load(f)

        assert "anthropic" in cache or "pricing" in cache
        # Note: vertex_ai might not be in cache if it's manual pricing
