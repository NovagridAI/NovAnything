"""
问答日志数据访问对象
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from qanything_kernel.utils.custom_log import debug_logger, insert_logger
from qanything_kernel.connector.database.mysql.daos.base_dao import BaseDAO
from qanything_kernel.connector.database.mysql.models.qa_log import QaLog


class QaLogDAO(BaseDAO):
    """问答日志数据访问对象类"""
    
    def __init__(self, db_connection):
        """初始化"""
        super().__init__(db_connection)
        self.table = 'QaLogs'
    
    def create_table(self):
        """创建问答日志表"""
        query = """
            CREATE TABLE IF NOT EXISTS QaLogs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                qa_id VARCHAR(255) UNIQUE,
                user_id VARCHAR(255) NOT NULL,
                bot_id VARCHAR(255),
                kb_ids VARCHAR(2048) NOT NULL,
                query VARCHAR(512) NOT NULL,
                model VARCHAR(64) NOT NULL,
                product_source VARCHAR(64) NOT NULL,
                time_record VARCHAR(512) NOT NULL,
                history MEDIUMTEXT NOT NULL,
                condense_question VARCHAR(1024) NOT NULL,
                prompt MEDIUMTEXT NOT NULL,
                result TEXT NOT NULL,
                retrieval_documents MEDIUMTEXT NOT NULL,
                source_documents MEDIUMTEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute_query(query, commit=True)
        
        # 创建索引
        index_queries = [
            "CREATE INDEX index_bot_id ON QaLogs (bot_id)",
            "CREATE INDEX index_query ON QaLogs (query)",
            "CREATE INDEX index_timestamp ON QaLogs (timestamp)"
        ]
        
        for query in index_queries:
            try:
                self.execute_query(query, commit=True)
                debug_logger.info(f"Index created successfully: {query}")
            except Exception as e:
                if "Duplicate key" in str(e):
                    debug_logger.info(f"Index already exists (this is okay): {query}")
                else:
                    debug_logger.error(f"Error creating index: {e}")
    
    def add_qa_log(self, qa_log: QaLog) -> None:
        """添加问答日志
        
        Args:
            qa_log: 问答日志对象
        """
        if not qa_log.qa_id:
            qa_log.qa_id = uuid.uuid4().hex
            
        qa_data = qa_log.to_dict()
        
        query = (
            "INSERT INTO QaLogs (qa_id, user_id, bot_id, kb_ids, query, model, product_source, time_record, "
            "history, condense_question, prompt, result, retrieval_documents, source_documents) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        
        self.execute_query(
            query, 
            (
                qa_data.get('qa_id'),
                qa_data.get('user_id'),
                qa_data.get('bot_id'),
                qa_data.get('kb_ids'),
                qa_data.get('query'),
                qa_data.get('model'),
                qa_data.get('product_source'),
                qa_data.get('time_record'),
                qa_data.get('history'),
                qa_data.get('condense_question'),
                qa_data.get('prompt'),
                qa_data.get('result'),
                qa_data.get('retrieval_documents'),
                qa_data.get('source_documents')
            ),
            commit=True
        )
        debug_logger.info(f"添加问答日志: {qa_data.get('query')}")
    
    def get_qa_log_by_filter(self, need_info: List[str], user_id: Optional[str] = None, 
                              query: Optional[str] = None, bot_id: Optional[str] = None, 
                              time_range: Optional[Tuple[datetime, datetime]] = None,
                              any_kb_id: Optional[str] = None, qa_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """根据条件获取问答日志
        
        Args:
            need_info: 需要获取的字段列表
            user_id: 用户ID
            query: 查询内容
            bot_id: 机器人ID
            time_range: 时间范围元组 (开始时间, 结束时间)
            any_kb_id: 包含特定知识库ID
            qa_ids: 问答ID列表
            
        Returns:
            符合条件的问答日志列表
        """
        # 将需要的字段转为字符串
        need_info_str = ", ".join(need_info)
        
        # 如果有指定qa_ids，则直接按ID查询
        if qa_ids is not None:
            placeholders = ','.join(['%s'] * len(qa_ids))
            mysql_query = f"SELECT {need_info_str} FROM QaLogs WHERE qa_id IN ({placeholders})"
            qa_infos = self.execute_query(mysql_query, tuple(qa_ids), fetch=True)
        else:
            # 否则按条件查询
            if not time_range:
                # 默认查询全部时间
                time_range = (datetime(1970, 1, 1), datetime.now())
                
            mysql_query = f"SELECT {need_info_str} FROM QaLogs WHERE timestamp BETWEEN %s AND %s"
            params = list(time_range)
            
            if user_id:
                mysql_query += " AND user_id = %s"
                params.append(user_id)
                
            if any_kb_id:
                mysql_query += " AND kb_ids LIKE %s"
                params.append(f'%{any_kb_id}%')
                
            if bot_id:
                mysql_query += " AND bot_id = %s"
                params.append(bot_id)
                
            if query:
                mysql_query += " AND query = %s"
                params.append(query)
                
            debug_logger.info(f"get_qa_log_by_filter: {params}")
            qa_infos = self.execute_query(mysql_query, tuple(params), fetch=True)
            
        # 处理结果并转换为字典
        if not qa_infos:
            return []
            
        # 将结果转为字典列表
        field_names = need_info
        result_dicts = []
        
        for qa_info in qa_infos:
            result_dict = dict(zip(field_names, qa_info))
            
            # 处理时间戳格式
            if 'timestamp' in result_dict:
                result_dict['timestamp'] = result_dict['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                
            # 解析JSON字段
            for field in ['kb_ids', 'time_record', 'retrieval_documents', 'source_documents', 'history']:
                if field in result_dict and isinstance(result_dict[field], str):
                    try:
                        result_dict[field] = json.loads(result_dict[field])
                    except json.JSONDecodeError:
                        # 如果解析失败，保持原样
                        pass
                        
            result_dicts.append(result_dict)
            
        # 根据时间戳排序（如果有要求）
        if 'timestamp' in need_info:
            result_dicts = sorted(result_dicts, key=lambda x: x["timestamp"], reverse=True)
            
        return result_dicts
    
    def get_qa_log_by_id(self, qa_id: str, need_info: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """根据ID获取问答日志
        
        Args:
            qa_id: 问答ID
            need_info: 需要获取的字段列表
            
        Returns:
            问答日志详情
        """
        if need_info is None:
            need_info = ["user_id", "kb_ids", "query", "condense_question", "result", "timestamp", "product_source"]
            
        if "user_id" not in need_info:
            need_info.append("user_id")
            
        if "kb_ids" not in need_info:
            need_info.append("kb_ids")
            
        need_info_str = ", ".join(need_info)
        query = f"SELECT {need_info_str} FROM QaLogs WHERE qa_id = %s"
        
        result = self.execute_query(query, (qa_id,), fetch=True)
        if not result:
            return None
            
        # 转为字典
        qa_log = dict(zip(need_info, result[0]))
        
        # 处理时间戳
        if 'timestamp' in qa_log:
            qa_log['timestamp'] = qa_log['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            
        # 解析JSON字段
        for field in ['kb_ids', 'time_record', 'retrieval_documents', 'source_documents', 'history']:
            if field in qa_log and isinstance(qa_log[field], str):
                try:
                    qa_log[field] = json.loads(qa_log[field])
                except json.JSONDecodeError:
                    # 如果解析失败，保持原样
                    pass
                    
        return qa_log
    
    def get_related_qa_logs(self, qa_id: str, need_info: Optional[List[str]] = None, 
                             need_more: bool = False) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """获取与指定问答相关的其他问答日志
        
        Args:
            qa_id: 问答ID
            need_info: 需要获取的字段列表
            need_more: 是否需要获取更多相关问答
            
        Returns:
            (当前问答, 最近7天内的问答, 7天前的问答)
        """
        # 1. 获取当前问答
        current_qa = self.get_qa_log_by_id(qa_id, need_info)
        if not current_qa:
            return {}, [], []
            
        if not need_more:
            return current_qa, [], []
            
        user_id = current_qa.get('user_id')
        
        # 获取当前时间和7天前的时间
        current_time = datetime.utcnow()
        seven_days_ago = current_time - timedelta(days=7)
        
        need_info_str = ", ".join(need_info) if need_info else "*"
        
        # 2. 查询7天以内的日志
        recent_logs = []
        limit = 50
        
        query_recent_logs = f"""
            SELECT {need_info_str}
            FROM QaLogs
            WHERE user_id = %s AND timestamp >= %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        
        results = self.execute_query(query_recent_logs, (user_id, seven_days_ago, limit), fetch=True)
        if results:
            # 转换为字典列表
            field_names = need_info or self._get_column_names(results)
            for result in results:
                log = dict(zip(field_names, result))
                
                # 处理时间戳
                if 'timestamp' in log:
                    log['timestamp'] = log['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                    
                # 解析JSON字段
                for field in ['kb_ids', 'time_record', 'retrieval_documents', 'source_documents', 'history']:
                    if field in log and isinstance(log[field], str):
                        try:
                            log[field] = json.loads(log[field])
                        except json.JSONDecodeError:
                            # 如果解析失败，保持原样
                            pass
                            
                recent_logs.append(log)
        
        # 3. 查询7天之前的日志
        older_logs = []
        
        query_older_logs = f"""
            SELECT {need_info_str}
            FROM QaLogs
            WHERE user_id = %s AND timestamp < %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        
        results = self.execute_query(query_older_logs, (user_id, seven_days_ago, limit), fetch=True)
        if results:
            # 转换为字典列表
            field_names = need_info or self._get_column_names(results)
            for result in results:
                log = dict(zip(field_names, result))
                
                # 处理时间戳
                if 'timestamp' in log:
                    log['timestamp'] = log['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                    
                # 解析JSON字段
                for field in ['kb_ids', 'time_record', 'retrieval_documents', 'source_documents', 'history']:
                    if field in log and isinstance(log[field], str):
                        try:
                            log[field] = json.loads(log[field])
                        except json.JSONDecodeError:
                            # 如果解析失败，保持原样
                            pass
                            
                older_logs.append(log)
                
        return current_qa, recent_logs, older_logs
    
    def get_statistic(self, time_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        """获取指定时间范围内的统计信息
        
        Args:
            time_range: 时间范围元组 (开始时间, 结束时间)
            
        Returns:
            统计信息字典，包含用户数和查询数
        """
        query = """
            SELECT COUNT(DISTINCT user_id) AS total_users, COUNT(query) AS total_queries
            FROM QaLogs
            WHERE timestamp BETWEEN %s AND %s
        """
        
        result = self.execute_query(query, time_range, fetch=True)
        if not result:
            return {"total_users": 0, "total_queries": 0}
            
        return {
            "total_users": result[0][0],
            "total_queries": result[0][1]
        }
    
    def get_random_qa_logs(self, limit: int = 10, time_range: Optional[Tuple[datetime, datetime]] = None,
                          need_info: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取随机问答日志
        
        Args:
            limit: 最大返回数量
            time_range: 时间范围元组 (开始时间, 结束时间)
            need_info: 需要获取的字段列表
            
        Returns:
            随机问答日志列表
        """
        if need_info is None:
            need_info = ["qa_id", "user_id", "kb_ids", "query", "result", "timestamp"]
            
        if "qa_id" not in need_info:
            need_info.append("qa_id")
            
        if "user_id" not in need_info:
            need_info.append("user_id")
            
        if "timestamp" not in need_info:
            need_info.append("timestamp")
            
        need_info_str = ", ".join(need_info)
        
        if not time_range:
            # 默认查询全部时间
            time_range = (datetime(1970, 1, 1), datetime.now())
            
        query = f"SELECT {need_info_str} FROM QaLogs WHERE timestamp BETWEEN %s AND %s ORDER BY RAND() LIMIT %s"
        
        results = self.execute_query(query, (time_range[0], time_range[1], limit), fetch=True)
        if not results:
            return []
            
        # 转换为字典列表
        qa_logs = []
        
        for result in results:
            log = dict(zip(need_info, result))
            
            # 处理时间戳
            if 'timestamp' in log:
                log['timestamp'] = log['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                
            # 解析JSON字段
            for field in ['kb_ids', 'time_record', 'retrieval_documents', 'source_documents', 'history']:
                if field in log and isinstance(log[field], str):
                    try:
                        log[field] = json.loads(log[field])
                    except json.JSONDecodeError:
                        # 如果解析失败，保持原样
                        pass
                        
            qa_logs.append(log)
            
        return qa_logs
    
    def _get_column_names(self, results) -> List[str]:
        """获取查询结果的列名
        
        Args:
            results: 查询结果
            
        Returns:
            列名列表
        """
        # 这是一个辅助方法，当没有提供need_info时使用
        # 实际实现可能需要根据数据库连接的能力来定制
        # 这里作为占位符实现
        return [
            "qa_id", "user_id", "bot_id", "kb_ids", "query", "model", 
            "product_source", "time_record", "history", "condense_question", 
            "prompt", "result", "retrieval_documents", "source_documents", "timestamp"
        ] 