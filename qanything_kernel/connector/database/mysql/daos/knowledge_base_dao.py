"""
知识库数据访问对象
"""
import uuid
from typing import List, Optional, Dict, Any, Tuple
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.configs.model_config import KB_SUFFIX
from qanything_kernel.connector.database.mysql.daos.base_dao import BaseDAO
from qanything_kernel.connector.database.mysql.models.knowledge_base import KnowledgeBase, KnowledgeBaseAccess


class KnowledgeBaseDAO(BaseDAO):
    """知识库数据访问对象类"""
    
    def __init__(self, db_connection):
        """初始化"""
        super().__init__(db_connection)
        self.table = 'KnowledgeBase'
        self.access_table = 'KnowledgeBaseAccess'
    
    def create_table(self):
        """创建知识库相关表"""
        # 创建知识库表
        query = """
            CREATE TABLE IF NOT EXISTS KnowledgeBase (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kb_id VARCHAR(255) UNIQUE,
                user_id VARCHAR(255),
                kb_name VARCHAR(255),
                deleted BOOL DEFAULT 0,
                latest_qa_time TIMESTAMP NULL,
                latest_insert_time TIMESTAMP NULL
            );
        """
        self.execute_query(query, commit=True)
        
        # 创建知识库权限表
        query = """
        CREATE TABLE IF NOT EXISTS KnowledgeBaseAccess (
            id INT AUTO_INCREMENT PRIMARY KEY,
            kb_id VARCHAR(255),
            subject_id VARCHAR(255),
            subject_type ENUM('user', 'department', 'group'),
            permission_type ENUM('read', 'write', 'admin'),
            granted_by VARCHAR(255),
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_kb_id (kb_id),
            INDEX idx_subject (subject_id, subject_type),
            INDEX idx_granted_by (granted_by),
            UNIQUE KEY unique_access (kb_id, subject_id, subject_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute_query(query, commit=True)
    
    def new_knowledge_base(self, kb_id: str, user_id: str, kb_name: str) -> Tuple[str, str]:
        """创建新知识库
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            kb_name: 知识库名称
            
        Returns:
            (知识库ID, 状态消息)
        """
        # 创建知识库
        query = "INSERT INTO KnowledgeBase (kb_id, user_id, kb_name) VALUES (%s, %s, %s)"
        self.execute_query(query, (kb_id, user_id, kb_name), commit=True)
        
        # 设置所有者权限
        self.set_kb_access(kb_id, user_id, "user", "admin", user_id)
        
        return kb_id, "success"
    
    def get_knowledge_bases(self, user_id: str) -> List[Tuple[str, str]]:
        """获取用户可访问的所有知识库
        
        Args:
            user_id: 用户ID
            
        Returns:
            知识库ID和名称的元组列表
        """
        # 首先获取用户直接拥有的知识库
        query = (f"SELECT kb_id, kb_name FROM KnowledgeBase WHERE user_id = %s AND deleted = 0 AND "
                 f"(kb_id LIKE '%{KB_SUFFIX}' OR kb_id LIKE '%{KB_SUFFIX}_FAQ')")
        owned_kbs = self.execute_query(query, (user_id,), fetch=True)
        
        # 获取用户通过权限可以访问的知识库
        query = f"""
            SELECT DISTINCT kb.kb_id, kb.kb_name 
            FROM KnowledgeBase kb
            JOIN KnowledgeBaseAccess kba ON kb.kb_id = kba.kb_id
            JOIN User u ON u.user_id = %s
            WHERE kb.deleted = 0 
            AND kb.user_id != %s
            AND (
                (kba.subject_id = %s AND kba.subject_type = 'user')
                OR (kba.subject_id = u.dept_id AND kba.subject_type = 'department')
            )
            AND (
                kb.kb_id LIKE '%{KB_SUFFIX}'
                OR kb.kb_id LIKE '%{KB_SUFFIX}_FAQ'
            )
        """
        shared_kbs = self.execute_query(query, (user_id, user_id, user_id), fetch=True)
        
        # 合并结果
        return owned_kbs + shared_kbs
    
    def get_knowledge_base_by_id(self, kb_id: str) -> Optional[KnowledgeBase]:
        """根据知识库ID获取知识库
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            知识库对象，如果不存在则返回None
        """
        query = "SELECT * FROM KnowledgeBase WHERE kb_id = %s AND deleted = 0"
        result = self.execute_query(query, (kb_id,), fetch=True, dictionary=True)
        
        if not result:
            return None
            
        return KnowledgeBase.from_dict(result[0])
    
    def get_knowledge_base_name(self, kb_ids: List[str]) -> List[Tuple[str, str, str]]:
        """获取指定kb_ids的知识库信息
        
        Args:
            kb_ids: 知识库ID列表
            
        Returns:
            (用户ID, 知识库ID, 知识库名称)的元组列表
        """
        if not kb_ids:
            return []
            
        kb_ids_str = ','.join(['%s'] * len(kb_ids))
        query = f"SELECT user_id, kb_id, kb_name FROM KnowledgeBase WHERE kb_id IN ({kb_ids_str}) AND deleted = 0"
        
        return self.execute_query(query, kb_ids, fetch=True)
    
    def check_kb_exist(self, kb_ids: List[str]) -> List[str]:
        """检查知识库是否存在
        
        Args:
            kb_ids: 知识库ID列表
            
        Returns:
            不存在的知识库ID列表
        """
        if not kb_ids:
            return []
            
        kb_ids_str = ','.join(['%s'] * len(kb_ids))
        query = f"SELECT kb_id FROM KnowledgeBase WHERE kb_id IN ({kb_ids_str}) AND deleted = 0"
        
        result = self.execute_query(query, kb_ids, fetch=True)
        debug_logger.info(f"check_kb_exist {result}")
        
        valid_kb_ids = [kb_info[0] for kb_info in result]
        invalid_kb_ids = list(set(kb_ids) - set(valid_kb_ids))
        
        return invalid_kb_ids
    
    def delete_knowledge_base(self, user_id: str, kb_ids: List[str]) -> None:
        """删除知识库
        
        Args:
            user_id: 用户ID
            kb_ids: 要删除的知识库ID列表
        """
        if not kb_ids:
            return
            
        # 标记知识库为已删除
        kb_ids_str = ','.join(['%s'] * len(kb_ids))
        query = f"UPDATE KnowledgeBase SET deleted = 1 WHERE user_id = %s AND kb_id IN ({kb_ids_str})"
        self.execute_query(query, (user_id,) + tuple(kb_ids), commit=True)
        
        # 标记知识库下的所有文件为已删除
        query = f"""
            UPDATE File SET deleted = 1 
            WHERE kb_id IN ({kb_ids_str}) 
            AND kb_id IN (SELECT kb_id FROM KnowledgeBase WHERE user_id = %s)
        """
        self.execute_query(query, tuple(kb_ids) + (user_id,), commit=True)
    
    def rename_knowledge_base(self, user_id: str, kb_id: str, kb_name: str) -> None:
        """重命名知识库
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            kb_name: 新的知识库名称
        """
        query = "UPDATE KnowledgeBase SET kb_name = %s WHERE kb_id = %s AND user_id = %s"
        self.execute_query(query, (kb_name, kb_id, user_id), commit=True)
    
    def update_knowledge_base_latest_qa_time(self, kb_id: str, timestamp: str) -> None:
        """更新知识库的最新问答时间
        
        Args:
            kb_id: 知识库ID
            timestamp: 时间戳，格式为'2021-08-01 00:00:00'
        """
        query = "UPDATE KnowledgeBase SET latest_qa_time = %s WHERE kb_id = %s"
        self.execute_query(query, (timestamp, kb_id), commit=True)
    
    def update_knowledge_base_latest_insert_time(self, kb_id: str, timestamp: str) -> None:
        """更新知识库的最新插入时间
        
        Args:
            kb_id: 知识库ID
            timestamp: 时间戳，格式为'2021-08-01 00:00:00'
        """
        query = "UPDATE KnowledgeBase SET latest_insert_time = %s WHERE kb_id = %s"
        self.execute_query(query, (timestamp, kb_id), commit=True)
    
    def get_user_by_kb_id(self, kb_id: str) -> Optional[str]:
        """根据知识库ID获取所有者用户ID
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            用户ID，如果不存在则返回None
        """
        query = "SELECT user_id FROM KnowledgeBase WHERE kb_id = %s"
        result = self.execute_query(query, (kb_id,), fetch=True)
        
        if result:
            return result[0][0]
        else:
            return None
    
    def check_kb_access(self, user_id: str, kb_id: str, required_permission: str) -> bool:
        """检查用户是否有权限访问知识库
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            required_permission: 所需权限类型：'read', 'write', 'admin'
            
        Returns:
            是否有权限
        """
        debug_logger.info(f"正在检查用户 {user_id} 对知识库 {kb_id} 的 {required_permission} 权限")
        
        # 1. 检查知识库是否存在
        query = "SELECT kb_id FROM KnowledgeBase WHERE kb_id = %s AND deleted = 0"
        if not self.execute_query(query, (kb_id,), fetch=True):
            debug_logger.error(f"知识库 {kb_id} 不存在或已删除")
            return False
        
        # 2. 获取用户信息
        query = "SELECT role, dept_id FROM User WHERE user_id = %s AND status = 'active'"
        user_info = self.execute_query(query, (user_id,), fetch=True)
        if not user_info:
            debug_logger.error(f"用户 {user_id} 不存在或未激活")
            return False
        
        user_role, user_dept_id = user_info[0]
        debug_logger.info(f"用户角色: {user_role}, 部门ID: {user_dept_id}")
        
        # 如果用户是超级管理员，直接放开所有权限
        if user_role == 'superadmin':
            debug_logger.info(f"用户 {user_id} 是超级管理员，拥有所有权限")
            return True
        
        # 3. 检查用户是否是知识库所有者
        query = "SELECT user_id FROM KnowledgeBase WHERE kb_id = %s AND user_id = %s AND deleted = 0"
        if self.execute_query(query, (kb_id, user_id), fetch=True):
            debug_logger.info(f"用户 {user_id} 是知识库 {kb_id} 的所有者")
            return True
        
        # 4. 检查用户直接权限
        query = """
            SELECT permission_type 
            FROM KnowledgeBaseAccess 
            WHERE kb_id = %s AND subject_id = %s AND subject_type = 'user'
        """
        user_permission = self.execute_query(query, (kb_id, user_id), fetch=True)
        if user_permission:
            permission_type = user_permission[0][0]
            debug_logger.info(f"用户 {user_id} 对知识库 {kb_id} 有直接权限: {permission_type}")
            
            # 如果用户是该知识库的admin，放开该知识库的权限
            if permission_type == 'admin':
                debug_logger.info(f"用户 {user_id} 是知识库 {kb_id} 的管理员，拥有所有权限")
                return True
                
            if self._is_permission_sufficient(permission_type, required_permission):
                return True
        
        # 5. 检查部门权限
        if user_dept_id:
            query = """
                SELECT permission_type 
                FROM KnowledgeBaseAccess 
                WHERE kb_id = %s AND subject_id = %s AND subject_type = 'department'
            """
            dept_permission = self.execute_query(query, (kb_id, user_dept_id), fetch=True)
            if dept_permission:
                debug_logger.info(f"用户 {user_id} 通过部门 {user_dept_id} 对知识库 {kb_id} 有权限: {dept_permission[0][0]}")
                if self._is_permission_sufficient(dept_permission[0][0], required_permission):
                    return True
        
        # 6. 检查用户组权限
        query = """
            SELECT kba.permission_type
            FROM KnowledgeBaseAccess kba
            JOIN GroupMember gm ON kba.subject_id = gm.group_id
            WHERE kba.kb_id = %s 
            AND gm.user_id = %s 
            AND kba.subject_type = 'group'
        """
        group_permissions = self.execute_query(query, (kb_id, user_id), fetch=True)
        for perm in group_permissions:
            debug_logger.info(f"用户 {user_id} 通过用户组对知识库 {kb_id} 有权限: {perm[0]}")
            if self._is_permission_sufficient(perm[0], required_permission):
                return True
                
        return False
    
    def _is_permission_sufficient(self, granted_permission: str, required_permission: str) -> bool:
        """检查权限是否足够
        
        Args:
            granted_permission: 已授予的权限
            required_permission: 所需的权限
            
        Returns:
            是否足够
        """
        permission_levels = {
            'read': 1,
            'write': 2,
            'admin': 3
        }
        granted_level = permission_levels.get(granted_permission, 0)
        required_level = permission_levels.get(required_permission, 0)
        debug_logger.info(f"权限检查: 已授权级别 {granted_permission}({granted_level}), 所需级别 {required_permission}({required_level})")
        return granted_level >= required_level
    
    def set_kb_access(self, kb_id: str, subject_id: str, subject_type: str, 
                     permission_type: str, granted_by: str) -> bool:
        """设置知识库访问权限
        
        Args:
            kb_id: 知识库ID
            subject_id: 主体ID（用户ID、部门ID或用户组ID）
            subject_type: 主体类型 ('user', 'department', 'group')
            permission_type: 权限类型 ('read', 'write', 'admin')
            granted_by: 授权者的用户ID
            
        Returns:
            是否成功设置
        """
        debug_logger.info(f"正在设置知识库权限 - 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}, 权限: {permission_type}, 授权者: {granted_by}")
        
        # 1. 验证知识库是否存在
        query = "SELECT kb_id FROM KnowledgeBase WHERE kb_id = %s AND deleted = 0"
        if not self.execute_query(query, (kb_id,), fetch=True):
            debug_logger.error(f"知识库 {kb_id} 不存在或已删除")
            return False

        # 2. 验证授权者是否存在
        query = "SELECT user_id FROM User WHERE user_id = %s AND status = 'active'"
        if not self.execute_query(query, (granted_by,), fetch=True):
            debug_logger.error(f"授权用户 {granted_by} 不存在或未激活")
            return False

        # 3. 根据subject_type验证subject是否存在
        if subject_type == 'user':
            query = "SELECT user_id FROM User WHERE user_id = %s AND status = 'active'"
            debug_logger.info(f"正在验证用户 {subject_id} 是否存在")
        elif subject_type == 'department':
            query = "SELECT dept_id FROM Department WHERE dept_id = %s"
            debug_logger.info(f"正在验证部门 {subject_id} 是否存在")
        elif subject_type == 'group':
            query = "SELECT group_id FROM UserGroup WHERE group_id = %s"
            debug_logger.info(f"正在验证用户组 {subject_id} 是否存在")
        else:
            debug_logger.error(f"无效的主体类型: {subject_type}")
            return False

        if not self.execute_query(query, (subject_id,), fetch=True):
            debug_logger.error(f"主体 {subject_id} (类型: {subject_type}) 不存在或未激活")
            return False

        # 4. 设置或更新权限
        query = """
            INSERT INTO KnowledgeBaseAccess 
            (kb_id, subject_id, subject_type, permission_type, granted_by)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            permission_type = VALUES(permission_type),
            granted_by = VALUES(granted_by)
        """
        try:
            self.execute_query(query, (kb_id, subject_id, subject_type, permission_type, granted_by), commit=True)
            debug_logger.info(f"成功设置知识库权限 - 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}, 权限: {permission_type}")
            return True
        except Exception as e:
            debug_logger.error(f"设置权限失败: {str(e)}")
            return False 
            