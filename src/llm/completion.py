import re
from typing import List, Dict
from openai import OpenAI

from .config import LLMAPIConfig
 

def generate_completion(prompt: str, model: str, temperature: float = 0, system_prompt: str = None, **kwargs):
    messages: List[Dict[str, str]] = [{"role": "user", "content": prompt}]
    if system_prompt:
        messages.insert(0, {"role": "system", "content": system_prompt})

    if model.startswith("gpt"):
        openai_client = OpenAI(
            api_key=LLMAPIConfig.OPENAI_API_KEY
        )
    elif model.startswith("qwen"):
        openai_client = OpenAI(
            api_key=LLMAPIConfig.DASHSCOPE_API_KEY,
            base_url=LLMAPIConfig.DASHSCOPE_BASE_URL,
        )
    elif model.startswith("deepseek"):
        openai_client = OpenAI(
            api_key=LLMAPIConfig.DEEPSEEK_API_KEY,
            base_url=LLMAPIConfig.DEEPSEEK_BASE_URL,
        )
    elif model.startswith("gemini"):
        openai_client = OpenAI(
            api_key=LLMAPIConfig.GEMINI_API_KEY,
            base_url=LLMAPIConfig.GEMINI_BASE_URL,
        )
    elif model.startswith("kimi"):
        openai_client = OpenAI(
            api_key=LLMAPIConfig.MOONSHOT_API_KEY,
            base_url=LLMAPIConfig.MOONSHOT_BASE_URL,
        )

    elif model.startswith("meta-llama"):
        openai_client = OpenAI(
            api_key=LLMAPIConfig.GROQ_CLOUD_API_KEY,
            base_url=LLMAPIConfig.GROQ_CLOUD_BASE_URL,
        )
    elif model.startswith("mistral"):
        openai_client = OpenAI(
            api_key=LLMAPIConfig.MISTRAL_API_KEY,
            base_url=LLMAPIConfig.MISTRAL_BASE_URL,
        )

    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        **kwargs,
    )
    return response

def extract_json(response: str) -> str:
    pattern = r"```json\n(.*?)\n```"
    match = re.search(pattern, response, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return response
