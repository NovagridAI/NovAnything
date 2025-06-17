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
        # 首先创建基础表结构
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
                top_k INT DEFAULT 1,
                api_context_length INT DEFAULT 1024,
                top_p FLOAT DEFAULT 1.0,
                max_token INT DEFAULT 1024,
                context_length INT DEFAULT 10,
                is_global TINYINT(1) DEFAULT 0,
                is_active TINYINT(1) DEFAULT 0,
                is_deleted TINYINT(1) DEFAULT 0,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute_query(query, commit=True)
        
        # 检查并添加缺失的字段
        self._check_and_add_missing_columns()
        
        # 创建索引
        self._create_indexes()
    
    def _check_and_add_missing_columns(self):
        """检查并添加缺失的字段"""
        try:
            # 获取当前表的所有字段
            current_columns_query = f"SHOW COLUMNS FROM {self.table}"
            current_columns = self.execute_query(current_columns_query, fetch=True)
            current_column_names = [col[0] for col in current_columns]
            
            debug_logger.info(f"当前表{self.table}的字段: {current_column_names}")
            
            # 定义需要的字段及其定义
            required_columns = {
                'is_active': 'TINYINT(1) DEFAULT 0',
                'is_global': 'TINYINT(1) DEFAULT 0',
                'is_deleted': 'TINYINT(1) DEFAULT 0',
                'create_time': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'update_time': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
            }
            
            # 检查每个必需字段，如果不存在则添加
            for column_name, column_definition in required_columns.items():
                if column_name not in current_column_names:
                    debug_logger.info(f"字段 {column_name} 不存在，正在添加...")
                    alter_query = f"ALTER TABLE {self.table} ADD COLUMN {column_name} {column_definition}"
                    self.execute_query(alter_query, commit=True)
                    debug_logger.info(f"成功添加字段: {column_name}")
                    
        except Exception as e:
            debug_logger.error(f"检查和添加字段时出错: {str(e)}")
            raise
    
    def _create_indexes(self):
        """创建索引"""
        indexes = [
            ("idx_user_id", "user_id"),
            ("idx_is_global", "is_global"),
            ("idx_is_active", "is_active"),
            ("idx_is_deleted", "is_deleted")
        ]
        
        for index_name, column_name in indexes:
            try:
                # 先检查索引是否存在
                check_query = f"SHOW INDEX FROM {self.table} WHERE Key_name = %s"
                existing_indexes = self.execute_query(check_query, (index_name,), fetch=True)
                
                if not existing_indexes:
                    # 索引不存在，创建索引
                    create_query = f"CREATE INDEX {index_name} ON {self.table}({column_name})"
                    self.execute_query(create_query, commit=True)
                    debug_logger.info(f"索引创建成功: {index_name}")
                else:
                    debug_logger.info(f"索引已存在，跳过创建: {index_name}")
                    
            except Exception as e:
                debug_logger.info(f"索引创建失败或已存在 (这是正常的): {index_name}, 错误: {str(e)}")
                continue
    
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
            是否成功更新（包括数据无变化的情况）
        """
        # 移除时间字段，使用数据库自动更新
        if 'create_time' in update_data:
            update_data.pop('create_time')
        if 'update_time' in update_data:
            update_data.pop('update_time')
            
        # 执行更新操作
        set_clause = ', '.join([f"{column} = %s" for column in update_data.keys()])
        values = tuple(update_data.values()) + (config_id,)
        
        query = f"UPDATE {self.table} SET {set_clause} WHERE config_id = %s"
        result = self.execute_query(query, values, commit=True, check=True)
        
        debug_logger.info(f"模型配置更新结果: 影响行数={result}")
        
        # 如果影响行数为0，检查记录是否存在
        if result == 0:
            # 检查配置是否存在
            exists_query = f"SELECT 1 FROM {self.table} WHERE config_id = %s AND is_deleted = 0"
            exists_result = self.execute_query(exists_query, (config_id,), fetch=True)
            if exists_result:
                debug_logger.info(f"配置存在但数据无变化，视为更新成功: {config_id}")
                return True
            else:
                debug_logger.error(f"配置不存在: {config_id}")
                return False
        
        return result > 0
    
    def get_model_config(self, config_id: str) -> Optional[ModelConfig]:
        """获取指定模型配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            模型配置对象，如不存在则返回None
        """
        try:
            debug_logger.info(f"开始查询模型配置: config_id={config_id}")
            query = f"SELECT * FROM {self.table} WHERE config_id = %s AND is_deleted = 0"
            results = self.execute_query(query, (config_id,), fetch=True)
            debug_logger.info(f"数据库查询结果数量: {len(results) if results else 0}")
        
            if not results:
                debug_logger.warning(f"未找到模型配置: {config_id}")
                return None
        
            columns = self._get_columns()
            debug_logger.info(f"表列名: {columns}")
            debug_logger.info(f"查询结果原始数据: {results[0]}")
            
            data = self._row_to_dict(results[0], columns)
            debug_logger.info(f"转换后的字典数据: {data}")
            
            config = ModelConfig.from_dict(data)
            debug_logger.info(f"创建的ModelConfig对象: {config}")
            return config
        except Exception as e:
            debug_logger.error(f"获取模型配置出错: {str(e)}")
            import traceback
            debug_logger.error(f"错误详情: {traceback.format_exc()}")
            raise
    
    def get_model_configs_by_user(self, user_id: str) -> List[ModelConfig]:
        """获取用户的所有模型配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            模型配置对象列表
        """
        query = f"SELECT * FROM {self.table} WHERE (user_id = %s OR is_global = 1) AND is_deleted = 0 ORDER BY is_active DESC, create_time DESC"
        results = self.execute_query(query, (user_id,), fetch=True)
        
        if not results:
            return []
        
        columns = self._get_columns()
        configs = []
        for row in results:
            data = self._row_to_dict(row, columns)
            # 对于全局模型，需要检查用户是否将其设为活跃
            config = ModelConfig.from_dict(data)
            if config.is_global:
                # 检查用户是否将此全局模型设为活跃
                active_query = f"SELECT is_active FROM {self.table} WHERE config_id = %s AND user_id = %s"
                active_result = self.execute_query(active_query, (config.config_id, user_id), fetch=True)
                if active_result:
                    config.is_active = bool(active_result[0][0])
            configs.append(config)
            
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
    
    def get_all_model_configs(self) -> List[ModelConfig]:
        """获取所有模型配置（管理员专用）
        
        Returns:
            所有模型配置对象列表
        """
        query = f"SELECT * FROM {self.table} WHERE is_deleted = 0 ORDER BY is_active DESC, create_time DESC"
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
    
    def set_active_model_for_user(self, user_id: str, config_id: str) -> bool:
        """为用户设置活跃模型
        
        Args:
            user_id: 用户ID
            config_id: 要设置为活跃的配置ID
            
        Returns:
            是否成功设置
        """
        try:
            # 首先验证配置是否存在
            config = self.get_model_config(config_id)
            if not config:
                debug_logger.error(f"模型配置不存在: {config_id}")
                return False
            
            # 检查用户角色
            user_role_query = "SELECT role FROM User WHERE user_id = %s"
            user_role_result = self.execute_query(user_role_query, (user_id,), fetch=True)
            user_role = user_role_result[0][0] if user_role_result else 'user'
            
            if user_role in ('admin', 'superadmin'):
                # 管理员操作：将所有模型设为非活跃，然后设置指定模型为活跃
                debug_logger.info(f"管理员{user_id}设置全局活跃模型: {config_id}")
                
                # 首先将所有模型设置为非活跃
                query1 = f"UPDATE {self.table} SET is_active = 0 WHERE is_deleted = 0"
                self.execute_query(query1, commit=True)
                debug_logger.info(f"已将所有模型设为非活跃")
                
                # 然后将指定的模型设置为活跃
                query2 = f"UPDATE {self.table} SET is_active = 1 WHERE config_id = %s AND is_deleted = 0"
                result = self.execute_query(query2, (config_id,), commit=True, check=True)
                debug_logger.info(f"设置模型{config_id}为活跃，影响行数: {result}")
                
            else:
                # 普通用户操作：检查权限并设置活跃
                if config.user_id != user_id and not config.is_global:
                    debug_logger.error(f"用户{user_id}无权使用模型{config_id}")
                    return False
                
                # 首先将该用户的所有模型设置为非活跃
                query1 = f"UPDATE {self.table} SET is_active = 0 WHERE user_id = %s"
                self.execute_query(query1, (user_id,), commit=True)
                debug_logger.info(f"已将用户{user_id}的所有模型设为非活跃")
                
                # 然后将指定的模型设置为活跃
                query2 = f"UPDATE {self.table} SET is_active = 1 WHERE config_id = %s AND (user_id = %s OR is_global = 1)"
                result = self.execute_query(query2, (config_id, user_id), commit=True, check=True)
                debug_logger.info(f"设置模型{config_id}为活跃，影响行数: {result}")
            
            # 验证设置是否成功
            verify_query = f"SELECT is_active FROM {self.table} WHERE config_id = %s AND is_deleted = 0"
            verify_result = self.execute_query(verify_query, (config_id,), fetch=True)
            
            if verify_result and len(verify_result) > 0:
                is_active = bool(verify_result[0][0])
                debug_logger.info(f"验证结果：模型{config_id}的is_active状态为{is_active}")
                return is_active
            else:
                debug_logger.error(f"验证失败：未找到模型{config_id}")
                return False
                
        except Exception as e:
            debug_logger.error(f"设置活跃模型失败: {str(e)}")
            return False
    
    def get_active_model_for_user(self, user_id: str) -> Optional[ModelConfig]:
        """获取用户的活跃模型
        
        Args:
            user_id: 用户ID
            
        Returns:
            活跃的模型配置对象，如不存在则返回None
        """
        # 首先检查用户角色
        user_role_query = "SELECT role FROM User WHERE user_id = %s"
        user_role_result = self.execute_query(user_role_query, (user_id,), fetch=True)
        user_role = user_role_result[0][0] if user_role_result else 'user'
        
        if user_role in ('admin', 'superadmin'):
            # 管理员用户：查找系统中唯一的活跃模型（全局活跃状态）
            query = f"SELECT * FROM {self.table} WHERE is_active = 1 AND is_deleted = 0 LIMIT 1"
            results = self.execute_query(query, fetch=True)
            
            if results:
                columns = self._get_columns()
                data = self._row_to_dict(results[0], columns)
                debug_logger.info(f"管理员用户 {user_id} 使用全局活跃模型: {data.get('service_name', 'Unknown')}")
                return ModelConfig.from_dict(data)
        else:
            # 普通用户：查找系统中的全局活跃模型
            query = f"SELECT * FROM {self.table} WHERE is_active = 1 AND is_deleted = 0 LIMIT 1"
            results = self.execute_query(query, fetch=True)
            
            if results:
                columns = self._get_columns()
                data = self._row_to_dict(results[0], columns)
                debug_logger.info(f"普通用户 {user_id} 使用全局活跃模型: {data.get('service_name', 'Unknown')}")
                return ModelConfig.from_dict(data)
        
        debug_logger.warning(f"用户 {user_id} 没有找到任何活跃模型")
        return None 