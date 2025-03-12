import functools
import jwt
from datetime import datetime, timedelta
import os
from sanic import response, request

from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.utils.general_utils import safe_get

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # 生产环境中应使用环境变量
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # 令牌有效期

def get_user_role(user_id, req):
    """获取用户角色"""
    local_doc_qa = req.app.ctx.local_doc_qa
    query = "SELECT role FROM User WHERE user_id = %s AND status = 'active'"
    result = local_doc_qa.milvus_summary.execute_query_(query, (user_id,), fetch=True)
    if result:
        return result[0][0]
    return None

def has_permission(role, required_permission):
    """检查角色是否有所需权限"""
    # 权限层级: superadmin > admin > user
    if role == 'superadmin':
        return True
    if role == 'admin' and required_permission in ['write', 'read']:
        return True
    if role == 'user' and required_permission == 'read':
        return True
    return False

def auth_required(permission_level="read", check_kb_access=False):
    """
    权限控制装饰器
    :param permission_level: 所需权限级别（read/write/admin）
    :param check_kb_access: 是否检查知识库访问权限（针对特定知识库的操作）
    """
    def decorator(f):
        @functools.wraps(f)
        async def decorated_function(req, *args, **kwargs):
            # 获取用户ID和令牌
            user_id = safe_get(req, 'user_id')
            # 如果user_id是列表，取第一个元素
            if isinstance(user_id, list) and user_id:
                user_id = user_id[0]
            token = req.headers.get('Authorization', '').replace('Bearer ', '')
            
            debug_logger.info(f"权限验证开始 - 用户: {user_id}, 所需权限: {permission_level}, 检查知识库权限: {check_kb_access}")
            
            if not user_id:
                debug_logger.error("未提供用户ID")
                return response.json({"code": 401, "msg": "未提供用户ID"})
                
            if not token:
                debug_logger.error(f"用户 {user_id} 未提供认证令牌")
                return response.json({"code": 401, "msg": "未提供认证令牌"})
                
            # 验证令牌
            try:
                # 解码JWT令牌
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                
                # 验证令牌中的用户ID与请求中的用户ID是否匹配
                token_user_id = payload.get("user_id")
                if token_user_id != user_id:
                    debug_logger.error(f"令牌与用户ID不匹配 - 令牌用户: {token_user_id}, 请求用户: {user_id}")
                    return response.json({"code": 401, "msg": "令牌与用户ID不匹配"})
                
                # 检查令牌是否过期
                exp = payload.get("exp")
                if not exp or datetime.utcfromtimestamp(exp) < datetime.utcnow():
                    debug_logger.error(f"用户 {user_id} 的令牌已过期")
                    return response.json({"code": 401, "msg": "令牌已过期"})
                
                # 检查用户角色和权限
                user_role = payload.get("role") or get_user_role(user_id, req)
                debug_logger.info(f"用户角色验证 - 用户: {user_id}, 角色: {user_role}, 所需权限: {permission_level}")
                
                # 根据角色和请求的权限级别判断是否有权限
                if not has_permission(user_role, permission_level):
                    debug_logger.error(f"权限不足 - 用户: {user_id}, 角色: {user_role}, 所需权限: {permission_level}")
                    return response.json({"code": 403, "msg": f"没有{permission_level}权限执行此操作"})
                
                # 如果需要检查知识库访问权限
                if check_kb_access:
                    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
                    kb_id = safe_get(req, 'kb_id')
                    if kb_id:
                        # 检查用户是否有权限访问该知识库
                        if not local_doc_qa.milvus_summary.check_kb_access(user_id, kb_id, permission_level):
                            debug_logger.error(f"知识库访问权限不足 - 用户: {user_id}, 知识库: {kb_id}, 所需权限: {permission_level}")
                            return response.json({"code": 403, "msg": f"没有权限{permission_level}访问知识库 {kb_id}"})
                    
                    # 如果是批量操作多个知识库
                    kb_ids = safe_get(req, 'kb_ids')
                    if kb_ids and isinstance(kb_ids, list):
                        for kb_id in kb_ids:
                            if not local_doc_qa.milvus_summary.check_kb_access(user_id, kb_id, permission_level):
                                debug_logger.error(f"知识库访问权限不足 - 用户: {user_id}, 知识库: {kb_id}, 所需权限: {permission_level}")
                                return response.json({"code": 403, "msg": f"没有权限{permission_level}访问知识库 {kb_id}"})
                
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

async def login(req: request):
    """用户登录"""
    local_doc_qa = req.app.ctx.local_doc_qa
    username = safe_get(req, 'username')
    password = safe_get(req, 'password')
    
    if not username or not password:
        return response.json({"code": 400, "msg": "用户名和密码不能为空"})
    
    # 查询用户信息
    query = "SELECT user_id, password, role, user_name FROM User WHERE user_name = %s AND status = 'active'"
    user_info = local_doc_qa.milvus_summary.execute_query_(query, (username,), fetch=True)
    
    if not user_info:
        return response.json({"code": 401, "msg": "用户不存在或已被禁用"})
    
    user_id, hashed_password, role, user_name = user_info[0]
    
    # 验证密码
    import bcrypt
    if not bcrypt.checkpw(password.encode(), hashed_password.encode()):
        return response.json({"code": 401, "msg": "密码错误"})
    
    # 生成访问令牌
    access_token_expires = datetime.utcnow() + JWT_ACCESS_TOKEN_EXPIRES
    access_token_payload = {
        "user_id": user_id,
        "role": role,
        "exp": access_token_expires
    }
    access_token = jwt.encode(access_token_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return response.json({
        "code": 200,
        "msg": "登录成功",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": JWT_ACCESS_TOKEN_EXPIRES.total_seconds(),
            "user_id": user_id,
            "role": role,
            "user_name": user_name
        }
    })

async def refresh_token(req: request):
    """刷新令牌"""
    token = req.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return response.json({"code": 401, "msg": "未提供认证令牌"})
    
    try:
        # 解码JWT令牌
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # 获取用户信息
        user_id = payload.get("user_id")
        role = payload.get("role")
        
        # 生成新的访问令牌
        access_token_expires = datetime.utcnow() + JWT_ACCESS_TOKEN_EXPIRES
        access_token_payload = {
            "user_id": user_id,
            "role": role,
            "exp": access_token_expires
        }
        access_token = jwt.encode(access_token_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        return response.json({
            "code": 200,
            "msg": "令牌刷新成功",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": JWT_ACCESS_TOKEN_EXPIRES.total_seconds(),
                "user_id": user_id,
                "role": role
            }
        })
    except jwt.ExpiredSignatureError:
        return response.json({"code": 401, "msg": "令牌已过期，请重新登录"})
    except jwt.InvalidTokenError:
        return response.json({"code": 401, "msg": "无效的令牌"})
    except Exception as e:
        debug_logger.error(f"刷新令牌失败: {str(e)}")
        return response.json({"code": 500, "msg": f"刷新令牌失败: {str(e)}"})
    