import google.generativeai as genai
print(dir(genai))
try:
    print(genai.GenerationConfig)
except AttributeError:
    print("genai.GenerationConfig not found")

try:
    print(genai.types.GenerationConfig)
except AttributeError:
    print("genai.types.GenerationConfig not found")
