"""
文档相关数据模型
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
import json


@dataclass
class Document:
    """文档模型"""
    doc_id: str
    json_data: Dict[str, Any]
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'doc_id': self.doc_id,
            'json_data': self.json_data if isinstance(self.json_data, str) else json.dumps(self.json_data, ensure_ascii=False)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """从字典创建对象"""
        json_data = data.get('json_data')
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError:
                # 保持原样
                pass
                
        return cls(
            id=data.get('id'),
            doc_id=data.get('doc_id'),
            json_data=json_data
        ) 