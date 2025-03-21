from qanything_kernel.configs.model_config import (MYSQL_HOST_LOCAL, MYSQL_PORT_LOCAL, MYSQL_USER_LOCAL,
                                                 MYSQL_PASSWORD_LOCAL, MYSQL_DATABASE_LOCAL)
from qanything_kernel.utils.custom_log import debug_logger
import mysql.connector
from mysql.connector import pooling
from mysql.connector.errors import Error as MySQLError
from typing import Any, Dict, List, Optional, Tuple, Union


class DatabaseConnection:
    """数据库连接管理类，负责管理连接池和执行基本查询操作"""
    
    def __init__(self, pool_size=8):
        """初始化数据库连接池
        
        Args:
            pool_size: 连接池大小，默认为8
        """
        self.host = MYSQL_HOST_LOCAL
        self.port = MYSQL_PORT_LOCAL
        self.user = MYSQL_USER_LOCAL
        self.password = MYSQL_PASSWORD_LOCAL
        self.database = MYSQL_DATABASE_LOCAL
        
        self.check_database()
        
        dbconfig = {
            "host": self.host,
            "user": self.user,
            "port": self.port,
            "password": self.password,
            "database": self.database,
        }
        
        self.cnxpool = pooling.MySQLConnectionPool(pool_size=pool_size, pool_reset_session=True, **dbconfig)
        self.free_cnx = pool_size
        self.used_cnx = 0
        debug_logger.info(f"[SUCCESS] 数据库{self.database}连接成功")

    def check_database(self):
        """检查数据库是否存在，不存在则创建"""
        # 连接 MySQL 服务器
        cnx = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password
        )

        # 检查数据库是否存在
        cursor = cnx.cursor(buffered=True)
        cursor.execute('SHOW DATABASES')
        databases = [database[0] for database in cursor]

        if self.database not in databases:
            # 如果数据库不存在，则新建数据库
            cursor.execute(f'CREATE DATABASE IF NOT EXISTS {self.database}')
            debug_logger.info(f"数据库{self.database}新建成功或已存在")
        
        debug_logger.info(f"[SUCCESS] 数据库{self.database}检查通过")
        
        # 关闭游标
        cursor.close()
        # 连接到数据库
        cnx.database = self.database
        # 关闭数据库连接
        cnx.close()

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
        try:
            conn = self.cnxpool.get_connection()
            self.used_cnx += 1
            self.free_cnx -= 1
            if self.free_cnx < 4:
                debug_logger.info(f"获取连接成功，当前连接池状态：空闲连接数 {self.free_cnx}，已使用连接数 {self.used_cnx}")
        except MySQLError as err:
            debug_logger.error(f"从连接池获取连接失败：{err}")
            return None

        result = None
        cursor = None
        try:
            if dictionary:
                cursor = conn.cursor(dictionary=True)
            else:
                cursor = conn.cursor(buffered=True)
            
            cursor.execute(query, params)

            if commit:
                conn.commit()

            if fetch:
                result = cursor.fetchall()
            elif check:
                result = cursor.rowcount
        except MySQLError as err:
            if err.errno == 1061:
                debug_logger.info(f"Index already exists (this is okay): {query}")
            else:
                debug_logger.error(f"执行数据库操作失败：{err}，SQL：{query}")
            if commit:
                conn.rollback()
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()
            self.used_cnx -= 1
            self.free_cnx += 1
            if self.free_cnx <= 4:
                debug_logger.info(f"连接关闭，返回连接池。当前连接池状态：空闲连接数 {self.free_cnx}，已使用连接数 {self.used_cnx}")

        return result 