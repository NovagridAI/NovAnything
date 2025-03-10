import uuid
import bcrypt
import string
import random
from qanything_kernel.qanything_server.handler import auth_required
from qanything_kernel.utils.general_utils import get_time_async, safe_get
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.utils.custom_log import debug_logger, qa_logger
from sanic import request, response
from sanic.response import json as sanic_json


@get_time_async
@auth_required("admin")
async def create_user(req: request):
    """管理员创建新用户"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    
    # 新用户信息
    user_name = safe_get(req, 'user_name')
    email = safe_get(req, 'email', '')
    password = safe_get(req, 'password')  # 管理员直接设置密码
    dept_id = safe_get(req, 'dept_id', None)  # 可选，部门ID
    role = safe_get(req, 'role', 'user')  # 默认为普通用户
    
    if not user_name or not password:
        return sanic_json({"code": 400, "msg": "用户名、邮箱和密码不能为空"})
    
    # 检查邮箱是否已存在
    query = "SELECT user_id FROM User WHERE email = %s"
    if local_doc_qa.milvus_summary.execute_query_(query, (email,), fetch=True):
        return sanic_json({"code": 400, "msg": "该邮箱已被注册"})
    
    # 如果指定了部门，检查部门是否存在
    if dept_id:
        query = "SELECT dept_id FROM Department WHERE dept_id = %s"
        if not local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), fetch=True):
            return sanic_json({"code": 404, "msg": "部门不存在"})
    
    # 生成唯一的用户ID
    new_user_id = f"user_{uuid.uuid4().hex[:8]}"
    
    # 对密码进行哈希处理
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # 创建用户
    query = """
        INSERT INTO User (user_id, user_name, email, password, dept_id, role, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'active')
    """
    try:
        local_doc_qa.milvus_summary.execute_query_(
            query, (new_user_id, user_name, email, hashed_password, dept_id, role), commit=True
        )
        
        return sanic_json({
            "code": 200, 
            "msg": "用户创建成功", 
            "data": {
                "user_id": new_user_id,
                "user_name": user_name,
                "email": email,
                "dept_id": dept_id,
                "role": role
            }
        })
    except Exception as e:
        debug_logger.error(f"创建用户失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"创建用户失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def list_users(req: request):
    """获取用户列表"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    
    # 获取所有用户
    query = """
        SELECT u.user_id, u.user_name, u.email, u.role, u.dept_id, u.status, u.creation_time, d.dept_name
        FROM User u
        LEFT JOIN Department d ON u.dept_id = d.dept_id
        ORDER BY u.creation_time
    """
    users = local_doc_qa.milvus_summary.execute_query_(query, (), fetch=True)
    
    result = []
    for user in users:
        result.append({
            "user_id": user[0],
            "user_name": user[1],
            "email": user[2],
            "role": user[3],
            "dept_id": user[4],
            "dept_name": user[7],
            "status": user[5],
            "creation_time": user[6].strftime("%Y-%m-%d %H:%M:%S") if user[6] else None
        })
    
    return sanic_json({"code": 200, "msg": "获取用户列表成功", "data": result})


@get_time_async
@auth_required("admin")
async def delete_user(req: request):
    """删除用户（实际上是将状态设为inactive）"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    target_user_id = safe_get(req, 'target_user_id')  # 要删除的用户ID
    
    if not target_user_id:
        return sanic_json({"code": 400, "msg": "目标用户ID不能为空"})
    
    # 检查用户是否存在
    query = "SELECT user_id FROM User WHERE user_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    # 不允许删除自己
    if user_id == target_user_id:
        return sanic_json({"code": 400, "msg": "不能删除当前登录的用户"})
    
    # 将用户状态设为inactive
    query = "UPDATE User SET status = 'inactive' WHERE user_id = %s"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), commit=True)
        
        # 从所有用户组中移除该用户
        query = "DELETE FROM GroupMember WHERE user_id = %s"
        local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), commit=True)
        
        # 删除该用户的所有知识库权限
        query = "DELETE FROM KnowledgeBaseAccess WHERE subject_id = %s AND subject_type = 'user'"
        local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), commit=True)
        
        return sanic_json({"code": 200, "msg": "用户删除成功"})
    except Exception as e:
        debug_logger.error(f"删除用户失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"删除用户失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def assign_user_to_department(req: request):
    """将用户分配到部门"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    target_user_id = safe_get(req, 'target_user_id')  # 要分配的用户ID
    dept_id = safe_get(req, 'dept_id')  # 部门ID，如果为null则表示从部门中移除
    
    if not target_user_id:
        return sanic_json({"code": 400, "msg": "目标用户ID不能为空"})
    
    # 检查用户是否存在
    query = "SELECT user_id FROM User WHERE user_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    # 如果指定了部门，检查部门是否存在
    if dept_id:
        query = "SELECT dept_id FROM Department WHERE dept_id = %s"
        if not local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), fetch=True):
            return sanic_json({"code": 404, "msg": "部门不存在"})
    
    # 更新用户的部门
    query = "UPDATE User SET dept_id = %s WHERE user_id = %s"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (dept_id, target_user_id), commit=True)
        return sanic_json({"code": 200, "msg": "用户部门分配成功"})
    except Exception as e:
        debug_logger.error(f"分配用户到部门失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"分配用户到部门失败: {str(e)}"})
