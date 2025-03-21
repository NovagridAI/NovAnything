"""
部门相关数据模型
"""
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Department:
    """部门模型"""
    dept_id: str
    dept_name: str
    parent_dept_id: Optional[str] = None
    description: Optional[str] = None
    creation_time: Optional[datetime] = None
    id: Optional[int] = None
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'dept_id': self.dept_id,
            'dept_name': self.dept_name
        }
        
        if self.parent_dept_id is not None:
            data['parent_dept_id'] = self.parent_dept_id
            
        if self.description is not None:
            data['description'] = self.description
            
        return data
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            dept_id=data.get('dept_id'),
            dept_name=data.get('dept_name'),
            parent_dept_id=data.get('parent_dept_id'),
            description=data.get('description'),
            creation_time=data.get('creation_time')
        ) 