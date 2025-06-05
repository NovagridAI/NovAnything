"""
用户组成员相关数据模型
"""
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GroupMember:
    """用户组成员模型"""
    group_id: str
    user_id: str
    role: str = 'member'  # 'owner', 'admin', 'member'
    status: str = 'active'  # 'active', 'inactive'
    join_time: Optional[datetime] = None
    id: Optional[int] = None
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'group_id': self.group_id,
            'user_id': self.user_id,
            'role': self.role,
            'status': self.status
        }
        
        return data
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            group_id=data.get('group_id'),
            user_id=data.get('user_id'),
            role=data.get('role', 'member'),
            status=data.get('status', 'active'),
            join_time=data.get('join_time')
        ) 