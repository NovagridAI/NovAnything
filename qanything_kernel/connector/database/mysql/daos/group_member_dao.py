"""
用户组成员数据访问对象
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.connector.database.mysql.daos.base_dao import BaseDAO
from qanything_kernel.connector.database.mysql.models.group_member import GroupMember


class GroupMemberDAO(BaseDAO):
    """用户组成员数据访问对象类"""
    
    def __init__(self, db_connection):
        """初始化"""
        super().__init__(db_connection)
        self.table = 'GroupMember'
    
    def create_table(self):
        """创建用户组成员表"""
        query = """
            CREATE TABLE IF NOT EXISTS GroupMember (
                id INT AUTO_INCREMENT PRIMARY KEY,
                group_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'member',
                status VARCHAR(20) DEFAULT 'active',
                join_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_group_member (group_id, user_id)
            );
        """
        self.execute_query(query, commit=True)
        
        # 创建索引
        index_queries = [
            "CREATE INDEX idx_member_user ON GroupMember(user_id)",
            "CREATE INDEX idx_member_group ON GroupMember(group_id)",
            "CREATE INDEX idx_member_status ON GroupMember(status)",
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
    
    def add_member(self, member: GroupMember) -> bool:
        """添加用户组成员
        
        Args:
            member: 用户组成员对象
            
        Returns:
            是否成功添加
        """
        # 检查用户是否已经在组中
        if self.is_user_in_group(member.group_id, member.user_id):
            # 如果已经存在但状态为inactive，则更新为active
            query = """
                UPDATE GroupMember 
                SET status = 'active', role = %s, join_time = CURRENT_TIMESTAMP
                WHERE group_id = %s AND user_id = %s
            """
            self.execute_query(query, (member.role, member.group_id, member.user_id), commit=True)
            return True
            
        return self.insert(self.table, member.to_dict())
    
    def update_member_role(self, group_id: str, user_id: str, role: str) -> bool:
        """更新用户组成员角色
        
        Args:
            group_id: 用户组ID
            user_id: 用户ID
            role: 角色名称
            
        Returns:
            是否成功更新
        """
        query = "UPDATE GroupMember SET role = %s WHERE group_id = %s AND user_id = %s AND status = 'active'"
        result = self.execute_query(query, (role, group_id, user_id), commit=True, check=True)
        
        return result is not None and result > 0
    
    def get_group_members(self, group_id: str) -> List[Dict[str, Any]]:
        """获取用户组所有成员
        
        Args:
            group_id: 用户组ID
            
        Returns:
            成员信息列表
        """
        query = """
            SELECT gm.*, u.user_name
            FROM GroupMember gm
            JOIN User u ON gm.user_id = u.user_id
            WHERE gm.group_id = %s AND gm.status = 'active'
        """
        results = self.execute_query(query, (group_id,), fetch=True, dictionary=True)
        
        return results if results else []
    
    def get_member(self, group_id: str, user_id: str) -> Optional[GroupMember]:
        """获取特定用户组成员
        
        Args:
            group_id: 用户组ID
            user_id: 用户ID
            
        Returns:
            用户组成员对象，如果不存在则返回None
        """
        query = "SELECT * FROM GroupMember WHERE group_id = %s AND user_id = %s"
        result = self.execute_query(query, (group_id, user_id), fetch=True, dictionary=True)
        
        if not result:
            return None
            
        return GroupMember.from_dict(result[0])
    
    def remove_member(self, group_id: str, user_id: str) -> bool:
        """移除用户组成员（软删除）
        
        Args:
            group_id: 用户组ID
            user_id: 用户ID
            
        Returns:
            是否成功移除
        """
        query = "UPDATE GroupMember SET status = 'inactive' WHERE group_id = %s AND user_id = %s"
        result = self.execute_query(query, (group_id, user_id), commit=True, check=True)
        
        return result is not None and result > 0
    
    def is_user_in_group(self, group_id: str, user_id: str, active_only: bool = True) -> bool:
        """检查用户是否在用户组中
        
        Args:
            group_id: 用户组ID
            user_id: 用户ID
            active_only: 是否只检查活跃状态的成员
            
        Returns:
            用户是否在用户组中
        """
        if active_only:
            query = "SELECT 1 FROM GroupMember WHERE group_id = %s AND user_id = %s AND status = 'active'"
        else:
            query = "SELECT 1 FROM GroupMember WHERE group_id = %s AND user_id = %s"
            
        result = self.execute_query(query, (group_id, user_id), fetch=True)
        
        return result is not None and len(result) > 0
    
    def get_member_role(self, group_id: str, user_id: str) -> Optional[str]:
        """获取用户在用户组中的角色
        
        Args:
            group_id: 用户组ID
            user_id: 用户ID
            
        Returns:
            用户角色，如果用户不在组中则返回None
        """
        query = "SELECT role FROM GroupMember WHERE group_id = %s AND user_id = %s AND status = 'active'"
        result = self.execute_query(query, (group_id, user_id), fetch=True)
        
        return result[0][0] if result else None
    
    def batch_add_members(self, group_id: str, user_ids: List[str], role: str = 'member') -> int:
        """批量添加用户组成员
        
        Args:
            group_id: 用户组ID
            user_ids: 用户ID列表
            role: 角色名称
            
        Returns:
            成功添加的成员数量
        """
        if not user_ids:
            return 0
            
        # 准备批量插入数据
        values = []
        placeholders = []
        
        for user_id in user_ids:
            # 不重复添加已在组中的用户
            if not self.is_user_in_group(group_id, user_id, active_only=False):
                values.extend([group_id, user_id, role])
                placeholders.append("(%s, %s, %s)")
                
        if not placeholders:
            return 0
            
        # 构建批量插入SQL
        query = f"""
            INSERT INTO GroupMember (group_id, user_id, role)
            VALUES {', '.join(placeholders)}
        """
        
        result = self.execute_query(query, tuple(values), commit=True, check=True)
        return result if result is not None else 0
    
    def get_user_groups_count(self, user_id: str) -> int:
        """获取用户所属的组数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户所属的组数量
        """
        query = "SELECT COUNT(*) FROM GroupMember WHERE user_id = %s AND status = 'active'"
        result = self.execute_query(query, (user_id,), fetch=True)
        
        return result[0][0] if result else 0 