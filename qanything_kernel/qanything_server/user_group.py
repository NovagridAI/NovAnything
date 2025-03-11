import uuid
from qanything_kernel.qanything_server.handler import auth_required
from qanything_kernel.utils.general_utils import get_time_async, safe_get
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.utils.custom_log import debug_logger
from sanic import request
from sanic.response import json as sanic_json


@get_time_async
@auth_required("admin")
async def create_group(req: request):
    """创建用户组"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    group_name = safe_get(req, 'group_name')
    
    if not group_name:
        return sanic_json({"code": 400, "msg": "用户组名称不能为空"})
    
    # 检查用户组名称是否已存在
    query = "SELECT group_id FROM UserGroup WHERE group_name = %s"
    if local_doc_qa.milvus_summary.execute_query_(query, (group_name,), fetch=True):
        return sanic_json({"code": 400, "msg": "该用户组名称已存在"})
    
    # 生成唯一的用户组ID
    group_id = f"group_{uuid.uuid4().hex[:8]}"
    
    # 创建用户组
    query = "INSERT INTO UserGroup (group_id, group_name) VALUES (%s, %s)"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (group_id, group_name), commit=True)
        return sanic_json({
            "code": 200, 
            "msg": "用户组创建成功", 
            "data": {
                "group_id": group_id, 
                "group_name": group_name
            }
        })
    except Exception as e:
        debug_logger.error(f"创建用户组失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"创建用户组失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def list_groups(req: request):
    """获取用户组列表"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    
    # 获取所有用户组
    query = """
        SELECT g.group_id, g.group_name, g.creation_time,
               COUNT(gm.user_id) as member_count
        FROM UserGroup g
        LEFT JOIN GroupMember gm ON g.group_id = gm.group_id
        GROUP BY g.group_id
        ORDER BY g.creation_time
    """
    groups = local_doc_qa.milvus_summary.execute_query_(query, (), fetch=True)
    
    result = []
    for group in groups:
        result.append({
            "group_id": group[0],
            "group_name": group[1],
            "creation_time": group[2].strftime("%Y-%m-%d %H:%M:%S") if group[2] else None,
            "member_count": group[3]
        })
    
    return sanic_json({"code": 200, "msg": "获取用户组列表成功", "data": result})


@get_time_async
@auth_required("admin")
async def update_group(req: request):
    """更新用户组信息"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    group_id = safe_get(req, 'group_id')
    group_name = safe_get(req, 'group_name')
    
    if not group_id:
        return sanic_json({"code": 400, "msg": "用户组ID不能为空"})
    
    # 检查用户组是否存在
    query = "SELECT group_id FROM UserGroup WHERE group_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (group_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户组不存在"})
    
    # 构建更新语句
    update_fields = []
    params = []
    
    if group_name:
        # 检查用户组名称是否已被其他用户组使用
        query = "SELECT group_id FROM UserGroup WHERE group_name = %s AND group_id != %s"
        if local_doc_qa.milvus_summary.execute_query_(query, (group_name, group_id), fetch=True):
            return sanic_json({"code": 400, "msg": "该用户组名称已被其他用户组使用"})
        update_fields.append("group_name = %s")
        params.append(group_name)
    
    if description is not None:  # 允许设置为空字符串
        update_fields.append("description = %s")
        params.append(description)
    
    if not update_fields:
        return sanic_json({"code": 400, "msg": "没有提供要更新的字段"})
    
    # 更新用户组
    query = f"UPDATE UserGroup SET {', '.join(update_fields)} WHERE group_id = %s"
    params.append(group_id)
    
    try:
        local_doc_qa.milvus_summary.execute_query_(query, tuple(params), commit=True)
        return sanic_json({"code": 200, "msg": "用户组更新成功"})
    except Exception as e:
        debug_logger.error(f"更新用户组失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"更新用户组失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def delete_group(req: request):
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
        # 先删除用户组成员关系
        member_query = "DELETE FROM GroupMember WHERE group_id = %s"
        local_doc_qa.milvus_summary.execute_query_(member_query, (group_id,), commit=True)
        
        # 删除用户组
        local_doc_qa.milvus_summary.execute_query_(query, (group_id,), commit=True)
        
        # 删除该用户组的所有知识库权限
        access_query = "DELETE FROM KnowledgeBaseAccess WHERE subject_id = %s AND subject_type = 'group'"
        local_doc_qa.milvus_summary.execute_query_(access_query, (group_id,), commit=True)
        
        return sanic_json({"code": 200, "msg": "用户组删除成功"})
    except Exception as e:
        debug_logger.error(f"删除用户组失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"删除用户组失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def add_user_to_group(req: request):
    """将用户添加到用户组"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    target_user_id = safe_get(req, 'target_user_id')  # 要添加的用户ID
    group_id = safe_get(req, 'group_id')  # 用户组ID
    
    if not target_user_id or not group_id:
        return sanic_json({"code": 400, "msg": "用户ID和用户组ID不能为空"})
    
    # 检查用户是否存在
    query = "SELECT user_id FROM User WHERE user_id = %s AND status = 'active'"
    if not local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户不存在或已被禁用"})
    
    # 检查用户组是否存在
    query = "SELECT group_id FROM UserGroup WHERE group_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (group_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户组不存在"})
    
    # 检查用户是否已在用户组中
    query = "SELECT user_id FROM GroupMember WHERE user_id = %s AND group_id = %s"
    if local_doc_qa.milvus_summary.execute_query_(query, (target_user_id, group_id), fetch=True):
        return sanic_json({"code": 400, "msg": "用户已在该用户组中"})
    
    # 添加用户到用户组
    query = "INSERT INTO GroupMember (user_id, group_id) VALUES (%s, %s)"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (target_user_id, group_id), commit=True)
        return sanic_json({"code": 200, "msg": "用户添加到用户组成功"})
    except Exception as e:
        debug_logger.error(f"添加用户到用户组失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"添加用户到用户组失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def remove_user_from_group(req: request):
    """从用户组中移除用户"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    target_user_id = safe_get(req, 'target_user_id')  # 要移除的用户ID
    group_id = safe_get(req, 'group_id')  # 用户组ID
    
    if not target_user_id or not group_id:
        return sanic_json({"code": 400, "msg": "用户ID和用户组ID不能为空"})
    
    # 检查用户是否在用户组中
    query = "SELECT user_id FROM GroupMember WHERE user_id = %s AND group_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (target_user_id, group_id), fetch=True):
        return sanic_json({"code": 404, "msg": "用户不在该用户组中"})
    
    # 从用户组中移除用户
    query = "DELETE FROM GroupMember WHERE user_id = %s AND group_id = %s"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (target_user_id, group_id), commit=True)
        return sanic_json({"code": 200, "msg": "从用户组中移除用户成功"})
    except Exception as e:
        debug_logger.error(f"从用户组中移除用户失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"从用户组中移除用户失败: {str(e)}"})


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
        SELECT u.user_id, u.user_name, u.email, u.role, u.dept_id, d.dept_name, gm.creation_time
        FROM GroupMember gm
        JOIN User u ON gm.user_id = u.user_id
        LEFT JOIN Department d ON u.dept_id = d.dept_id
        WHERE gm.group_id = %s AND u.status = 'active'
        ORDER BY gm.creation_time
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
            "dept_name": member[5],
            "creation_time": member[6].strftime("%Y-%m-%d %H:%M:%S") if member[6] else None
        })
    
    return sanic_json({"code": 200, "msg": "获取用户组成员列表成功", "data": result})
    