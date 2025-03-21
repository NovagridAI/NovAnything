"""
用户组相关数据模型
"""
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserGroup:
    """用户组模型"""
    group_id: str
    group_name: str
    owner_id: str
    description: Optional[str] = None
    creation_time: Optional[datetime] = None
    id: Optional[int] = None
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'group_id': self.group_id,
            'group_name': self.group_name,
            'owner_id': self.owner_id
        }
        
        if self.description is not None:
            data['description'] = self.description
            
        return data
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            group_id=data.get('group_id'),
            group_name=data.get('group_name'),
            owner_id=data.get('owner_id'),
            description=data.get('description'),
            creation_time=data.get('creation_time')
        ) 