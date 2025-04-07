from sanic import Sanic
from qanything_kernel.qanything_server.handler import *
from qanything_kernel.qanything_server.user import *
from qanything_kernel.qanything_server.dept import *
from qanything_kernel.qanything_server.user_group import *
from qanything_kernel.qanything_server.kb import *
from qanything_kernel.qanything_server.document import *
from qanything_kernel.qanything_server.faq import *
from qanything_kernel.qanything_server.bot import *
from qanything_kernel.qanything_server.auth import login, refresh_token
from qanything_kernel.qanything_server.qa_log import get_qa_logs, get_qa_log, update_qa_log, delete_qa_log, toggle_qa_favorite, create_qa_log
from qanything_kernel.qanything_server.model_config import create_model_config, update_model_config, get_model_config, list_model_configs, delete_model_config


def register_routes(app: Sanic):
    """注册所有路由"""
    
    # 知识库管理相关接口
    app.add_route(document, "/api/docs", methods=['GET'])
    app.add_route(health_check, "/api/health_check", methods=['GET'])  # tags=["健康检查"]
    app.add_route(new_knowledge_base, "/api/local_doc_qa/new_knowledge_base", methods=['POST'])  # tags=["新建知识库"]
    app.add_route(list_kbs, "/api/local_doc_qa/list_knowledge_base", methods=['POST'])  # tags=["知识库列表"]
    app.add_route(upload_weblink, "/api/local_doc_qa/upload_weblink", methods=['POST'])  # tags=["上传网页链接"]
    app.add_route(upload_files, "/api/local_doc_qa/upload_files", methods=['POST'])  # tags=["上传文件"]
    app.add_route(upload_faqs, "/api/local_doc_qa/upload_faqs", methods=['POST'])  # tags=["上传FAQ"]
    app.add_route(local_doc_chat, "/api/local_doc_qa/local_doc_chat", methods=['POST'])  # tags=["问答接口"]
    app.add_route(list_docs, "/api/local_doc_qa/list_files", methods=['POST'])  # tags=["文件列表"]
    app.add_route(get_total_status, "/api/local_doc_qa/get_total_status", methods=['POST'])  # tags=["获取所有知识库状态数据库"]
    app.add_route(clean_files_by_status, "/api/local_doc_qa/clean_files_by_status", methods=['POST'])  # tags=["清理数据库"]
    app.add_route(delete_docs, "/api/local_doc_qa/delete_files", methods=['POST'])  # tags=["删除文件"]
    app.add_route(delete_knowledge_base, "/api/local_doc_qa/delete_knowledge_base", methods=['POST'])  # tags=["删除知识库"]
    app.add_route(update_knowledge_base, "/api/local_doc_qa/update_knowledge_base", methods=['POST'])  # tags=["重命名知识库"]
    app.add_route(get_doc_completed, "/api/local_doc_qa/get_doc_completed", methods=['POST'])  # tags=["获取文档完整解析内容"]
    # app.add_route(get_qa_info, "/api/local_doc_qa/get_qa_info", methods=['POST'])  # tags=["获取QA信息"]
    # app.add_route(get_doc, "/api/local_doc_qa/get_doc", methods=['POST'])  # tags=["获取doc详细内容"]
    app.add_route(get_rerank_results, "/api/local_doc_qa/get_rerank_results", methods=['POST'])  # tags=["获取rerank结果"]
    app.add_route(get_user_status, "/api/local_doc_qa/get_user_status", methods=['POST'])  # tags=["获取用户状态"]
    # app.add_route(get_random_qa, "/api/local_doc_qa/get_random_qa", methods=['POST'])  # tags=["获取随机QA"]
    # app.add_route(get_related_qa, "/api/local_doc_qa/get_related_qa", methods=['POST'])  # tags=["获取相关QA"]
    app.add_route(update_chunks, "/api/local_doc_qa/update_chunks", methods=['POST'])  # tags=["更新chunk"]
    app.add_route(get_file_base64, "/api/local_doc_qa/get_file_base64", methods=['POST'])  # tags=["获取文件的base64编码"]

    # 问答日志相关接口
    app.add_route(get_qa_logs, "/api/local_doc_qa/get_qa_logs", methods=['POST'])  # tags=["获取问答日志列表"]
    app.add_route(get_qa_log, "/api/local_doc_qa/get_qa_log", methods=['GET'])  # tags=["获取问答日志详情"]
    app.add_route(create_qa_log, "/api/local_doc_qa/create_qa_log", methods=['POST'])  # tags=["创建问答日志"]
    app.add_route(update_qa_log, "/api/local_doc_qa/update_qa_log", methods=['POST'])  # tags=["更新问答日志"]
    app.add_route(delete_qa_log, "/api/local_doc_qa/delete_qa_log", methods=['POST'])  # tags=["删除问答日志"]
    app.add_route(toggle_qa_favorite, "/api/local_doc_qa/toggle_qa_favorite", methods=['POST'])  # tags=["切换问答日志收藏状态"]

    # 机器人相关接口
    app.add_route(new_bot, "/api/local_doc_qa/new_bot", methods=['POST'])  # tags=["新建Bot"]
    app.add_route(delete_bot, "/api/local_doc_qa/delete_bot", methods=['POST'])  # tags=["删除Bot"]
    app.add_route(update_bot, "/api/local_doc_qa/update_bot", methods=['POST'])  # tags=["更新Bot"]
    app.add_route(get_bot_info, "/api/local_doc_qa/get_bot_info", methods=['POST'])  # tags=["获取Bot信息"]

    # 用户认证相关接口
    app.add_route(login, "/api/auth/login", methods=['POST'])  # tags=["用户登录"]
    app.add_route(refresh_token, "/api/auth/refresh_token", methods=['POST'])  # tags=["刷新令牌"]

    # 用户管理接口
    app.add_route(get_user_info, "/api/local_doc_qa/get_user_info", methods=['POST'])  # tags=["获取用户信息"]
    app.add_route(create_user, "/api/user/create", methods=['POST'])  # tags=["创建用户"]
    app.add_route(list_users, "/api/user/list", methods=['GET'])  # tags=["用户列表"]
    app.add_route(delete_user, "/api/user/delete", methods=['POST'])  # tags=["删除用户"]
    app.add_route(update_user_info, "/api/user/update", methods=['POST'])  # tags=["更新用户信息"]
    app.add_route(change_password, "/api/user/change_password", methods=['POST'])  # tags=["修改用户密码"]
    app.add_route(reset_password, "/api/user/reset_password", methods=['POST'])  # tags=["重置用户密码"]

    # 部门管理接口
    app.add_route(create_department, "/api/department/create", methods=['POST'])  # tags=["创建部门"]
    app.add_route(list_departments, "/api/department/list", methods=['GET'])  # tags=["部门列表"]
    app.add_route(update_department, "/api/department/update", methods=['POST'])  # tags=["更新部门"]
    app.add_route(delete_department, "/api/department/delete", methods=['POST'])  # tags=["删除部门"]
    app.add_route(add_user_to_department, "/api/department/add_user", methods=['POST'])  # tags=["添加用户到部门"]
    app.add_route(get_users_by_department, "/api/department/users", methods=['POST'])  # tags=["获取部门用户列表"]

    # 知识库权限管理接口
    app.add_route(get_kb_permission_data, "/api/kb/permission_data", methods=['POST'])  # tags=["获取知识库权限分配数据"]
    app.add_route(update_kb_permissions, "/api/kb/update_permissions", methods=['POST'])  # tags=["批量更新知识库权限"] 
    
    # 模型配置管理接口
    app.add_route(create_model_config, "/api/model/create", methods=['POST'])  # tags=["创建模型配置"]
    app.add_route(update_model_config, "/api/model/update", methods=['POST'])  # tags=["更新模型配置"]
    app.add_route(get_model_config, "/api/model/get", methods=['GET'])  # tags=["获取模型配置详情"]
    app.add_route(list_model_configs, "/api/model/list", methods=['GET'])  # tags=["获取模型配置列表"]
    app.add_route(delete_model_config, "/api/model/delete", methods=['POST'])  # tags=["删除模型配置"] 