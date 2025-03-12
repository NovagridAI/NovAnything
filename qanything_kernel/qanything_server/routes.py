from sanic import Blueprint
from qanything_kernel.qanything_server import handler, kb, dept, user, user_group, auth, bot

# 创建蓝图
api_bp = Blueprint('api', url_prefix='/api')
local_doc_qa_bp = Blueprint('local_doc_qa', url_prefix='/api/local_doc_qa')
auth_bp = Blueprint('auth', url_prefix='/api/auth')
user_bp = Blueprint('user', url_prefix='/api/user')
dept_bp = Blueprint('department', url_prefix='/api/department')
group_bp = Blueprint('group', url_prefix='/api/group')
kb_bp = Blueprint('kb', url_prefix='/api/kb')
bot_bp = Blueprint('bot', url_prefix='/api/bot')

# 基础API路由
api_bp.add_route(handler.document, "/docs", methods=['GET'])  # tags=["API文档"]
api_bp.add_route(handler.health_check, "/health_check", methods=['GET'])  # tags=["健康检查"]

# 知识库相关路由
local_doc_qa_bp.add_route(kb.new_knowledge_base, "/new_knowledge_base", methods=['POST'])  # tags=["新建知识库"]
local_doc_qa_bp.add_route(kb.upload_weblink, "/upload_weblink", methods=['POST'])  # tags=["上传网页链接"]
local_doc_qa_bp.add_route(kb.upload_files, "/upload_files", methods=['POST'])  # tags=["上传文件"]
local_doc_qa_bp.add_route(kb.upload_faqs, "/upload_faqs", methods=['POST'])  # tags=["上传FAQ"]
local_doc_qa_bp.add_route(kb.local_doc_chat, "/local_doc_chat", methods=['POST'])  # tags=["知识库问答"]
local_doc_qa_bp.add_route(kb.list_docs, "/list_files", methods=['POST'])  # tags=["文件列表"]
local_doc_qa_bp.add_route(kb.get_total_status, "/get_total_status", methods=['POST'])  # tags=["获取知识库状态"]
local_doc_qa_bp.add_route(kb.clean_files_by_status, "/clean_files_by_status", methods=['POST'])  # tags=["清理文件"]
local_doc_qa_bp.add_route(kb.delete_docs, "/delete_files", methods=['POST'])  # tags=["删除文件"]
local_doc_qa_bp.add_route(kb.delete_knowledge_base, "/delete_knowledge_base", methods=['POST'])  # tags=["删除知识库"]
local_doc_qa_bp.add_route(kb.rename_knowledge_base, "/rename_knowledge_base", methods=['POST'])  # tags=["重命名知识库"]
local_doc_qa_bp.add_route(kb.get_doc_completed, "/get_doc_completed", methods=['POST'])  # tags=["获取文档完整内容"]
local_doc_qa_bp.add_route(kb.get_qa_info, "/get_qa_info", methods=['POST'])  # tags=["获取QA信息"]
local_doc_qa_bp.add_route(kb.get_user_id, "/get_user_id", methods=['POST'])  # tags=["获取用户ID"]
local_doc_qa_bp.add_route(kb.get_doc, "/get_doc", methods=['POST'])  # tags=["获取文档详情"]
local_doc_qa_bp.add_route(kb.get_rerank_results, "/get_rerank_results", methods=['POST'])  # tags=["获取重排结果"]
local_doc_qa_bp.add_route(kb.get_user_status, "/get_user_status", methods=['POST'])  # tags=["获取用户状态"]
local_doc_qa_bp.add_route(kb.get_random_qa, "/get_random_qa", methods=['POST'])  # tags=["获取随机QA"]
local_doc_qa_bp.add_route(kb.get_related_qa, "/get_related_qa", methods=['POST'])  # tags=["获取相关QA"]
local_doc_qa_bp.add_route(kb.update_chunks, "/update_chunks", methods=['POST'])  # tags=["更新文档块"]
local_doc_qa_bp.add_route(kb.get_file_base64, "/get_file_base64", methods=['POST'])  # tags=["获取文件Base64"]

# 机器人相关路由
bot_bp.add_route(bot.new_bot, "/new_bot", methods=['POST'])  # tags=["创建机器人"]
bot_bp.add_route(bot.delete_bot, "/delete_bot", methods=['POST'])  # tags=["删除机器人"]
bot_bp.add_route(bot.update_bot, "/update_bot", methods=['POST'])  # tags=["更新机器人"]
bot_bp.add_route(bot.get_bot_info, "/get_bot_info", methods=['POST'])  # tags=["获取机器人信息"]

# 用户认证相关路由
auth_bp.add_route(auth.login, "/login", methods=['POST'])  # tags=["用户登录"]
auth_bp.add_route(auth.refresh_token, "/refresh_token", methods=['POST'])  # tags=["刷新令牌"]

# 用户管理路由
user_bp.add_route(user.create_user, "/create", methods=['POST'])  # tags=["创建用户"]
user_bp.add_route(user.list_users, "/list", methods=['GET'])  # tags=["用户列表"]
user_bp.add_route(user.delete_user, "/delete", methods=['POST'])  # tags=["删除用户"]
user_bp.add_route(user.update_user, "/update", methods=['POST'])  # tags=["更新用户"]
user_bp.add_route(user.reset_user_password, "/reset_password", methods=['POST'])  # tags=["重置密码"]
user_bp.add_route(user.change_password, "/change_password", methods=['POST'])  # tags=["修改密码"]
user_bp.add_route(user.set_user_kb_access, "/set_kb_access", methods=['POST'])  # tags=["设置用户知识库权限"]
user_bp.add_route(user.batch_set_user_kb_access, "/batch_set_kb_access", methods=['POST'])  # tags=["批量设置用户知识库权限"]
user_bp.add_route(user.get_user_kb_access, "/get_kb_access", methods=['GET'])  # tags=["获取用户知识库权限"]
user_bp.add_route(user.update_user_profile, "/update_user_profile", methods=['POST'])  # tags=["更新用户信息"]
user_bp.add_route(user.get_user_profile, "/get_user_profile", methods=['GET'])  # tags=["获取用户信息"]
user_bp.add_route(user.get_accessible_kbs, "/list_knowledge_base", methods=['POST'])  # tags=["获取可访问知识库"]


# 部门管理路由
dept_bp.add_route(dept.create_department, "/create", methods=['POST'])  # tags=["创建部门"]
dept_bp.add_route(dept.list_departments, "/list", methods=['GET'])  # tags=["部门列表"]
dept_bp.add_route(dept.update_department, "/update", methods=['POST'])  # tags=["更新部门"]
dept_bp.add_route(dept.delete_department, "/delete", methods=['POST'])  # tags=["删除部门"]
dept_bp.add_route(dept.add_users_to_dept, "/add_user", methods=['POST'])  # tags=["添加用户到部门"]

# 用户组管理路由
group_bp.add_route(user_group.create_group, "/create", methods=['POST'])  # tags=["创建用户组"]
group_bp.add_route(user_group.list_groups, "/list", methods=['GET'])  # tags=["用户组列表"]
group_bp.add_route(user_group.update_group, "/update", methods=['POST'])  # tags=["更新用户组"]
group_bp.add_route(user_group.delete_group, "/delete", methods=['POST'])  # tags=["删除用户组"]
group_bp.add_route(user_group.add_user_to_group, "/add_user", methods=['POST'])  # tags=["添加用户到用户组"]
group_bp.add_route(user_group.remove_user_from_group, "/remove_user", methods=['POST'])  # tags=["从用户组移除用户"]
group_bp.add_route(user_group.list_group_members, "/members", methods=['GET'])  # tags=["用户组成员列表"]

# 知识库权限管理路由
kb_bp.add_route(kb.grant_kb_access, "/grant_access", methods=['POST'])  # tags=["授予知识库访问权限"]
kb_bp.add_route(kb.revoke_kb_access, "/revoke_access", methods=['POST'])  # tags=["撤销知识库访问权限"]
kb_bp.add_route(kb.get_kb_access_list, "/access_list", methods=['GET'])  # tags=["获取知识库访问权限列表"]
kb_bp.add_route(kb.check_kb_permission, "/check_access", methods=['GET'])  # tags=["检查知识库权限"]
kb_bp.add_route(kb.batch_set_kb_access, "/batch_set_access", methods=['POST'])  # tags=["批量设置知识库访问权限"]
kb_bp.add_route(kb.get_kb_detail, "/detail", methods=['GET'])  # tags=["获取知识库详情"]
kb_bp.add_route(kb.transfer_kb_ownership, "/transfer_kb_ownership", methods=['POST'])  # tags=["转移知识库所有权"]

def register_routes(app):
    """注册所有路由到应用"""
    from qanything_kernel.utils.custom_log import debug_logger
    
    debug_logger.info("开始注册路由...")
    
    app.blueprint(api_bp)
    debug_logger.info(f"注册api_bp蓝图，包含 {len(api_bp.routes)} 个路由")
    
    app.blueprint(local_doc_qa_bp)
    debug_logger.info(f"注册local_doc_qa_bp蓝图，包含 {len(local_doc_qa_bp.routes)} 个路由")
    
    app.blueprint(auth_bp)
    debug_logger.info(f"注册auth_bp蓝图，包含 {len(auth_bp.routes)} 个路由")
    
    app.blueprint(user_bp)
    debug_logger.info(f"注册user_bp蓝图，包含 {len(user_bp.routes)} 个路由")
    
    app.blueprint(dept_bp)
    debug_logger.info(f"注册dept_bp蓝图，包含 {len(dept_bp.routes)} 个路由")
    
    app.blueprint(group_bp)
    debug_logger.info(f"注册group_bp蓝图，包含 {len(group_bp.routes)} 个路由")
    
    app.blueprint(kb_bp)
    debug_logger.info(f"注册kb_bp蓝图，包含 {len(kb_bp.routes)} 个路由")
    
    # 添加bot_bp蓝图注册，这个在原代码中漏掉了
    app.blueprint(bot_bp)
    debug_logger.info(f"注册bot_bp蓝图，包含 {len(bot_bp.routes)} 个路由")
    
    debug_logger.info("所有路由注册完成")
    