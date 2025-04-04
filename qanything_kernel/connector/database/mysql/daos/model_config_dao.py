"""
模型配置数据访问对象
"""
import uuid
import datetime
from typing import List, Optional, Dict, Any

from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.connector.database.mysql.daos.base_dao import BaseDAO
from qanything_kernel.connector.database.mysql.models.model_config import ModelConfig


class ModelConfigDAO(BaseDAO):
    """模型配置数据访问对象类"""
    
    def __init__(self, db_connection):
        """初始化"""
        super().__init__(db_connection)
        self.table = 'ModelConfig'
    
    def create_table(self):
        """创建模型配置表"""
        query = """
            CREATE TABLE IF NOT EXISTS ModelConfig (
                id INT AUTO_INCREMENT PRIMARY KEY,
                config_id VARCHAR(255) UNIQUE,
                user_id VARCHAR(255) NOT NULL,
                service_id VARCHAR(255) NOT NULL,
                service_name VARCHAR(255) NOT NULL,
                request_format VARCHAR(64) NOT NULL,
                api_key VARCHAR(512) NOT NULL,
                api_proxy VARCHAR(512) NOT NULL,
                model_endpoint VARCHAR(255) NOT NULL,
                temperature FLOAT DEFAULT 1.0,
                topk INT DEFAULT 1,
                api_context_length INT DEFAULT 1024,
                top_p FLOAT DEFAULT 1.0,
                max_token INT DEFAULT 1024,
                context_length INT DEFAULT 10,
                is_global TINYINT(1) DEFAULT 0,
                is_deleted TINYINT(1) DEFAULT 0,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_is_global (is_global),
                INDEX idx_is_deleted (is_deleted)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute_query(query, commit=True)
    
    def _row_to_dict(self, row: tuple, columns: List[str]) -> Dict[str, Any]:
        """将数据库行转换为字典
        
        Args:
            row: 数据库查询结果行
            columns: 列名列表
            
        Returns:
            字典形式的数据
        """
        result = {}
        for i, col in enumerate(columns):
            value = row[i]
            # 处理datetime类型，转换为字符串
            if isinstance(value, datetime.datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            result[col] = value
        return result
    
    def _get_columns(self) -> List[str]:
        """获取表的列名
        
        Returns:
            列名列表
        """
        query = f"SHOW COLUMNS FROM {self.table}"
        results = self.execute_query(query, fetch=True)
        return [row[0] for row in results]
    
    def add_model_config(self, model_config: ModelConfig) -> bool:
        """添加模型配置
        
        Args:
            model_config: 模型配置对象
            
        Returns:
            是否成功添加
        """
        if not model_config.config_id:
            model_config.config_id = f"model_cfg_{uuid.uuid4().hex[:8]}"
        
        data = model_config.to_dict()
        # 移除时间字段，使用数据库自动生成
        if 'create_time' in data:
            data.pop('create_time')
        if 'update_time' in data:
            data.pop('update_time')
            
        return self.insert(self.table, data)
    
    def update_model_config(self, config_id: str, update_data: Dict[str, Any]) -> bool:
        """更新模型配置
        
        Args:
            config_id: 配置ID
            update_data: 更新数据
            
        Returns:
            是否成功更新
        """
        # 移除时间字段，使用数据库自动更新
        if 'create_time' in update_data:
            update_data.pop('create_time')
        if 'update_time' in update_data:
            update_data.pop('update_time')
            
        return self.update(self.table, update_data, "config_id = %s", (config_id,))
    
    def get_model_config(self, config_id: str) -> Optional[ModelConfig]:
        """获取指定模型配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            模型配置对象，如不存在则返回None
        """
        query = f"SELECT * FROM {self.table} WHERE config_id = %s AND is_deleted = 0"
        results = self.execute_query(query, (config_id,), fetch=True)
        
        if not results:
            return None
        
        columns = self._get_columns()
        data = self._row_to_dict(results[0], columns)
        return ModelConfig.from_dict(data)
    
    def get_model_configs_by_user(self, user_id: str) -> List[ModelConfig]:
        """获取用户的所有模型配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            模型配置对象列表
        """
        query = f"SELECT * FROM {self.table} WHERE (user_id = %s OR is_global = 1) AND is_deleted = 0 ORDER BY create_time DESC"
        results = self.execute_query(query, (user_id,), fetch=True)
        
        if not results:
            return []
        
        columns = self._get_columns()
        configs = []
        for row in results:
            data = self._row_to_dict(row, columns)
            configs.append(ModelConfig.from_dict(data))
            
        return configs
    
    def get_global_model_configs(self) -> List[ModelConfig]:
        """获取全局模型配置
        
        Returns:
            全局模型配置对象列表
        """
        query = f"SELECT * FROM {self.table} WHERE is_global = 1 AND is_deleted = 0 ORDER BY create_time DESC"
        results = self.execute_query(query, fetch=True)
        
        if not results:
            return []
        
        columns = self._get_columns()
        configs = []
        for row in results:
            data = self._row_to_dict(row, columns)
            configs.append(ModelConfig.from_dict(data))
            
        return configs
    
    def delete_model_config(self, config_id: str) -> bool:
        """逻辑删除模型配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            是否成功删除
        """
        return self.update(self.table, {"is_deleted": 1}, "config_id = %s", (config_id,))
    
    def physically_delete_model_config(self, config_id: str) -> bool:
        """物理删除模型配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            是否成功删除
        """
        query = f"DELETE FROM {self.table} WHERE config_id = %s"
        result = self.execute_query(query, (config_id,), commit=True)
        return result > 0 