"""
用户组数据访问对象
"""
import uuid
from typing import List, Optional, Dict, Any
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.connector.database.mysql.daos.base_dao import BaseDAO
from qanything_kernel.connector.database.mysql.models.user_group import UserGroup


class UserGroupDAO(BaseDAO):
    """用户组数据访问对象类"""
    
    def __init__(self, db_connection):
        """初始化"""
        super().__init__(db_connection)
        self.table = 'UserGroup'
    
    def create_table(self):
        """创建用户组表"""
        query = """
            CREATE TABLE IF NOT EXISTS UserGroup (
                id INT AUTO_INCREMENT PRIMARY KEY,
                group_id VARCHAR(255) UNIQUE,
                group_name VARCHAR(255) NOT NULL,
                owner_id VARCHAR(255) NOT NULL,
                description TEXT,
                creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        self.execute_query(query, commit=True)
        
        # 创建索引
        index_queries = [
            "CREATE INDEX idx_group_owner ON UserGroup(owner_id)",
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
    
    def add_group(self, group: UserGroup) -> str:
        """添加用户组
        
        Args:
            group: 用户组对象
            
        Returns:
            group_id: 用户组ID
        """
        if not group.group_id:
            group.group_id = f"group_{uuid.uuid4().hex[:8]}"
            
        success = self.insert(self.table, group.to_dict())
        return group.group_id if success else ""
    
    def update_group(self, group: UserGroup) -> bool:
        """更新用户组
        
        Args:
            group: 用户组对象
            
        Returns:
            是否成功更新
        """
        return self.update(self.table, group.to_dict(), "group_id = %s", (group.group_id,))
    
    def get_group_by_id(self, group_id: str) -> Optional[UserGroup]:
        """根据用户组ID获取用户组
        
        Args:
            group_id: 用户组ID
            
        Returns:
            用户组对象，如果不存在则返回None
        """
        query = "SELECT * FROM UserGroup WHERE group_id = %s"
        result = self.execute_query(query, (group_id,), fetch=True, dictionary=True)
        
        if not result:
            return None
            
        return UserGroup.from_dict(result[0])
    
    def get_groups_by_owner(self, owner_id: str) -> List[UserGroup]:
        """获取用户创建的所有用户组
        
        Args:
            owner_id: 所有者用户ID
            
        Returns:
            用户组对象列表
        """
        query = "SELECT * FROM UserGroup WHERE owner_id = %s"
        results = self.execute_query(query, (owner_id,), fetch=True, dictionary=True)
        
        return [UserGroup.from_dict(row) for row in results] if results else []
    
    def get_groups_by_user(self, user_id: str) -> List[UserGroup]:
        """获取用户所属的所有用户组
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户组对象列表
        """
        query = """
            SELECT g.* FROM UserGroup g
            JOIN GroupMember m ON g.group_id = m.group_id
            WHERE m.user_id = %s AND m.status = 'active'
        """
        results = self.execute_query(query, (user_id,), fetch=True, dictionary=True)
        
        return [UserGroup.from_dict(row) for row in results] if results else []
    
    def get_all_groups(self) -> List[UserGroup]:
        """获取所有用户组
        
        Returns:
            用户组对象列表
        """
        query = "SELECT * FROM UserGroup"
        results = self.execute_query(query, fetch=True, dictionary=True)
        
        return [UserGroup.from_dict(row) for row in results] if results else []
    
    def delete_group(self, group_id: str) -> bool:
        """删除用户组
        
        Args:
            group_id: 用户组ID
            
        Returns:
            是否成功删除
        """
        return self.delete(self.table, "group_id = %s", (group_id,))
    
    def check_group_exists(self, group_id: str) -> bool:
        """检查用户组是否存在
        
        Args:
            group_id: 用户组ID
            
        Returns:
            用户组是否存在
        """
        return self.exists(self.table, "group_id = %s", (group_id,))
    
    def check_group_name_exists(self, group_name: str, owner_id: str) -> bool:
        """检查用户组名称是否已存在
        
        Args:
            group_name: 用户组名称
            owner_id: 所有者用户ID
            
        Returns:
            用户组名称是否已存在
        """
        return self.exists(self.table, "group_name = %s AND owner_id = %s", (group_name, owner_id)) 