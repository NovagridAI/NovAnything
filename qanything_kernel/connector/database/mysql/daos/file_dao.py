"""
文件数据访问对象
"""
import json
from datetime import datetime
from collections import defaultdict
from typing import List, Optional, Dict, Any, Tuple
from qanything_kernel.utils.custom_log import debug_logger, insert_logger
from qanything_kernel.connector.database.mysql.daos.base_dao import BaseDAO
from qanything_kernel.connector.database.mysql.models.file import File, FileImage


class FileDAO(BaseDAO):
    """文件数据访问对象类"""
    
    def __init__(self, db_connection):
        """初始化"""
        super().__init__(db_connection)
        self.table = 'File'
        self.image_table = 'FileImages'
    
    def create_table(self):
        """创建文件相关表"""
        # 创建文件表
        query = """
            CREATE TABLE IF NOT EXISTS File (
                id INT AUTO_INCREMENT PRIMARY KEY,
                file_id VARCHAR(255) UNIQUE,
                user_id VARCHAR(255) DEFAULT 'unknown',
                kb_id VARCHAR(255),
                file_name VARCHAR(255),
                status VARCHAR(255),
                msg VARCHAR(255) DEFAULT 'success',
                transfer_status VARCHAR(255),
                deleted BOOL DEFAULT 0,
                file_size INT DEFAULT -1,
                content_length INT DEFAULT -1,
                chunks_number INT DEFAULT -1,
                file_location VARCHAR(255) DEFAULT 'unknown',
                file_url VARCHAR(2048) DEFAULT '',
                upload_infos TEXT,
                chunk_size INT DEFAULT -1,
                timestamp VARCHAR(255) DEFAULT '197001010000'
            );
        """
        self.execute_query(query, commit=True)
        
        # 创建文件图片表
        query = """
            CREATE TABLE IF NOT EXISTS FileImages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                image_id VARCHAR(255) UNIQUE,
                file_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                kb_id VARCHAR(255) NOT NULL,
                nos_key VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute_query(query, commit=True)
        
        # 创建索引
        index_queries = [
            "CREATE INDEX index_kb_id_deleted ON File (kb_id, deleted)",
            "CREATE INDEX idx_user_id_status ON File (user_id, status)",
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
    
    def add_file(self, file: File) -> str:
        """添加文件
        
        Args:
            file: 文件对象
            
        Returns:
            状态信息
        """
        query = (
            "INSERT INTO File (file_id, user_id, kb_id, file_name, status, file_size, file_location, "
            "chunk_size, timestamp, file_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        self.execute_query(
            query,
            (
                file.file_id, file.user_id, file.kb_id, file.file_name, file.status, 
                file.file_size, file.file_location, file.chunk_size, file.timestamp, file.file_url
            ),
            commit=True
        )
        return "success"
    
    def update_file_msg(self, file_id: str, msg: str) -> None:
        """更新文件消息
        
        Args:
            file_id: 文件ID
            msg: 消息内容
        """
        query = "UPDATE File SET msg = %s WHERE file_id = %s"
        insert_logger.info(f"Update file msg: {file_id} {msg}")
        self.execute_query(query, (msg, file_id), commit=True)
    
    def update_file_upload_infos(self, file_id: str, upload_infos: Dict) -> None:
        """更新文件上传信息
        
        Args:
            file_id: 文件ID
            upload_infos: 上传信息
        """
        upload_infos_json = json.dumps(upload_infos, ensure_ascii=False)
        query = "UPDATE File SET upload_infos = %s WHERE file_id = %s"
        self.execute_query(query, (upload_infos_json, file_id), commit=True)
    
    def update_content_length(self, file_id: str, content_length: int) -> None:
        """更新文件内容长度
        
        Args:
            file_id: 文件ID
            content_length: 内容长度
        """
        query = "UPDATE File SET content_length = %s WHERE file_id = %s"
        self.execute_query(query, (content_length, file_id), commit=True)
    
    def update_chunks_number(self, file_id: str, chunks_number: int) -> None:
        """更新文件分块数量
        
        Args:
            file_id: 文件ID
            chunks_number: 分块数量
        """
        query = "UPDATE File SET chunks_number = %s WHERE file_id = %s"
        self.execute_query(query, (chunks_number, file_id), commit=True)
    
    def update_file_status(self, file_id: str, status: str) -> None:
        """更新文件状态
        
        Args:
            file_id: 文件ID
            status: 状态
        """
        query = "UPDATE File SET status = %s WHERE file_id = %s"
        self.execute_query(query, (status, file_id), commit=True)
    
    def from_status_to_status(self, file_ids: List[str], from_status: str, to_status: str) -> None:
        """更新指定文件的状态
        
        Args:
            file_ids: 文件ID列表
            from_status: 原状态
            to_status: 目标状态
        """
        if not file_ids:
            return
            
        file_ids_str = ','.join(['%s'] * len(file_ids))
        query = f"UPDATE File SET status = %s WHERE file_id IN ({file_ids_str}) AND status = %s"
        self.execute_query(query, (to_status,) + tuple(file_ids) + (from_status,), commit=True)
    
    def get_files(self, kb_id: str, file_id: Optional[str] = None) -> List[Tuple]:
        """获取文件信息
        
        Args:
            kb_id: 知识库ID
            file_id: 文件ID，如果指定则只获取该文件
            
        Returns:
            文件信息列表
        """
        limit = 100
        offset = 0
        all_files = []

        base_query = """
            SELECT file_id, file_name, status, file_size, content_length, timestamp,
                   file_location, file_url, chunk_size, msg
            FROM File
            WHERE kb_id = %s AND deleted = 0
        """

        params = [kb_id]

        if file_id is not None:
            base_query += " AND file_id = %s"
            params.append(file_id)
            # Since file_id is specified, we only need one query
            query = base_query
            current_params = tuple(params)
            files = self.execute_query(query, current_params, fetch=True)
            return files if files else []

        while True:
            query = base_query + " LIMIT %s OFFSET %s"
            current_params = tuple(params + [limit, offset])
            files = self.execute_query(query, current_params, fetch=True)

            if not files:
                break

            all_files.extend(files)
            offset += limit

        return all_files
    
    def get_file_by_status(self, kb_ids: List[str], status: str) -> List[Tuple[str, str]]:
        """根据状态获取文件
        
        Args:
            kb_ids: 知识库ID列表
            status: 状态
            
        Returns:
            文件ID和名称列表
        """
        if not kb_ids:
            return []
            
        kb_ids_str = ','.join(['%s'] * len(kb_ids))
        query = f"SELECT file_id, file_name FROM File WHERE kb_id IN ({kb_ids_str}) AND deleted = 0 AND status = %s"
        result = self.execute_query(query, tuple(kb_ids) + (status,), fetch=True)
        return result if result else []
    
    def get_file_timestamp(self, file_id: str) -> Optional[str]:
        """获取文件时间戳
        
        Args:
            file_id: 文件ID
            
        Returns:
            时间戳
        """
        query = "SELECT timestamp FROM File WHERE file_id = %s"
        result = self.execute_query(query, (file_id,), fetch=True)
        return result[0][0] if result else None
    
    def get_file_location(self, file_id: str) -> Optional[str]:
        """获取文件位置
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件位置
        """
        query = "SELECT file_location FROM File WHERE file_id = %s"
        result = self.execute_query(query, (file_id,), fetch=True)
        return result[0][0] if result else None
    
    def check_file_exist(self, user_id: str, kb_id: str, file_ids: List[str]) -> List[Tuple]:
        """检查文件是否存在
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            file_ids: 文件ID列表
            
        Returns:
            存在的文件ID和状态列表
        """
        if not file_ids:
            debug_logger.info("check_file_exist: file_ids is empty")
            return []

        file_ids_str = ','.join(['%s'] * len(file_ids))
        query = f"""
            SELECT file_id, status FROM File
            WHERE deleted = 0
            AND file_id IN ({file_ids_str})
            AND kb_id = %s
            AND kb_id IN (SELECT kb_id FROM KnowledgeBase WHERE user_id = %s)
        """
        result = self.execute_query(query, tuple(file_ids) + (kb_id, user_id), fetch=True)
        debug_logger.info(f"check_file_exist {result}")
        return result if result else []
    
    def check_file_exist_by_name(self, user_id: str, kb_id: str, file_names: List[str]) -> List[Tuple]:
        """根据文件名检查文件是否存在
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            file_names: 文件名列表
            
        Returns:
            存在的文件信息列表
        """
        results = []
        batch_size = 100  # 根据实际情况调整批次大小

        # 分批处理file_names
        for i in range(0, len(file_names), batch_size):
            batch_file_names = file_names[i:i + batch_size]

            # 创建参数化的查询
            placeholders = ','.join(['%s'] * len(batch_file_names))
            query = f"""
                SELECT file_id, file_name, file_size, status FROM File
                WHERE deleted = 0
                AND file_name IN ({placeholders})
                AND kb_id = %s
                AND kb_id IN (SELECT kb_id FROM KnowledgeBase WHERE user_id = %s)
            """

            # 使用参数化查询，将文件名作为参数传递
            query_params = tuple(batch_file_names) + (kb_id, user_id)
            batch_result = self.execute_query(query, query_params, fetch=True)
            debug_logger.info(f"check_file_exist_by_name batch {i // batch_size}: {batch_result}")
            
            if batch_result:
                results.extend(batch_result)

        return results
    
    def is_deleted_file(self, file_id: str) -> bool:
        """检查文件是否已删除
        
        Args:
            file_id: 文件ID
            
        Returns:
            是否已删除
        """
        query = "SELECT deleted FROM File WHERE file_id = %s"
        result = self.execute_query(query, (file_id,), fetch=True)
        if result:
            return result[0][0] == 1
        else:
            return False
    
    def delete_files(self, kb_id: str, file_ids: List[str]) -> None:
        """删除文件
        
        Args:
            kb_id: 知识库ID
            file_ids: 文件ID列表
        """
        if not file_ids:
            return
            
        file_ids_str = ','.join(['%s'] * len(file_ids))
        query = f"UPDATE File SET deleted = 1 WHERE kb_id = %s AND file_id IN ({file_ids_str})"
        debug_logger.info(f"delete_files: {file_ids}")
        self.execute_query(query, (kb_id,) + tuple(file_ids), commit=True)
    
    def get_total_status_by_date(self, user_id: str) -> Dict[str, Dict[str, int]]:
        """获取用户文件按日期和状态的统计
        
        Args:
            user_id: 用户ID
            
        Returns:
            按日期和状态分组的文件数量统计
        """
        query = """
        SELECT
            LEFT(timestamp, 8) as date,  -- 提取前8个字符作为日期 (YYYYMMDD)
            status,
            COUNT(*) as number
        FROM File
        WHERE user_id = %s
        GROUP BY LEFT(timestamp, 8), status
        """
        result = self.execute_query(query, (user_id,), fetch=True)

        files_by_date = defaultdict(lambda: defaultdict(int))

        for date, status, number in result:
            files_by_date[date][status] = number

        return {date: dict(status_dict) for date, status_dict in files_by_date.items()}
    
    def get_chunk_size(self, file_ids: List[str]) -> List[int]:
        """获取文件分块大小
        
        Args:
            file_ids: 文件ID列表
            
        Returns:
            分块大小列表
        """
        if not file_ids:
            return []
            
        limit = 100
        offset = 0
        all_chunk_sizes = []

        while True:
            file_ids_sublist = file_ids[offset:offset + limit]
            if not file_ids_sublist:
                break

            file_ids_str = ','.join(['%s'] * len(file_ids_sublist))
            query = f"SELECT chunk_size FROM File WHERE file_id IN ({file_ids_str})"
            chunk_sizes = self.execute_query(query, tuple(file_ids_sublist), fetch=True)
            
            if not chunk_sizes:
                break
                
            all_chunk_sizes.extend([row[0] for row in chunk_sizes])
            offset += limit

        return all_chunk_sizes
    
    def get_files_by_status(self, status: str) -> List[Tuple[str, str]]:
        """获取指定状态的所有文件
        
        Args:
            status: 文件状态
            
        Returns:
            文件ID和名称列表
        """
        query = "SELECT file_id, file_name FROM File WHERE status = %s AND deleted = 0"
        return self.execute_query(query, (status,), fetch=True) or []
    
    # FileImage 相关方法
    
    def add_file_images(self, image: FileImage) -> None:
        """添加文件图片
        
        Args:
            image: 文件图片对象
        """
        nos_key = image.nos_key.split(' ')[0] if ' ' in image.nos_key else image.nos_key
        query = "INSERT INTO FileImages (image_id, file_id, user_id, kb_id, nos_key) VALUES (%s, %s, %s, %s, %s)"
        self.execute_query(query, (image.image_id, image.file_id, image.user_id, image.kb_id, nos_key), commit=True)
        insert_logger.info(f"Add file image: {image.image_id} {image.file_id} {image.user_id} {image.kb_id} {nos_key}")
    
    def get_image_id_by_nos_key(self, nos_key: str) -> Optional[str]:
        """根据NOS键获取图片ID
        
        Args:
            nos_key: NOS键
            
        Returns:
            图片ID
        """
        query = "SELECT image_id FROM FileImages WHERE nos_key = %s"
        result = self.execute_query(query, (nos_key,), fetch=True)
        return result[0][0] if result else None
    
    def get_nos_key_by_image_id(self, image_id: str) -> Optional[str]:
        """根据图片ID获取NOS键
        
        Args:
            image_id: 图片ID
            
        Returns:
            NOS键
        """
        query = "SELECT nos_key FROM FileImages WHERE image_id = %s"
        result = self.execute_query(query, (image_id,), fetch=True)
        return result[0][0] if result else None 