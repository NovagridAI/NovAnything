"""
文件相关数据模型
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class File:
    """文件模型"""
    file_id: str
    kb_id: str
    file_name: str
    status: str
    user_id: str = "unknown"
    msg: str = "success"
    transfer_status: Optional[str] = None
    deleted: bool = False
    file_size: int = -1
    content_length: int = -1
    chunks_number: int = -1
    file_location: str = "unknown"
    file_url: str = ""
    upload_infos: Optional[str] = None
    chunk_size: int = -1
    timestamp: str = "197001010000"
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'file_id': self.file_id,
            'kb_id': self.kb_id,
            'file_name': self.file_name,
            'status': self.status,
            'user_id': self.user_id,
            'msg': self.msg,
            'deleted': self.deleted,
            'file_size': self.file_size,
            'content_length': self.content_length,
            'chunks_number': self.chunks_number,
            'file_location': self.file_location,
            'file_url': self.file_url,
            'chunk_size': self.chunk_size,
            'timestamp': self.timestamp
        }
        
        if self.transfer_status is not None:
            data['transfer_status'] = self.transfer_status
            
        if self.upload_infos is not None:
            data['upload_infos'] = self.upload_infos
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'File':
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            file_id=data.get('file_id'),
            kb_id=data.get('kb_id'),
            file_name=data.get('file_name'),
            status=data.get('status'),
            user_id=data.get('user_id', 'unknown'),
            msg=data.get('msg', 'success'),
            transfer_status=data.get('transfer_status'),
            deleted=bool(data.get('deleted', 0)),
            file_size=int(data.get('file_size', -1)),
            content_length=int(data.get('content_length', -1)),
            chunks_number=int(data.get('chunks_number', -1)),
            file_location=data.get('file_location', 'unknown'),
            file_url=data.get('file_url', ''),
            upload_infos=data.get('upload_infos'),
            chunk_size=int(data.get('chunk_size', -1)),
            timestamp=data.get('timestamp', '197001010000')
        )


@dataclass
class FileImage:
    """文件图片模型"""
    image_id: str
    file_id: str
    user_id: str
    kb_id: str
    nos_key: str
    timestamp: Optional[datetime] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'image_id': self.image_id,
            'file_id': self.file_id,
            'user_id': self.user_id,
            'kb_id': self.kb_id,
            'nos_key': self.nos_key
        }
        
        if self.timestamp is not None:
            data['timestamp'] = self.timestamp
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileImage':
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            image_id=data.get('image_id'),
            file_id=data.get('file_id'),
            user_id=data.get('user_id'),
            kb_id=data.get('kb_id'),
            nos_key=data.get('nos_key'),
            timestamp=data.get('timestamp')
        ) 