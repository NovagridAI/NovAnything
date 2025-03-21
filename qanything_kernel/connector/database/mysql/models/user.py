"""
用户相关数据模型
"""
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """用户模型"""
    user_id: str
    user_name: str
    dept_id: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: str = 'user'
    status: str = 'active'
    creation_time: datetime = None
    id: Optional[int] = None
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'role': self.role,
            'status': self.status
        }
        
        if self.dept_id is not None:
            data['dept_id'] = self.dept_id
            
        if self.email is not None:
            data['email'] = self.email
            
        if self.password is not None:
            data['password'] = self.password
            
        return data
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            user_name=data.get('user_name'),
            dept_id=data.get('dept_id'),
            email=data.get('email'),
            password=data.get('password'),
            role=data.get('role', 'user'),
            status=data.get('status', 'active'),
            creation_time=data.get('creation_time')
        )
        