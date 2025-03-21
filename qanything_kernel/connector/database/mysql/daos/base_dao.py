"""
基础数据访问对象，所有其他DAO类都应该继承自这个类
"""
from typing import List, Dict, Any, Optional, Union, Tuple
from qanything_kernel.connector.database.mysql.connection import DatabaseConnection


class BaseDAO:
    """基础数据访问对象类
    
    提供基本的数据库操作方法，所有具体业务领域的DAO类应该继承自这个类
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """初始化
        
        Args:
            db_connection: 数据库连接对象
        """
        self.db = db_connection
    
    def execute_query(self, query: str, params: tuple = (), 
                     commit: bool = False, 
                     fetch: bool = False, 
                     check: bool = False,
                     dictionary: bool = False) -> Optional[Union[List[tuple], List[dict], int]]:
        """执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            commit: 是否提交事务
            fetch: 是否获取结果
            check: 是否返回影响的行数
            dictionary: 是否返回字典格式的结果
            
        Returns:
            查询结果，或影响的行数，或None
        """
        return self.db.execute_query(query, params, commit, fetch, check, dictionary)
    
    def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """插入数据
        
        Args:
            table: 表名
            data: 数据字典，键为列名，值为列值
            
        Returns:
            是否成功插入
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        result = self.execute_query(query, values, commit=True, check=True)
        
        return result is not None and result > 0
    
    def update(self, table: str, data: Dict[str, Any], condition: str, condition_params: tuple) -> bool:
        """更新数据
        
        Args:
            table: 表名
            data: 待更新的数据字典，键为列名，值为列值
            condition: 条件语句，如 "id = %s AND status = %s"
            condition_params: 条件参数
            
        Returns:
            是否成功更新
        """
        set_clause = ', '.join([f"{column} = %s" for column in data.keys()])
        values = tuple(data.values()) + condition_params
        
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        result = self.execute_query(query, values, commit=True, check=True)
        
        return result is not None and result > 0
    
    def delete(self, table: str, condition: str, condition_params: tuple) -> bool:
        """删除数据
        
        Args:
            table: 表名
            condition: 条件语句，如 "id = %s AND status = %s"
            condition_params: 条件参数
            
        Returns:
            是否成功删除
        """
        query = f"DELETE FROM {table} WHERE {condition}"
        result = self.execute_query(query, condition_params, commit=True, check=True)
        
        return result is not None and result > 0
    
    def select(self, table: str, columns: List[str] = None, 
               condition: str = None, condition_params: tuple = None,
               dictionary: bool = False) -> List[Union[tuple, Dict[str, Any]]]:
        """查询数据
        
        Args:
            table: 表名
            columns: 要查询的列名列表，如果为None则查询所有列
            condition: 条件语句，如 "id = %s AND status = %s"
            condition_params: 条件参数
            dictionary: 是否返回字典格式的结果
            
        Returns:
            查询结果
        """
        columns_str = '*' if columns is None else ', '.join(columns)
        query = f"SELECT {columns_str} FROM {table}"
        
        if condition:
            query += f" WHERE {condition}"
        
        params = () if condition_params is None else condition_params
        result = self.execute_query(query, params, fetch=True, dictionary=dictionary)
        
        return result if result else []
    
    def select_one(self, table: str, columns: List[str] = None, 
                  condition: str = None, condition_params: tuple = None,
                  dictionary: bool = False) -> Optional[Union[tuple, Dict[str, Any]]]:
        """查询单条数据
        
        Args:
            table: 表名
            columns: 要查询的列名列表，如果为None则查询所有列
            condition: 条件语句，如 "id = %s AND status = %s"
            condition_params: 条件参数
            dictionary: 是否返回字典格式的结果
            
        Returns:
            查询结果，如果没有找到则返回None
        """
        columns_str = '*' if columns is None else ', '.join(columns)
        query = f"SELECT {columns_str} FROM {table}"
        
        if condition:
            query += f" WHERE {condition}"
        
        query += " LIMIT 1"
        
        params = () if condition_params is None else condition_params
        result = self.execute_query(query, params, fetch=True, dictionary=dictionary)
        
        return result[0] if result else None
    
    def exists(self, table: str, condition: str, condition_params: tuple) -> bool:
        """检查是否存在满足条件的记录
        
        Args:
            table: 表名
            condition: 条件语句，如 "id = %s AND status = %s"
            condition_params: 条件参数
            
        Returns:
            是否存在满足条件的记录
        """
        query = f"SELECT 1 FROM {table} WHERE {condition} LIMIT 1"
        result = self.execute_query(query, condition_params, fetch=True)
        
        return result is not None and len(result) > 0
    
    def count(self, table: str, condition: str = None, condition_params: tuple = None) -> int:
        """计数
        
        Args:
            table: 表名
            condition: 条件语句，如 "id = %s AND status = %s"
            condition_params: 条件参数
            
        Returns:
            记录数量
        """
        query = f"SELECT COUNT(*) FROM {table}"
        
        if condition:
            query += f" WHERE {condition}"
        
        params = () if condition_params is None else condition_params
        result = self.execute_query(query, params, fetch=True)
        
        return result[0][0] if result else 0
    
    def batch_insert(self, table: str, columns: List[str], values_list: List[tuple]) -> int:
        """批量插入
        
        Args:
            table: 表名
            columns: 列名列表
            values_list: 值元组的列表，每个元组对应一行记录
            
        Returns:
            成功插入的行数
        """
        if not values_list:
            return 0
            
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        placeholders_groups = ', '.join([f'({placeholders})'] * len(values_list))
        
        # 展开所有值
        all_values = []
        for values in values_list:
            all_values.extend(values)
            
        query = f"INSERT INTO {table} ({columns_str}) VALUES {placeholders_groups}"
        result = self.execute_query(query, tuple(all_values), commit=True, check=True)
        
        return result if result is not None else 0 