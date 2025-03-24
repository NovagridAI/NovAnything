import functools
import jwt
from datetime import datetime, timedelta
import bcrypt
import os
from sanic import request, response
from sanic.response import json as sanic_json
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.utils.general_utils import get_time_async, safe_get
from qanything_kernel.core.local_doc_qa import LocalDocQA

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # 生产环境中应使用环境变量
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # 令牌有效期

# 角色定义 - 系统级权限采用角色模型
ROLE_USER = "user"           # 普通用户
ROLE_ADMIN = "admin"         # 管理员
ROLE_SUPERADMIN = "superadmin"  # 超级管理员

# 知识库权限定义 - 知识库权限采用细分权限模型
KB_PERM_READ = "read"        # 知识库读取权限
KB_PERM_WRITE = "write"      # 知识库写入/修改权限
KB_PERM_ADMIN = "admin"      # 知识库管理权限（包括权限分配，但不包括删除）

def auth_required(required_role=ROLE_USER, check_kb_access=False, kb_permission=KB_PERM_READ):
    """
    权限检查装饰器
    
    Args:
        required_role: 所需角色，可选值：user, admin, superadmin
        check_kb_access: 是否检查知识库访问权限
        kb_permission: 所需知识库权限级别，仅当check_kb_access为True时有效
    
    角色与权限说明:
        - 超级管理员(superadmin)：
          * 拥有所有系统权限，包括用户管理（创建、删除用户等）
          * 拥有所有知识库的所有权限
        
        - 管理员(admin)：
          * 可以管理知识库（创建、删除知识库）
          * 不能管理用户（不能创建、删除用户）
          * 需要被分配权限才能访问特定知识库
        
        - 普通用户(user)：
          * 基本访问权限
          * 需要被分配权限才能访问特定知识库
          * 如被分配足够的知识库权限，可以管理其权限范围内的知识库
    
    知识库权限继承关系:
        - 知识库权限: admin > write > read
        - 知识库创建者拥有该知识库的所有权限
        - 用户可以通过直接授权、部门或用户组获得知识库权限
    """
    def decorator(f):
        @functools.wraps(f)
        async def decorated_function(req, *args, **kwargs):
            # 获取用户ID和令牌
            user_id = safe_get(req, 'user_id')
            if not user_id:
                debug_logger.error("未提供用户ID")
                return response.json({"code": 401, "msg": "未提供用户ID"})
            
            # 从请求头获取令牌
            auth_header = req.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                debug_logger.error(f"用户 {user_id} 未提供令牌或令牌格式错误")
                return response.json({"code": 401, "msg": "未提供令牌或令牌格式错误"})
            
            token = auth_header.split(' ')[1]
            try:
                # 验证令牌
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                token_user_id = payload.get("user_id")
                
                # 检查令牌中的用户ID是否与请求中的一致
                if token_user_id != user_id:
                    debug_logger.error(f"令牌用户ID {token_user_id} 与请求用户ID {user_id} 不匹配")
                    return response.json({"code": 403, "msg": "令牌用户ID与请求用户ID不匹配"})
                
                # 获取用户角色
                user_role = payload.get("role", ROLE_USER)  # 从令牌中获取用户角色，默认为普通用户
                
                # 检查用户角色是否满足要求
                if not has_role_permission(user_role, required_role):
                    debug_logger.error(f"用户 {user_id} 权限不足，角色 {user_role} 不足以执行需要 {required_role} 角色的操作")
                    return response.json({"code": 403, "msg": f"权限不足，需要 {required_role} 角色权限"})
                
                # 如果需要检查知识库访问权限
                if check_kb_access:
                    # 如果用户是超级管理员，则不需要进一步检查知识库权限
                    if user_role != ROLE_SUPERADMIN:
                        kb_id = safe_get(req, 'kb_id')
                        if kb_id:
                            local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
                            # 检查用户是否有权限访问该知识库
                            if not local_doc_qa.milvus_summary.check_kb_access(user_id, kb_id, kb_permission):
                                debug_logger.error(f"知识库访问权限不足 - 用户: {user_id}, 知识库: {kb_id}, 所需权限: {kb_permission}")
                                return response.json({"code": 403, "msg": f"没有权限{kb_permission}访问知识库 {kb_id}"})
                        
                        # 如果是批量操作多个知识库
                        kb_ids = safe_get(req, 'kb_ids')
                        if kb_ids and isinstance(kb_ids, list):
                            local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
                            for kb_id in kb_ids:
                                if not local_doc_qa.milvus_summary.check_kb_access(user_id, kb_id, kb_permission):
                                    debug_logger.error(f"知识库访问权限不足 - 用户: {user_id}, 知识库: {kb_id}, 所需权限: {kb_permission}")
                                    return response.json({"code": 403, "msg": f"没有权限{kb_permission}访问知识库 {kb_id}"})
                
                # 将用户信息添加到请求上下文中，方便后续使用
                req.ctx.user = {
                    "user_id": user_id,
                    "role": user_role
                }
                
                debug_logger.info(f"权限验证通过 - 用户: {user_id}, 角色: {user_role}")
                return await f(req, *args, **kwargs)
            except jwt.ExpiredSignatureError:
                debug_logger.error(f"用户 {user_id} 的令牌已过期")
                return response.json({"code": 401, "msg": "令牌已过期"})
            except jwt.InvalidTokenError:
                debug_logger.error(f"用户 {user_id} 提供了无效的令牌")
                return response.json({"code": 401, "msg": "无效的令牌"})
            except Exception as e:
                debug_logger.error(f"认证失败 - 用户: {user_id}, 错误: {str(e)}")
                return response.json({"code": 401, "msg": f"认证失败: {str(e)}"})
        return decorated_function
    return decorator

def get_user_role(user_id, req: request):
    """
    从数据库获取用户角色
    
    Args:
        user_id: 用户ID
        req: Sanic请求对象
        
    Returns:
        用户角色字符串或None
    """
    try:
        local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
        
        # 查询用户角色
        query = "SELECT role FROM User WHERE user_id = %s AND status = 'active'"
        result = local_doc_qa.milvus_summary.execute_query_(query, (user_id,), fetch=True)
        
        if result and result[0]:
            role = result[0][0]
            debug_logger.info(f"用户 {user_id} 的角色是 {role}")
            return role
        else:
            debug_logger.warn(f"未找到用户 {user_id} 或用户已禁用")
            return None
    except Exception as e:
        debug_logger.error(f"获取用户角色失败: {str(e)}")
        return None

def has_role_permission(user_role, required_role):
    """
    检查用户角色是否满足所需角色要求
    
    Args:
        user_role: 用户角色 (user, admin, superadmin)
        required_role: 所需角色 (user, admin, superadmin)
        
    Returns:
        布尔值，表示是否有权限
    """
    # 角色等级
    role_levels = {
        ROLE_USER: 1,       # 普通用户
        ROLE_ADMIN: 2,      # 管理员
        ROLE_SUPERADMIN: 3  # 超级管理员
    }
    
    # 获取用户角色等级
    user_level = role_levels.get(user_role, 0)
    # 获取所需角色等级
    required_level = role_levels.get(required_role, 0)
    
    # 检查权限
    has_perm = user_level >= required_level
    debug_logger.info(f"角色权限检查 - 用户角色: {user_role}({user_level}), 所需角色: {required_role}({required_level}), 结果: {has_perm}")
    return has_perm

def verify_password(plain_password, hashed_password):
    """
    验证密码是否匹配
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        布尔值，表示密码是否匹配
    """
    try:
        # 使用 bcrypt 进行密码验证
        result = bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        debug_logger.info(f"密码验证{'成功' if result else '失败'}")
        return result
    except Exception as e:
        debug_logger.error(f"密码验证出错: {str(e)}")
        return False

@get_time_async
async def login(req: request):
    """
    用户登录接口
    
    Args:
        req: Sanic请求对象，包含用户ID和密码
        
    Returns:
        JSON响应，包含令牌和用户信息
    """
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    password = safe_get(req, 'password')
    
    debug_logger.info(f"用户登录尝试 - 用户ID: {user_id}")
    
    if not user_id or not password:
        debug_logger.error(f"登录参数不完整 - 用户ID: {user_id}")
        return sanic_json({"code": 400, "msg": "用户ID和密码不能为空"})
    
    # 查询用户信息
    query = "SELECT password_hash, role, user_name, dept_id FROM User WHERE user_id = %s AND status = 'active'"
    user_info = local_doc_qa.milvus_summary.execute_query_(query, (user_id,), fetch=True)
    
    if not user_info:
        debug_logger.error(f"用户不存在或已禁用 - 用户ID: {user_id}")
        return sanic_json({"code": 401, "msg": "用户不存在或已禁用"})
    
    hashed_password = user_info[0][0]
    user_role = user_info[0][1]
    user_name = user_info[0][2]
    dept_id = user_info[0][3]
    
    # 验证密码
    if not verify_password(password, hashed_password):
        debug_logger.error(f"密码验证失败 - 用户ID: {user_id}")
        return sanic_json({"code": 401, "msg": "用户名或密码错误"})
    
    # 获取用户所属部门名称
    dept_name = None
    if dept_id:
        query = "SELECT dept_name FROM Department WHERE dept_id = %s"
        dept_result = local_doc_qa.milvus_summary.execute_query_(query, (dept_id,), fetch=True)
        if dept_result:
            dept_name = dept_result[0][0]
    
    # 查询用户所属的用户组
    query = """
        SELECT g.group_id, g.group_name 
        FROM UserGroup g
        JOIN GroupMember m ON g.group_id = m.group_id
        WHERE m.user_id = %s AND m.status = 'active'
    """
    groups_result = local_doc_qa.milvus_summary.execute_query_(query, (user_id,), fetch=True)
    user_groups = [{"group_id": row[0], "group_name": row[1]} for row in groups_result] if groups_result else []
    
    # 生成JWT令牌
    payload = {
        "user_id": user_id,
        "role": user_role,
        "exp": datetime.utcnow() + JWT_ACCESS_TOKEN_EXPIRES
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    # 更新用户最后登录时间
    update_query = "UPDATE User SET last_login = NOW() WHERE user_id = %s"
    local_doc_qa.milvus_summary.execute_query_(update_query, (user_id,), commit=True)
    
    debug_logger.info(f"用户登录成功 - 用户ID: {user_id}, 角色: {user_role}")
    return sanic_json({
        "code": 200, 
        "msg": "登录成功", 
        "data": {
            "token": token,
            "user_id": user_id,
            "user_name": user_name,
            "role": user_role,
            "dept_id": dept_id,
            "dept_name": dept_name,
            "groups": user_groups
        }
    })

@get_time_async
@auth_required(ROLE_USER)  # 刷新令牌只需要普通用户权限
async def refresh_token(req: request):
    """
    刷新JWT令牌
    
    Args:
        req: Sanic请求对象
        
    Returns:
        JSON响应，包含新的令牌
    """
    user_id = req.ctx.user["user_id"]
    role = req.ctx.user["role"]
    
    debug_logger.info(f"刷新令牌 - 用户: {user_id}, 角色: {role}")
    
    # 生成新的JWT令牌
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + JWT_ACCESS_TOKEN_EXPIRES
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    debug_logger.info(f"令牌刷新成功 - 用户: {user_id}")
    return response.json({
        "code": 200,
        "msg": "令牌刷新成功",
        "data": {
            "token": token
        }
    }) 