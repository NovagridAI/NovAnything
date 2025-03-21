"""
FAQ相关数据模型
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Faq:
    """FAQ模型"""
    faq_id: str
    user_id: str
    kb_id: str
    question: str
    answer: str
    nos_keys: Optional[str] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'faq_id': self.faq_id,
            'user_id': self.user_id,
            'kb_id': self.kb_id,
            'question': self.question,
            'answer': self.answer
        }
        
        if self.nos_keys is not None:
            data['nos_keys'] = self.nos_keys
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Faq':
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            faq_id=data.get('faq_id'),
            user_id=data.get('user_id'),
            kb_id=data.get('kb_id'),
            question=data.get('question'),
            answer=data.get('answer'),
            nos_keys=data.get('nos_keys')
        ) 