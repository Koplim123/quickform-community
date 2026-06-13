import json
import logging
import requests

from .crypto import validate_url_safe

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "你是一个专业的数据分析助手。请基于用户提供的数据，生成一份详细、专业、有洞察力的分析报告。"


def _build_messages(prompt):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]


def _call_chat_api(url, api_key, model, prompt, timeout, provider_label):
    """标准 OpenAI-compatible chat completions 调用。"""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    data = {
        "model": model,
        "messages": _build_messages(prompt),
        "temperature": 0.7,
        "max_tokens": 4000
    }

    try:
        logger.info(f"调用{provider_label}，URL: {url}，模型: {model}")
        response = requests.post(url, headers=headers, json=data, timeout=timeout)
        logger.info(f"{provider_label}响应状态码: {response.status_code}")
        logger.info(f"{provider_label}响应内容: {response.text[:500]}")
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"{provider_label}调用失败: {str(e)}")
        raise Exception(f"{provider_label}调用失败: {str(e)}")


def call_ai_model(prompt, ai_config):
    """调用AI模型生成分析报告"""

    def get_model_config(model_name):
        for mc in ai_config.model_configs:
            if mc.model_name == model_name:
                return mc
        return None

    model = ai_config.selected_model
    model_cfg = get_model_config(model)

    if model == 'deepseek':
        api_key = model_cfg.api_key if model_cfg else ''
        return _call_chat_api(
            url="https://api.deepseek.com/v1/chat/completions",
            api_key=api_key,
            model="deepseek-chat",
            prompt=prompt,
            timeout=60,
            provider_label="DeepSeek API"
        )

    elif model == 'doubao':
        api_key = model_cfg.api_key if model_cfg else ''
        return _call_chat_api(
            url="https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            api_key=api_key,
            model="doubao-seed-1-6-251015",
            prompt=prompt,
            timeout=120,
            provider_label="豆包API"
        )

    elif model == 'qwen':
        api_key = model_cfg.api_key if model_cfg else ''
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        data = {
            "model": "qwen-plus",
            "input": {
                "messages": _build_messages(prompt)
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 4000
            }
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        try:
            logger.info(f"调用阿里云百炼API，模型: qwen-plus")
            logger.info(f"请求URL: {url}")
            logger.info(f"请求数据: {json.dumps(data, ensure_ascii=False)[:200]}...")

            response = requests.post(url, headers=headers, json=data, timeout=120)

            logger.info(f"阿里云百炼API响应状态码: {response.status_code}")
            logger.info(f"阿里云百炼API响应内容: {response.text[:500]}...")

            if response.status_code != 200:
                raise Exception(f"阿里云百炼API调用失败，状态码: {response.status_code}，响应: {response.text[:200]}")

            if not response.text:
                raise Exception("阿里云百炼API返回空响应")

            try:
                result = response.json()
                logger.info(f"阿里云百炼API响应JSON结构: {list(result.keys()) if isinstance(result, dict) else '非字典结构'}")
            except ValueError:
                raise Exception(f"阿里云百炼API返回非JSON响应: {response.text[:200]}")

            if isinstance(result, dict) and "code" in result and result["code"] != "200":
                raise Exception(f"阿里云百炼API调用失败: {result.get('message', '未知错误')} (错误码: {result.get('code')})")

            if isinstance(result, dict):
                if "output" in result and "text" in result["output"]:
                    return result["output"]["text"]
                elif "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    elif "text" in choice:
                        return choice["text"]
                elif "data" in result and "choices" in result["data"] and len(result["data"]["choices"]) > 0:
                    choice = result["data"]["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]

            raise Exception(f"阿里云百炼API返回未知格式的响应: {str(result)[:200]}")
        except requests.exceptions.RequestException as re:
            logger.error(f"阿里云百炼API网络请求异常: {str(re)}")
            raise Exception(f"阿里云百炼API网络请求异常: {str(re)}")
        except Exception as e:
            logger.error(f"阿里云百炼API调用失败: {str(e)}")
            raise Exception(f"阿里云百炼API调用失败: {str(e)}")

    elif model == 'glm':
        api_key = model_cfg.api_key if model_cfg else ''
        return _call_chat_api(
            url="https://open.bigmodel.cn/api/paas/v4/chat/completions",
            api_key=api_key,
            model="glm-4",
            prompt=prompt,
            timeout=120,
            provider_label="GLM API"
        )

    elif model == 'siliconflow':
        api_key = model_cfg.api_key if model_cfg else ''
        model_name = model_cfg.extra_settings if (model_cfg and model_cfg.extra_settings) else 'Qwen/Qwen2.5-72B-Instruct'
        return _call_chat_api(
            url="https://api.siliconflow.cn/v1/chat/completions",
            api_key=api_key,
            model=model_name,
            prompt=prompt,
            timeout=120,
            provider_label="硅基流动API"
        )

    elif model == 'ollama':
        api_url = model_cfg.api_url if model_cfg else 'http://localhost:11434'
        extra_settings = model_cfg.extra_settings if model_cfg else ''
        ollama_model = extra_settings if extra_settings else 'llama3.2'
        if not api_url.startswith('http'):
            api_url = 'http://' + api_url
        url = f"{api_url.rstrip('/')}/v1/chat/completions"
        validate_url_safe(url, allow_private=True)
        return _call_chat_api(
            url=url,
            api_key='',
            model=ollama_model,
            prompt=prompt,
            timeout=180,
            provider_label="Ollama API"
        )

    elif model == 'openai':
        api_key = model_cfg.api_key if model_cfg else ''
        api_url = model_cfg.api_url if model_cfg else 'https://api.openai.com/v1'
        extra_settings = model_cfg.extra_settings if model_cfg else ''
        openai_model = extra_settings if extra_settings else 'gpt-5.5'

        if not api_url.endswith('/chat/completions'):
            api_url = api_url.rstrip('/') + '/chat/completions'

        validate_url_safe(api_url)
        return _call_chat_api(
            url=api_url,
            api_key=api_key,
            model=openai_model,
            prompt=prompt,
            timeout=120,
            provider_label="OpenAI API"
        )

    elif model == 'anthropic':
        api_key = model_cfg.api_key if model_cfg else ''
        api_url = model_cfg.api_url if model_cfg else 'https://api.anthropic.com/v1/messages'
        extra_settings = model_cfg.extra_settings if model_cfg else ''
        model_name = extra_settings if extra_settings else 'claude-sonnet-4-6'

        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": model_name,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000
        }

        try:
            logger.info(f"调用Anthropic API，URL: {api_url}，模型: {model_name}")
            response = requests.post(api_url, headers=headers, json=data, timeout=120)
            logger.info(f"Anthropic API响应状态码: {response.status_code}")
            logger.info(f"Anthropic API响应内容: {response.text[:500]}")
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]
        except Exception as e:
            logger.error(f"Anthropic API调用失败: {str(e)}")
            raise Exception(f"Anthropic API调用失败: {str(e)}")

    elif model == 'gemini':
        api_key = model_cfg.api_key if model_cfg else ''
        api_url = model_cfg.api_url if model_cfg else 'https://generativelanguage.googleapis.com/v1beta'
        extra_settings = model_cfg.extra_settings if model_cfg else ''
        # extra_settings 格式: "model_name|auth_type"
        parts = extra_settings.split('|') if extra_settings else []
        gemini_model = parts[0] if parts and parts[0] else 'gemini-3.1-pro'
        auth_type = parts[1] if len(parts) > 1 else 'api_key'

        url = f"{api_url.rstrip('/')}/models/{gemini_model}:generateContent"

        if auth_type == 'api_key':
            url += f"?key={api_key}"
            headers = {"Content-Type": "application/json"}
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

        data = {
            "systemInstruction": {
                "role": "system",
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4000
            }
        }

        try:
            logger.info(f"调用Gemini API，URL: {url.split('?')[0]}，模型: {gemini_model}")
            response = requests.post(url, headers=headers, json=data, timeout=120)
            logger.info(f"Gemini API响应状态码: {response.status_code}")
            logger.info(f"Gemini API响应内容: {response.text[:500]}")
            response.raise_for_status()
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.error(f"Gemini API调用失败: {str(e)}")
            raise Exception(f"Gemini API调用失败: {str(e)}")

    else:
        raise Exception(f"不支持的AI模型: {model}")
