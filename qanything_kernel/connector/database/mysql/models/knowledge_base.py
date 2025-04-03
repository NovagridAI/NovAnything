"""
知识库相关数据模型
"""
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class KnowledgeBase:
    """知识库模型"""
    kb_id: str
    user_id: str
    kb_name: str
    deleted: bool = False
    latest_qa_time: Optional[datetime] = None
    latest_insert_time: Optional[datetime] = None
    id: Optional[int] = None
    kb_type: str = 'personal'  # 'personal', 'team', 'temporary'
    expired_at: Optional[datetime] = None  # 临时知识库过期时间
    description: Optional[str] = None  # 知识库描述
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'kb_id': self.kb_id,
            'user_id': self.user_id,
            'kb_name': self.kb_name,
            'kb_type': self.kb_type,
            'deleted': self.deleted
        }
        
        if self.expired_at is not None:
            data['expired_at'] = self.expired_at
            
        if self.latest_qa_time is not None:
            data['latest_qa_time'] = self.latest_qa_time
            
        if self.latest_insert_time is not None:
            data['latest_insert_time'] = self.latest_insert_time
        
        if self.description is not None:
            data['description'] = self.description
            
        return data
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            kb_id=data.get('kb_id'),
            user_id=data.get('user_id'),
            kb_name=data.get('kb_name'),
            kb_type=data.get('kb_type', 'personal'),
            expired_at=data.get('expired_at'),
            deleted=bool(data.get('deleted', 0)),
            latest_qa_time=data.get('latest_qa_time'),
            latest_insert_time=data.get('latest_insert_time'),
            description=data.get('description')
        )


@dataclass
class KnowledgeBaseAccess:
    """知识库访问权限模型"""
    kb_id: str
    subject_id: str  # 用户ID、部门ID或用户组ID
    subject_type: str  # 'user', 'department', 'group'
    permission_type: str  # 'read', 'write', 'admin'
    granted_by: str
    granted_at: datetime = None
    id: Optional[int] = None
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'kb_id': self.kb_id,
            'subject_id': self.subject_id,
            'subject_type': self.subject_type,
            'permission_type': self.permission_type,
            'granted_by': self.granted_by
        }
        
        if self.granted_at is not None:
            data['granted_at'] = self.granted_at
            
        return data
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            kb_id=data.get('kb_id'),
            subject_id=data.get('subject_id'),
            subject_type=data.get('subject_type'),
            permission_type=data.get('permission_type'),
            granted_by=data.get('granted_by'),
            granted_at=data.get('granted_at')
        ) 