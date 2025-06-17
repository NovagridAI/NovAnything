import uuid
import bcrypt
import string
import random
from qanything_kernel.qanything_server.auth import auth_required, ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_USER, verify_password
from qanything_kernel.utils.general_utils import get_time_async, safe_get
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.utils.custom_log import debug_logger, qa_logger
from qanything_kernel.connector.database.mysql.daos.user_dao import UserDAO
from qanything_kernel.connector.database.mysql.models.user import User
from sanic import request, response
from sanic.response import json as sanic_json


@get_time_async
@auth_required(required_role=ROLE_ADMIN)
async def create_user(req: request):
    """创建新用户 - 管理员及以上可操作"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    user_role = req.ctx.user["role"]
    
    # 新用户信息
    username = safe_get(req, 'username')
    email = safe_get(req, 'email', '')
    password = safe_get(req, 'password')  # 管理员直接设置密码
    dept_id = safe_get(req, 'dept_id', None)  # 可选，部门ID
    role = safe_get(req, 'role', 'user')  # 默认为普通用户
    
    if not username or not password:
        return sanic_json({"code": 400, "msg": "用户名和密码不能为空"})
    
    user_dao = UserDAO(local_doc_qa.milvus_summary.db_connection)
    dept_dao = local_doc_qa.milvus_summary.department_dao
    
    # 管理员权限检查
    if user_role == ROLE_ADMIN:
        # 管理员只能创建普通用户
        if role != 'user':
            return sanic_json({"code": 403, "msg": "管理员只能创建普通用户账号"})
        
        # 获取当前用户的部门信息
        admin_info = user_dao.get_user_by_id(user_id)
        if not admin_info or not admin_info.dept_id:
            return sanic_json({"code": 403, "msg": "您没有被分配到任何部门"})
        
        admin_dept_id = admin_info.dept_id
        
        # 如果没有指定部门，默认在管理员所属部门创建
        if not dept_id:
            dept_id = admin_dept_id
        else:
            # 检查指定的部门是否在管理员的管辖范围内
            from qanything_kernel.qanything_server.dept import _is_department_in_scope
            if not _is_department_in_scope(dept_dao, admin_dept_id, dept_id):
                return sanic_json({"code": 403, "msg": "您只能在自己管辖范围内的部门创建用户"})
    
    # 检查用户名是否已存在
    query = "SELECT user_id FROM User WHERE username = %s"
    username_exists = user_dao.execute_query(query, (username,), fetch=True)
    if username_exists:
        return sanic_json({"code": 400, "msg": "该用户名已被使用"})
    
    # 如果提供了邮箱，检查邮箱是否已存在
    if email:
        query = "SELECT user_id FROM User WHERE email = %s"
        email_exists = user_dao.execute_query(query, (email,), fetch=True)
        if email_exists:
            return sanic_json({"code": 400, "msg": "该邮箱已被注册"})
    
    # 如果指定了部门，检查部门是否存在
    if dept_id:
        query = "SELECT dept_id FROM Department WHERE dept_id = %s"
        dept_exists = user_dao.execute_query(query, (dept_id,), fetch=True)
        if not dept_exists:
            return sanic_json({"code": 404, "msg": "部门不存在"})
    
    # 生成唯一的用户ID
    new_user_id = f"user_{uuid.uuid4().hex[:8]}"
    
    # 对密码进行哈希处理
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # 创建用户
    new_user = User(
        user_id=new_user_id,
        username=username,
        email=email,
        password=hashed_password,
        dept_id=dept_id,
        role=role,
        status='active'
    )
    
    try:
        user_dao.create_user(new_user)
        
        return sanic_json({
            "code": 200, 
            "msg": "用户创建成功", 
            "data": {
                "user_id": new_user_id,
                "username": username,
                "email": email,
                "dept_id": dept_id,
                "role": role
            }
        })
    except Exception as e:
        debug_logger.error(f"创建用户失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"创建用户失败: {str(e)}"})


@get_time_async
@auth_required(required_role=ROLE_ADMIN)
async def list_users(req: request):
    """获取用户列表 - 管理员及以上可操作"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    user_role = req.ctx.user["role"]
    
    # 确保 user_id 是字符串而不是列表
    if isinstance(user_id, list) and len(user_id) > 0:
        user_id = user_id[0]
        debug_logger.info(f"list_users: 用户ID从列表转换为字符串: {user_id}")
    elif not isinstance(user_id, str):
        debug_logger.error(f"list_users: 无效的用户ID类型: {type(user_id)}, 值: {user_id}")
        return sanic_json({"code": 400, "msg": "无效的用户ID"})
    
    user_dao = UserDAO(local_doc_qa.milvus_summary.db_connection)
    dept_dao = local_doc_qa.milvus_summary.department_dao
    
    if user_role == ROLE_SUPERADMIN:
        # 超级管理员可以看到所有用户
        query = """
            SELECT u.user_id, u.username, u.email, u.role, u.dept_id, u.status, u.creation_time, d.dept_name
            FROM User u
            LEFT JOIN Department d ON u.dept_id = d.dept_id
            ORDER BY u.creation_time
        """
        users = user_dao.execute_query(query, (), fetch=True)
    else:
        # 管理员只能看到自己管辖范围内的用户
        # 获取当前用户的部门信息
        user_info = user_dao.get_user_by_id(user_id)
        if not user_info or not user_info.dept_id:
            return sanic_json({"code": 403, "msg": "您没有被分配到任何部门"})
        
        user_dept_id = user_info.dept_id
        
        # 获取管辖范围内的所有部门ID
        from qanything_kernel.qanything_server.dept import _get_departments_in_scope
        dept_ids = _get_departments_in_scope(dept_dao, user_dept_id)
        
        # 查询这些部门中的所有用户
        dept_ids_str = ','.join(['%s'] * len(dept_ids))
        query = f"""
            SELECT u.user_id, u.username, u.email, u.role, u.dept_id, u.status, u.creation_time, d.dept_name
            FROM User u
            LEFT JOIN Department d ON u.dept_id = d.dept_id
            WHERE u.dept_id IN ({dept_ids_str})
            ORDER BY u.creation_time
        """
        users = user_dao.execute_query(query, tuple(dept_ids), fetch=True)
    
    result = []
    for user in users:
        result.append({
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "role": user[3],
            "dept_id": user[4],
            "dept_name": user[7],
            "status": user[5],
            "creation_time": user[6].strftime("%Y-%m-%d %H:%M:%S") if user[6] else None
        })
    
    return sanic_json({"code": 200, "msg": "获取用户列表成功", "data": result})


@get_time_async
@auth_required(required_role=ROLE_ADMIN)
async def delete_user(req: request):
    """彻底删除用户及其所有数据 - 管理员及以上可操作"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    user_role = req.ctx.user["role"]
    target_user_id = safe_get(req, 'target_user_id')  # 要删除的用户ID
    
    if not target_user_id:
        return sanic_json({"code": 400, "msg": "目标用户ID不能为空"})
    
    user_dao = UserDAO(local_doc_qa.milvus_summary.db_connection)
    dept_dao = local_doc_qa.milvus_summary.department_dao
    
    # 检查用户是否存在
    target_user = user_dao.get_user_by_id(target_user_id)
    if not target_user:
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    # 不允许删除自己
    if user_id == target_user_id:
        return sanic_json({"code": 400, "msg": "不能删除当前登录的用户"})
    
    # 管理员权限检查
    if user_role == ROLE_ADMIN:
        # 管理员只能删除普通用户，不能删除管理员或超级管理员
        if target_user.role in [ROLE_ADMIN, ROLE_SUPERADMIN]:
            return sanic_json({"code": 403, "msg": "您不能删除管理员账号"})
        
        # 获取当前用户的部门信息
        admin_info = user_dao.get_user_by_id(user_id)
        if not admin_info or not admin_info.dept_id:
            return sanic_json({"code": 403, "msg": "您没有被分配到任何部门"})
        
        admin_dept_id = admin_info.dept_id
        
        # 检查目标用户是否在管理员的管辖范围内
        if not target_user.dept_id:
            return sanic_json({"code": 403, "msg": "目标用户没有部门信息，无法删除"})
        
        from qanything_kernel.qanything_server.dept import _is_department_in_scope
        if not _is_department_in_scope(dept_dao, admin_dept_id, target_user.dept_id):
            return sanic_json({"code": 403, "msg": "您只能删除自己管辖范围内的用户"})
    
    try:
        debug_logger.info(f"开始删除用户 {target_user_id} 的所有数据")
        
        # 1. 删除用户的所有知识库（这会级联删除相关文件）
        query = "SELECT kb_id FROM KnowledgeBase WHERE user_id = %s AND deleted = 0"
        kb_results = user_dao.execute_query(query, (target_user_id,), fetch=True)
        if kb_results:
            kb_ids = [row[0] for row in kb_results]
            debug_logger.info(f"删除用户 {target_user_id} 的 {len(kb_ids)} 个知识库")
            
            # 标记知识库为已删除
            kb_ids_str = ','.join(['%s'] * len(kb_ids))
            query = f"UPDATE KnowledgeBase SET deleted = 1 WHERE user_id = %s AND kb_id IN ({kb_ids_str})"
            user_dao.execute_query(query, (target_user_id,) + tuple(kb_ids), commit=True)
            
            # 标记知识库下的所有文件为已删除
            query = f"UPDATE File SET deleted = 1 WHERE kb_id IN ({kb_ids_str})"
            user_dao.execute_query(query, tuple(kb_ids), commit=True)
        
        # 2. 获取用户的所有文件ID，用于后续删除相关文档
        query = "SELECT file_id FROM File WHERE user_id = %s"
        file_results = user_dao.execute_query(query, (target_user_id,), fetch=True)
        file_ids = [row[0] for row in file_results] if file_results else []
        
        # 删除用户的所有文件记录和文件图片记录
        query = "DELETE FROM File WHERE user_id = %s"
        user_dao.execute_query(query, (target_user_id,), commit=True)
        
        query = "DELETE FROM FileImages WHERE user_id = %s"
        user_dao.execute_query(query, (target_user_id,), commit=True)
        
        # 删除与用户文件相关的所有文档记录
        if file_ids:
            for file_id in file_ids:
                query = "DELETE FROM Documents WHERE doc_id LIKE %s"
                user_dao.execute_query(query, (f"{file_id}_%",), commit=True)
        
        # 3. 删除用户的所有FAQ记录
        query = "DELETE FROM FAQ WHERE user_id = %s"
        user_dao.execute_query(query, (target_user_id,), commit=True)
        
        # 4. 删除用户的所有问答日志
        query = "DELETE FROM QALog WHERE user_id = %s"
        user_dao.execute_query(query, (target_user_id,), commit=True)
        
        # 5. 删除用户的所有机器人
        query = "DELETE FROM Bot WHERE user_id = %s"
        user_dao.execute_query(query, (target_user_id,), commit=True)
        
        # 6. 删除用户的所有模型配置
        query = "DELETE FROM ModelConfig WHERE user_id = %s"
        user_dao.execute_query(query, (target_user_id,), commit=True)
        
        # 7. 从所有用户组中移除该用户
        query = "DELETE FROM GroupMember WHERE user_id = %s"
        user_dao.execute_query(query, (target_user_id,), commit=True)
        
        # 8. 删除该用户的所有知识库访问权限
        query = "DELETE FROM KnowledgeBaseAccess WHERE subject_id = %s AND subject_type = 'user'"
        user_dao.execute_query(query, (target_user_id,), commit=True)
        
        # 9. 删除用户被授予的知识库权限
        query = "DELETE FROM KnowledgeBaseAccess WHERE granted_by = %s"
        user_dao.execute_query(query, (target_user_id,), commit=True)
        
        # 10. 最后删除用户记录本身
        query = "DELETE FROM User WHERE user_id = %s"
        user_dao.execute_query(query, (target_user_id,), commit=True)
        
        debug_logger.info(f"成功删除用户 {target_user_id} 及其所有数据")
        return sanic_json({"code": 200, "msg": "用户及其所有数据删除成功"})
        
    except Exception as e:
        debug_logger.error(f"删除用户失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"删除用户失败: {str(e)}"})


@get_time_async
@auth_required(required_role=ROLE_ADMIN)
async def assign_user_to_department(req: request):
    """将用户分配到部门 - 管理员及以上可操作"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    user_role = req.ctx.user["role"]
    target_user_id = safe_get(req, 'target_user_id')  # 要分配的用户ID
    dept_id = safe_get(req, 'dept_id')  # 部门ID，如果为null则表示从部门中移除
    
    if not target_user_id:
        return sanic_json({"code": 400, "msg": "目标用户ID不能为空"})
    
    user_dao = UserDAO(local_doc_qa.milvus_summary.db_connection)
    dept_dao = local_doc_qa.milvus_summary.department_dao
    
    # 检查用户是否存在
    target_user = user_dao.get_user_by_id(target_user_id)
    if not target_user:
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    # 管理员权限检查
    if user_role == ROLE_ADMIN:
        # 管理员只能移动普通用户
        if target_user.role in [ROLE_ADMIN, ROLE_SUPERADMIN]:
            return sanic_json({"code": 403, "msg": "您不能移动管理员账号"})
        
        # 获取当前用户的部门信息
        admin_info = user_dao.get_user_by_id(user_id)
        if not admin_info or not admin_info.dept_id:
            return sanic_json({"code": 403, "msg": "您没有被分配到任何部门"})
        
        admin_dept_id = admin_info.dept_id
        
        # 检查目标用户当前是否在管理员的管辖范围内
        if target_user.dept_id:
            from qanything_kernel.qanything_server.dept import _is_department_in_scope
            if not _is_department_in_scope(dept_dao, admin_dept_id, target_user.dept_id):
                return sanic_json({"code": 403, "msg": "您只能移动自己管辖范围内的用户"})
        
        # 检查目标部门是否在管理员的管辖范围内
        if dept_id:
            if not _is_department_in_scope(dept_dao, admin_dept_id, dept_id):
                return sanic_json({"code": 403, "msg": "您只能将用户移动到自己管辖范围内的部门"})
    
    # 如果指定了部门，检查部门是否存在
    if dept_id:
        query = "SELECT dept_id FROM Department WHERE dept_id = %s"
        dept_exists = user_dao.execute_query(query, (dept_id,), fetch=True)
        if not dept_exists:
            return sanic_json({"code": 404, "msg": "部门不存在"})
    
    # 更新用户的部门
    try:
        target_user.dept_id = dept_id
        user_dao.update_user(target_user)
        return sanic_json({"code": 200, "msg": "用户部门分配成功"})
    except Exception as e:
        debug_logger.error(f"分配用户到部门失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"分配用户到部门失败: {str(e)}"})


@get_time_async
@auth_required(required_role=ROLE_USER)
async def get_user_info(req: request):
    """获取用户信息 - 普通用户可获取自己的信息，管理员可获取任意用户信息"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    current_user_id = safe_get(req, 'user_id')  # 当前操作用户
    target_user_id = safe_get(req, 'target_user_id', current_user_id)  # 要查询的用户ID，默认为当前用户
    
    user_dao = UserDAO(local_doc_qa.milvus_summary.db_connection)
    
    # 如果要查询其他用户的信息，需要检查当前用户权限
    if target_user_id != current_user_id and req.ctx.user["role"] not in ['admin', 'superadmin']:
        return sanic_json({"code": 403, "msg": "没有权限查询其他用户的信息"})
    
    # 获取用户信息
    user = user_dao.get_user_by_id(target_user_id)
    if not user:
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    # 获取部门名称
    dept_name = None
    if user.dept_id:
        query = "SELECT dept_name FROM Department WHERE dept_id = %s"
        dept_result = user_dao.execute_query(query, (user.dept_id,), fetch=True)
        if dept_result and len(dept_result) > 0:
            dept_name = dept_result[0][0]
    
    # 获取用户所属的用户组
    query = """
        SELECT g.group_id, g.group_name 
        FROM UserGroup g
        JOIN GroupMember m ON g.group_id = m.group_id
        WHERE m.user_id = %s AND m.status = 'active'
    """
    groups_result = user_dao.execute_query(query, (user.user_id,), fetch=True)
    user_groups = [{"group_id": row[0], "group_name": row[1]} for row in groups_result] if groups_result else []
    
    return sanic_json({
        "code": 200, 
        "msg": "获取用户信息成功", 
        "data": {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "dept_id": user.dept_id,
            "dept_name": dept_name,
            "status": user.status,
            "groups": user_groups
        }
    })


@get_time_async
@auth_required(required_role=ROLE_USER)
async def change_password(req: request):
    """用户修改自己的密码"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    old_password = safe_get(req, 'old_password')  # 旧密码
    new_password = safe_get(req, 'new_password')  # 新密码
    
    if not old_password or not new_password:
        return sanic_json({"code": 400, "msg": "旧密码和新密码不能为空"})
    
    user_dao = UserDAO(local_doc_qa.milvus_summary.db_connection)
    
    # 获取用户信息
    user = user_dao.get_user_by_id(user_id)
    if not user:
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    # 验证旧密码
    if not verify_password(old_password, user.password):
        return sanic_json({"code": 401, "msg": "旧密码不正确"})
    
    # 更新密码
    try:
        # 对新密码进行哈希处理
        hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        user.password = hashed_password
        user_dao.update_user(user)
        
        return sanic_json({"code": 200, "msg": "密码修改成功"})
    except Exception as e:
        debug_logger.error(f"修改密码失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"修改密码失败: {str(e)}"})


@get_time_async
@auth_required(required_role=ROLE_USER)
async def reset_password(req: request):
    """用户重置自己的密码"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    new_password = safe_get(req, 'new_password')  # 新密码
    
    if not new_password:
        return sanic_json({"code": 400, "msg": "新密码不能为空"})
    
    user_dao = UserDAO(local_doc_qa.milvus_summary.db_connection)
    
    # 获取用户信息
    user = user_dao.get_user_by_id(user_id)
    if not user:
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    # 更新密码
    try:
        # 对新密码进行哈希处理
        hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        user.password = hashed_password
        user_dao.update_user(user)
        
        debug_logger.info(f"用户 {user_id} 重置了密码")
        return sanic_json({"code": 200, "msg": "密码重置成功"})
    except Exception as e:
        debug_logger.error(f"重置密码失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"重置密码失败: {str(e)}"})


@get_time_async
@auth_required(required_role=ROLE_ADMIN)
async def update_user_info(req: request):
    """更新用户信息 - 管理员及以上可操作
    支持更新用户名、邮箱和角色，这些字段都是可选的
    """
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    admin_user_id = safe_get(req, 'user_id')  # 当前操作用户（管理员）
    user_role = req.ctx.user["role"]
    target_user_id = safe_get(req, 'target_user_id')  # 要更新的用户ID
    
    # 获取要更新的字段（所有字段都是可选的）
    username = safe_get(req, 'username', None)
    email = safe_get(req, 'email', None)
    role = safe_get(req, 'role', None)
    
    if not target_user_id:
        return sanic_json({"code": 400, "msg": "目标用户ID不能为空"})
    
    # 至少需要一个要更新的字段
    if not any([username, email, role]):
        return sanic_json({"code": 400, "msg": "至少需要提供一个要更新的字段"})
    
    user_dao = UserDAO(local_doc_qa.milvus_summary.db_connection)
    dept_dao = local_doc_qa.milvus_summary.department_dao
    
    # 检查目标用户是否存在
    target_user = user_dao.get_user_by_id(target_user_id)
    if not target_user:
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    # 管理员权限检查
    if user_role == ROLE_ADMIN:
        # 管理员不能修改管理员或超级管理员账号
        if target_user.role in [ROLE_ADMIN, ROLE_SUPERADMIN]:
            return sanic_json({"code": 403, "msg": "您不能修改管理员账号"})
        
        # 管理员不能修改用户角色
        if role:
            return sanic_json({"code": 403, "msg": "您没有权限修改用户角色"})
        
        # 获取当前用户的部门信息
        admin_info = user_dao.get_user_by_id(admin_user_id)
        if not admin_info or not admin_info.dept_id:
            return sanic_json({"code": 403, "msg": "您没有被分配到任何部门"})
        
        admin_dept_id = admin_info.dept_id
        
        # 检查目标用户是否在管理员的管辖范围内
        if not target_user.dept_id:
            return sanic_json({"code": 403, "msg": "目标用户没有部门信息，无法修改"})
        
        from qanything_kernel.qanything_server.dept import _is_department_in_scope
        if not _is_department_in_scope(dept_dao, admin_dept_id, target_user.dept_id):
            return sanic_json({"code": 403, "msg": "您只能修改自己管辖范围内的用户"})
    
    # 如果更新用户名，检查新用户名是否已存在
    if username and username != target_user.username:
        query = "SELECT user_id FROM User WHERE username = %s AND user_id != %s"
        username_exists = user_dao.execute_query(query, (username, target_user_id), fetch=True)
        if username_exists:
            return sanic_json({"code": 400, "msg": "该用户名已被使用"})
    
    # 如果更新邮箱，检查新邮箱是否已存在
    if email and email != target_user.email:
        query = "SELECT user_id FROM User WHERE email = %s AND user_id != %s"
        email_exists = user_dao.execute_query(query, (email, target_user_id), fetch=True)
        if email_exists:
            return sanic_json({"code": 400, "msg": "该邮箱已被注册"})
    
    # 如果更新角色，验证角色是否有效
    valid_roles = ['user', 'admin', 'superadmin']
    if role and role not in valid_roles:
        return sanic_json({"code": 400, "msg": f"无效的角色，可选值: {', '.join(valid_roles)}"})
    
    # 更新用户信息
    try:
        if username:
            target_user.username = username
        if email:
            target_user.email = email
        if role:
            target_user.role = role
        
        user_dao.update_user(target_user)
        
        # 返回更新后的用户信息
        return sanic_json({
            "code": 200, 
            "msg": "用户信息更新成功", 
            "data": {
                "user_id": target_user.user_id,
                "username": target_user.username,
                "email": target_user.email,
                "role": target_user.role
            }
        })
    except Exception as e:
        debug_logger.error(f"更新用户信息失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"更新用户信息失败: {str(e)}"})


@get_time_async
@auth_required(required_role=ROLE_ADMIN)
async def get_available_departments_for_user_move(req: request):
    """获取用户移动时可选的部门列表 - 管理员及以上可操作"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    user_role = req.ctx.user["role"]

    # 初始化DAO
    user_dao = UserDAO(local_doc_qa.milvus_summary.db_connection)
    dept_dao = local_doc_qa.milvus_summary.department_dao

    if user_role == ROLE_SUPERADMIN:
        # 超级管理员可以将用户移动到任何部门
        departments = dept_dao.get_departments()
    else:
        # 管理员只能将用户移动到自己管辖范围内的部门
        # 获取当前用户的部门信息
        user_info = user_dao.get_user_by_id(user_id)
        if not user_info or not user_info.dept_id:
            return sanic_json({"code": 403, "msg": "您没有被分配到任何部门"})
        
        user_dept_id = user_info.dept_id
        
        # 获取管辖范围内的所有部门ID
        from qanything_kernel.qanything_server.dept import _get_departments_in_scope
        dept_ids = _get_departments_in_scope(dept_dao, user_dept_id)
        
        # 获取部门详细信息
        departments = []
        for dept_id in dept_ids:
            dept = dept_dao.get_department_by_id(dept_id)
            if dept:
                departments.append(dept)

    # 构建结果，包含部门的层级信息
    result = []
    for dept in departments:
        # 获取父部门名称
        parent_dept_name = None
        if dept.parent_dept_id:
            parent_dept = dept_dao.get_department_by_id(dept.parent_dept_id)
            if parent_dept:
                parent_dept_name = parent_dept.dept_name

        result.append({
            "dept_id": dept.dept_id,
            "dept_name": dept.dept_name,
            "parent_dept_id": dept.parent_dept_id,
            "parent_dept_name": parent_dept_name
        })
    
    return sanic_json({"code": 200, "msg": "获取可选部门列表成功", "data": result})
