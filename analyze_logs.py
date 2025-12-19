import json
import re

def analyze_logs(file_path):
    with open(file_path, 'r') as f:
        logs = json.load(f)
    
    total_cost = 0.0
    total_tokens_in = 0
    total_tokens_out = 0
    total_tokens_cached = 0
    
    calls_count = 0
    success_count = 0
    failure_count = 0
    
    # Regex patterns
    pricing_pattern = re.compile(r"Pricing: model='(.*?)', tier=(\d+), cost=\$(.*)")
    api_call_pattern = re.compile(r"API call: (.*)s, Total: (.*)s, Tokens: (\d+)/(\d+), Cached: (.*)")
    error_pattern = re.compile(r"Unexpected Gemini error: (.*)")
    
    for entry in logs:
        msg = entry.get("message", "")
        
        # Check for pricing
        pricing_match = pricing_pattern.search(msg)
        if pricing_match:
            total_cost += float(pricing_match.group(3))
            
        # Check for API call metrics
        api_match = api_call_pattern.search(msg)
        if api_match:
            calls_count += 1
            total_tokens_in += int(api_match.group(3))
            total_tokens_out += int(api_match.group(4))
            cached_val = api_match.group(5)
            if cached_val != "None":
                total_tokens_cached += int(cached_val)
            success_count += 1 # We consider it an API success if we got tokens back
            
        # Check for specific errors
        if "Unexpected Gemini error" in msg:
            failure_count += 1

    print("--- Economic Analysis ---")
    print(f"Total API Calls: {calls_count}")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"Total Tokens: {total_tokens_in + total_tokens_out + total_tokens_cached}")
    print(f"  - Input:  {total_tokens_in}")
    print(f"  - Output: {total_tokens_out}")
    print(f"  - Cached: {total_tokens_cached}")
    print(f"Cache Efficiency: {(total_tokens_cached / (total_tokens_in + total_tokens_cached) * 100 if (total_tokens_in + total_tokens_cached) > 0 else 0):.2f}%")
    print(f"Failures identified: {failure_count}")
    print("--------------------------")

if __name__ == "__main__":
    # Create the logs.json file from the raw data provided in the prompt if needed
    # (In this simulation, I'll assume the data is in 'provided_logs.json')
    analyze_logs('provided_logs.json')
