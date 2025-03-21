"""
部门数据访问对象
"""
import uuid
from typing import List, Optional, Dict, Any
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.connector.database.mysql.daos.base_dao import BaseDAO
from qanything_kernel.connector.database.mysql.models.department import Department


class DepartmentDAO(BaseDAO):
    """部门数据访问对象类"""
    
    def __init__(self, db_connection):
        """初始化"""
        super().__init__(db_connection)
        self.table = 'Department'
    
    def create_table(self):
        """创建部门表"""
        query = """
            CREATE TABLE IF NOT EXISTS Department (
                id INT AUTO_INCREMENT PRIMARY KEY,
                dept_id VARCHAR(255) UNIQUE,
                dept_name VARCHAR(255) NOT NULL,
                parent_dept_id VARCHAR(255),
                description TEXT,
                creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        self.execute_query(query, commit=True)
        
        # 创建索引
        index_queries = [
            "CREATE INDEX idx_dept_parent ON Department(parent_dept_id)",
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
    
    def add_department(self, department: Department) -> bool:
        """添加部门
        
        Args:
            department: 部门对象
            
        Returns:
            是否成功添加
        """
        if not department.dept_id:
            department.dept_id = f"dept_{uuid.uuid4().hex[:8]}"
            
        return self.insert(self.table, department.to_dict())
    
    def update_department(self, department: Department) -> bool:
        """更新部门
        
        Args:
            department: 部门对象
            
        Returns:
            是否成功更新
        """
        return self.update(self.table, department.to_dict(), "dept_id = %s", (department.dept_id,))
    
    def get_department_by_id(self, dept_id: str) -> Optional[Department]:
        """根据部门ID获取部门
        
        Args:
            dept_id: 部门ID
            
        Returns:
            部门对象，如果不存在则返回None
        """
        query = "SELECT * FROM Department WHERE dept_id = %s"
        result = self.execute_query(query, (dept_id,), fetch=True, dictionary=True)
        
        if not result:
            return None
            
        return Department.from_dict(result[0])
    
    def get_departments(self) -> List[Department]:
        """获取所有部门
        
        Returns:
            部门对象列表
        """
        query = "SELECT * FROM Department"
        results = self.execute_query(query, fetch=True, dictionary=True)
        
        return [Department.from_dict(row) for row in results] if results else []
    
    def get_child_departments(self, parent_dept_id: str) -> List[Department]:
        """获取子部门
        
        Args:
            parent_dept_id: 父部门ID
            
        Returns:
            子部门对象列表
        """
        query = "SELECT * FROM Department WHERE parent_dept_id = %s"
        results = self.execute_query(query, (parent_dept_id,), fetch=True, dictionary=True)
        
        return [Department.from_dict(row) for row in results] if results else []
    
    def delete_department(self, dept_id: str) -> bool:
        """删除部门
        
        Args:
            dept_id: 部门ID
            
        Returns:
            是否成功删除
        """
        return self.delete(self.table, "dept_id = %s", (dept_id,))
    
    def check_department_exists(self, dept_id: str) -> bool:
        """检查部门是否存在
        
        Args:
            dept_id: 部门ID
            
        Returns:
            部门是否存在
        """
        return self.exists(self.table, "dept_id = %s", (dept_id,))
    
    def check_department_name_exists(self, dept_name: str, parent_dept_id: Optional[str] = None) -> bool:
        """检查部门名称是否已存在
        
        Args:
            dept_name: 部门名称
            parent_dept_id: 父部门ID
            
        Returns:
            部门名称是否已存在
        """
        if parent_dept_id:
            return self.exists(self.table, "dept_name = %s AND parent_dept_id = %s", (dept_name, parent_dept_id))
        else:
            return self.exists(self.table, "dept_name = %s AND parent_dept_id IS NULL", (dept_name,))
    
    def get_department_tree(self, root_dept_id: Optional[str] = None) -> Dict[str, Any]:
        """获取部门树
        
        Args:
            root_dept_id: 根部门ID，如果为None则从顶级部门开始
            
        Returns:
            部门树结构
        """
        if root_dept_id:
            root_dept = self.get_department_by_id(root_dept_id)
            if not root_dept:
                return {}
        else:
            # 获取所有顶级部门（parent_dept_id为NULL的部门）
            query = "SELECT * FROM Department WHERE parent_dept_id IS NULL"
            results = self.execute_query(query, fetch=True, dictionary=True)
            if not results:
                return {}
            # 使用第一个顶级部门作为根
            root_dept = Department.from_dict(results[0])
            
        # 构建部门树
        tree = self._build_department_tree(root_dept)
        return tree
    
    def _build_department_tree(self, department: Department) -> Dict[str, Any]:
        """构建部门树
        
        Args:
            department: 部门对象
            
        Returns:
            部门树结构
        """
        tree = {
            'dept_id': department.dept_id,
            'dept_name': department.dept_name,
            'description': department.description,
            'children': []
        }
        
        # 获取子部门
        children = self.get_child_departments(department.dept_id)
        for child in children:
            tree['children'].append(self._build_department_tree(child))
            
        return tree 