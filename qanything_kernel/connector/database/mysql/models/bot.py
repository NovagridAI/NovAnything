"""
聊天机器人相关数据模型
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class QanythingBot:
    """聊天机器人模型"""
    bot_id: str
    user_id: str
    bot_name: str
    description: str
    head_image: str
    prompt_setting: str
    welcome_message: str
    kb_ids_str: str
    deleted: int = 0
    llm_setting: Optional[Dict[str, Any]] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'bot_id': self.bot_id,
            'user_id': self.user_id,
            'bot_name': self.bot_name,
            'description': self.description,
            'head_image': self.head_image,
            'prompt_setting': self.prompt_setting,
            'welcome_message': self.welcome_message,
            'kb_ids_str': self.kb_ids_str,
            'deleted': self.deleted
        }
        
        if self.llm_setting is not None:
            data['llm_setting'] = json.dumps(self.llm_setting, ensure_ascii=False)
            
        if self.create_time is not None:
            data['create_time'] = self.create_time
            
        if self.update_time is not None:
            data['update_time'] = self.update_time
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QanythingBot':
        """从字典创建对象"""
        llm_setting = data.get('llm_setting')
        if isinstance(llm_setting, str):
            try:
                llm_setting = json.loads(llm_setting)
            except json.JSONDecodeError:
                llm_setting = {}
                
        return cls(
            id=data.get('id'),
            bot_id=data.get('bot_id'),
            user_id=data.get('user_id'),
            bot_name=data.get('bot_name'),
            description=data.get('description'),
            head_image=data.get('head_image'),
            prompt_setting=data.get('prompt_setting'),
            welcome_message=data.get('welcome_message'),
            kb_ids_str=data.get('kb_ids_str'),
            deleted=int(data.get('deleted', 0)),
            llm_setting=llm_setting,
            create_time=data.get('create_time'),
            update_time=data.get('update_time')
        ) 