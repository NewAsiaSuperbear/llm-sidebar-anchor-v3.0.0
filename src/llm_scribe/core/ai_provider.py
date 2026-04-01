from abc import ABC, abstractmethod
from typing import Optional


class AIProvider(ABC):
    """AI提供商抽象基类"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass
    
    @abstractmethod
    async def chat(self, 
                  messages: list[dict[str, str]], 
                  model: Optional[str] = None, 
                  **kwargs) -> str:
        """发送聊天消息"""
        pass
    
    @abstractmethod
    async def generate_text(self, 
                          prompt: str, 
                          model: Optional[str] = None, 
                          **kwargs) -> str:
        """生成文本"""
        pass
    
    def get_available_models(self) -> list[str]:
        """获取可用模型列表"""
        return []
