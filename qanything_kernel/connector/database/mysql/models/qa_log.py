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
    result: str
    retrieval_documents: List[Dict[str, Any]]
    source_documents: List[Dict[str, Any]]
    bot_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'qa_id': self.qa_id,
            'user_id': self.user_id,
            'kb_ids': json.dumps(self.kb_ids, ensure_ascii=False),
            'query': self.query,
            'model': self.model,
            'product_source': self.product_source,
            'time_record': json.dumps(self.time_record, ensure_ascii=False),
            'history': json.dumps(self.history, ensure_ascii=False),
            'condense_question': self.condense_question,
            'prompt': self.prompt,
            'result': self.result,
            'retrieval_documents': json.dumps(self.retrieval_documents, ensure_ascii=False),
            'source_documents': json.dumps(self.source_documents, ensure_ascii=False)
        }
        
        if self.bot_id is not None:
            data['bot_id'] = self.bot_id
            
        if self.timestamp is not None:
            data['timestamp'] = self.timestamp
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QaLog':
        """从字典创建对象"""
        kb_ids = data.get('kb_ids')
        if isinstance(kb_ids, str):
            kb_ids = json.loads(kb_ids)
            
        time_record = data.get('time_record')
        if isinstance(time_record, str):
            time_record = json.loads(time_record)
            
        history = data.get('history')
        if isinstance(history, str):
            history = json.loads(history)
            
        retrieval_documents = data.get('retrieval_documents')
        if isinstance(retrieval_documents, str):
            retrieval_documents = json.loads(retrieval_documents)
            
        source_documents = data.get('source_documents')
        if isinstance(source_documents, str):
            source_documents = json.loads(source_documents)
            
        return cls(
            id=data.get('id'),
            qa_id=data.get('qa_id'),
            user_id=data.get('user_id'),
            bot_id=data.get('bot_id'),
            kb_ids=kb_ids,
            query=data.get('query'),
            model=data.get('model'),
            product_source=data.get('product_source'),
            time_record=time_record,
            history=history,
            condense_question=data.get('condense_question'),
            prompt=data.get('prompt'),
            result=data.get('result'),
            retrieval_documents=retrieval_documents,
            source_documents=source_documents,
            timestamp=data.get('timestamp')
        ) 