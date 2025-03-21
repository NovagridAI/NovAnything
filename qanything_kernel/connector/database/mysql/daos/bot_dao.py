"""
聊天机器人数据访问对象
"""
import json
import uuid
from typing import List, Optional, Dict, Any, Tuple

from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.connector.database.mysql.daos.base_dao import BaseDAO
from qanything_kernel.connector.database.mysql.models.bot import QanythingBot


class BotDAO(BaseDAO):
    """聊天机器人数据访问对象类"""
    
    def __init__(self, db_connection):
        """初始化"""
        super().__init__(db_connection)
        self.table = 'QanythingBot'
    
    def create_table(self):
        """创建聊天机器人表"""
        query = """
            CREATE TABLE IF NOT EXISTS QanythingBot (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bot_id VARCHAR(255) UNIQUE,
                user_id VARCHAR(255) NOT NULL,
                bot_name VARCHAR(255) NOT NULL,
                description TEXT,
                head_image VARCHAR(1024),
                prompt_setting TEXT,
                welcome_message TEXT,
                kb_ids_str TEXT NOT NULL,
                llm_setting TEXT,
                is_deleted TINYINT(1) DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.execute_query(query, commit=True)
        
        # 创建索引
        index_queries = [
            "CREATE INDEX index_user_id ON QanythingBot (user_id)",
            "CREATE INDEX index_bot_name ON QanythingBot (bot_name)",
            "CREATE INDEX index_is_deleted ON QanythingBot (is_deleted)"
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
    
    def add_bot(self, bot: QanythingBot) -> str:
        """添加聊天机器人
        
        Args:
            bot: 聊天机器人对象
            
        Returns:
            bot_id: 机器人ID
        """
        if not bot.bot_id:
            bot.bot_id = uuid.uuid4().hex
            
        bot_data = bot.to_dict()
        
        # 确保llm_setting是字符串形式
        if 'llm_setting' in bot_data and isinstance(bot_data['llm_setting'], dict):
            bot_data['llm_setting'] = json.dumps(bot_data['llm_setting'])
            
        query = (
            "INSERT INTO QanythingBot (bot_id, user_id, bot_name, description, head_image, "
            "prompt_setting, welcome_message, kb_ids_str, llm_setting) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        
        self.execute_query(
            query, 
            (
                bot_data.get('bot_id'),
                bot_data.get('user_id'),
                bot_data.get('bot_name'),
                bot_data.get('description'),
                bot_data.get('head_image'),
                bot_data.get('prompt_setting'),
                bot_data.get('welcome_message'),
                bot_data.get('kb_ids_str'),
                bot_data.get('llm_setting')
            ),
            commit=True
        )
        debug_logger.info(f"添加机器人: {bot_data.get('bot_name')}")
        return bot.bot_id
    
    def update_bot(self, bot: QanythingBot) -> bool:
        """更新聊天机器人
        
        Args:
            bot: 聊天机器人对象
            
        Returns:
            是否更新成功
        """
        if not bot.bot_id:
            debug_logger.error("更新机器人失败：缺少bot_id")
            return False
            
        bot_data = bot.to_dict()
        
        # 确保llm_setting是字符串形式
        if 'llm_setting' in bot_data and isinstance(bot_data['llm_setting'], dict):
            bot_data['llm_setting'] = json.dumps(bot_data['llm_setting'])
            
        query = (
            "UPDATE QanythingBot SET "
            "bot_name = %s, description = %s, head_image = %s, "
            "prompt_setting = %s, welcome_message = %s, kb_ids_str = %s, llm_setting = %s "
            "WHERE bot_id = %s AND is_deleted = 0"
        )
        
        result = self.execute_query(
            query, 
            (
                bot_data.get('bot_name'),
                bot_data.get('description'),
                bot_data.get('head_image'),
                bot_data.get('prompt_setting'),
                bot_data.get('welcome_message'),
                bot_data.get('kb_ids_str'),
                bot_data.get('llm_setting'),
                bot_data.get('bot_id')
            ),
            commit=True
        )
        
        success = result and result.rowcount > 0
        if success:
            debug_logger.info(f"更新机器人成功: {bot_data.get('bot_name')}")
        else:
            debug_logger.error(f"更新机器人失败: {bot_data.get('bot_name')}")
            
        return success
    
    def get_bot_by_id(self, bot_id: str) -> Optional[QanythingBot]:
        """根据ID获取聊天机器人
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            聊天机器人对象
        """
        query = """
            SELECT bot_id, user_id, bot_name, description, head_image, 
                   prompt_setting, welcome_message, kb_ids_str, llm_setting, is_deleted, timestamp
            FROM QanythingBot
            WHERE bot_id = %s AND is_deleted = 0
        """
        
        result = self.execute_query(query, (bot_id,), fetch=True)
        if not result:
            return None
            
        # 转为字典
        columns = [
            'bot_id', 'user_id', 'bot_name', 'description', 'head_image',
            'prompt_setting', 'welcome_message', 'kb_ids_str', 'llm_setting', 'is_deleted', 'timestamp'
        ]
        bot_data = dict(zip(columns, result[0]))
        
        # 处理时间戳
        if 'timestamp' in bot_data:
            bot_data['timestamp'] = bot_data['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            
        # 将llm_setting转为字典（如果是字符串形式）
        if 'llm_setting' in bot_data and isinstance(bot_data['llm_setting'], str) and bot_data['llm_setting']:
            try:
                bot_data['llm_setting'] = json.loads(bot_data['llm_setting'])
            except json.JSONDecodeError:
                # 如果解析失败，保持原样
                pass
                
        # 创建QanythingBot对象
        bot = QanythingBot.from_dict(bot_data)
        return bot
    
    def get_bots_by_user(self, user_id: str) -> List[QanythingBot]:
        """获取用户的所有聊天机器人
        
        Args:
            user_id: 用户ID
            
        Returns:
            聊天机器人对象列表
        """
        query = """
            SELECT bot_id, user_id, bot_name, description, head_image, 
                   prompt_setting, welcome_message, kb_ids_str, llm_setting, is_deleted, timestamp
            FROM QanythingBot
            WHERE user_id = %s AND is_deleted = 0
            ORDER BY timestamp DESC
        """
        
        results = self.execute_query(query, (user_id,), fetch=True)
        if not results:
            return []
            
        # 转为机器人对象列表
        columns = [
            'bot_id', 'user_id', 'bot_name', 'description', 'head_image',
            'prompt_setting', 'welcome_message', 'kb_ids_str', 'llm_setting', 'is_deleted', 'timestamp'
        ]
        
        bots = []
        for result in results:
            bot_data = dict(zip(columns, result))
            
            # 处理时间戳
            if 'timestamp' in bot_data:
                bot_data['timestamp'] = bot_data['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                
            # 将llm_setting转为字典（如果是字符串形式）
            if 'llm_setting' in bot_data and isinstance(bot_data['llm_setting'], str) and bot_data['llm_setting']:
                try:
                    bot_data['llm_setting'] = json.loads(bot_data['llm_setting'])
                except json.JSONDecodeError:
                    # 如果解析失败，保持原样
                    pass
                    
            # 创建QanythingBot对象
            bot = QanythingBot.from_dict(bot_data)
            bots.append(bot)
            
        return bots
    
    def get_bots_by_kb_id(self, kb_id: str) -> List[QanythingBot]:
        """获取与知识库关联的所有聊天机器人
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            聊天机器人对象列表
        """
        query = """
            SELECT bot_id, user_id, bot_name, description, head_image, 
                   prompt_setting, welcome_message, kb_ids_str, llm_setting, is_deleted, timestamp
            FROM QanythingBot
            WHERE kb_ids_str LIKE %s AND is_deleted = 0
            ORDER BY timestamp DESC
        """
        
        results = self.execute_query(query, (f'%{kb_id}%',), fetch=True)
        if not results:
            return []
            
        # 转为机器人对象列表
        columns = [
            'bot_id', 'user_id', 'bot_name', 'description', 'head_image',
            'prompt_setting', 'welcome_message', 'kb_ids_str', 'llm_setting', 'is_deleted', 'timestamp'
        ]
        
        bots = []
        for result in results:
            bot_data = dict(zip(columns, result))
            
            # 处理时间戳
            if 'timestamp' in bot_data:
                bot_data['timestamp'] = bot_data['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                
            # 将llm_setting转为字典（如果是字符串形式）
            if 'llm_setting' in bot_data and isinstance(bot_data['llm_setting'], str) and bot_data['llm_setting']:
                try:
                    bot_data['llm_setting'] = json.loads(bot_data['llm_setting'])
                except json.JSONDecodeError:
                    # 如果解析失败，保持原样
                    pass
                    
            # 创建QanythingBot对象
            bot = QanythingBot.from_dict(bot_data)
            bots.append(bot)
            
        return bots
    
    def delete_bot(self, bot_id: str) -> bool:
        """删除聊天机器人（软删除）
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            是否删除成功
        """
        query = "UPDATE QanythingBot SET is_deleted = 1 WHERE bot_id = %s"
        
        result = self.execute_query(query, (bot_id,), commit=True)
        success = result and result.rowcount > 0
        
        if success:
            debug_logger.info(f"删除机器人成功: {bot_id}")
        else:
            debug_logger.error(f"删除机器人失败: {bot_id}")
            
        return success
    
    def check_bot_exist(self, bot_id: str) -> bool:
        """检查聊天机器人是否存在
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            是否存在
        """
        query = "SELECT COUNT(*) FROM QanythingBot WHERE bot_id = %s AND is_deleted = 0"
        
        result = self.execute_query(query, (bot_id,), fetch=True)
        return result[0][0] > 0 if result else False
    
    def check_bot_name_exist(self, user_id: str, bot_name: str, exclude_bot_id: Optional[str] = None) -> bool:
        """检查聊天机器人名称是否已存在
        
        Args:
            user_id: 用户ID
            bot_name: 机器人名称
            exclude_bot_id: 排除的机器人ID（用于更新时检查）
            
        Returns:
            是否存在
        """
        if exclude_bot_id:
            query = """
                SELECT COUNT(*) FROM QanythingBot 
                WHERE user_id = %s AND bot_name = %s AND bot_id != %s AND is_deleted = 0
            """
            result = self.execute_query(query, (user_id, bot_name, exclude_bot_id), fetch=True)
        else:
            query = "SELECT COUNT(*) FROM QanythingBot WHERE user_id = %s AND bot_name = %s AND is_deleted = 0"
            result = self.execute_query(query, (user_id, bot_name), fetch=True)
            
        return result[0][0] > 0 if result else False
    
    def get_total_bots_count(self, user_id: Optional[str] = None) -> int:
        """获取聊天机器人总数
        
        Args:
            user_id: 用户ID（如果指定，则获取该用户的机器人数量）
            
        Returns:
            机器人总数
        """
        if user_id:
            query = "SELECT COUNT(*) FROM QanythingBot WHERE user_id = %s AND is_deleted = 0"
            result = self.execute_query(query, (user_id,), fetch=True)
        else:
            query = "SELECT COUNT(*) FROM QanythingBot WHERE is_deleted = 0"
            result = self.execute_query(query, fetch=True)
            
        return result[0][0] if result else 0 