import uuid
import bcrypt
from qanything_kernel.qanything_server.handler import auth_required
from qanything_kernel.utils.general_utils import get_time_async, safe_get
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.utils.custom_log import debug_logger
from sanic import request
from sanic.response import json as sanic_json


@get_time_async
@auth_required("admin")
async def create_user(req: request):
    """创建新用户"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    
    # 新用户信息
    user_name = safe_get(req, 'user_name')
    email = safe_get(req, 'email', '')
    password = safe_get(req, 'password')  # 管理员直接设置密码
    dept_id = safe_get(req, 'dept_id', None)  # 可选，部门ID
    role = safe_get(req, 'role', 'user')  # 默认为普通用户
    
    if not user_name or not password:
        return sanic_json({"code": 400, "msg": "用户名和密码不能为空"})
    
    # 检查用户名是否已存在
    query = "SELECT user_id FROM User WHERE user_name = %s"
    if local_doc_qa.milvus_summary.execute_query_(query, (user_name,), fetch=True):
        return sanic_json({"code": 400, "msg": "该用户名已被使用"})
    
    # 检查邮箱是否已存在
    if email:
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
            "status": user[5],
            "creation_time": user[6].strftime("%Y-%m-%d %H:%M:%S") if user[6] else None,
            "dept_name": user[7]
        })
    
    return sanic_json({"code": 200, "msg": "获取用户列表成功", "data": result})


@get_time_async
@auth_required("admin")
async def update_user(req: request):
    """更新用户信息"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    target_user_id = safe_get(req, 'target_user_id')  # 要更新的用户ID
    user_name = safe_get(req, 'user_name')
    email = safe_get(req, 'email')
    password = safe_get(req, 'password')  # 可选，更新密码
    dept_id = safe_get(req, 'dept_id')
    role = safe_get(req, 'role')
    status = safe_get(req, 'status')
    
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
    
    # 构建更新语句
    update_fields = []
    params = []
    
    if user_name:
        # 检查用户名是否已被其他用户使用
        query = "SELECT user_id FROM User WHERE user_name = %s AND user_id != %s"
        if local_doc_qa.milvus_summary.execute_query_(query, (user_name, target_user_id), fetch=True):
            return sanic_json({"code": 400, "msg": "该用户名已被其他用户使用"})
        update_fields.append("user_name = %s")
        params.append(user_name)
    
    if email:
        # 检查邮箱是否已被其他用户使用
        query = "SELECT user_id FROM User WHERE email = %s AND user_id != %s"
        if local_doc_qa.milvus_summary.execute_query_(query, (email, target_user_id), fetch=True):
            return sanic_json({"code": 400, "msg": "该邮箱已被其他用户使用"})
        update_fields.append("email = %s")
        params.append(email)
    
    if password:
        # 对密码进行哈希处理
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        update_fields.append("password = %s")
        params.append(hashed_password)
    
    if dept_id is not None:  # 允许设置为NULL
        update_fields.append("dept_id = %s")
        params.append(dept_id)
    
    if role:
        update_fields.append("role = %s")
        params.append(role)
    
    if status:
        update_fields.append("status = %s")
        params.append(status)
    
    if not update_fields:
        return sanic_json({"code": 400, "msg": "没有提供要更新的字段"})
    
    # 更新用户
    query = f"UPDATE User SET {', '.join(update_fields)} WHERE user_id = %s"
    params.append(target_user_id)
    
    try:
        local_doc_qa.milvus_summary.execute_query_(query, tuple(params), commit=True)
        return sanic_json({"code": 200, "msg": "用户信息更新成功"})
    except Exception as e:
        debug_logger.error(f"更新用户信息失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"更新用户信息失败: {str(e)}"})


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
async def reset_user_password(req: request):
    """重置用户密码"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    target_user_id = safe_get(req, 'target_user_id')  # 要重置密码的用户ID
    new_password = safe_get(req, 'new_password')  # 新密码
    
    if not target_user_id or not new_password:
        return sanic_json({"code": 400, "msg": "目标用户ID和新密码不能为空"})
    
    # 检查用户是否存在
    query = "SELECT user_id FROM User WHERE user_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    # 对新密码进行哈希处理
    hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    
    # 更新密码
    query = "UPDATE User SET password = %s WHERE user_id = %s"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (hashed_password, target_user_id), commit=True)
        return sanic_json({"code": 200, "msg": "用户密码重置成功"})
    except Exception as e:
        debug_logger.error(f"重置用户密码失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"重置用户密码失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def set_user_kb_access(req: request):
    """设置用户对知识库的访问权限"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    admin_user_id = safe_get(req, 'user_id')  # 当前操作用户（管理员）
    target_user_id = safe_get(req, 'target_user_id')  # 目标用户
    kb_id = safe_get(req, 'kb_id')  # 知识库ID
    permission_type = safe_get(req, 'permission_type', 'read')  # 权限级别：read, write, admin
    
    if not target_user_id or not kb_id:
        return sanic_json({"code": 400, "msg": "目标用户ID和知识库ID不能为空"})
    
    # 验证权限级别
    if permission_type not in ['read', 'write', 'admin', 'none']:
        return sanic_json({"code": 400, "msg": "权限级别必须是read、write、admin或none"})
    
    # 检查用户是否存在
    query = "SELECT user_id FROM User WHERE user_id = %s AND status = 'active'"
    if not local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户不存在或已被禁用"})
    
    # 检查知识库是否存在
    query = "SELECT kb_id FROM KnowledgeBase WHERE kb_id = %s"
    if not local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "知识库不存在"})
    
    try:
        # 检查是否已有权限记录
        query = """
            SELECT id FROM KnowledgeBaseAccess 
            WHERE kb_id = %s AND subject_type = 'user' AND subject_id = %s
        """
        existing_access = local_doc_qa.milvus_summary.execute_query_(
            query, (kb_id, target_user_id), fetch=True
        )
        
        if permission_type == 'none':
            # 如果设置为none，则删除权限记录
            if existing_access:
                delete_query = """
                    DELETE FROM KnowledgeBaseAccess 
                    WHERE kb_id = %s AND subject_type = 'user' AND subject_id = %s
                """
                local_doc_qa.milvus_summary.execute_query_(
                    delete_query, (kb_id, target_user_id), commit=True
                )
                return sanic_json({"code": 200, "msg": "已移除用户的知识库访问权限"})
            else:
                return sanic_json({"code": 200, "msg": "用户本来就没有此知识库的直接访问权限"})
        else:
            # 设置或更新权限
            if existing_access:
                # 更新现有权限
                update_query = """
                    UPDATE KnowledgeBaseAccess SET permission_type = %s, granted_by = %s
                    WHERE kb_id = %s AND subject_type = 'user' AND subject_id = %s
                """
                local_doc_qa.milvus_summary.execute_query_(
                    update_query, (permission_type, admin_user_id, kb_id, target_user_id), commit=True
                )
                return sanic_json({"code": 200, "msg": f"用户权限已更新为{permission_type}"})
            else:
                # 创建新权限记录
                insert_query = """
                    INSERT INTO KnowledgeBaseAccess 
                    (kb_id, subject_type, subject_id, permission_type, granted_by)
                    VALUES (%s, %s, %s, %s, %s)
                """
                local_doc_qa.milvus_summary.execute_query_(
                    insert_query, (kb_id, 'user', target_user_id, permission_type, admin_user_id), commit=True
                )
                return sanic_json({"code": 200, "msg": f"已授予用户{permission_type}权限"})
    except Exception as e:
        debug_logger.error(f"设置用户知识库权限失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"设置用户知识库权限失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def batch_set_user_kb_access(req: request):
    """批量设置用户对知识库的访问权限"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    admin_user_id = safe_get(req, 'user_id')  # 当前操作用户（管理员）
    target_user_id = safe_get(req, 'target_user_id')  # 目标用户
    kb_list = safe_get(req, 'kb_list', [])  # 知识库列表，格式为[{kb_id, permission_type}]
    
    if not target_user_id or not kb_list:
        return sanic_json({"code": 400, "msg": "目标用户ID和知识库列表不能为空"})
    
    # 检查用户是否存在
    query = "SELECT user_id FROM User WHERE user_id = %s AND status = 'active'"
    if not local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "用户不存在或已被禁用"})
    
    success_count = 0
    failed_list = []
    
    for kb_item in kb_list:
        kb_id = kb_item.get('kb_id')
        permission_type = kb_item.get('permission_type', 'read')
        
        if not kb_id:
            failed_list.append({
                "kb_id": kb_id,
                "reason": "知识库ID不能为空"
            })
            continue
        
        # 验证权限级别
        if permission_type not in ['read', 'write', 'admin', 'none']:
            failed_list.append({
                "kb_id": kb_id,
                "reason": "权限级别必须是read、write、admin或none"
            })
            continue
        
        # 检查知识库是否存在
        query = "SELECT kb_id FROM KnowledgeBase WHERE kb_id = %s"
        if not local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True):
            failed_list.append({
                "kb_id": kb_id,
                "reason": "知识库不存在"
            })
            continue
        
        try:
            # 检查是否已有权限记录
            query = """
                SELECT id FROM KnowledgeBaseAccess 
                WHERE kb_id = %s AND subject_type = 'user' AND subject_id = %s
            """
            existing_access = local_doc_qa.milvus_summary.execute_query_(
                query, (kb_id, target_user_id), fetch=True
            )
            
            if permission_type == 'none':
                # 如果设置为none，则删除权限记录
                if existing_access:
                    delete_query = """
                        DELETE FROM KnowledgeBaseAccess 
                        WHERE kb_id = %s AND subject_type = 'user' AND subject_id = %s
                    """
                    local_doc_qa.milvus_summary.execute_query_(
                        delete_query, (kb_id, target_user_id), commit=True
                    )
            else:
                # 设置或更新权限
                if existing_access:
                    # 更新现有权限
                    update_query = """
                        UPDATE KnowledgeBaseAccess SET permission_type = %s, granted_by = %s
                        WHERE kb_id = %s AND subject_type = 'user' AND subject_id = %s
                    """
                    local_doc_qa.milvus_summary.execute_query_(
                        update_query, (permission_type, admin_user_id, kb_id, target_user_id), commit=True
                    )
                else:
                    # 创建新权限记录
                    insert_query = """
                        INSERT INTO KnowledgeBaseAccess 
                        (kb_id, subject_type, subject_id, permission_type, granted_by)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    local_doc_qa.milvus_summary.execute_query_(
                        insert_query, (kb_id, 'user', target_user_id, permission_type, admin_user_id), commit=True
                    )
            
            success_count += 1
        except Exception as e:
            debug_logger.error(f"设置用户知识库权限失败: {str(e)}")
            failed_list.append({
                "kb_id": kb_id,
                "reason": f"设置权限失败: {str(e)}"
            })
    
    return sanic_json({
        "code": 200, 
        "msg": f"批量设置权限完成，成功: {success_count}，失败: {len(failed_list)}", 
        "data": {
            "success_count": success_count,
            "failed_count": len(failed_list),
            "failed_list": failed_list
        }
    })


@get_time_async
@auth_required("admin")
async def get_user_kb_access(req: request):
    """获取用户对所有知识库的访问权限"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    admin_user_id = safe_get(req, 'user_id')  # 当前操作用户（管理员）
    target_user_id = safe_get(req, 'target_user_id')  # 目标用户
    
    if not target_user_id:
        return sanic_json({"code": 400, "msg": "目标用户ID不能为空"})
    
    # 检查用户是否存在
    query = "SELECT user_id, user_name, dept_id, role FROM User WHERE user_id = %s"
    user_info = local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), fetch=True)
    if not user_info:
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    user_name = user_info[0][1]
    dept_id = user_info[0][2]
    user_role = user_info[0][3]
    
    # 获取用户所在的所有用户组
    query = """
        SELECT g.group_id, g.group_name 
        FROM GroupMember m
        JOIN UserGroup g ON m.group_id = g.group_id
        WHERE m.user_id = %s
    """
    user_groups = local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), fetch=True)
    groups = [{"group_id": g[0], "group_name": g[1]} for g in user_groups]
    
    # 获取部门信息
    dept_name = None
    if dept_id:
        query = "SELECT dept_name FROM Department WHERE dept_id = %s"
        dept_info = local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), fetch=True)
        if dept_info:
            dept_name = dept_info[0][0]
    
    # 获取所有知识库
    query = "SELECT kb_id, kb_name, owner_id FROM KnowledgeBase ORDER BY creation_time DESC"
    all_kbs = local_doc_qa.milvus_summary.execute_query_(query, (), fetch=True)
    
    # 获取用户直接权限
    query = """
        SELECT kb_id, permission_type FROM KnowledgeBaseAccess 
        WHERE subject_type = 'user' AND subject_id = %s
    """
    user_access = local_doc_qa.milvus_summary.execute_query_(query, (target_user_id,), fetch=True)
    user_access_dict = {a[0]: a[1] for a in user_access}
    
    # 获取部门权限
    dept_access_dict = {}
    if dept_id:
        query = """
            SELECT kb_id, permission_type FROM KnowledgeBaseAccess 
            WHERE subject_type = 'department' AND subject_id = %s
        """
        dept_access = local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), fetch=True)
        dept_access_dict = {a[0]: a[1] for a in dept_access}
    
    # 获取用户组权限
    group_access_dict = {}
    for group in groups:
        group_id = group["group_id"]
        query = """
            SELECT kb_id, permission_type FROM KnowledgeBaseAccess 
            WHERE subject_type = 'group' AND subject_id = %s
        """
        group_access = local_doc_qa.milvus_summary.execute_query_(query, (group_id,), fetch=True)
        for a in group_access:
            kb_id, level = a
            if kb_id not in group_access_dict or level > group_access_dict[kb_id]["level"]:
                group_access_dict[kb_id] = {"level": level, "group_id": group_id, "group_name": group["group_name"]}
    
    # 权限级别映射，用于比较权限高低
    level_map = {'read': 1, 'write': 2, 'admin': 3}
    
    # 整合所有知识库的权限信息
    kb_access_list = []
    for kb in all_kbs:
        kb_id, kb_name, owner_id = kb
        
        access_info = {
            "kb_id": kb_id,
            "kb_name": kb_name,
            "is_owner": (owner_id == target_user_id),
            "direct_access": user_access_dict.get(kb_id, None),
            "dept_access": dept_access_dict.get(kb_id, None),
            "group_access": None,
            "effective_access": None,
            "access_source": None
        }
        
        # 设置用户组权限信息
        if kb_id in group_access_dict:
            access_info["group_access"] = {
                "level": group_access_dict[kb_id]["level"],
                "group_id": group_access_dict[kb_id]["group_id"],
                "group_name": group_access_dict[kb_id]["group_name"]
            }
        
        # 计算有效权限
        if access_info["is_owner"]:
            access_info["effective_access"] = "admin"
            access_info["access_source"] = "owner"
        else:
            # 初始化最高权限级别
            highest_level = 0
            access_source = None
            
            # 检查直接权限
            if access_info["direct_access"]:
                direct_level = level_map.get(access_info["direct_access"], 0)
                if direct_level > highest_level:
                    highest_level = direct_level
                    access_source = "direct"
            
            # 检查部门权限
            if access_info["dept_access"]:
                dept_level = level_map.get(access_info["dept_access"], 0)
                if dept_level > highest_level:
                    highest_level = dept_level
                    access_source = "department"
            
            # 检查用户组权限
            if access_info["group_access"]:
                group_level = level_map.get(access_info["group_access"]["level"], 0)
                if group_level > highest_level:
                    highest_level = group_level
                    access_source = "group"
            
            # 设置有效权限
            if highest_level > 0:
                for level_name, level_value in level_map.items():
                    if level_value == highest_level:
                        access_info["effective_access"] = level_name
                        access_info["access_source"] = access_source
                        break
        
        kb_access_list.append(access_info)
    
    # 构建返回结果
    result = {
        "user_info": {
            "user_id": target_user_id,
            "user_name": user_name,
            "role": user_role,
            "dept_id": dept_id,
            "dept_name": dept_name,
            "groups": groups
        },
        "kb_access_list": kb_access_list
    }
    
    return sanic_json({"code": 200, "msg": "获取用户知识库权限成功", "data": result})


@get_time_async
@auth_required("read")
async def get_accessible_kbs(req: request):
    """获取当前用户可访问的所有知识库列表"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前用户
    role = req.ctx.user.get("role", "user")  # 用户角色
    dept_id = req.ctx.user.get("dept_id")  # 用户部门
    
    # 如果是管理员，返回所有知识库
    if role == "superadmin":
        query = """
            SELECT kb_id, kb_name, user_id, latest_qa_time, latest_insert_time, deleted
            FROM KnowledgeBase
            WHERE deleted = 0
            ORDER BY latest_insert_time DESC
        """
        kbs = local_doc_qa.milvus_summary.execute_query_(query, (), fetch=True)
        
        result = []
        for kb in kbs:
            result.append({
                "kb_id": kb[0],
                "kb_name": kb[1],
                "owner_id": kb[2],
                "latest_qa_time": kb[3].strftime("%Y-%m-%d %H:%M:%S") if kb[3] else None,
                "latest_insert_time": kb[4].strftime("%Y-%m-%d %H:%M:%S") if kb[4] else None,
                "deleted": kb[5],
                "permission_type": "admin",
                "access_source": "admin_role"
            })
        
        return sanic_json({"code": 200, "msg": "获取知识库列表成功", "data": result})
    
    # 非管理员用户，需要检查权限
    # 1. 获取用户拥有的知识库
    query = """
        SELECT kb_id, kb_name, user_id, latest_qa_time, latest_insert_time, deleted
        FROM KnowledgeBase
        WHERE user_id = %s AND deleted = 0
        ORDER BY latest_insert_time DESC
    """
    owned_kbs = local_doc_qa.milvus_summary.execute_query_(query, (user_id,), fetch=True)
    
    # 2. 获取用户直接被授权的知识库
    query = """
        SELECT k.kb_id, k.kb_name, k.user_id, k.latest_qa_time, 
               k.latest_insert_time, k.deleted, a.permission_type
        FROM KnowledgeBase k
        JOIN KnowledgeBaseAccess a ON k.kb_id = a.kb_id
        WHERE a.subject_type = 'user' AND a.subject_id = %s AND k.user_id != %s AND k.deleted = 0
        ORDER BY k.latest_insert_time DESC
    """
    direct_kbs = local_doc_qa.milvus_summary.execute_query_(query, (user_id, user_id), fetch=True)
    
    # 3. 获取用户通过部门被授权的知识库
    dept_kbs = []
    if dept_id:
        query = """
            SELECT k.kb_id, k.kb_name, k.user_id, k.latest_qa_time, 
                   k.latest_insert_time, k.deleted, a.permission_type
            FROM KnowledgeBase k
            JOIN KnowledgeBaseAccess a ON k.kb_id = a.kb_id
            WHERE a.subject_type = 'department' AND a.subject_id = %s 
                  AND k.user_id != %s AND k.deleted = 0
                  AND k.kb_id NOT IN (
                      SELECT kb_id FROM KnowledgeBaseAccess 
                      WHERE subject_type = 'user' AND subject_id = %s
                  )
            ORDER BY k.latest_insert_time DESC
        """
        dept_kbs = local_doc_qa.milvus_summary.execute_query_(query, (dept_id, user_id, user_id), fetch=True)
    
    # 4. 获取用户通过用户组被授权的知识库
    # 先获取用户所在的所有用户组
    query = "SELECT group_id FROM GroupMember WHERE user_id = %s"
    user_groups = local_doc_qa.milvus_summary.execute_query_(query, (user_id,), fetch=True)
    
    group_kbs = []
    if user_groups:
        group_ids = [g[0] for g in user_groups]
        placeholders = ', '.join(['%s'] * len(group_ids))
        
        # 排除用户已经通过直接权限或部门权限访问的知识库
        exclude_kb_query = """
            SELECT kb_id FROM KnowledgeBaseAccess 
            WHERE (subject_type = 'user' AND subject_id = %s)
            OR (subject_type = 'department' AND subject_id = %s)
        """
        exclude_params = [user_id]
        if dept_id:
            exclude_params.append(dept_id)
        else:
            exclude_kb_query = exclude_kb_query.replace("OR (subject_type = 'department' AND subject_id = %s)", "")
        
        exclude_kbs = local_doc_qa.milvus_summary.execute_query_(exclude_kb_query, tuple(exclude_params), fetch=True)
        exclude_kb_ids = [kb[0] for kb in exclude_kbs] if exclude_kbs else []
        
        # 构建排除条件
        exclude_condition = ""
        if exclude_kb_ids:
            exclude_placeholders = ', '.join(['%s'] * len(exclude_kb_ids))
            exclude_condition = f"AND k.kb_id NOT IN ({exclude_placeholders})"
        
        # 获取通过用户组授权的知识库
        query = f"""
            SELECT k.kb_id, k.kb_name, k.description, k.owner_id, k.creation_time, 
                   k.update_time, k.status, k.embedding_model, k.kb_type, a.permission_type, a.subject_id
            FROM KnowledgeBase k
            JOIN KnowledgeBaseAccess a ON k.kb_id = a.kb_id
            WHERE a.subject_type = 'group' AND a.subject_id IN ({placeholders})
                  AND k.owner_id != %s
                  {exclude_condition}
            ORDER BY k.creation_time DESC
        """
        
        params = group_ids + [user_id]
        if exclude_kb_ids:
            params.extend(exclude_kb_ids)
        
        group_kbs_raw = local_doc_qa.milvus_summary.execute_query_(query, tuple(params), fetch=True)
        
        # 处理可能有多个用户组授权同一个知识库的情况，选择最高权限
        kb_group_map = {}
        for kb in group_kbs_raw:
            kb_id = kb[0]
            permission_type = kb[9]
            group_id = kb[10]
            
            level_map = {'read': 1, 'write': 2, 'admin': 3}
            current_level = level_map.get(permission_type, 0)
            
            if kb_id not in kb_group_map or current_level > level_map.get(kb_group_map[kb_id]['permission_type'], 0):
                kb_group_map[kb_id] = {
                    'kb_data': kb[:10],
                    'permission_type': permission_type,
                    'group_id': group_id
                }
        
        # 获取用户组名称
        for kb_id, kb_info in kb_group_map.items():
            group_id = kb_info['group_id']
            query = "SELECT group_name FROM UserGroup WHERE group_id = %s"
            group_name_result = local_doc_qa.milvus_summary.execute_query_(query, (group_id,), fetch=True)
            group_name = group_name_result[0][0] if group_name_result else "未知用户组"
            
            kb_data = list(kb_info['kb_data'])
            kb_data.append(group_id)
            kb_data.append(group_name)
            group_kbs.append(kb_data)
    
    # 整合所有可访问的知识库
    result = []
    
    # 添加用户拥有的知识库
    for kb in owned_kbs:
        result.append({
            "kb_id": kb[0],
            "kb_name": kb[1],
            "owner_id": kb[2],
            "latest_qa_time": kb[3].strftime("%Y-%m-%d %H:%M:%S") if kb[3] else None,
            "latest_insert_time": kb[4].strftime("%Y-%m-%d %H:%M:%S") if kb[4] else None,
            "deleted": kb[5],
            "permission_type": "admin",
            "access_source": "owner"
        })
    
    # 添加用户直接被授权的知识库
    for kb in direct_kbs:
        result.append({
            "kb_id": kb[0],
            "kb_name": kb[1],
            "owner_id": kb[2],
            "latest_qa_time": kb[3].strftime("%Y-%m-%d %H:%M:%S") if kb[3] else None,
            "latest_insert_time": kb[4].strftime("%Y-%m-%d %H:%M:%S") if kb[4] else None,
            "deleted": kb[5],
            "permission_type": kb[6],
            "access_source": "direct"
        })
    
    # 添加用户通过部门被授权的知识库
    for kb in dept_kbs:
        result.append({
            "kb_id": kb[0],
            "kb_name": kb[1],
            "owner_id": kb[2],
            "latest_qa_time": kb[3].strftime("%Y-%m-%d %H:%M:%S") if kb[3] else None,
            "latest_insert_time": kb[4].strftime("%Y-%m-%d %H:%M:%S") if kb[4] else None,
            "deleted": kb[5],
            "permission_type": kb[6],
            "access_source": "department"
        })
    
    # 添加用户通过用户组被授权的知识库
    for kb in group_kbs:
        result.append({
            "kb_id": kb[0],
            "kb_name": kb[1],
            "owner_id": kb[2],
            "latest_qa_time": kb[3].strftime("%Y-%m-%d %H:%M:%S") if kb[3] else None,
            "latest_insert_time": kb[4].strftime("%Y-%m-%d %H:%M:%S") if kb[4] else None,
            "deleted": kb[5],
            "permission_type": kb[6],
            "access_source": "group",
            "group_id": kb[7],
            "group_name": kb[8]
        })
    
    return sanic_json({"code": 200, "msg": "获取可访问知识库列表成功", "data": result})


@get_time_async
@auth_required("read")
async def change_password(req: request):
    """用户修改自己的密码"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前用户
    old_password = safe_get(req, 'old_password')  # 旧密码
    new_password = safe_get(req, 'new_password')  # 新密码
    
    if not old_password or not new_password:
        return sanic_json({"code": 400, "msg": "旧密码和新密码不能为空"})
    
    # 验证旧密码
    query = "SELECT password FROM User WHERE user_id = %s"
    result = local_doc_qa.milvus_summary.execute_query_(query, (user_id,), fetch=True)
    if not result:
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    stored_password = result[0][0]
    if not bcrypt.checkpw(old_password.encode(), stored_password.encode()):
        return sanic_json({"code": 401, "msg": "旧密码不正确"})
    
    # 对新密码进行哈希处理
    hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    
    # 更新密码
    query = "UPDATE User SET password = %s WHERE user_id = %s"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (hashed_password, user_id), commit=True)
        return sanic_json({"code": 200, "msg": "密码修改成功"})
    except Exception as e:
        debug_logger.error(f"修改密码失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"修改密码失败: {str(e)}"})


@get_time_async
@auth_required("read")
async def get_user_profile(req: request):
    """获取当前用户的个人信息"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前用户
    
    # 获取用户基本信息
    query = """
        SELECT u.user_name, u.email, u.role, u.dept_id, u.status, u.creation_time, d.dept_name
        FROM User u
        LEFT JOIN Department d ON u.dept_id = d.dept_id
        WHERE u.user_id = %s
    """
    user_info = local_doc_qa.milvus_summary.execute_query_(query, (user_id,), fetch=True)
    
    if not user_info:
        return sanic_json({"code": 404, "msg": "用户不存在"})
    
    # 获取用户所在的所有用户组
    query = """
        SELECT g.group_id, g.group_name 
        FROM GroupMember m
        JOIN UserGroup g ON m.group_id = g.group_id
        WHERE m.user_id = %s
    """
    user_groups = local_doc_qa.milvus_summary.execute_query_(query, (user_id,), fetch=True)
    groups = [{"group_id": g[0], "group_name": g[1]} for g in user_groups]
    
    # 构建返回结果
    result = {
        "user_id": user_id,
        "user_name": user_info[0][0],
        "email": user_info[0][1],
        "role": user_info[0][2],
        "dept_id": user_info[0][3],
        "dept_name": user_info[0][6],
        "status": user_info[0][4],
        "creation_time": user_info[0][5].strftime("%Y-%m-%d %H:%M:%S") if user_info[0][5] else None,
        "groups": groups
    }
    
    return sanic_json({"code": 200, "msg": "获取用户信息成功", "data": result})


@get_time_async
@auth_required("read")
async def update_user_profile(req: request):
    """更新当前用户的个人信息（仅限于用户名和邮箱）"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前用户
    user_name = safe_get(req, 'user_name')
    email = safe_get(req, 'email')
    
    if not user_name and not email:
        return sanic_json({"code": 400, "msg": "至少需要提供一个要更新的字段"})
    
    # 构建更新语句
    update_fields = []
    params = []
    
    if user_name:
        # 检查用户名是否已被其他用户使用
        query = "SELECT user_id FROM User WHERE user_name = %s AND user_id != %s"
        if local_doc_qa.milvus_summary.execute_query_(query, (user_name, user_id), fetch=True):
            return sanic_json({"code": 400, "msg": "该用户名已被其他用户使用"})
        update_fields.append("user_name = %s")
        params.append(user_name)
    
    if email:
        # 检查邮箱是否已被其他用户使用
        query = "SELECT user_id FROM User WHERE email = %s AND user_id != %s"
        if local_doc_qa.milvus_summary.execute_query_(query, (email, user_id), fetch=True):
            return sanic_json({"code": 400, "msg": "该邮箱已被其他用户使用"})
        update_fields.append("email = %s")
        params.append(email)
    
    # 更新用户信息
    query = f"UPDATE User SET {', '.join(update_fields)} WHERE user_id = %s"
    params.append(user_id)
    
    try:
        local_doc_qa.milvus_summary.execute_query_(query, tuple(params), commit=True)
        return sanic_json({"code": 200, "msg": "个人信息更新成功"})
    except Exception as e:
        debug_logger.error(f"更新个人信息失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"更新个人信息失败: {str(e)}"})
