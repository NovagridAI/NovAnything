"""
用户数据访问对象
"""
import bcrypt
import uuid
from typing import List, Optional, Dict, Any
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.connector.database.mysql.daos.base_dao import BaseDAO
from qanything_kernel.connector.database.mysql.models.user import User


class UserDAO(BaseDAO):
    """用户数据访问对象类"""
    
    def __init__(self, db_connection):
        """初始化"""
        super().__init__(db_connection)
        self.table = 'User'
    
    def create_table(self):
        """创建用户表"""
        query = """
            CREATE TABLE IF NOT EXISTS User (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) UNIQUE,
                user_name VARCHAR(255),
                dept_id VARCHAR(255),
                email VARCHAR(255),
                password VARCHAR(255),
                role VARCHAR(20) DEFAULT 'user',
                status VARCHAR(20) DEFAULT 'active',
                creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        self.execute_query(query, commit=True)
        
        # 创建索引
        index_queries = [
            "CREATE INDEX idx_user_dept ON User(dept_id)",
            "CREATE INDEX idx_user_email ON User(email)",
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
    
    def create_admin_if_not_exists(self):
        """如果不存在超级管理员用户，则创建一个"""
        debug_logger.info("检查是否存在超级管理员用户...")
        check_admin_query = "SELECT * FROM User WHERE role = 'superadmin' LIMIT 1"
        result = self.execute_query(check_admin_query, fetch=True)
        
        if not result:
            debug_logger.info("未找到超级管理员用户，开始创建初始超级管理员账户...")
            # 如果不存在管理员用户，创建一个初始管理员用户
            admin_password = "admin@123"  # 初始密码
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), salt)
            
            admin_data = {
                'user_id': str(f"user_{uuid.uuid4().hex[:8]}"),
                'user_name': "admin",
                'email': "admin@example.com",
                'password': hashed_password.decode('utf-8'),
                'role': "superadmin",
                'status': "active"
            }
            
            self.insert(self.table, admin_data)
            debug_logger.info("初始超级管理员用户创建成功 - 邮箱: admin@example.com, 密码: admin@123")
        else:
            debug_logger.info("已存在超级管理员用户，跳过初始超级管理员创建")
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        query = "SELECT * FROM User WHERE user_id = %s"
        result = self.execute_query(query, (user_id,), fetch=True, dictionary=True)
        
        if not result:
            return None
            
        return User.from_dict(result[0])
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据用户邮箱获取用户
        
        Args:
            email: 用户邮箱
            
        Returns:
            用户对象，如果不存在则返回None
        """
        query = "SELECT * FROM User WHERE email = %s"
        result = self.execute_query(query, (email,), fetch=True, dictionary=True)
        
        if not result:
            return None
            
        return User.from_dict(result[0])
    
    def check_user_exists(self, user_id: str) -> bool:
        """检查用户是否存在
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户是否存在
        """
        query = "SELECT user_id FROM User WHERE user_id = %s"
        result = self.execute_query(query, (user_id,), fetch=True)
        debug_logger.info(f"check_user_exist {result}")
        return result is not None and len(result) > 0
    
    def create_user(self, user: User) -> bool:
        """创建用户
        
        Args:
            user: 用户对象
            
        Returns:
            是否成功创建
        """
        return self.insert(self.table, user.to_dict())
    
    def update_user(self, user: User) -> bool:
        """更新用户
        
        Args:
            user: 用户对象
            
        Returns:
            是否成功更新
        """
        return self.update(self.table, user.to_dict(), "user_id = %s", (user.user_id,))
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功删除
        """
        return self.update(self.table, {'status': 'inactive'}, "user_id = %s", (user_id,))
    
    def get_users(self) -> List[str]:
        """获取所有用户ID
        
        Returns:
            用户ID列表
        """
        query = "SELECT user_id FROM User"
        result = self.execute_query(query, fetch=True)
        return [row[0] for row in result] if result else []
    
    def get_users_by_dept(self, dept_id: str) -> List[User]:
        """获取指定部门的所有用户
        
        Args:
            dept_id: 部门ID
            
        Returns:
            用户对象列表
        """
        query = "SELECT * FROM User WHERE dept_id = %s"
        result = self.execute_query(query, (dept_id,), fetch=True, dictionary=True)
        
        return [User.from_dict(row) for row in result] if result else []
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """验证用户
        
        Args:
            email: 用户邮箱
            password: 用户密码
            
        Returns:
            验证成功返回用户对象，失败返回None
        """
        user = self.get_user_by_email(email)
        
        if not user or user.status != 'active':
            return None
            
        if not user.password:
            return None
            
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return user
            
        return None 