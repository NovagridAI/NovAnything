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
               p.dept_name as parent_dept_name
        FROM Department d
        LEFT JOIN Department p ON d.parent_dept_id = p.dept_id
        ORDER BY d.creation_time
    """
    depts = local_doc_qa.milvus_summary.execute_query_(query, (), fetch=True)
    
    result = []
    for dept in depts:
        result.append({
            "dept_id": dept[0],
            "dept_name": dept[1],
            "parent_dept_id": dept[2],
            "creation_time": dept[3].strftime("%Y-%m-%d %H:%M:%S") if dept[3] else None,
            "parent_dept_name": dept[4]
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
