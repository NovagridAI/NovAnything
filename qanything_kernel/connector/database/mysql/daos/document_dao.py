"""
文档数据访问对象
"""
import json
from typing import List, Optional, Dict, Any, Tuple
from qanything_kernel.utils.custom_log import debug_logger, insert_logger
from qanything_kernel.connector.database.mysql.daos.base_dao import BaseDAO
from qanything_kernel.connector.database.mysql.models.document import Document


class DocumentDAO(BaseDAO):
    """文档数据访问对象类"""
    
    def __init__(self, db_connection):
        """初始化"""
        super().__init__(db_connection)
        self.table = 'Documents'
    
    def create_table(self):
        """创建文档表"""
        query = """
            CREATE TABLE IF NOT EXISTS Documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                doc_id VARCHAR(255) UNIQUE,
                json_data LONGTEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute_query(query, commit=True)
    
    def add_document(self, document: Document) -> bool:
        """添加文档
        
        Args:
            document: 文档对象
            
        Returns:
            是否成功
        """
        json_data = document.to_dict().get('json_data')
        
        query = "INSERT IGNORE INTO Documents (doc_id, json_data) VALUES (%s, %s)"
        result = self.execute_query(query, (document.doc_id, json_data), commit=True, check=True)
        return result > 0
    
    def update_document(self, doc_id: str, update_content: str) -> bool:
        """更新文档内容
        
        Args:
            doc_id: 文档ID
            update_content: 更新的内容
            
        Returns:
            是否成功
        """
        # 先获取原始文档
        original_doc = self.get_document_by_doc_id(doc_id)
        if not original_doc:
            return False
            
        # 更新内容
        original_doc.json_data['kwargs']['page_content'] = update_content
        json_data = json.dumps(original_doc.json_data, ensure_ascii=False)
        
        # 执行更新
        query = "UPDATE Documents SET json_data = %s WHERE doc_id = %s"
        result = self.execute_query(query, (json_data, doc_id), commit=True, check=True)
        return result > 0
    
    def get_document_by_doc_id(self, doc_id: str) -> Optional[Document]:
        """根据文档ID获取文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档对象
        """
        query = "SELECT json_data FROM Documents WHERE doc_id = %s"
        result = self.execute_query(query, (doc_id,), fetch=True)
        
        if result:
            json_data = json.loads(result[0][0])
            return Document(doc_id=doc_id, json_data=json_data)
        else:
            debug_logger.error(f"get_document: doc_id: {doc_id} not found")
            return None
    
    def get_document_by_file_id(self, file_id: str, batch_size: int = 100) -> Optional[List[Dict[str, Any]]]:
        """根据文件ID获取所有相关文档
        
        Args:
            file_id: 文件ID
            batch_size: 批处理大小
            
        Returns:
            文档对象列表
        """
        # 初始化结果列表
        all_json_datas = []

        # 搜索doc_id中包含file_id的所有Doc
        query = "SELECT doc_id, json_data FROM Documents WHERE doc_id LIKE %s"
        offset = 0

        while True:
            # 执行带有LIMIT和OFFSET的查询语句
            paginated_query = f"{query} LIMIT %s OFFSET %s"
            doc_all = self.execute_query(paginated_query, (f"{file_id}_%", batch_size, offset), fetch=True)

            if not doc_all:
                break  # 如果没有更多数据，跳出循环

            doc_ids = [doc[0].split('_')[1] for doc in doc_all]
            json_datas = [json.loads(doc[1]) for doc in doc_all]
            for doc_id, json_data in zip(doc_ids, json_datas):
                json_data['kwargs']['chunk_id'] = file_id + '_' + str(doc_id)

            # 将doc_id和json_data打包并追加到结果列表
            all_json_datas.extend(zip(doc_ids, json_datas))

            offset += batch_size  # 更新offset

        debug_logger.info(f"get_document: file_id: {file_id}, mysql parent documents res: {len(all_json_datas)}")
        if all_json_datas:
            # 对所有数据进行排序
            all_json_datas.sort(key=lambda x: int(x[0]))
            # 解压排序后的结果
            sorted_json_datas = [json_data for _, json_data in all_json_datas]
            return sorted_json_datas
        return None
    
    def delete_documents(self, file_ids: List[str]) -> int:
        """删除与文件关联的所有文档
        
        Args:
            file_ids: 文件ID列表
            
        Returns:
            删除的数量
        """
        if not file_ids:
            return 0
            
        total_deleted = 0
        
        for file_id in file_ids:
            # 首先查找所有与file_id关联的文档
            query = f"SELECT doc_id FROM Documents WHERE doc_id LIKE %s"
            doc_ids_result = self.execute_query(query, (f"{file_id}_%",), fetch=True)
            
            if not doc_ids_result:
                continue
                
            doc_ids = [doc_id[0] for doc_id in doc_ids_result]
            debug_logger.info(f"Found documents to delete: {len(doc_ids)}, file_id: {file_id}")

            # 分批删除文档
            batch_size = 100
            for i in range(0, len(doc_ids), batch_size):
                batch_doc_ids = doc_ids[i:i + batch_size]
                placeholders = ','.join(['%s'] * len(batch_doc_ids))
                delete_query = f"DELETE FROM Documents WHERE doc_id IN ({placeholders})"
                res = self.execute_query(delete_query, tuple(batch_doc_ids), commit=True, check=True)
                total_deleted += res
                
        debug_logger.info(f"Deleted documents count: {total_deleted}")
        return total_deleted 