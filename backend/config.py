# Free GenAI Models Configuration (Working models only)
FREE_MODELS = {
    "primary": "mistralai/mistral-7b-instruct:free",
    "fallback": "google/gemma-7b-it:free",
    "alternative": "microsoft/phi-3-mini-128k-instruct:free",
    "backup": "meta-llama/llama-3.2-3b-instruct:free"
}

# OpenRouter API Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUIRED_HEADERS = {
    "HTTP-Referer": "https://localhost:8000",
    "X-Title": "Auto Form Filling Agent"
}

# Llama Cloud Configuration
LLAMA_CLOUD_BASE_URL = "https://api.cloud.llamaindex.ai/api/parsing/upload"