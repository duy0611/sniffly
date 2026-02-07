# Multi-Provider Pricing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add configuration-based support for switching between pricing providers (Claude API, Vertex AI, Bedrock, etc.) to calculate costs accurately based on where users call models from.

**Architecture:** Extend the existing PricingService to manage multiple provider pricing sources, add a `pricing_provider` config option, and modify cost calculation functions to lookup provider-specific pricing with intelligent fallbacks.

**Tech Stack:** Python 3.12+, FastAPI, pytest

---

## Task 1: Add Configuration Support

**Files:**
- Modify: `sniffly/config.py`
- Test: `tests/sniffly/test_cli.py`

**Step 1: Write the failing test**

Add to `tests/sniffly/test_cli.py` in the `TestConfig` class:

```python
def test_pricing_provider_default(self):
    """Test that pricing_provider defaults to 'anthropic'."""
    config = Config(config_dir=self.temp_dir)
    assert config.get("pricing_provider") == "anthropic"

def test_pricing_provider_set_and_get(self):
    """Test setting and getting pricing_provider."""
    config = Config(config_dir=self.temp_dir)
    config.set("pricing_provider", "vertex_ai")
    assert config.get("pricing_provider") == "vertex_ai"

def test_pricing_provider_environment_override(self):
    """Test that PRICING_PROVIDER environment variable overrides config."""
    os.environ["PRICING_PROVIDER"] = "vertex_ai_regional"
    config = Config(config_dir=self.temp_dir)
    assert config.get("pricing_provider") == "vertex_ai_regional"
    del os.environ["PRICING_PROVIDER"]

def test_pricing_provider_validation(self):
    """Test that invalid pricing providers are handled."""
    config = Config(config_dir=self.temp_dir)
    # Should not raise - validation happens at usage time
    config.set("pricing_provider", "invalid_provider")
    assert config.get("pricing_provider") == "invalid_provider"
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/sniffly/test_cli.py::TestConfig::test_pricing_provider_default -v`

Expected: FAIL with KeyError for "pricing_provider"

**Step 3: Add config defaults and mappings**

In `sniffly/config.py`, add to DEFAULTS dict (around line 13-27):

```python
DEFAULTS = {
    "port": 8081,
    "host": "127.0.0.1",
    "cache_max_projects": 5,
    "cache_max_mb_per_project": 500,
    "auto_browser": True,
    "max_date_range_days": 30,
    "messages_initial_load": 500,
    "enable_memory_monitor": False,
    "enable_background_processing": True,
    "cache_warm_on_startup": 3,
    "log_level": "INFO",
    "share_base_url": "https://sniffly.dev",
    "share_api_url": "https://sniffly.dev",
    "share_enabled": True,
    "pricing_provider": "anthropic",  # ADD THIS LINE
}
```

Add to ENV_MAPPINGS dict (around line 31-46):

```python
ENV_MAPPINGS = {
    "port": "PORT",
    "host": "HOST",
    "cache_max_projects": "CACHE_MAX_PROJECTS",
    "cache_max_mb_per_project": "CACHE_MAX_MB_PER_PROJECT",
    "auto_browser": "AUTO_BROWSER",
    "max_date_range_days": "MAX_DATE_RANGE_DAYS",
    "messages_initial_load": "MESSAGES_INITIAL_LOAD",
    "enable_memory_monitor": "ENABLE_MEMORY_MONITOR",
    "enable_background_processing": "ENABLE_BACKGROUND_PROCESSING",
    "cache_warm_on_startup": "CACHE_WARM_ON_STARTUP",
    "log_level": "LOG_LEVEL",
    "share_base_url": "SHARE_BASE_URL",
    "share_api_url": "SHARE_API_URL",
    "share_enabled": "SHARE_ENABLED",
    "pricing_provider": "PRICING_PROVIDER",  # ADD THIS LINE
}
```

**Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/sniffly/test_cli.py::TestConfig -k pricing_provider -v`

Expected: All 4 new tests PASS

**Step 5: Commit**

```bash
git add sniffly/config.py tests/sniffly/test_cli.py
git commit -m "feat: add pricing_provider configuration option

Add pricing_provider config with default 'anthropic' to support
switching between pricing providers (Claude API, Vertex AI, etc.)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Add Vertex AI Pricing Data

**Files:**
- Modify: `sniffly/utils/pricing.py`
- Test: `tests/sniffly/utils/test_pricing.py` (create new file)

**Step 1: Write the failing test**

Create `tests/sniffly/utils/test_pricing.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && python -m pytest tests/sniffly/utils/test_pricing.py -v`

Expected: FAIL with "cannot import name 'VERTEX_AI_PRICING'"

**Step 3: Add VERTEX_AI_PRICING constant**

In `sniffly/utils/pricing.py`, add after DEFAULT_CLAUDE_PRICING (around line 50):

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/sniffly/utils/test_pricing.py -v`

Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add sniffly/utils/pricing.py tests/sniffly/utils/test_pricing.py
git commit -m "feat: add Vertex AI pricing data

Add VERTEX_AI_PRICING constant with pricing matching Anthropic API
for global endpoints. Regional premium applied at calculation time.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Update PricingService for Multi-Provider Support

**Files:**
- Modify: `sniffly/services/pricing_service.py`
- Test: `tests/sniffly/services/test_pricing_service.py` (create new file)

**Step 1: Write the failing test**

Create `tests/sniffly/services/test_pricing_service.py`:

```python
"""Tests for pricing service."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sniffly.services.pricing_service import PricingService
from sniffly.utils.pricing import DEFAULT_CLAUDE_PRICING, VERTEX_AI_PRICING


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
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && python -m pytest tests/sniffly/services/test_pricing_service.py -v`

Expected: FAIL with "get_pricing() got an unexpected keyword argument 'provider'"

**Step 3: Update PricingService.get_pricing() signature**

In `sniffly/services/pricing_service.py`, modify the `get_pricing` method (around line 29):

```python
def get_pricing(self, provider: str = "anthropic") -> dict[str, any]:
    """
    Get pricing with intelligent cache and fallback logic.

    Args:
        provider: Pricing provider ('anthropic', 'vertex_ai', 'vertex_ai_regional')

    Returns:
        Dict with keys:
        - pricing: Dict of model prices
        - source: 'cache', 'litellm', 'manual', or 'default'
        - timestamp: When prices were fetched
        - is_stale: Boolean indicating if cache is expired
    """
    # Handle Vertex AI providers with manual pricing
    if provider in ("vertex_ai", "vertex_ai_regional"):
        from ..utils.pricing import VERTEX_AI_PRICING
        return {
            "pricing": VERTEX_AI_PRICING,
            "source": "manual",
            "timestamp": "2026-02-05T00:00:00Z",
            "is_stale": False,
        }

    # For anthropic and unknown providers, use existing logic
    # Check if cache exists and load it
    cache_data = self._load_cache()

    if cache_data:
        is_valid = self._is_cache_valid(cache_data.get("timestamp"))

        if is_valid:
            # Cache is fresh, use it
            return {
                "pricing": cache_data["pricing"],
                "source": "cache",
                "timestamp": cache_data["timestamp"],
                "is_stale": False,
            }
        else:
            # Cache is stale, try to refresh
            fresh_data = self._fetch_from_litellm()

            if fresh_data:
                # Successfully fetched fresh data
                self._save_to_cache(fresh_data)
                return {
                    "pricing": fresh_data,
                    "source": "litellm",
                    "timestamp": datetime.utcnow().isoformat(),
                    "is_stale": False,
                }
            else:
                # Failed to fetch, use stale cache
                return {
                    "pricing": cache_data["pricing"],
                    "source": "cache",
                    "timestamp": cache_data["timestamp"],
                    "is_stale": True,
                }
    else:
        # No cache exists, try to fetch
        fresh_data = self._fetch_from_litellm()

        if fresh_data:
            # Successfully fetched data
            self._save_to_cache(fresh_data)
            return {
                "pricing": fresh_data,
                "source": "litellm",
                "timestamp": datetime.utcnow().isoformat(),
                "is_stale": False,
            }
        else:
            # No cache and can't fetch - use defaults
            return {
                "pricing": DEFAULT_CLAUDE_PRICING,
                "source": "default",
                "timestamp": datetime.utcnow().isoformat(),
                "is_stale": False,
            }
```

**Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/sniffly/services/test_pricing_service.py -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add sniffly/services/pricing_service.py tests/sniffly/services/test_pricing_service.py
git commit -m "feat: add multi-provider support to PricingService

Update get_pricing() to accept provider parameter and return
provider-specific pricing (Anthropic, Vertex AI, etc.)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Update Cost Calculation with Provider Support

**Files:**
- Modify: `sniffly/utils/pricing.py`
- Test: `tests/sniffly/utils/test_pricing.py`

**Step 1: Write the failing test**

Add to `tests/sniffly/utils/test_pricing.py`:

```python
from unittest.mock import patch
from sniffly.utils.pricing import calculate_cost, get_dynamic_pricing


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
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && python -m pytest tests/sniffly/utils/test_pricing.py::TestProviderPricing -v`

Expected: FAIL - functions don't read config yet

**Step 3: Update get_dynamic_pricing() to read config**

In `sniffly/utils/pricing.py`, update `get_dynamic_pricing()` (around line 56):

```python
def get_dynamic_pricing() -> dict[str, dict[str, float]]:
    """Get pricing from service or fallback to defaults."""
    global _dynamic_pricing_cache

    if _dynamic_pricing_cache is None:
        try:
            from ..config import Config
            from ..services.pricing_service import PricingService

            # Get pricing provider from config
            config = Config()
            provider = config.get("pricing_provider", "anthropic")

            service = PricingService()
            pricing_data = service.get_pricing(provider=provider)
            _dynamic_pricing_cache = pricing_data.get("pricing", DEFAULT_CLAUDE_PRICING)
        except Exception as e:
            logger.info(f"Error loading dynamic pricing: {e}")
            _dynamic_pricing_cache = DEFAULT_CLAUDE_PRICING

    return _dynamic_pricing_cache
```

**Step 4: Update calculate_cost() to apply regional premium**

In `sniffly/utils/pricing.py`, update `calculate_cost()` (around line 96):

```python
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

    # Apply regional premium if using vertex_ai_regional
    try:
        from ..config import Config
        config = Config()
        provider = config.get("pricing_provider", "anthropic")

        if provider == "vertex_ai_regional":
            # Apply 10% premium to all costs
            costs = {k: v * 1.10 for k, v in costs.items()}
    except Exception:
        # If config fails, use costs as-is
        pass

    costs["total_cost"] = sum(costs.values())
    return costs
```

**Step 5: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/sniffly/utils/test_pricing.py::TestProviderPricing -v`

Expected: All tests PASS

**Step 6: Commit**

```bash
git add sniffly/utils/pricing.py tests/sniffly/utils/test_pricing.py
git commit -m "feat: add provider-aware cost calculation

Update get_dynamic_pricing() and calculate_cost() to read
pricing_provider config and apply regional premium for Vertex AI.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Run Full Test Suite

**Step 1: Run all tests**

Run: `source .venv/bin/activate && python run_tests.py`

Expected: All tests PASS (no regressions)

**Step 2: Fix any failures**

If any tests fail, debug and fix them. Common issues:
- Import errors - add missing imports
- Cache state - tests may need to reset `_dynamic_pricing_cache`
- Mock config - ensure config mocks are properly cleaned up

**Step 3: Commit any fixes**

```bash
git add <fixed-files>
git commit -m "fix: resolve test failures

<describe what was fixed>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Add CLI Documentation

**Files:**
- Modify: `sniffly/cli.py`
- Test: Manual testing

**Step 1: Update help text for config command**

In `sniffly/cli.py`, find the config command help (around line with `@cli.group()`):

Add documentation showing the new pricing_provider option:

```python
@cli.group()
def config():
    """Manage Sniffly configuration.

    Available settings:
    - pricing_provider: Pricing source ('anthropic', 'vertex_ai', 'vertex_ai_regional')
    - port: Server port (default: 8081)
    - host: Server host (default: 127.0.0.1)
    - auto_browser: Auto-open browser (default: true)
    - ... (other settings)

    Examples:
      sniffly config set pricing_provider vertex_ai
      sniffly config show
    """
    pass
```

**Step 2: Test CLI manually**

Run: `source .venv/bin/activate && sniffly config show`

Should show `pricing_provider: anthropic`

Run: `sniffly config set pricing_provider vertex_ai && sniffly config show`

Should show `pricing_provider: vertex_ai`

**Step 3: Commit**

```bash
git add sniffly/cli.py
git commit -m "docs: add pricing_provider to CLI help

Document new pricing_provider config option in CLI help text.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `CLAUDE.md`
- Create: `docs/pricing-providers.md`

**Step 1: Create pricing providers documentation**

Create `docs/pricing-providers.md`:

```markdown
# Pricing Providers

Sniffly supports multiple pricing providers to accurately calculate costs based on where you're calling Claude models from.

## Supported Providers

### Anthropic (Default)

Direct Claude API pricing from Anthropic.

```bash
sniffly config set pricing_provider anthropic
```

### Vertex AI Global

Google Cloud Vertex AI pricing for global endpoints. Same pricing as Anthropic API.

```bash
sniffly config set pricing_provider vertex_ai
```

### Vertex AI Regional

Google Cloud Vertex AI pricing for regional endpoints. Adds 10% premium to global pricing for dedicated regional capacity.

```bash
sniffly config set pricing_provider vertex_ai_regional
```

## How It Works

1. **Configuration**: Set your pricing provider via `sniffly config set pricing_provider <provider>`
2. **Cost Calculation**: Sniffly uses provider-specific pricing when calculating costs
3. **Caching**: Pricing data is cached locally for 24 hours
4. **Fallback**: If provider pricing fails, falls back to Anthropic pricing

## Pricing Sources

- **Anthropic**: Fetched from LiteLLM (auto-updated)
- **Vertex AI**: Manual pricing based on Google Cloud documentation
- **Last Updated**: 2026-02-05

## See Also

- [Google Cloud Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
```

**Step 2: Update CLAUDE.md**

Add to `CLAUDE.md` after the "CLI Commands" section:

```markdown
### Pricing Providers

Configure pricing provider to match where you call Claude from:

```bash
sniffly config set pricing_provider anthropic           # Direct Claude API (default)
sniffly config set pricing_provider vertex_ai           # Vertex AI global endpoints
sniffly config set pricing_provider vertex_ai_regional  # Vertex AI regional (+10%)
```

See `docs/pricing-providers.md` for details.
```

**Step 3: Commit**

```bash
git add docs/pricing-providers.md CLAUDE.md
git commit -m "docs: add pricing provider documentation

Add comprehensive pricing provider docs and update CLAUDE.md
with configuration examples.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Integration Testing

**Step 1: Test end-to-end with different providers**

Manual test:

```bash
# Test with Anthropic (default)
sniffly config set pricing_provider anthropic
sniffly init  # Start server, check dashboard shows costs

# Test with Vertex AI
sniffly config set pricing_provider vertex_ai
sniffly init  # Verify costs are calculated

# Test with Vertex AI regional
sniffly config set pricing_provider vertex_ai_regional
sniffly init  # Verify costs are ~10% higher
```

**Step 2: Verify pricing consistency**

Check that:
- Dashboard loads without errors
- Costs are displayed correctly
- Switching providers updates costs appropriately
- No console errors in browser

**Step 3: Document any issues found**

Create issues for any problems discovered during testing.

---

## Task 9: Final Cleanup and Review

**Step 1: Run linter**

Run: `source .venv/bin/activate && ./lint.sh`

Fix any linting issues.

**Step 2: Run full test suite one more time**

Run: `source .venv/bin/activate && python run_tests.py`

Expected: All tests PASS

**Step 3: Review all changes**

Run: `git log --oneline main..HEAD`

Verify all commits are present and properly attributed.

**Step 4: Final commit if needed**

If there were lint fixes:

```bash
git add <fixed-files>
git commit -m "chore: fix linting issues

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Completion Checklist

- [ ] Configuration support added (`pricing_provider`)
- [ ] Vertex AI pricing data added
- [ ] PricingService updated for multi-provider support
- [ ] Cost calculation updated with provider awareness
- [ ] Regional premium (10%) implemented
- [ ] All tests passing
- [ ] CLI documentation updated
- [ ] User documentation created
- [ ] Integration testing completed
- [ ] Code linted and clean
- [ ] All commits properly attributed

## Next Steps

After implementation:
1. Use @superpowers:finishing-a-development-branch to merge
2. Create PR with design doc and implementation plan
3. Manual testing on real Claude logs
4. Consider adding AWS Bedrock pricing support
5. Consider adding Azure pricing support
