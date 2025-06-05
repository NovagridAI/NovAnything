"""
模型配置数据模型
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ModelConfig:
    """模型配置类"""
    
    # 自定义模型配置
    config_id: str  # 配置ID
    user_id: str  # 所属用户ID
    service_id: str  # 服务ID（唯一标识）
    service_name: str  # 服务名称
    request_format: str  # 请求格式（如OpenAI）
    api_key: str  # API密钥
    api_proxy: str  # API代理地址
    model_endpoint: str  # 模型endpoint
    temperature: float = 1.0  # 温度参数
    top_k: int = 1  # Top-K采样
    api_context_length: int = 1024  # API上下文长度
    top_p: float = 1.0  # Top-P采样
    max_token: int = 1024  # 最大生成token数
    context_length: int = 10  # 上下文长度
    is_global: bool = False  # 是否为全局模型
    is_deleted: bool = False  # 是否已删除
    create_time: str = None  # 创建时间
    update_time: str = None  # 更新时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "config_id": self.config_id,
            "user_id": self.user_id,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "request_format": self.request_format,
            "api_key": self.api_key,
            "api_proxy": self.api_proxy,
            "model_endpoint": self.model_endpoint,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "api_context_length": self.api_context_length,
            "top_p": self.top_p,
            "max_token": self.max_token,
            "context_length": self.context_length,
            "is_global": self.is_global,
            "is_deleted": self.is_deleted,
            "create_time": self.create_time,
            "update_time": self.update_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """从字典创建对象"""
        return cls(
            config_id=data.get('config_id'),
            user_id=data.get('user_id'),
            service_id=data.get('service_id'),
            service_name=data.get('service_name'),
            request_format=data.get('request_format'),
            api_key=data.get('api_key'),
            api_proxy=data.get('api_proxy'),
            model_endpoint=data.get('model_endpoint'),
            temperature=data.get('temperature', 1.0),
            top_k=data.get('top_k', 1),
            api_context_length=data.get('api_context_length', 1024),
            top_p=data.get('top_p', 1.0),
            max_token=data.get('max_token', 1024),
            context_length=data.get('context_length', 10),
            is_global=data.get('is_global', False),
            is_deleted=data.get('is_deleted', False),
            create_time=data.get('create_time'),
            update_time=data.get('update_time')
        )