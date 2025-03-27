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
    creativity: float = 1.0  # 创意活跃度
    thinking_depth: float = 1.0  # 思维开放度
    expression_style: float = 1.0  # 表达发散度
    vocabulary_richness: float = 1.0  # 词汇丰富度
    token_limit: float = 1.0  # 单次回复限制
    reasoning_strength: str = "中"  # 推理强度
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
            "creativity": self.creativity,
            "thinking_depth": self.thinking_depth,
            "expression_style": self.expression_style,
            "vocabulary_richness": self.vocabulary_richness,
            "token_limit": self.token_limit,
            "reasoning_strength": self.reasoning_strength,
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
            creativity=data.get('creativity', 1.0),
            thinking_depth=data.get('thinking_depth', 1.0),
            expression_style=data.get('expression_style', 1.0),
            vocabulary_richness=data.get('vocabulary_richness', 1.0),
            token_limit=data.get('token_limit', 1.0),
            reasoning_strength=data.get('reasoning_strength', '中'),
            is_global=data.get('is_global', False),
            is_deleted=data.get('is_deleted', False),
            create_time=data.get('create_time'),
            update_time=data.get('update_time')
        ) 