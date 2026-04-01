import logging
from typing import Any, Optional

import requests

from .ai_provider import AIProvider

HTTP_OK = 200


class OllamaProvider(AIProvider):
    """Ollama 本地模型提供商"""
    
    def __init__(self):
        # 硬编码配置, 不读取外部配置文件
        self.base_url = "http://localhost:11434"
        self.default_model = "qwen2.5:7b"
        self.timeout = 30  # 本地调用可以长一些
        self._available = None
        self._models_cache = None
        
    def is_available(self) -> bool:
        """检查 Ollama 服务是否在运行"""
        if self._available is not None:
            return self._available
            
        try:
            # 简单的连接测试
            response = requests.get(
                f"{self.base_url}/api/tags", 
                timeout=2
            )
            if response.status_code == HTTP_OK:
                self._available = True
                return True
        except requests.exceptions.RequestException as e:
            logging.debug(f"Ollama 连接失败: {e}")
            
        self._available = False
        return False
    
    def get_available_models(self) -> list[str]:
        """获取已安装的模型列表"""
        if not self.is_available():
            return []
            
        if self._models_cache is not None:
            return self._models_cache
            
        try:
            response = requests.get(
                f"{self.base_url}/api/tags", 
                timeout=5
            )
            if response.status_code == HTTP_OK:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                self._models_cache = models
                return models
        except Exception as e:
            logging.debug(f"获取模型列表失败: {e}")
            
        return []
    
    async def chat(self, 
                  messages: list[dict[str, str]], 
                  model: Optional[str] = None, 
                  **kwargs) -> str:
        """发送聊天消息 (异步)"""
        if not self.is_available():
            raise ConnectionError("Ollama 服务未运行")
            
        model_name = model or self.default_model
        
        # 构建请求
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": kwargs.get("options", {})
        }
        
        try:
            # Note: requests is synchronous, but we're in an async method.
            # In a full implementation, we'd use aiohttp.
            # For this phase, we keep it simple as requested.
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Ollama 聊天请求失败: {e}")
            raise
    
    async def generate_text(self, 
                          prompt: str, 
                          model: Optional[str] = None, 
                          **kwargs) -> str:
        """生成文本 (简单提示词, 不带上下文)"""
        if not self.is_available():
            raise ConnectionError("Ollama 服务未运行")
            
        model_name = model or self.default_model
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": kwargs.get("options", {})
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Ollama 文本生成失败: {e}")
            raise
    
    def test_connection(self) -> dict[str, Any]:
        """测试连接并返回详细信息"""
        result = {
            "available": False,
            "models": [],
            "error": None
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/api/tags", 
                timeout=5
            )
            if response.status_code == HTTP_OK:
                data = response.json()
                result["available"] = True
                result["models"] = [m["name"] for m in data.get("models", [])]
            else:
                result["error"] = f"HTTP {response.status_code}"
        except Exception as e:
            result["error"] = str(e)
            
        return result
