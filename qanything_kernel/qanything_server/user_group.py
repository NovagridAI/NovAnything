import uuid
from qanything_kernel.qanything_server.handler import auth_required
from qanything_kernel.utils.general_utils import get_time_async, safe_get
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.utils.custom_log import debug_logger, qa_logger
from sanic import request, response
from sanic.response import json as sanic_json


@get_time_async
@auth_required("admin")
async def create_user_group(req: request):
    """创建新用户组"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    group_name = safe_get(req, 'group_name')
    
    if not group_name:
        return sanic_json({"code": 400, "msg": "用户组名称不能为空"})
    
    # 生成唯一的用户组ID
    group_id = f"group_{uuid.uuid4().hex[:8]}"
    
    # 创建用户组
    query = "INSERT INTO UserGroup (group_id, group_name) VALUES (%s, %s)"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (group_id, group_name), commit=True)
        return sanic_json({
            "code": 200, 
            "msg": "用户组创建成功", 
            "data": {"group_id": group_id, "group_name": group_name}
        })
    except Exception as e:
        debug_logger.error(f"创建用户组失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"创建用户组失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def list_user_groups(req: request):
    """获取用户组列表"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    
    # 获取所有用户组
    query = """
        SELECT group_id, group_name, creation_time
        FROM UserGroup
        ORDER BY creation_time
    """
    groups = local_doc_qa.milvus_summary.execute_query_(query, (), fetch=True)
    
    result = []
    for group in groups:
        # 获取每个组的成员数量
        count_query = "SELECT COUNT(*) FROM GroupMember WHERE group_id = %s"
        count_result = local_doc_qa.milvus_summary.execute_query_(count_query, (group[0],), fetch=True)
        member_count = count_result[0][0] if count_result else 0
        
        result.append({
            "group_id": group[0],
            "group_name": group[1],
            "creation_time": group[2].strftime("%Y-%m-%d %H:%M:%S") if group[2] else None,
            "member_count": member_count
        })
    
    return sanic_json({"code": 200, "msg": "获取用户组列表成功", "data": result})


@get_time_async
@auth_required("admin")
async def delete_user_group(req: request):
    """删除用户组"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    group_id = safe_get(req, 'group_id')
    
    if not group_id:
        return sanic_json({"code": 400, "msg": "用户组ID不能为空"})
    
    # 检查用户组是否存在
    query = "SELECT group_id FROM UserGroup WHERE group_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (group_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户组不存在"})
    
    # 删除用户组
    query = "DELETE FROM UserGroup WHERE group_id = %s"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (group_id,), commit=True)
        
        # 同时删除该用户组的所有成员关系
        query = "DELETE FROM GroupMember WHERE group_id = %s"
        local_doc_qa.milvus_summary.execute_query_(query, (group_id,), commit=True)
        
        # 同时删除该用户组的所有知识库权限
        query = "DELETE FROM KnowledgeBaseAccess WHERE subject_id = %s AND subject_type = 'group'"
        local_doc_qa.milvus_summary.execute_query_(query, (group_id,), commit=True)
        
        return sanic_json({"code": 200, "msg": "用户组删除成功"})
    except Exception as e:
        debug_logger.error(f"删除用户组失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"删除用户组失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def add_user_to_group(req: request):
    """添加用户到用户组"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    target_user_id = safe_get(req, 'target_user_id')  # 要添加的用户ID
    group_id = safe_get(req, 'group_id')  # 用户组ID
    
    if not target_user_id or not group_id:
        return sanic_json({"code": 400, "msg": "用户ID和用户组ID不能为空"})
    
    # 检查用户是否存在
    query = "SELECT user_id FROM User WHERE user_id = %s AND status = 'active'"
    if not local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户不存在或已禁用"})
    
    # 检查用户组是否存在
    query = "SELECT group_id FROM UserGroup WHERE group_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (group_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户组不存在"})
    
    # 检查用户是否已在用户组中
    query = "SELECT id FROM GroupMember WHERE group_id = %s AND user_id = %s"
    if local_doc_qa.milvus_summary.execute_query_(query, (group_id, target_user_id), fetch=True):
        return sanic_json({"code": 400, "msg": "用户已在该用户组中"})
    
    # 添加用户到用户组
    query = "INSERT INTO GroupMember (group_id, user_id) VALUES (%s, %s)"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (group_id, target_user_id), commit=True)
        return sanic_json({"code": 200, "msg": "用户添加到用户组成功"})
    except Exception as e:
        debug_logger.error(f"添加用户到用户组失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"添加用户到用户组失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def remove_user_from_group(req: request):
    """从用户组移除用户"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    target_user_id = safe_get(req, 'target_user_id')  # 要移除的用户ID
    group_id = safe_get(req, 'group_id')  # 用户组ID
    
    if not target_user_id or not group_id:
        return sanic_json({"code": 400, "msg": "用户ID和用户组ID不能为空"})
    
    # 检查用户是否在用户组中
    query = "SELECT id FROM GroupMember WHERE group_id = %s AND user_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (group_id, target_user_id), fetch=True):
        return sanic_json({"code": 404, "msg": "用户不在该用户组中"})
    
    # 从用户组移除用户
    query = "DELETE FROM GroupMember WHERE group_id = %s AND user_id = %s"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (group_id, target_user_id), commit=True)
        return sanic_json({"code": 200, "msg": "用户从用户组移除成功"})
    except Exception as e:
        debug_logger.error(f"从用户组移除用户失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"从用户组移除用户失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def list_group_members(req: request):
    """获取用户组成员列表"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    group_id = safe_get(req, 'group_id')
    
    if not group_id:
        return sanic_json({"code": 400, "msg": "用户组ID不能为空"})
    
    # 检查用户组是否存在
    query = "SELECT group_id FROM UserGroup WHERE group_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (group_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户组不存在"})
    
    # 获取用户组成员
    query = """
        SELECT u.user_id, u.user_name, u.email, u.role, u.dept_id, d.dept_name
        FROM GroupMember gm
        JOIN User u ON gm.user_id = u.user_id
        LEFT JOIN Department d ON u.dept_id = d.dept_id
        WHERE gm.group_id = %s AND u.status = 'active'
    """
    members = local_doc_qa.milvus_summary.execute_query_(query, (group_id,), fetch=True)
    
    result = []
    for member in members:
        result.append({
            "user_id": member[0],
            "user_name": member[1],
            "email": member[2],
            "role": member[3],
            "dept_id": member[4],
            "dept_name": member[5]
        })
    
    return sanic_json({"code": 200, "msg": "获取用户组成员列表成功", "data": result})
    