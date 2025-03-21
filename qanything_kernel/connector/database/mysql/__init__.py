"""
MySQL 数据库连接器
"""
from qanything_kernel.connector.database.mysql.manager import DatabaseManager

# 为了向后兼容，将KnowledgeBaseManager别名指向DatabaseManager
KnowledgeBaseManager = DatabaseManager
