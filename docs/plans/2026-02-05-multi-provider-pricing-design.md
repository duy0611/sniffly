# Multi-Provider Pricing Support Design

**Date:** 2026-02-05
**Status:** Approved
**Author:** User with Claude Sonnet 4.5

## Overview

Add support for switching between different pricing providers (Claude API, Vertex AI, Bedrock, etc.) to calculate costs accurately based on where users are calling the models from.

## Current Architecture

The system currently:
1. Fetches pricing from LiteLLM's GitHub repo (Anthropic provider only)
2. Caches pricing locally for 24 hours
3. Falls back to hardcoded `DEFAULT_CLAUDE_PRICING` if fetch fails
4. Uses `calculate_cost()` in `sniffly/utils/pricing.py` for all cost calculations

### Key Insight

LiteLLM doesn't currently track Vertex AI Claude models separately (they only have `bedrock`, `bedrock_converse`, and `azure_ai` providers). We'll add manual Vertex AI pricing based on Google Cloud's official rates, with flexibility to switch to LiteLLM data if/when they add it.

## Proposed Solution

### 1. Configuration Layer

Add a new config setting `pricing_provider` with options:
- `"anthropic"` (default) - Claude API pricing
- `"vertex_ai"` - Google Vertex AI global endpoint pricing
- `"vertex_ai_regional"` - Vertex AI regional endpoints with 10% premium
- `"bedrock"` - AWS Bedrock pricing (future extensibility)
- `"azure"` - Azure pricing (future extensibility)

Users can set this via:
```bash
sniffly config set pricing_provider vertex_ai
```

### 2. Pricing Data Structure

Extend `PricingService` to manage multiple provider pricing:
```python
{
    "anthropic": {
        "claude-3-5-sonnet-20241022": {
            "input_cost_per_token": 3.0e-6,
            "output_cost_per_token": 15.0e-6,
            ...
        },
        "source": "litellm",
        "timestamp": "2026-02-05T12:00:00Z"
    },
    "vertex_ai": {
        "claude-3-5-sonnet-20241022": {
            "input_cost_per_token": 3.0e-6,
            "output_cost_per_token": 15.0e-6,
            ...
        },
        "source": "manual",
        "timestamp": "2026-02-05T12:00:00Z"
    }
}
```

### 3. Provider-Specific Pricing Sources

- **Anthropic**: LiteLLM data (current approach)
- **Vertex AI**: Manual pricing config initially, with ability to use LiteLLM if they add it
- **Regional Premium**: Apply 10% multiplier automatically for `vertex_ai_regional`

## Implementation Details

### 1. Config Changes (`sniffly/config.py`)

```python
DEFAULTS = {
    ...
    "pricing_provider": "anthropic",  # New default
}

ENV_MAPPINGS = {
    ...
    "pricing_provider": "PRICING_PROVIDER",
}
```

### 2. Pricing Service Enhancements (`sniffly/services/pricing_service.py`)

Add:
- `VERTEX_AI_PRICING` - Manual pricing dict based on Google Cloud rates
- Modify `_fetch_from_litellm()` to check for Vertex AI models in LiteLLM data
- Update cache structure to store multi-provider pricing
- Add `get_pricing(provider: str)` method to return provider-specific pricing

### 3. Cost Calculation Updates (`sniffly/utils/pricing.py`)

- Modify `get_dynamic_pricing()` to accept optional `provider` parameter
- Update `get_model_pricing(model, provider)` to look up provider-specific pricing
- `calculate_cost()` reads `pricing_provider` from config automatically
- Apply regional premium multiplier (1.10) for `vertex_ai_regional`

### 4. Model Name Handling

Support both naming conventions:
- Direct API: `claude-3-5-sonnet-20241022`
- Vertex AI API: `claude-sonnet-4-5@20250929`

Map Vertex model IDs to standard names for pricing lookup.

## Data Flow

### Request Flow
```
1. Stats calculation needs cost → calculate_cost(tokens, model)
2. calculate_cost() reads config.get("pricing_provider")
3. get_dynamic_pricing(provider) returns provider-specific pricing
4. PricingService.get_pricing(provider) returns cached or fetched pricing
5. Apply regional premium if provider == "vertex_ai_regional"
6. Return cost breakdown
```

### Fallback Strategy
```
1. Try provider-specific pricing (e.g., vertex_ai)
2. If model not found in provider, fall back to anthropic pricing
3. If still not found, use DEFAULT_CLAUDE_PRICING
4. Log warnings when falling back
```

## Cache Management

- **Cache file**: `~/.sniffly/cache/pricing.json`
- **Structure**: Store all providers in single file with timestamps per provider
- **Expiration**: 24-hour expiration per provider (can refresh independently)
- **Compatibility**: Backward compatible with existing cache

## Vertex AI Pricing Data

Based on Google Cloud's pricing (manually maintained in code):
- Same models as Anthropic API initially
- 10% premium calculation: `cost * 1.10` for regional endpoints
- Include comment with source URL and last updated date

**Source**: https://cloud.google.com/vertex-ai/generative-ai/pricing

## Testing Considerations

- Add tests for multi-provider pricing lookup
- Test regional premium calculation (10% multiplier)
- Test fallback behavior (provider → anthropic → default)
- Mock config to test different providers
- Test model name mapping (Vertex API format vs standard format)

## Future Extensions

- Support for AWS Bedrock pricing
- Support for Azure pricing
- Auto-detection of provider from log metadata
- Provider-specific model name normalization
- Support for LiteLLM Vertex AI pricing when available

## References

- [Claude on Vertex AI](https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai)
- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [LiteLLM Vertex AI Documentation](https://docs.litellm.ai/docs/providers/vertex_partner)
- [LiteLLM Model Pricing Data](https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json)
