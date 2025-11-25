#!/usr/bin/env python3
"""
Script to list all available Gemini models via API
"""
import google.generativeai as genai
import os
from pathlib import Path

# Read API key from .env
env_path = Path(__file__).parent / '.env'
with open(env_path, 'r') as f:
    for line in f:
        if line.startswith('GEMINI_API_KEY='):
            api_key = line.split('=', 1)[1].strip()
            break

# Configure API
genai.configure(api_key=api_key)

# Get list of available models
print('=' * 80)
print('ДОСТУПНЫЕ МОДЕЛИ GEMINI С ВАШИМ API КЛЮЧОМ')
print('=' * 80)
print()

models_by_version = {
    '3.0': [],
    '2.5': [],
    '2.0': [],
    '1.5': [],
    'other': []
}

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        model_name = model.name.replace('models/', '')
        
        # Categorize by version
        if 'gemini-3' in model_name or 'nano-banana-pro' in model_name:
            models_by_version['3.0'].append(model)
        elif 'gemini-2.5' in model_name or 'gemini-2-5' in model_name:
            models_by_version['2.5'].append(model)
        elif 'gemini-2.0' in model_name or 'gemini-2-0' in model_name:
            models_by_version['2.0'].append(model)
        elif 'gemini-1.5' in model_name or 'gemini-1-5' in model_name:
            models_by_version['1.5'].append(model)
        else:
            models_by_version['other'].append(model)

# Print by version
for version in ['3.0', '2.5', '2.0', '1.5', 'other']:
    if models_by_version[version]:
        print(f'\n{"=" * 80}')
        print(f'GEMINI {version.upper()} SERIES')
        print(f'{"=" * 80}\n')
        
        for model in models_by_version[version]:
            model_name = model.name.replace('models/', '')
            print(f'📌 {model_name}')
            print(f'   Display Name: {model.display_name}')
            if model.description:
                print(f'   Description: {model.description}')
            print(f'   Input Tokens: {model.input_token_limit:,}')
            print(f'   Output Tokens: {model.output_token_limit:,}')
            print(f'   Methods: {", ".join(model.supported_generation_methods)}')
            print()

print('=' * 80)
print(f'ВСЕГО МОДЕЛЕЙ: {sum(len(v) for v in models_by_version.values())}')
print('=' * 80)
