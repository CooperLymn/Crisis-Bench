import yaml
from pathlib import Path


_config_path = Path(__file__).parent / "config.yaml"
with open(_config_path, 'r', encoding='utf-8') as f:
    _config = yaml.safe_load(f)

class LLMAPIConfig:
    OPENAI_API_KEY = _config.get("OPENAI_API_KEY", "...")

    DASHSCOPE_API_KEY = _config.get("DASHSCOPE_API_KEY", "...")
    DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    DEEPSEEK_API_KEY = _config.get("DEEPSEEK_API_KEY", "...")
    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/"

    MOONSHOT_API_KEY = _config.get("MOONSHOT_API_KEY", "...")
    MOONSHOT_BASE_URL = "https://api.moonshot.cn/v1"

    GEMINI_API_KEY = _config.get("GEMINI_API_KEY", "...")
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

    GROQ_CLOUD_API_KEY = _config.get("GROQ_CLOUD_API_KEY", "...")
    GROQ_CLOUD_BASE_URL = "https://api.groq.com/openai/v1"

    MISTRAL_API_KEY = _config.get("MISTRAL_API_KEY", "...")
    MISTRAL_BASE_URL = "https://api.mistral.ai/v1"

class LLMModelLiterals:
    DEEPSEEK_CHAT = "deepseek-chat"
    QWEN3_235B = "qwen3-235b-a22b-instruct-2507"
    QWEN3_NEXT_80B = "qwen3-next-80b-a3b-instruct"
    QWEN3_30B = "qwen3-30b-a3b-instruct-2507"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_1 = "gpt-5.1"
    KIMI_K2 = "kimi-k2-0905-preview"
    GEMINI_3_FLASH = "gemini-3-flash-preview"
    GEMINI_3_PRO = "gemini-3-pro-preview"
    LLAMA_4_MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"
    LLAMA_4_SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"
    MISTRAL_LARGE_3 = "mistral-large-2512"