"""
数据库管理器
集成所有DAO，提供统一的接口
"""
from qanything_kernel.connector.database.mysql.connection import DatabaseConnection
from qanything_kernel.connector.database.mysql.daos.user_dao import UserDAO
from qanything_kernel.connector.database.mysql.daos.knowledge_base_dao import KnowledgeBaseDAO
from qanything_kernel.connector.database.mysql.daos.file_dao import FileDAO
from qanything_kernel.connector.database.mysql.daos.faq_dao import FaqDAO
from qanything_kernel.connector.database.mysql.daos.document_dao import DocumentDAO
from qanything_kernel.connector.database.mysql.daos.qa_log_dao import QaLogDAO
from qanything_kernel.connector.database.mysql.daos.bot_dao import BotDAO
from qanything_kernel.connector.database.mysql.daos.department_dao import DepartmentDAO
from qanything_kernel.connector.database.mysql.daos.user_group_dao import UserGroupDAO
from qanything_kernel.connector.database.mysql.daos.group_member_dao import GroupMemberDAO
from qanything_kernel.connector.database.mysql.models.file import File, FileImage
from qanything_kernel.connector.database.mysql.models.faq import Faq
from qanything_kernel.connector.database.mysql.models.document import Document
from qanything_kernel.connector.database.mysql.models.qa_log import QaLog
from qanything_kernel.connector.database.mysql.models.bot import QanythingBot
from qanything_kernel.connector.database.mysql.models.department import Department
from qanything_kernel.connector.database.mysql.models.user_group import UserGroup
from qanything_kernel.connector.database.mysql.models.group_member import GroupMember
from qanything_kernel.utils.custom_log import debug_logger


class DatabaseManager:
    """数据库管理器类
    
    集成所有DAO，提供统一的接口，允许应用程序访问各个领域的数据
    """
    
    def __init__(self, pool_size=8):
        """初始化
        
        Args:
            pool_size: 连接池大小，默认为8
        """
        self.db_connection = DatabaseConnection(pool_size=pool_size)
        
        # 初始化各个DAO
        self.user_dao = UserDAO(self.db_connection)
        self.kb_dao = KnowledgeBaseDAO(self.db_connection)
        self.file_dao = FileDAO(self.db_connection)
        self.faq_dao = FaqDAO(self.db_connection)
        self.document_dao = DocumentDAO(self.db_connection)
        self.qa_log_dao = QaLogDAO(self.db_connection)
        self.bot_dao = BotDAO(self.db_connection)
        self.department_dao = DepartmentDAO(self.db_connection)
        self.user_group_dao = UserGroupDAO(self.db_connection)
        self.group_member_dao = GroupMemberDAO(self.db_connection)
        
        self.create_tables()
        
    def create_tables(self):
        """创建数据库表"""
        debug_logger.info("正在检查并创建数据库表...")
        
        # 创建用户表
        self.user_dao.create_table()
        self.user_dao.create_admin_if_not_exists()
        
        # 创建知识库表
        self.kb_dao.create_table()
        
        # 创建文件表
        self.file_dao.create_table()
        
        # 创建FAQ表
        self.faq_dao.create_table()
        
        # 创建文档表
        self.document_dao.create_table()
        
        # 创建问答日志表
        self.qa_log_dao.create_table()
        
        # 创建机器人表
        self.bot_dao.create_table()
        
        # 创建部门表
        self.department_dao.create_table()
        
        # 创建用户组表
        self.user_group_dao.create_table()
        
        # 创建用户组成员表
        self.group_member_dao.create_table()
        
        debug_logger.info("数据库表检查和创建完成")
        
    # 用户相关方法
    def check_user_exist(self, user_id):
        """检查用户是否存在"""
        return self.user_dao.check_user_exists(user_id)
    
    def get_users(self):
        """获取所有用户ID"""
        return self.user_dao.get_users()
    
    # 知识库相关方法
    def new_milvus_base(self, kb_id, user_id, kb_name, user_name=None):
        """创建新知识库"""
        if not self.check_user_exist(user_id):
            # 如果用户不存在，先创建用户
            from qanything_kernel.connector.database.mysql.models.user import User
            user = User(user_id=user_id, user_name=user_name or user_id)
            self.user_dao.create_user(user)
            
        return self.kb_dao.new_knowledge_base(kb_id, user_id, kb_name)
    
    def get_knowledge_bases(self, user_id):
        """获取用户可访问的所有知识库"""
        return self.kb_dao.get_knowledge_bases(user_id)
    
    def check_kb_exist(self, user_id, kb_ids):
        """检查知识库是否存在"""
        return self.kb_dao.check_kb_exist(kb_ids)
    
    def get_knowledge_base_name(self, kb_ids):
        """获取指定kb_ids的知识库信息"""
        return self.kb_dao.get_knowledge_base_name(kb_ids)
    
    def delete_knowledge_base(self, user_id, kb_ids):
        """删除知识库"""
        return self.kb_dao.delete_knowledge_base(user_id, kb_ids)
    
    def rename_knowledge_base(self, user_id, kb_id, kb_name):
        """重命名知识库"""
        return self.kb_dao.rename_knowledge_base(user_id, kb_id, kb_name)
    
    def update_knowledge_base_latest_qa_time(self, kb_id, timestamp):
        """更新知识库的最新问答时间"""
        return self.kb_dao.update_knowledge_base_latest_qa_time(kb_id, timestamp)
    
    def update_knowlegde_base_latest_insert_time(self, kb_id, timestamp):
        """更新知识库的最新插入时间"""
        return self.kb_dao.update_knowledge_base_latest_insert_time(kb_id, timestamp)
    
    def get_user_by_kb_id(self, kb_id):
        """根据知识库ID获取所有者用户ID"""
        return self.kb_dao.get_user_by_kb_id(kb_id)
    
    def check_kb_access(self, user_id, kb_id, required_permission):
        """检查用户是否有权限访问知识库"""
        return self.kb_dao.check_kb_access(user_id, kb_id, required_permission)
    
    def set_kb_access(self, kb_id, subject_id, subject_type, permission_type, granted_by):
        """设置知识库访问权限"""
        return self.kb_dao.set_kb_access(kb_id, subject_id, subject_type, permission_type, granted_by)
    
    # 文件相关方法
    def add_file(self, file_id, user_id, kb_id, file_name, file_size, file_location, chunk_size, timestamp, file_url='',
                 status="gray"):
        """添加文件"""
        file = File(
            file_id=file_id,
            user_id=user_id,
            kb_id=kb_id,
            file_name=file_name,
            status=status,
            file_size=file_size,
            file_location=file_location,
            chunk_size=chunk_size,
            timestamp=timestamp,
            file_url=file_url
        )
        return self.file_dao.add_file(file)
    
    def update_file_msg(self, file_id, msg):
        """更新文件消息"""
        return self.file_dao.update_file_msg(file_id, msg)
    
    def update_file_upload_infos(self, file_id, upload_infos):
        """更新文件上传信息"""
        return self.file_dao.update_file_upload_infos(file_id, upload_infos)
    
    def update_content_length(self, file_id, content_length):
        """更新文件内容长度"""
        return self.file_dao.update_content_length(file_id, content_length)
    
    def update_chunks_number(self, file_id, chunks_number):
        """更新文件分块数量"""
        return self.file_dao.update_chunks_number(file_id, chunks_number)
    
    def update_file_status(self, file_id, status):
        """更新文件状态"""
        return self.file_dao.update_file_status(file_id, status)
    
    def from_status_to_status(self, file_ids, from_status, to_status):
        """更新指定文件的状态"""
        return self.file_dao.from_status_to_status(file_ids, from_status, to_status)
    
    def get_files(self, user_id, kb_id, file_id=None):
        """获取文件信息"""
        return self.file_dao.get_files(kb_id, file_id)
    
    def get_file_by_status(self, kb_ids, status):
        """根据状态获取文件"""
        return self.file_dao.get_file_by_status(kb_ids, status)
    
    def get_file_timestamp(self, file_id):
        """获取文件时间戳"""
        return self.file_dao.get_file_timestamp(file_id)
    
    def get_file_location(self, file_id):
        """获取文件位置"""
        return self.file_dao.get_file_location(file_id)
    
    def check_file_exist(self, user_id, kb_id, file_ids):
        """检查文件是否存在"""
        return self.file_dao.check_file_exist(user_id, kb_id, file_ids)
    
    def check_file_exist_by_name(self, user_id, kb_id, file_names):
        """根据文件名检查文件是否存在"""
        return self.file_dao.check_file_exist_by_name(user_id, kb_id, file_names)
    
    def is_deleted_file(self, file_id):
        """检查文件是否已删除"""
        return self.file_dao.is_deleted_file(file_id)
    
    def delete_files(self, kb_id, file_ids):
        """删除文件"""
        return self.file_dao.delete_files(kb_id, file_ids)
    
    def get_total_status_by_date(self, user_id):
        """获取用户文件按日期和状态的统计"""
        return self.file_dao.get_total_status_by_date(user_id)
    
    def get_chunk_size(self, file_ids):
        """获取文件分块大小"""
        return self.file_dao.get_chunk_size(file_ids)
    
    def get_files_by_status(self, status):
        """获取指定状态的所有文件"""
        return self.file_dao.get_files_by_status(status)
    
    # 文件图片相关方法
    def add_file_images(self, image_id, file_id, user_id, kb_id, nos_key):
        """添加文件图片"""
        image = FileImage(
            image_id=image_id,
            file_id=file_id,
            user_id=user_id,
            kb_id=kb_id,
            nos_key=nos_key
        )
        return self.file_dao.add_file_images(image)
    
    def get_image_id_by_nos_key(self, nos_key):
        """根据NOS键获取图片ID"""
        return self.file_dao.get_image_id_by_nos_key(nos_key)
    
    def get_nos_key_by_image_id(self, image_id):
        """根据图片ID获取NOS键"""
        return self.file_dao.get_nos_key_by_image_id(image_id)
    
    # FAQ相关方法
    def add_faq(self, faq_id, user_id, kb_id, question, answer, nos_keys=None):
        """添加FAQ"""
        faq = Faq(
            faq_id=faq_id,
            user_id=user_id,
            kb_id=kb_id,
            question=question,
            answer=answer,
            nos_keys=nos_keys
        )
        return self.faq_dao.add_faq(faq)
    
    def get_faq(self, faq_id):
        """获取FAQ"""
        return self.faq_dao.get_faq(faq_id)
    
    def get_faq_by_question(self, question, kb_id):
        """根据问题获取FAQ ID"""
        return self.faq_dao.get_faq_by_question(question, kb_id)
    
    def delete_faqs(self, faq_ids):
        """删除FAQ"""
        return self.faq_dao.delete_faqs(faq_ids)
    
    # 文档相关方法
    def add_document(self, doc_id, json_data):
        """添加文档"""
        document = Document(
            doc_id=doc_id,
            json_data=json_data
        )
        return self.document_dao.add_document(document)
    
    def update_document(self, doc_id, update_content):
        """更新文档内容"""
        return self.document_dao.update_document(doc_id, update_content)
    
    def get_document_by_doc_id(self, doc_id):
        """根据文档ID获取文档"""
        document = self.document_dao.get_document_by_doc_id(doc_id)
        return document.json_data if document else None
    
    def get_document_by_file_id(self, file_id, batch_size=100):
        """根据文件ID获取文档"""
        return self.document_dao.get_document_by_file_id(file_id, batch_size)
    
    def delete_documents(self, file_ids):
        """删除文档"""
        return self.document_dao.delete_documents(file_ids)
    
    # QaLog相关方法
    def add_qa_log(self, qa_log: QaLog) -> None:
        """添加问答日志
        
        Args:
            qa_log: 问答日志对象
        """
        return self.qa_log_dao.add_qa_log(qa_log)
    
    def get_qa_log_by_filter(self, need_info: List[str], user_id: Optional[str] = None, 
                             query: Optional[str] = None, bot_id: Optional[str] = None, 
                             time_range: Optional[Tuple[datetime, datetime]] = None,
                             any_kb_id: Optional[str] = None, qa_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """根据条件获取问答日志
        
        Args:
            need_info: 需要获取的字段列表
            user_id: 用户ID
            query: 查询内容
            bot_id: 机器人ID
            time_range: 时间范围元组 (开始时间, 结束时间)
            any_kb_id: 包含特定知识库ID
            qa_ids: 问答ID列表
            
        Returns:
            符合条件的问答日志列表
        """
        return self.qa_log_dao.get_qa_log_by_filter(
            need_info, user_id, query, bot_id, time_range, any_kb_id, qa_ids
        )
    
    def get_qa_log_by_id(self, qa_id: str, need_info: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """根据ID获取问答日志
        
        Args:
            qa_id: 问答ID
            need_info: 需要获取的字段列表
            
        Returns:
            问答日志详情
        """
        return self.qa_log_dao.get_qa_log_by_id(qa_id, need_info)
    
    def get_related_qa_logs(self, qa_id: str, need_info: Optional[List[str]] = None, 
                           need_more: bool = False) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """获取与指定问答相关的其他问答日志
        
        Args:
            qa_id: 问答ID
            need_info: 需要获取的字段列表
            need_more: 是否需要获取更多相关问答
            
        Returns:
            (当前问答, 最近7天内的问答, 7天前的问答)
        """
        return self.qa_log_dao.get_related_qa_logs(qa_id, need_info, need_more)
    
    def get_qa_statistics(self, time_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        """获取指定时间范围内的问答统计信息
        
        Args:
            time_range: 时间范围元组 (开始时间, 结束时间)
            
        Returns:
            统计信息字典，包含用户数和查询数
        """
        return self.qa_log_dao.get_statistic(time_range)
    
    def get_random_qa_logs(self, limit: int = 10, time_range: Optional[Tuple[datetime, datetime]] = None,
                          need_info: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取随机问答日志
        
        Args:
            limit: 最大返回数量
            time_range: 时间范围元组 (开始时间, 结束时间)
            need_info: 需要获取的字段列表
            
        Returns:
            随机问答日志列表
        """
        return self.qa_log_dao.get_random_qa_logs(limit, time_range, need_info)
    
    # Bot相关方法
    def add_bot(self, bot: QanythingBot) -> str:
        """添加聊天机器人
        
        Args:
            bot: 聊天机器人对象
            
        Returns:
            bot_id: 机器人ID
        """
        return self.bot_dao.add_bot(bot)
    
    def update_bot(self, bot: QanythingBot) -> bool:
        """更新聊天机器人
        
        Args:
            bot: 聊天机器人对象
            
        Returns:
            是否更新成功
        """
        return self.bot_dao.update_bot(bot)
    
    def get_bot_by_id(self, bot_id: str) -> Optional[QanythingBot]:
        """根据ID获取聊天机器人
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            聊天机器人对象
        """
        return self.bot_dao.get_bot_by_id(bot_id)
    
    def get_bots_by_user(self, user_id: str) -> List[QanythingBot]:
        """获取用户的所有聊天机器人
        
        Args:
            user_id: 用户ID
            
        Returns:
            聊天机器人对象列表
        """
        return self.bot_dao.get_bots_by_user(user_id)
    
    def get_bots_by_kb_id(self, kb_id: str) -> List[QanythingBot]:
        """获取与知识库关联的所有聊天机器人
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            聊天机器人对象列表
        """
        return self.bot_dao.get_bots_by_kb_id(kb_id)
    
    def delete_bot(self, bot_id: str) -> bool:
        """删除聊天机器人
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            是否删除成功
        """
        return self.bot_dao.delete_bot(bot_id)
    
    def check_bot_exist(self, bot_id: str) -> bool:
        """检查聊天机器人是否存在
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            是否存在
        """
        return self.bot_dao.check_bot_exist(bot_id)
    
    def check_bot_name_exist(self, user_id: str, bot_name: str, exclude_bot_id: Optional[str] = None) -> bool:
        """检查聊天机器人名称是否已存在
        
        Args:
            user_id: 用户ID
            bot_name: 机器人名称
            exclude_bot_id: 排除的机器人ID（用于更新时检查）
            
        Returns:
            是否存在
        """
        return self.bot_dao.check_bot_name_exist(user_id, bot_name, exclude_bot_id)
    
    def get_total_bots_count(self, user_id: Optional[str] = None) -> int:
        """获取聊天机器人总数
        
        Args:
            user_id: 用户ID（如果指定，则获取该用户的机器人数量）
            
        Returns:
            机器人总数
        """
        return self.bot_dao.get_total_bots_count(user_id)
    
    # 部门相关方法
    def add_department(self, department: Department) -> bool:
        """添加部门
        
        Args:
            department: 部门对象
            
        Returns:
            是否成功添加
        """
        return self.department_dao.add_department(department)
    
    def update_department(self, department: Department) -> bool:
        """更新部门
        
        Args:
            department: 部门对象
            
        Returns:
            是否成功更新
        """
        return self.department_dao.update_department(department)
    
    def get_department_by_id(self, dept_id: str) -> Optional[Department]:
        """根据部门ID获取部门
        
        Args:
            dept_id: 部门ID
            
        Returns:
            部门对象，如果不存在则返回None
        """
        return self.department_dao.get_department_by_id(dept_id)
    
    def get_departments(self) -> List[Department]:
        """获取所有部门
        
        Returns:
            部门对象列表
        """
        return self.department_dao.get_departments()
    
    def get_child_departments(self, parent_dept_id: str) -> List[Department]:
        """获取子部门
        
        Args:
            parent_dept_id: 父部门ID
            
        Returns:
            子部门对象列表
        """
        return self.department_dao.get_child_departments(parent_dept_id)
    
    def delete_department(self, dept_id: str) -> bool:
        """删除部门
        
        Args:
            dept_id: 部门ID
            
        Returns:
            是否成功删除
        """
        return self.department_dao.delete_department(dept_id)
    
    def check_department_exists(self, dept_id: str) -> bool:
        """检查部门是否存在
        
        Args:
            dept_id: 部门ID
            
        Returns:
            部门是否存在
        """
        return self.department_dao.check_department_exists(dept_id)
    
    def get_department_tree(self, root_dept_id: Optional[str] = None) -> Dict[str, Any]:
        """获取部门树
        
        Args:
            root_dept_id: 根部门ID，如果为None则从顶级部门开始
            
        Returns:
            部门树结构
        """
        return self.department_dao.get_department_tree(root_dept_id)
    
    # 用户组相关方法
    def add_group(self, group: UserGroup) -> str:
        """添加用户组
        
        Args:
            group: 用户组对象
            
        Returns:
            group_id: 用户组ID
        """
        return self.user_group_dao.add_group(group)
    
    def update_group(self, group: UserGroup) -> bool:
        """更新用户组
        
        Args:
            group: 用户组对象
            
        Returns:
            是否成功更新
        """
        return self.user_group_dao.update_group(group)
    
    def get_group_by_id(self, group_id: str) -> Optional[UserGroup]:
        """根据用户组ID获取用户组
        
        Args:
            group_id: 用户组ID
            
        Returns:
            用户组对象，如果不存在则返回None
        """
        return self.user_group_dao.get_group_by_id(group_id)
    
    def get_groups_by_owner(self, owner_id: str) -> List[UserGroup]:
        """获取用户创建的所有用户组
        
        Args:
            owner_id: 所有者用户ID
            
        Returns:
            用户组对象列表
        """
        return self.user_group_dao.get_groups_by_owner(owner_id)
    
    def get_groups_by_user(self, user_id: str) -> List[UserGroup]:
        """获取用户所属的所有用户组
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户组对象列表
        """
        return self.user_group_dao.get_groups_by_user(user_id)
    
    def get_all_groups(self) -> List[UserGroup]:
        """获取所有用户组
        
        Returns:
            用户组对象列表
        """
        return self.user_group_dao.get_all_groups()
    
    def delete_group(self, group_id: str) -> bool:
        """删除用户组
        
        Args:
            group_id: 用户组ID
            
        Returns:
            是否成功删除
        """
        return self.user_group_dao.delete_group(group_id)
    
    def check_group_exists(self, group_id: str) -> bool:
        """检查用户组是否存在
        
        Args:
            group_id: 用户组ID
            
        Returns:
            用户组是否存在
        """
        return self.user_group_dao.check_group_exists(group_id)
    
    def check_group_name_exists(self, group_name: str, owner_id: str) -> bool:
        """检查用户组名称是否已存在
        
        Args:
            group_name: 用户组名称
            owner_id: 所有者用户ID
            
        Returns:
            用户组名称是否已存在
        """
        return self.user_group_dao.check_group_name_exists(group_name, owner_id)
    
    # 用户组成员相关方法
    def add_group_member(self, member: GroupMember) -> bool:
        """添加用户组成员
        
        Args:
            member: 用户组成员对象
            
        Returns:
            是否成功添加
        """
        return self.group_member_dao.add_member(member)
    
    def update_member_role(self, group_id: str, user_id: str, role: str) -> bool:
        """更新用户组成员角色
        
        Args:
            group_id: 用户组ID
            user_id: 用户ID
            role: 角色名称
            
        Returns:
            是否成功更新
        """
        return self.group_member_dao.update_member_role(group_id, user_id, role)
    
    def get_group_members(self, group_id: str) -> List[Dict[str, Any]]:
        """获取用户组所有成员
        
        Args:
            group_id: 用户组ID
            
        Returns:
            成员信息列表
        """
        return self.group_member_dao.get_group_members(group_id)
    
    def get_group_member(self, group_id: str, user_id: str) -> Optional[GroupMember]:
        """获取特定用户组成员
        
        Args:
            group_id: 用户组ID
            user_id: 用户ID
            
        Returns:
            用户组成员对象，如果不存在则返回None
        """
        return self.group_member_dao.get_member(group_id, user_id)
    
    def remove_group_member(self, group_id: str, user_id: str) -> bool:
        """移除用户组成员
        
        Args:
            group_id: 用户组ID
            user_id: 用户ID
            
        Returns:
            是否成功移除
        """
        return self.group_member_dao.remove_member(group_id, user_id)
    
    def is_user_in_group(self, group_id: str, user_id: str, active_only: bool = True) -> bool:
        """检查用户是否在用户组中
        
        Args:
            group_id: 用户组ID
            user_id: 用户ID
            active_only: 是否只检查活跃状态的成员
            
        Returns:
            用户是否在用户组中
        """
        return self.group_member_dao.is_user_in_group(group_id, user_id, active_only)
    
    def get_member_role(self, group_id: str, user_id: str) -> Optional[str]:
        """获取用户在用户组中的角色
        
        Args:
            group_id: 用户组ID
            user_id: 用户ID
            
        Returns:
            用户角色，如果用户不在组中则返回None
        """
        return self.group_member_dao.get_member_role(group_id, user_id)
    
    def batch_add_group_members(self, group_id: str, user_ids: List[str], role: str = 'member') -> int:
        """批量添加用户组成员
        
        Args:
            group_id: 用户组ID
            user_ids: 用户ID列表
            role: 角色名称
            
        Returns:
            成功添加的成员数量
        """
        return self.group_member_dao.batch_add_members(group_id, user_ids, role)
    
    def get_user_groups_count(self, user_id: str) -> int:
        """获取用户所属的组数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户所属的组数量
        """
        return self.group_member_dao.get_user_groups_count(user_id)
        