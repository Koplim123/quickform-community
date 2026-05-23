import json
import logging
import requests

logger = logging.getLogger(__name__)


def call_ai_model(prompt, ai_config):
    """
    调用AI模型生成分析报告
    """
    def get_model_config(model_name):
        for mc in ai_config.model_configs:
            if mc.model_name == model_name:
                return mc
        return None

    if ai_config.selected_model == 'deepseek':
        model_cfg = get_model_config('deepseek')
        api_key = model_cfg.api_key if model_cfg else ''
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的数据分析助手。请基于用户提供的数据，生成一份详细、专业、有洞察力的分析报告。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            raise Exception(f"DeepSeek API调用失败: {str(e)}")

    elif ai_config.selected_model == 'doubao':
        model_cfg = get_model_config('doubao')
        api_key = model_cfg.api_key if model_cfg else ''
        url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "doubao-seed-1-6-251015",
            "messages": [
                {"role": "system", "content": "你是一个专业的数据分析助手。请基于用户提供的数据，生成一份详细、专业、有洞察力的分析报告。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"豆包API调用失败: {str(e)}")
            raise Exception(f"豆包API调用失败: {str(e)}")

    elif ai_config.selected_model == 'qwen':
        model_cfg = get_model_config('qwen')
        api_key = model_cfg.api_key if model_cfg else ''
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "qwen-plus",
            "input": {
                "messages": [
                    {"role": "system", "content": "你是一个专业的数据分析助手。请基于用户提供的数据，生成一份详细、专业、有洞察力的分析报告。"},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 4000
            }
        }

        try:
            logger.info(f"调用阿里云百炼API，模型: qwen-plus")
            logger.info(f"请求URL: {url}")
            logger.info(f"请求头: {headers}")
            logger.info(f"请求数据: {json.dumps(data, ensure_ascii=False)[:200]}...")

            response = requests.post(url, headers=headers, json=data, timeout=120)

            logger.info(f"阿里云百炼API响应状态码: {response.status_code}")
            logger.info(f"阿里云百炼API响应头: {dict(response.headers)}")
            logger.info(f"阿里云百炼API响应内容: {response.text[:500]}...")

            if response.status_code != 200:
                raise Exception(f"阿里云百炼API调用失败，状态码: {response.status_code}，响应: {response.text[:200]}")

            if not response.text:
                raise Exception("阿里云百炼API返回空响应")

            try:
                result = response.json()
                logger.info(f"阿里云百炼API响应JSON结构: {list(result.keys()) if isinstance(result, dict) else '非字典结构'}")
            except ValueError as ve:
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

    elif ai_config.selected_model == 'glm':
        model_cfg = get_model_config('glm')
        api_key = model_cfg.api_key if model_cfg else ''
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "glm-4",
            "messages": [
                {"role": "system", "content": "你是一个专业的数据分析助手。请基于用户提供的数据，生成一份详细、专业、有洞察力的分析报告。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }

        try:
            logger.info(f"调用GLM API，URL: {url}")
            response = requests.post(url, headers=headers, json=data, timeout=120)
            logger.info(f"GLM API响应状态码: {response.status_code}")
            logger.info(f"GLM API响应内容: {response.text[:500]}")
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"GLM API调用失败: {str(e)}")
            raise Exception(f"GLM API调用失败: {str(e)}")

    elif ai_config.selected_model == 'siliconflow':
        model_cfg = get_model_config('siliconflow')
        api_key = model_cfg.api_key if model_cfg else ''
        model_name = model_cfg.extra_settings if model_cfg and model_cfg.extra_settings else 'Qwen/Qwen2.5-72B-Instruct'
        url = "https://api.siliconflow.cn/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "你是一个专业的数据分析助手。请基于用户提供的数据，生成一份详细、专业、有洞察力的分析报告。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }

        try:
            logger.info(f"调用硅基流动API，URL: {url}")
            response = requests.post(url, headers=headers, json=data, timeout=120)
            logger.info(f"硅基流动API响应状态码: {response.status_code}")
            logger.info(f"硅基流动API响应内容: {response.text[:500]}")
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"硅基流动API调用失败: {str(e)}")
            raise Exception(f"硅基流动API调用失败: {str(e)}")

    elif ai_config.selected_model == 'ollama':
        model_cfg = get_model_config('ollama')
        api_url = model_cfg.api_url if model_cfg else 'http://localhost:11434'
        extra_settings = model_cfg.extra_settings if model_cfg else ''
        ollama_model = extra_settings if extra_settings else 'llama3.2'
        if not api_url.startswith('http'):
            api_url = 'http://' + api_url
        url = f"{api_url.rstrip('/')}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "model": ollama_model,
            "messages": [
                {"role": "system", "content": "你是一个专业的数据分析助手。请基于用户提供的数据，生成一份详细、专业、有洞察力的分析报告。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }

        try:
            logger.info(f"调用Ollama API，URL: {url}，模型: {ollama_model}")
            response = requests.post(url, headers=headers, json=data, timeout=180)
            logger.info(f"Ollama API响应状态码: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama API调用失败: {str(e)}")
            raise Exception(f"Ollama API调用失败: {str(e)}")

    else:
        raise Exception(f"不支持的AI模型: {ai_config.selected_model}")
