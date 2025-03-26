"""
会话相关数据模型
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class Conversation:
    """会话模型"""
    conversation_id: str
    user_id: str
    title: str
    is_favorite: bool
    create_time: datetime
    update_time: datetime
    kb_ids: List[str]
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'title': self.title,
            'is_favorite': self.is_favorite,
            'create_time': self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            'update_time': self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
            'kb_ids': json.dumps(self.kb_ids, ensure_ascii=False) if isinstance(self.kb_ids, list) else self.kb_ids
        }
        
        if self.id is not None:
            data['id'] = self.id
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """从字典创建对象"""
        kb_ids = data.get('kb_ids')
        if isinstance(kb_ids, str):
            try:
                kb_ids = json.loads(kb_ids)
            except json.JSONDecodeError:
                kb_ids = []
        
        # 处理日期时间
        create_time = data.get('create_time')
        if isinstance(create_time, str):
            try:
                create_time = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                create_time = datetime.now()
        
        update_time = data.get('update_time')
        if isinstance(update_time, str):
            try:
                update_time = datetime.strptime(update_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                update_time = datetime.now()
                
        return cls(
            id=data.get('id'),
            conversation_id=data.get('conversation_id'),
            user_id=data.get('user_id'),
            title=data.get('title'),
            is_favorite=bool(data.get('is_favorite')),
            create_time=create_time,
            update_time=update_time,
            kb_ids=kb_ids
        ) 