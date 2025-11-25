# Gemini Pricing Update - January 2025

## Summary
Updated Gemini API pricing to include all latest models from 2.0 to 3.0 series with official pricing from [ai.google.dev/pricing](https://ai.google.dev/pricing).

## Updated Models

### Gemini 3.0 Series (Preview)
- **gemini-3-pro-preview**: $2.00 input / $12.00 output per 1M tokens (≤200K context)

### Gemini 2.5 Series
- **gemini-2.5-pro**: $1.25 input / $10.00 output per 1M tokens (≤200K context)
- **gemini-2.5-flash**: $0.30 input / $2.50 output per 1M tokens (with thinking mode)
- **gemini-2.5-flash-lite**: $0.10 input / $0.40 output per 1M tokens

### Gemini 2.0 Series
- **gemini-2.0-flash**: $0.10 input / $0.40 output per 1M tokens
- **gemini-2.0-flash-exp**: FREE (experimental) ← Currently used in .env
- **gemini-2.0-flash-lite**: $0.075 input / $0.30 output per 1M tokens

### Gemini 1.5 Series (Legacy)
- **gemini-1.5-pro**: $1.25 input / $5.00 output per 1M tokens (≤128K context)
- **gemini-1.5-flash**: $0.075 input / $0.30 output per 1M tokens

## Current Configuration
Your `.env` file is configured to use:
```
GEMINI_MODEL=gemini-2.0-flash-exp
```
This model is **FREE** (experimental), so all cost calculations will be $0.00.

## Recommendations for Production

### Budget-Friendly Option
```env
GEMINI_MODEL=gemini-2.0-flash-lite
```
- Cost: $0.075 input / $0.30 output per 1M tokens
- Best for: High-volume, cost-sensitive workloads

### Balanced Option
```env
GEMINI_MODEL=gemini-2.5-flash-lite
```
- Cost: $0.10 input / $0.40 output per 1M tokens
- Best for: General purpose usage with good performance

### Premium Option
```env
GEMINI_MODEL=gemini-2.5-pro
```
- Cost: $1.25 input / $10.00 output per 1M tokens
- Best for: Complex reasoning, coding tasks, high-quality content generation

## Context-Aware Pricing Notes

Some models have tiered pricing based on context length:

- **gemini-3-pro-preview**: >200K context costs $4.00 input / $18.00 output
- **gemini-2.5-pro**: >200K context costs $2.50 input / $15.00 output
- **gemini-1.5-pro**: >128K context costs $2.50 input / $10.00 output

Currently, the pricing implementation uses the base tier pricing. To implement context-aware pricing, you would need to:
1. Track the actual context length used in each request
2. Apply the appropriate pricing tier in `calculate_cost()`

## Files Modified
- `app/integrations/llm/gemini.py` - Updated PRICING dictionary

## Next Steps
1. ✅ Pricing updated in code
2. ⚠️ Consider implementing context-aware pricing for Pro models
3. ⚠️ Consider moving pricing to environment variables or database for easier updates
4. ⚠️ Monitor Google's pricing page for future changes

## Pricing Source
Official Google AI Developer pricing page: https://ai.google.dev/pricing
Last verified: January 2025
