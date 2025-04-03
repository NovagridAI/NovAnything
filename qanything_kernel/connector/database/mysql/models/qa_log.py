"""
问答日志相关数据模型
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class QaLog:
    """问答日志模型"""
    qa_id: str
    user_id: str
    kb_ids: List[str]
    query: str
    model: str
    product_source: str
    time_record: Dict[str, Any]
    history: List[List[str]]
    condense_question: str
    prompt: str
    retrieval_documents: List[Dict[str, Any]]
    source_documents: List[Dict[str, Any]]
    result: Optional[str] = None
    bot_id: Optional[str] = None
    is_favorite: Optional[bool] = False
    timestamp: Optional[datetime] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        # 确保kb_ids是字符串列表
        kb_ids = [str(item) for item in self.kb_ids] if isinstance(self.kb_ids, list) else []
        
        # 确保复杂对象都被正确序列化
        data = {
            'qa_id': self.qa_id,
            'user_id': self.user_id,
            'kb_ids': json.dumps(kb_ids, ensure_ascii=False),
            'query': self.query,
            'model': self.model,
            'product_source': self.product_source,
            'time_record': json.dumps(self.time_record if isinstance(self.time_record, dict) else {}, ensure_ascii=False),
            'history': json.dumps(self.history if isinstance(self.history, list) else [], ensure_ascii=False),
            'condense_question': self.condense_question,
            'prompt': self.prompt,
            'result': self.result,
            'retrieval_documents': json.dumps(self.retrieval_documents if isinstance(self.retrieval_documents, list) else [], ensure_ascii=False),
            'source_documents': json.dumps(self.source_documents if isinstance(self.source_documents, list) else [], ensure_ascii=False)
        }
        
        if self.bot_id is not None:
            data['bot_id'] = self.bot_id

        if self.is_favorite is not None:
            data['is_favorite'] = self.is_favorite
            
        if self.timestamp is not None:
            data['timestamp'] = self.timestamp
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QaLog':
        """从字典创建对象"""
        # 安全解析JSON字段
        def safe_json_loads(value, default=None):
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return default
            return value
            
        kb_ids = safe_json_loads(data.get('kb_ids'), [])
        # 确保kb_ids是字符串列表
        if isinstance(kb_ids, list):
            kb_ids = [str(item) for item in kb_ids]
        else:
            kb_ids = []
            
        time_record = safe_json_loads(data.get('time_record'), {})
        history = safe_json_loads(data.get('history'), [])
        retrieval_documents = safe_json_loads(data.get('retrieval_documents'), [])
        source_documents = safe_json_loads(data.get('source_documents'), [])
            
        return cls(
            id=data.get('id'),
            qa_id=data.get('qa_id'),
            user_id=data.get('user_id'),
            bot_id=data.get('bot_id'),
            kb_ids=kb_ids,
            query=data.get('query', ''),
            model=data.get('model', ''),
            product_source=data.get('product_source', 'unknown'),
            time_record=time_record,
            history=history,
            condense_question=data.get('condense_question', ''),
            prompt=data.get('prompt', ''),
            result=data.get('result', ''),
            retrieval_documents=retrieval_documents,
            source_documents=source_documents,
            is_favorite=data.get('is_favorite', False),
            timestamp=data.get('timestamp')
        ) 