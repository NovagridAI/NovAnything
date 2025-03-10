from qanything_kernel.qanything_server.handler import auth_required
from qanything_kernel.utils.general_utils import get_time_async, safe_get
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.utils.custom_log import debug_logger, qa_logger
from sanic import request, response
from sanic.response import json as sanic_json


@get_time_async
@auth_required("admin")
async def set_kb_permission(req: request):
    """设置知识库访问权限"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    kb_id = safe_get(req, 'kb_id')  # 知识库ID
    subject_id = safe_get(req, 'subject_id')  # 主体ID（用户/部门/用户组）
    subject_type = safe_get(req, 'subject_type')  # 主体类型（user/department/group）
    permission_type = safe_get(req, 'permission_type')  # 权限类型（read/write/admin）
    
    debug_logger.info(f"设置知识库权限 - 操作用户: {user_id}, 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}, 权限: {permission_type}")
    
    if not kb_id or not subject_id or not subject_type or not permission_type:
        debug_logger.error(f"参数错误 - kb_id: {kb_id}, subject_id: {subject_id}, subject_type: {subject_type}, permission_type: {permission_type}")
        return sanic_json({"code": 400, "msg": "知识库ID、主体ID、主体类型和权限类型不能为空"})
    
    # 验证主体类型
    if subject_type not in ['user', 'department', 'group']:
        debug_logger.error(f"无效的主体类型: {subject_type}")
        return sanic_json({"code": 400, "msg": "无效的主体类型，必须是user、department或group"})
    
    # 验证权限类型
    if permission_type not in ['read', 'write', 'admin']:
        debug_logger.error(f"无效的权限类型: {permission_type}")
        return sanic_json({"code": 400, "msg": "无效的权限类型，必须是read、write或admin"})
    
    # 设置权限
    result = local_doc_qa.milvus_summary.set_kb_access(kb_id, subject_id, subject_type, permission_type, user_id)
    if result:
        debug_logger.info(f"知识库权限设置成功 - 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}, 权限: {permission_type}")
        return sanic_json({"code": 200, "msg": "设置知识库访问权限成功"})
    else:
        debug_logger.error(f"知识库权限设置失败 - 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}, 权限: {permission_type}")
        return sanic_json({"code": 500, "msg": "设置知识库访问权限失败"})


@get_time_async
@auth_required("admin")
async def remove_kb_permission(req: request):
    """移除知识库访问权限"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    kb_id = safe_get(req, 'kb_id')  # 知识库ID
    subject_id = safe_get(req, 'subject_id')  # 主体ID（用户/部门/用户组）
    subject_type = safe_get(req, 'subject_type')  # 主体类型（user/department/group）
    
    debug_logger.info(f"移除知识库权限 - 操作用户: {user_id}, 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}")
    
    if not kb_id or not subject_id or not subject_type:
        debug_logger.error(f"参数错误 - kb_id: {kb_id}, subject_id: {subject_id}, subject_type: {subject_type}")
        return sanic_json({"code": 400, "msg": "知识库ID、主体ID和主体类型不能为空"})
    
    # 验证主体类型
    if subject_type not in ['user', 'department', 'group']:
        debug_logger.error(f"无效的主体类型: {subject_type}")
        return sanic_json({"code": 400, "msg": "无效的主体类型，必须是user、department或group"})
    
    # 检查知识库是否存在
    query = "SELECT kb_id, user_id FROM KnowledgeBase WHERE kb_id = %s AND deleted = 0"
    kb_info = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    if not kb_info:
        debug_logger.error(f"知识库不存在或已删除: {kb_id}")
        return sanic_json({"code": 404, "msg": "知识库不存在或已删除"})
    
    # 不允许删除所有者的admin权限
    if subject_type == 'user' and subject_id == kb_info[0][1]:
        query = "SELECT permission_type FROM KnowledgeBaseAccess WHERE kb_id = %s AND subject_id = %s AND subject_type = %s"
        perm = local_doc_qa.milvus_summary.execute_query_(query, (kb_id, subject_id, subject_type), fetch=True)
        if perm and perm[0][0] == 'admin':
            debug_logger.error(f"尝试删除知识库所有者的管理权限 - 知识库: {kb_id}, 用户: {subject_id}")
            return sanic_json({"code": 403, "msg": "不能删除知识库所有者的管理权限"})
    
    # 删除权限
    query = "DELETE FROM KnowledgeBaseAccess WHERE kb_id = %s AND subject_id = %s AND subject_type = %s"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (kb_id, subject_id, subject_type), commit=True)
        debug_logger.info(f"知识库权限移除成功 - 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}")
        return sanic_json({"code": 200, "msg": "移除知识库访问权限成功"})
    except Exception as e:
        debug_logger.error(f"移除知识库权限失败: {str(e)} - 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}")
        return sanic_json({"code": 500, "msg": f"移除知识库访问权限失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def list_kb_permissions(req: request):
    """获取知识库权限列表"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    kb_id = safe_get(req, 'kb_id')
    
    debug_logger.info(f"获取知识库权限列表 - 操作用户: {user_id}, 知识库: {kb_id}")
    
    if not kb_id:
        debug_logger.error("知识库ID不能为空")
        return sanic_json({"code": 400, "msg": "知识库ID不能为空"})
    
    # 检查知识库是否存在
    query = "SELECT kb_id FROM KnowledgeBase WHERE kb_id = %s AND deleted = 0"
    if not local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True):
        debug_logger.error(f"知识库不存在或已删除: {kb_id}")
        return sanic_json({"code": 404, "msg": "知识库不存在或已删除"})
    
    # 获取用户权限
    query = """
        SELECT kba.subject_id, 'user' as subject_type, kba.permission_type, 
               u.user_name as subject_name, kba.granted_by, kba.granted_at,
               gu.user_name as granted_by_name
        FROM KnowledgeBaseAccess kba
        JOIN User u ON kba.subject_id = u.user_id
        LEFT JOIN User gu ON kba.granted_by = gu.user_id
        WHERE kba.kb_id = %s AND kba.subject_type = 'user'
    """
    user_permissions = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    debug_logger.info(f"获取到用户权限数量: {len(user_permissions)}")
    
    # 获取部门权限
    query = """
        SELECT kba.subject_id, 'department' as subject_type, kba.permission_type, 
               d.dept_name as subject_name, kba.granted_by, kba.granted_at,
               u.user_name as granted_by_name
        FROM KnowledgeBaseAccess kba
        JOIN Department d ON kba.subject_id = d.dept_id
        LEFT JOIN User u ON kba.granted_by = u.user_id
        WHERE kba.kb_id = %s AND kba.subject_type = 'department'
    """
    dept_permissions = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    debug_logger.info(f"获取到部门权限数量: {len(dept_permissions)}")
    
    # 获取用户组权限
    query = """
        SELECT kba.subject_id, 'group' as subject_type, kba.permission_type, 
               g.group_name as subject_name, kba.granted_by, kba.granted_at,
               u.user_name as granted_by_name
        FROM KnowledgeBaseAccess kba
        JOIN UserGroup g ON kba.subject_id = g.group_id
        LEFT JOIN User u ON kba.granted_by = u.user_id
        WHERE kba.kb_id = %s AND kba.subject_type = 'group'
    """
    group_permissions = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    debug_logger.info(f"获取到用户组权限数量: {len(group_permissions)}")
    
    # 合并结果
    all_permissions = []
    
    for perm in user_permissions + dept_permissions + group_permissions:
        all_permissions.append({
            "subject_id": perm[0],
            "subject_type": perm[1],
            "permission_type": perm[2],
            "subject_name": perm[3],
            "granted_by": perm[4],
            "granted_at": perm[5].strftime("%Y-%m-%d %H:%M:%S") if perm[5] else None,
            "granted_by_name": perm[6]
        })
    
    debug_logger.info(f"获取知识库权限列表成功 - 知识库: {kb_id}, 总权限数量: {len(all_permissions)}")
    return sanic_json({"code": 200, "msg": "获取知识库权限列表成功", "data": all_permissions})


@get_time_async
@auth_required("admin")
async def batch_set_kb_permissions(req: request):
    """批量设置知识库权限（用于知识库创建或设置时）"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    kb_id = safe_get(req, 'kb_id')  # 知识库ID
    permissions = safe_get(req, 'permissions')  # 权限列表，格式为[{subject_id, subject_type, permission_type}, ...]
    
    debug_logger.info(f"批量设置知识库权限 - 操作用户: {user_id}, 知识库: {kb_id}, 权限数量: {len(permissions) if permissions else 0}")
    
    if not kb_id or not permissions or not isinstance(permissions, list):
        debug_logger.error(f"参数错误 - kb_id: {kb_id}, permissions: {permissions}")
        return sanic_json({"code": 400, "msg": "知识库ID和权限列表不能为空"})
    
    # 检查知识库是否存在
    query = "SELECT kb_id FROM KnowledgeBase WHERE kb_id = %s AND deleted = 0"
    if not local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True):
        debug_logger.error(f"知识库不存在或已删除: {kb_id}")
        return sanic_json({"code": 404, "msg": "知识库不存在或已删除"})
    
    success_count = 0
    failed_count = 0
    
    for perm in permissions:
        subject_id = perm.get('subject_id')
        subject_type = perm.get('subject_type')
        permission_type = perm.get('permission_type')
        
        if not subject_id or not subject_type or not permission_type:
            debug_logger.error(f"权限参数不完整 - subject_id: {subject_id}, subject_type: {subject_type}, permission_type: {permission_type}")
            failed_count += 1
            continue
        
        # 验证主体类型
        if subject_type not in ['user', 'department', 'group']:
            debug_logger.error(f"无效的主体类型: {subject_type}")
            failed_count += 1
            continue
        
        # 验证权限类型
        if permission_type not in ['read', 'write', 'admin']:
            debug_logger.error(f"无效的权限类型: {permission_type}")
            failed_count += 1
            continue
        
        # 设置权限
        result = local_doc_qa.milvus_summary.set_kb_access(kb_id, subject_id, subject_type, permission_type, user_id)
        if result:
            debug_logger.info(f"权限设置成功 - 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}, 权限: {permission_type}")
            success_count += 1
        else:
            debug_logger.error(f"权限设置失败 - 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}, 权限: {permission_type}")
            failed_count += 1
    
    debug_logger.info(f"批量设置知识库权限完成 - 知识库: {kb_id}, 成功: {success_count}, 失败: {failed_count}")
    return sanic_json({
        "code": 200, 
        "msg": "批量设置知识库权限完成", 
        "data": {
            "success_count": success_count,
            "failed_count": failed_count
        }
    })
