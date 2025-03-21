"""
FAQ数据访问对象
"""
from typing import List, Optional, Dict, Any, Tuple
from qanything_kernel.utils.custom_log import debug_logger, insert_logger
from qanything_kernel.connector.database.mysql.daos.base_dao import BaseDAO
from qanything_kernel.connector.database.mysql.models.faq import Faq


class FaqDAO(BaseDAO):
    """FAQ数据访问对象类"""
    
    def __init__(self, db_connection):
        """初始化"""
        super().__init__(db_connection)
        self.table = 'Faqs'
    
    def create_table(self):
        """创建FAQ表"""
        query = """
            CREATE TABLE IF NOT EXISTS Faqs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                faq_id  VARCHAR(255) UNIQUE,
                user_id VARCHAR(255) NOT NULL,
                kb_id VARCHAR(255) NOT NULL,
                question VARCHAR(512) NOT NULL,
                answer VARCHAR(2048) NOT NULL,
                nos_keys VARCHAR(768)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute_query(query, commit=True)
    
    def add_faq(self, faq: Faq) -> None:
        """添加FAQ
        
        Args:
            faq: FAQ对象
        """
        query = "INSERT INTO Faqs (faq_id, user_id, kb_id, question, answer, nos_keys) VALUES (%s, %s, %s, %s, %s, %s)"
        self.execute_query(
            query, 
            (faq.faq_id, faq.user_id, faq.kb_id, faq.question, faq.answer, faq.nos_keys), 
            commit=True
        )
        insert_logger.info(f"添加FAQ: {faq.faq_id}, {faq.user_id}, {faq.kb_id}, {faq.question}, {faq.nos_keys}")
    
    def get_faq(self, faq_id: str) -> Optional[Faq]:
        """获取FAQ
        
        Args:
            faq_id: FAQ ID
            
        Returns:
            FAQ对象
        """
        query = "SELECT user_id, kb_id, question, answer, nos_keys FROM Faqs WHERE faq_id = %s"
        result = self.execute_query(query, (faq_id,), fetch=True)
        
        if result:
            faq_data = result[0]
            debug_logger.info(f"获取FAQ: faq_id: {faq_id}, mysql结果: {faq_data}")
            
            faq = Faq(
                faq_id=faq_id,
                user_id=faq_data[0],
                kb_id=faq_data[1],
                question=faq_data[2],
                answer=faq_data[3],
                nos_keys=faq_data[4]
            )
            return faq
        else:
            debug_logger.error(f"获取FAQ: faq_id: {faq_id} 未找到")
            return None
    
    def get_faq_by_question(self, question: str, kb_id: str) -> Optional[str]:
        """根据问题获取FAQ ID
        
        Args:
            question: 问题内容
            kb_id: 知识库ID
            
        Returns:
            FAQ ID
        """
        query = "SELECT faq_id FROM Faqs WHERE question = %s AND kb_id = %s"
        result = self.execute_query(query, (question, kb_id), fetch=True)
        
        if not result:
            return None
            
        faq_id = result[0][0]
        # 检查文件状态
        # TODO: 这里依赖于文件状态，可能需要重构
        query = "SELECT status FROM File WHERE file_id = %s"
        result = self.execute_query(query, (faq_id,), fetch=True)
        if result and result[0][0] == 'green':
            return faq_id
            
        return None
    
    def delete_faqs(self, faq_ids: List[str]) -> int:
        """删除FAQ
        
        Args:
            faq_ids: FAQ ID列表
            
        Returns:
            删除的数量
        """
        if not faq_ids:
            return 0
            
        # 分批处理，防止SQL过长
        batch_size = 100
        total_deleted = 0
        
        for i in range(0, len(faq_ids), batch_size):
            batch_faq_ids = faq_ids[i:i + batch_size]
            placeholders = ','.join(['%s'] * len(batch_faq_ids))
            query = f"DELETE FROM Faqs WHERE faq_id IN ({placeholders})"
            res = self.execute_query(query, tuple(batch_faq_ids), commit=True, check=True)
            total_deleted += res
            
        debug_logger.info(f"删除FAQ数量: {total_deleted}")
        return total_deleted 