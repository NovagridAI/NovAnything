import uuid

from sanic import request
from sanic.response import json as sanic_json

from qanything_kernel.connector.database.mysql.daos.department_dao import DepartmentDAO
from qanything_kernel.connector.database.mysql.daos.knowledge_base_dao import KnowledgeBaseDAO
from qanything_kernel.connector.database.mysql.daos.user_dao import UserDAO
from qanything_kernel.connector.database.mysql.models.department import Department
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.qanything_server.auth import auth_required, ROLE_SUPERADMIN
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.utils.general_utils import get_time_async, safe_get


@get_time_async
@auth_required(required_role=ROLE_SUPERADMIN)
async def create_department(req: request):
    """创建新部门 - 仅超级管理员可操作"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    dept_name = safe_get(req, 'dept_name')
    parent_dept_id = safe_get(req, 'parent_dept_id', None)
    description = safe_get(req, 'description', None)
    
    if not dept_name:
        return sanic_json({"code": 400, "msg": "部门名称不能为空"})

    # 初始化部门DAO
    dept_dao = local_doc_qa.milvus_summary.department_dao
    
    # 如果指定了父部门，检查父部门是否存在
    if parent_dept_id:
        if not dept_dao.check_department_exists(parent_dept_id):
            return sanic_json({"code": 404, "msg": "父部门不存在"})

    # 检查同一父部门下是否已存在同名部门
    if dept_dao.check_department_name_exists(dept_name, parent_dept_id):
        return sanic_json({"code": 400, "msg": "同一层级下已存在同名部门"})

    # 创建部门对象
    dept_id = f"dept_{uuid.uuid4().hex[:8]}"
    new_dept = Department(
        dept_id=dept_id,
        dept_name=dept_name,
        parent_dept_id=parent_dept_id,
        description=description
    )

    # 添加部门
    try:
        success = dept_dao.add_department(new_dept)
        if success:
            return sanic_json({
                "code": 200,
                "msg": "部门创建成功",
                "data": {
                    "dept_id": dept_id,
                    "dept_name": dept_name,
                    "parent_dept_id": parent_dept_id,
                    "description": description
                }
            })
        else:
            return sanic_json({"code": 500, "msg": "部门创建失败"})
    except Exception as e:
        debug_logger.error(f"创建部门失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"创建部门失败: {str(e)}"})


@get_time_async
@auth_required(required_role=ROLE_SUPERADMIN)
async def list_departments(req: request):
    """获取部门列表 - 仅超级管理员可操作"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')

    # 初始化部门DAO
    dept_dao = local_doc_qa.milvus_summary.department_dao

    # 获取所有部门
    departments = dept_dao.get_departments()

    # 构建包含父部门名称的结果
    result = []
    for dept in departments:
        dept_dict = {
            "dept_id": dept.dept_id,
            "dept_name": dept.dept_name,
            "parent_dept_id": dept.parent_dept_id,
            "description": dept.description,
            "creation_time": dept.creation_time.strftime("%Y-%m-%d %H:%M:%S") if dept.creation_time else None,
            "parent_dept_name": None
        }

        # 如果有父部门，获取父部门名称
        if dept.parent_dept_id:
            parent_dept = dept_dao.get_department_by_id(dept.parent_dept_id)
            if parent_dept:
                dept_dict["parent_dept_name"] = parent_dept.dept_name

        result.append(dept_dict)
    
    return sanic_json({"code": 200, "msg": "获取部门列表成功", "data": result})

@get_time_async
@auth_required(required_role=ROLE_SUPERADMIN)
async def update_department(req: request):
    """更新部门信息 - 仅超级管理员可操作"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    dept_id = safe_get(req, 'dept_id')
    dept_name = safe_get(req, 'dept_name')
    parent_dept_id = safe_get(req, 'parent_dept_id')
    description = safe_get(req, 'description')
    
    if not dept_id:
        return sanic_json({"code": 400, "msg": "部门ID不能为空"})

    # 初始化部门DAO
    dept_dao = local_doc_qa.milvus_summary.department_dao

    # 检查部门是否存在
    dept = dept_dao.get_department_by_id(dept_id)
    if not dept:
        return sanic_json({"code": 404, "msg": "部门不存在"})
    
    # 如果指定了父部门，检查父部门是否存在
    if parent_dept_id:
        if not dept_dao.check_department_exists(parent_dept_id):
            return sanic_json({"code": 404, "msg": "父部门不存在"})
        
        # 检查是否形成循环依赖
        if parent_dept_id == dept_id:
            return sanic_json({"code": 400, "msg": "部门不能将自己设为父部门"})

    # 更新部门信息
    if dept_name:
        dept.dept_name = dept_name
    if parent_dept_id is not None:  # 允许设置为None
        dept.parent_dept_id = parent_dept_id
    if description is not None:
        dept.description = description
    
    # 更新部门
    try:
        success = dept_dao.update_department(dept)
        if success:
            return sanic_json({"code": 200, "msg": "部门更新成功"})
        else:
            return sanic_json({"code": 500, "msg": "部门更新失败"})
    except Exception as e:
        debug_logger.error(f"更新部门失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"更新部门失败: {str(e)}"})

@get_time_async
@auth_required(required_role=ROLE_SUPERADMIN)
async def delete_department(req: request):
    """删除部门 - 仅超级管理员可操作"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    dept_id = safe_get(req, 'dept_id')
    
    if not dept_id:
        return sanic_json({"code": 400, "msg": "部门ID不能为空"})

    # 初始化部门DAO和用户DAO
    dept_dao = local_doc_qa.milvus_summary.department_dao
    user_dao = local_doc_qa.milvus_summary.user_dao
    kb_dao = local_doc_qa.milvus_summary.kb_dao
    
    # 检查部门是否存在
    if not dept_dao.check_department_exists(dept_id):
        return sanic_json({"code": 404, "msg": "部门不存在"})
    
    # 检查是否有子部门
    child_depts = dept_dao.get_child_departments(dept_id)
    if child_depts:
        return sanic_json({"code": 400, "msg": "该部门下有子部门，无法删除"})
    
    # 检查是否有用户属于该部门
    query = "SELECT user_id FROM User WHERE dept_id = %s"
    users_in_dept = user_dao.execute_query(query, (dept_id,), fetch=True)
    if users_in_dept:
        return sanic_json({"code": 400, "msg": "该部门下有用户，无法删除"})
    
    # 删除部门
    try:
        success = dept_dao.delete_department(dept_id)
        if success:
            # 同时删除该部门的所有知识库权限
            kb_dao.remove_subject_access('department', dept_id)
            return sanic_json({"code": 200, "msg": "部门删除成功"})
        else:
            return sanic_json({"code": 500, "msg": "部门删除失败"})
    except Exception as e:
        debug_logger.error(f"删除部门失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"删除部门失败: {str(e)}"})


@get_time_async
@auth_required(required_role=ROLE_SUPERADMIN)
async def add_user_to_department(req: request):
    """将用户添加到部门 - 批量操作 - 仅超级管理员可操作"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    target_user_ids = safe_get(req, 'target_user_ids')  # 要添加的用户ID列表
    dept_id = safe_get(req, 'dept_id')  # 部门ID

    # 检查参数
    if not target_user_ids or not isinstance(target_user_ids, list) or len(target_user_ids) == 0:
        return sanic_json({"code": 400, "msg": "用户ID列表不能为空"})

    if not dept_id:
        return sanic_json({"code": 400, "msg": "部门ID不能为空"})

    # 初始化DAO
    user_dao = local_doc_qa.milvus_summary.user_dao
    dept_dao = local_doc_qa.milvus_summary.department_dao

    # 检查部门是否存在
    if not dept_dao.check_department_exists(dept_id):
        return sanic_json({"code": 404, "msg": "部门不存在"})

    # 获取部门名称
    dept = dept_dao.get_department_by_id(dept_id)
    dept_name = dept.dept_name if dept else "未知部门"

    # 批量获取所有用户信息（一次数据库查询）
    user_ids_str = ','.join(['%s'] * len(target_user_ids))
    query = f"SELECT user_id, status, dept_id FROM User WHERE user_id IN ({user_ids_str})"
    user_results = user_dao.execute_query(query, tuple(target_user_ids), fetch=True, dictionary=True)

    # 分类处理
    users_to_update = []  # 需要更新的用户
    already_in_dept = []  # 已在部门的用户
    non_exist_users = []  # 不存在的用户
    inactive_users = []  # 非活跃用户

    # 将查询结果转为dict便于查找
    users_dict = {user['user_id']: user for user in user_results} if user_results else {}

    # 分类用户
    for uid in target_user_ids:
        if uid not in users_dict:
            non_exist_users.append(uid)
            continue

        user = users_dict[uid]
        if user['status'] != 'active':
            inactive_users.append(uid)
            continue

        if user['dept_id'] == dept_id:
            already_in_dept.append(uid)
            continue

        users_to_update.append(uid)

    # 如果有需要更新的用户，批量更新（一次数据库操作）
    success_count = 0
    if users_to_update:
        try:
            # 构建批量更新语句
            update_ids_str = ','.join(['%s'] * len(users_to_update))
            update_query = f"UPDATE User SET dept_id = %s WHERE user_id IN ({update_ids_str})"
            update_params = [dept_id] + users_to_update

            # 执行批量更新
            result = user_dao.execute_query(update_query, tuple(update_params), commit=True, check=True)
            success_count = len(users_to_update)

            # 记录日志
            for uid in users_to_update:
                debug_logger.info(f"用户 {uid} 被添加到部门 {dept_id}({dept_name})")
        except Exception as e:
            debug_logger.error(f"批量添加用户到部门失败: {str(e)}")
            return sanic_json({
                "code": 500,
                "msg": f"数据库操作失败: {str(e)}",
                "data": {
                    "dept_id": dept_id,
                    "dept_name": dept_name
                }
            })

    # 构建响应
    failed_users = []
    for uid in non_exist_users:
        failed_users.append({"user_id": uid, "reason": "用户不存在"})
    for uid in inactive_users:
        failed_users.append({"user_id": uid, "reason": "用户状态异常"})

    result = {
        "code": 200,
        "msg": f"成功添加 {success_count} 个用户到部门",
        "data": {
            "dept_id": dept_id,
            "dept_name": dept_name,
            "total": len(target_user_ids),
            "success_count": success_count,
            "already_in_dept_count": len(already_in_dept),
            "failed_count": len(failed_users),
            "already_in_dept": already_in_dept,
            "failed_users": failed_users
        }
    }

    # 如果全部失败，返回错误状态码
    if success_count == 0 and len(target_user_ids) > 0 and len(already_in_dept) == 0:
        result["code"] = 400
        result["msg"] = "所有用户添加失败"

    return sanic_json(result)


@get_time_async
@auth_required(required_role=ROLE_SUPERADMIN)
async def get_users_by_department(req: request):
    """获取部门下所有用户信息 - 仅超级管理员可操作"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    dept_id = safe_get(req, 'dept_id')  # 部门ID

    # 检查部门ID参数
    if not dept_id:
        return sanic_json({"code": 400, "msg": "部门ID不能为空"})

    # 初始化DAO
    user_dao = UserDAO(local_doc_qa.milvus_summary.db_connection)
    dept_dao = DepartmentDAO(local_doc_qa.milvus_summary.db_connection)

    # 检查部门是否存在
    if not dept_dao.check_department_exists(dept_id):
        return sanic_json({"code": 404, "msg": "部门不存在"})

    # 获取部门信息
    dept = dept_dao.get_department_by_id(dept_id)

    try:
        # 查询该部门下的所有用户
        query = """
            SELECT u.user_id, u.username, u.email, u.role, u.dept_id, u.status, u.creation_time
            FROM User u
            WHERE u.dept_id = %s
            ORDER BY u.creation_time
        """
        users = user_dao.execute_query(query, (dept_id,), fetch=True, dictionary=True)

        # 格式化结果
        formatted_users = []
        if users:
            for user in users:
                formatted_users.append({
                    "user_id": user['user_id'],
                    "username": user['username'],
                    "email": user['email'],
                    "role": user['role'],
                    "status": user['status'],
                    "creation_time": user['creation_time'].strftime("%Y-%m-%d %H:%M:%S") if user[
                        'creation_time'] else None
                })

        # 返回结果
        return sanic_json({
            "code": 200,
            "msg": "获取部门用户成功",
            "data": {
                "dept_id": dept_id,
                "dept_name": dept.dept_name,
                "user_count": len(formatted_users),
                "users": formatted_users
            }
        })
    except Exception as e:
        debug_logger.error(f"获取部门用户失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"获取部门用户失败: {str(e)}"})
