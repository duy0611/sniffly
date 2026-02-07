# Pricing Providers

Sniffly supports multiple pricing sources to accurately calculate Claude API costs based on where you access the models.

## Supported Providers

Sniffly supports three pricing providers:

| Provider | Description | Use Case |
|----------|-------------|----------|
| `anthropic` | Anthropic API pricing | Direct API access via api.anthropic.com (default) |
| `vertex_ai_global` | Vertex AI global endpoint pricing | Google Cloud global endpoints (us-central1) |
| `vertex_ai_regional` | Vertex AI regional endpoint pricing | Google Cloud regional endpoints (+10% premium) |

## Configuration

### Using CLI

Set your pricing provider using the config command:

```bash
# Use Anthropic API pricing (default)
sniffly config set pricing_provider anthropic

# Use Vertex AI global endpoint pricing
sniffly config set pricing_provider vertex_ai_global

# Use Vertex AI regional endpoint pricing
sniffly config set pricing_provider vertex_ai_regional

# View current configuration
sniffly config show
```

### Using Environment Variable

You can also set the provider via environment variable:

```bash
# Set via export
export PRICING_PROVIDER=vertex_ai_global

# Or inline
PRICING_PROVIDER=vertex_ai_regional sniffly init
```

### Using Config File

Edit `~/.sniffly/config.json` directly:

```json
{
  "pricing_provider": "vertex_ai_global"
}
```

## How It Works

### Provider Selection

The pricing provider determines which pricing table is used for cost calculations:

1. **Anthropic**: Uses official Anthropic API pricing, fetched from LiteLLM with local cache
2. **Vertex AI Global**: Uses Google Cloud global endpoint pricing (matches Anthropic pricing)
3. **Vertex AI Regional**: Applies 10% premium to global pricing for regional deployments

### Cost Calculation

All providers calculate costs across four token types:

- **Input tokens**: Standard input processing
- **Output tokens**: Model-generated output
- **Cache creation tokens**: Prompt caching write operations
- **Cache read tokens**: Prompt caching read operations

### Caching Strategy

#### Anthropic Provider

- Fetches latest pricing from [LiteLLM's pricing database](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json)
- Caches pricing locally for 24 hours in `~/.sniffly/cache/pricing.json`
- Falls back to built-in defaults if fetch fails
- Automatically filters for Anthropic models only

#### Vertex AI Providers

- Uses manually maintained pricing tables (no external fetch)
- Pricing sourced from [Google Cloud Vertex AI pricing page](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- Regional provider applies 10% premium at calculation time
- No cache needed (static pricing data)

### Fallback Behavior

If pricing cannot be determined, Sniffly falls back in this order:

1. Cached pricing (even if stale)
2. Built-in default pricing
3. Claude 3.5 Sonnet pricing (for unknown models)

## Pricing Sources

### Official Documentation

- **Anthropic API**: [https://www.anthropic.com/pricing](https://www.anthropic.com/pricing)
- **Vertex AI**: [https://cloud.google.com/vertex-ai/generative-ai/pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- **LiteLLM Database**: [https://github.com/BerriAI/litellm](https://github.com/BerriAI/litellm)

### Pricing Updates

#### Anthropic Provider

Pricing is automatically updated from LiteLLM every 24 hours. To force an immediate refresh:

```bash
# Clear cache and restart
sniffly init --clear-cache
```

#### Vertex AI Providers

Vertex AI pricing is manually maintained. Updates require a Sniffly package update. Check the pricing table in `sniffly/utils/pricing.py` for the last update date.

## Examples

### Scenario: Using Anthropic API

```bash
sniffly config set pricing_provider anthropic
sniffly init
```

Costs are calculated using official Anthropic API pricing, auto-updated from LiteLLM.

### Scenario: Using Vertex AI Global

```bash
sniffly config set pricing_provider vertex_ai_global
sniffly init
```

Costs match Vertex AI global endpoint pricing (us-central1). No premium applied.

### Scenario: Using Vertex AI Regional

```bash
sniffly config set pricing_provider vertex_ai_regional
sniffly init
```

Costs include 10% regional premium over global pricing for regional deployments (us-east1, europe-west1, etc.).

### Scenario: Comparing Providers

```bash
# Check costs with Anthropic pricing
sniffly config set pricing_provider anthropic
sniffly init

# Switch to Vertex AI and compare
sniffly config set pricing_provider vertex_ai_global
sniffly init --clear-cache
```

The dashboard will recalculate all costs using the new provider's pricing.

## Technical Details

### Model Coverage

All providers support the same Claude models:

- Claude Opus 4 (claude-opus-4-20250514)
- Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
- Claude 3.5 Haiku (claude-3-5-haiku-20241022)
- Claude 3 Opus (claude-3-opus-20240229)
- Claude 3 Sonnet (claude-3-sonnet-20240229)
- Claude 3 Haiku (claude-3-haiku-20240307)

### Cache Duration

Anthropic provider caches pricing for 24 hours. The cache includes:

- Timestamp of last fetch
- Pricing data for all Claude models
- Source indicator (litellm, cache, or default)
- Staleness flag

View cache details in `~/.sniffly/cache/pricing.json`.

### Regional Premium

Vertex AI regional endpoints charge 10% more than global endpoints. The premium is applied at cost calculation time, not in the base pricing table.

Example for Claude 3.5 Sonnet input tokens:
- Global: $3.00 per million tokens
- Regional: $3.30 per million tokens (10% premium)

## Troubleshooting

### Pricing not updating

If you change providers and don't see updated costs:

```bash
# Clear cache and restart
sniffly init --clear-cache
```

### LiteLLM fetch failing

If the Anthropic provider can't fetch from LiteLLM:

1. Check your internet connection
2. Sniffly will automatically fall back to cached pricing
3. If cache is missing, built-in defaults are used
4. Pricing may be slightly outdated but will still work

To verify the pricing source:

```bash
# Check cache file
cat ~/.sniffly/cache/pricing.json
```

Look for the `source` field:
- `"litellm"` - Fresh data from LiteLLM
- `"cache"` - Using cached data
- `"default"` - Using built-in fallback pricing

### Wrong costs for regional deployment

Ensure you're using the correct provider:

```bash
# For us-central1 (global)
sniffly config set pricing_provider vertex_ai_global

# For other regions (us-east1, europe-west1, etc.)
sniffly config set pricing_provider vertex_ai_regional
```

## FAQ

**Q: Which provider should I use?**

A: Use the provider that matches your Claude access method:
- Anthropic API directly → `anthropic`
- Vertex AI in us-central1 → `vertex_ai_global`
- Vertex AI in other regions → `vertex_ai_regional`

**Q: Are Vertex AI prices the same as Anthropic?**

A: Yes for global endpoints (us-central1). Regional endpoints charge 10% more.

**Q: How often is pricing updated?**

A: Anthropic provider updates every 24 hours from LiteLLM. Vertex AI pricing is manually maintained.

**Q: Can I use custom pricing?**

A: Not currently supported. Pricing is sourced from official providers only.

**Q: Does changing providers affect historical data?**

A: Yes. Costs are recalculated on-the-fly based on the current provider setting. Historical cost data reflects the current pricing provider.
