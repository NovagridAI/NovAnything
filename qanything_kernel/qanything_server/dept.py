import uuid
from qanything_kernel.qanything_server.handler import auth_required
from qanything_kernel.utils.general_utils import get_time_async, safe_get
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.utils.custom_log import debug_logger, qa_logger
from sanic import request, response
from sanic.response import json as sanic_json


@get_time_async
@auth_required("admin")
async def create_department(req: request):
    """创建新部门"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    dept_name = safe_get(req, 'dept_name')
    parent_dept_id = safe_get(req, 'parent_dept_id', None)
    
    if not dept_name:
        return sanic_json({"code": 400, "msg": "部门名称不能为空"})
    
    # 如果指定了父部门，检查父部门是否存在
    if parent_dept_id:
        query = "SELECT dept_id FROM Department WHERE dept_id = %s"
        if not local_doc_qa.milvus_summary.execute_query_(query, (parent_dept_id,), fetch=True):
            return sanic_json({"code": 404, "msg": "父部门不存在"})
    
    # 生成唯一的部门ID
    dept_id = f"dept_{uuid.uuid4().hex[:8]}"
    
    # 创建部门
    query = "INSERT INTO Department (dept_id, dept_name, parent_dept_id) VALUES (%s, %s, %s)"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (dept_id, dept_name, parent_dept_id), commit=True)
        return sanic_json({
            "code": 200, 
            "msg": "部门创建成功", 
            "data": {
                "dept_id": dept_id, 
                "dept_name": dept_name, 
                "parent_dept_id": parent_dept_id
            }
        })
    except Exception as e:
        debug_logger.error(f"创建部门失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"创建部门失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def list_departments(req: request):
    """获取部门列表"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    
    # 获取所有部门
    query = """
        SELECT d.dept_id, d.dept_name, d.parent_dept_id, d.creation_time,
               p.dept_name as parent_dept_name,
               COUNT(DISTINCT u.user_id) as member_count
        FROM Department d
        LEFT JOIN Department p ON d.parent_dept_id = p.dept_id
        LEFT JOIN User u ON d.dept_id = u.dept_id AND u.status = 'active'
        GROUP BY d.dept_id, d.dept_name, d.parent_dept_id, d.creation_time, p.dept_name
        ORDER BY d.creation_time
    """
    depts = local_doc_qa.milvus_summary.execute_query_(query, (), fetch=True)
    
    result = []
    for dept in depts:
        dept_id = dept[0]
        
        # 查询部门的知识库权限
        kb_access_query = """
            SELECT kb.kb_id, kb.kb_name, kba.permission_type, 
                   kba.granted_by, u.user_name as granted_by_name,
                   kba.granted_at
            FROM KnowledgeBaseAccess kba
            JOIN KnowledgeBase kb ON kba.kb_id = kb.kb_id
            LEFT JOIN User u ON kba.granted_by = u.user_id
            WHERE kba.subject_type = 'department'
            AND kba.subject_id = %s
            AND kb.deleted = 0
            ORDER BY kba.granted_at DESC
        """
        kb_access = local_doc_qa.milvus_summary.execute_query_(kb_access_query, (dept_id,), fetch=True)
        
        result.append({
            "dept_id": dept[0],
            "dept_name": dept[1],
            "parent_dept_id": dept[2],
            "creation_time": dept[3].strftime("%Y-%m-%d %H:%M:%S") if dept[3] else None,
            "parent_dept_name": dept[4],
            "member_count": dept[5],
            "permissions": [
                {
                    "kb_id": acc[0],
                    "kb_name": acc[1],
                    "permission_type": acc[2],
                    "granted_by": {
                        "user_id": acc[3],
                        "user_name": acc[4]
                    },
                    "granted_at": acc[5].strftime("%Y-%m-%d %H:%M:%S") if acc[5] else None
                } for acc in kb_access
            ]
        })
    
    return sanic_json({"code": 200, "msg": "获取部门列表成功", "data": result})

@get_time_async
@auth_required("admin")
async def update_department(req: request):
    """更新部门信息"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    dept_id = safe_get(req, 'dept_id')
    dept_name = safe_get(req, 'dept_name')
    parent_dept_id = safe_get(req, 'parent_dept_id')
    
    if not dept_id:
        return sanic_json({"code": 400, "msg": "部门ID不能为空"})
    
    # 检查部门是否存在
    query = "SELECT dept_id FROM Department WHERE dept_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "部门不存在"})
    
    # 如果指定了父部门，检查父部门是否存在
    if parent_dept_id:
        query = "SELECT dept_id FROM Department WHERE dept_id = %s"
        if not local_doc_qa.milvus_summary.execute_query_(query, (parent_dept_id,), fetch=True):
            return sanic_json({"code": 404, "msg": "父部门不存在"})
        
        # 检查是否形成循环依赖
        if parent_dept_id == dept_id:
            return sanic_json({"code": 400, "msg": "部门不能将自己设为父部门"})
    
    # 构建更新语句
    update_fields = []
    params = []
    
    if dept_name:
        update_fields.append("dept_name = %s")
        params.append(dept_name)
    
    if parent_dept_id is not None:  # 允许设置为NULL
        update_fields.append("parent_dept_id = %s")
        params.append(parent_dept_id)
    
    if not update_fields:
        return sanic_json({"code": 400, "msg": "没有提供要更新的字段"})
    
    # 更新部门
    query = f"UPDATE Department SET {', '.join(update_fields)} WHERE dept_id = %s"
    params.append(dept_id)
    
    try:
        local_doc_qa.milvus_summary.execute_query_(query, tuple(params), commit=True)
        return sanic_json({"code": 200, "msg": "部门更新成功"})
    except Exception as e:
        debug_logger.error(f"更新部门失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"更新部门失败: {str(e)}"})

@get_time_async
@auth_required("admin")
async def delete_department(req: request):
    """删除部门"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    dept_id = safe_get(req, 'dept_id')
    
    if not dept_id:
        return sanic_json({"code": 400, "msg": "部门ID不能为空"})
    
    # 检查部门是否存在
    query = "SELECT dept_id FROM Department WHERE dept_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "部门不存在"})
    
    # 检查是否有子部门
    query = "SELECT dept_id FROM Department WHERE parent_dept_id = %s"
    if local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), fetch=True):
        return sanic_json({"code": 400, "msg": "该部门下有子部门，无法删除"})
    
    # 检查是否有用户属于该部门
    query = "SELECT user_id FROM User WHERE dept_id = %s"
    if local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), fetch=True):
        return sanic_json({"code": 400, "msg": "该部门下有用户，无法删除"})
    
    # 删除部门
    query = "DELETE FROM Department WHERE dept_id = %s"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), commit=True)
        
        # 同时删除该部门的所有知识库权限
        query = "DELETE FROM KnowledgeBaseAccess WHERE subject_id = %s AND subject_type = 'department'"
        local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), commit=True)
        
        return sanic_json({"code": 200, "msg": "部门删除成功"})
    except Exception as e:
        debug_logger.error(f"删除部门失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"删除部门失败: {str(e)}"})

@get_time_async
@auth_required("admin")
async def add_users_to_dept(req: request):
    """批量将用户添加到部门"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    target_user_ids = safe_get(req, 'target_user_ids', [])  # 要添加的用户ID列表
    dept_id = safe_get(req, 'dept_id')  # 部门ID
    
    if not target_user_ids or not dept_id:
        return sanic_json({"code": 400, "msg": "用户ID列表和部门ID不能为空"})
    
    if not isinstance(target_user_ids, list):
        return sanic_json({"code": 400, "msg": "target_user_ids必须是一个列表"})
    
    # 检查部门是否存在
    query = "SELECT dept_id FROM Department WHERE dept_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "部门不存在"})
    
    success_count = 0
    failed_list = []
    
    for target_user_id in target_user_ids:
        try:
            # 检查用户是否存在
            query = "SELECT user_id, dept_id FROM User WHERE user_id = %s AND status = 'active'"
            user_info = local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), fetch=True)
            
            if not user_info:
                failed_list.append({
                    "user_id": target_user_id,
                    "reason": "用户不存在或已被禁用"
                })
                continue
            
            current_dept_id = user_info[0][1]
            if current_dept_id == dept_id:
                failed_list.append({
                    "user_id": target_user_id,
                    "reason": "用户已在该部门中"
                })
                continue
            
            # 更新用户的部门
            query = "UPDATE User SET dept_id = %s WHERE user_id = %s"
            local_doc_qa.milvus_summary.execute_query_(query, (dept_id, target_user_id), commit=True)
            success_count += 1
            
        except Exception as e:
            debug_logger.error(f"添加用户 {target_user_id} 到部门失败: {str(e)}")
            failed_list.append({
                "user_id": target_user_id,
                "reason": f"添加失败: {str(e)}"
            })
    
    return sanic_json({
        "code": 200,
        "msg": f"批量添加用户完成，成功: {success_count}，失败: {len(failed_list)}",
        "data": {
            "success_count": success_count,
            "failed_count": len(failed_list),
            "failed_list": failed_list
        }
    })
