import asyncio
import base64
import json
import os
import re
import shutil
import time
import urllib.parse
import uuid
from collections import Counter, defaultdict
from datetime import datetime

from httpx._transports.default import ResponseStream
from langchain.schema import Document
from sanic import request, response
from sanic.response import ResponseStream
from sanic.response import json as sanic_json
from tqdm import tqdm

from qanything_kernel.configs.model_config import DEFAULT_PARENT_CHUNK_SIZE, MAX_CHARS, UPLOAD_ROOT_PATH, \
    IMAGES_ROOT_PATH, VECTOR_SEARCH_TOP_K, GATEWAY_IP
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.core.local_file import LocalFile
from qanything_kernel.qanything_server.handler import auth_required, run_in_background
from qanything_kernel.utils.custom_log import debug_logger, qa_logger
from qanything_kernel.utils.general_utils import get_time_async, safe_get, correct_kb_id, check_user_id_and_user_info, \
    truncate_filename, read_files_with_extensions, fast_estimate_file_char_count, simplify_filename, \
    check_and_transform_excel, format_source_documents, format_time_record, replace_image_references, get_time_range, \
    export_qalogs_to_excel, num_tokens_embed


def _check_kb_exists(local_doc_qa, kb_id):
    """检查知识库是否存在"""
    query = "SELECT kb_id FROM KnowledgeBase WHERE kb_id = %s AND deleted = 0"
    return local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)


def _check_subject_exists(local_doc_qa, subject_type, subject_id):
    """根据主体类型检查主体是否存在"""
    if subject_type == 'user':
        query = "SELECT user_id FROM User WHERE user_id = %s AND status = 'active'"
    elif subject_type == 'department':
        query = "SELECT dept_id FROM Department WHERE dept_id = %s"
    elif subject_type == 'group':
        query = "SELECT group_id FROM UserGroup WHERE group_id = %s"
    else:
        return False
    
    return local_doc_qa.milvus_summary.execute_query_(query, (subject_id,), fetch=True)


def _get_kb_access(local_doc_qa, kb_id, subject_type, subject_id):
    """获取知识库访问权限记录"""
    query = """
        SELECT id, permission_type FROM KnowledgeBaseAccess 
        WHERE kb_id = %s AND subject_type = %s AND subject_id = %s
    """
    return local_doc_qa.milvus_summary.execute_query_(
        query, (kb_id, subject_type, subject_id), fetch=True
    )


def _get_subject_name(local_doc_qa, subject_type, subject_id):
    """获取主体名称"""
    if subject_type == 'user':
        query = "SELECT user_name FROM User WHERE user_id = %s"
    elif subject_type == 'department':
        query = "SELECT dept_name FROM Department WHERE dept_id = %s"
    elif subject_type == 'group':
        query = "SELECT group_name FROM UserGroup WHERE group_id = %s"
    else:
        return "未知主体"
    
    subject_info = local_doc_qa.milvus_summary.execute_query_(query, (subject_id,), fetch=True)
    return subject_info[0][0] if subject_info else f"未知{subject_type}"

def _get_user_permission(local_doc_qa, kb_id, user_id, role, dept_id, owner_id):
    """获取用户对知识库的权限"""
    # 如果用户是管理员或知识库所有者，直接授予所有权限
    if role == "superadmin" or role == "admin" or user_id == owner_id:
        return True, "admin", "admin_role" if role == "admin" else "owner"
    
    # 获取用户所在的所有用户组
    query = "SELECT group_id FROM GroupMember WHERE user_id = %s"
    user_groups = local_doc_qa.milvus_summary.execute_query_(query, (user_id,), fetch=True)
    group_ids = [group[0] for group in user_groups] if user_groups else []

    # 权限级别映射，用于比较权限高低
    level_map = {'read': 1, 'write': 2, 'admin': 3}
    highest_level = 0
    permission_level = None
    permission_source = None

    # 检查用户直接权限
    query = """
        SELECT permission_type FROM KnowledgeBaseAccess 
        WHERE kb_id = %s AND subject_type = 'user' AND subject_id = %s
    """
    user_access = local_doc_qa.milvus_summary.execute_query_(query, (kb_id, user_id), fetch=True)
    if user_access:
        user_level = level_map.get(user_access[0][0], 0)
        if user_level > highest_level:
            highest_level = user_level
            permission_level = user_access[0][0]
            permission_source = "direct"

    # 检查部门权限
    if dept_id:
        query = """
            SELECT permission_type FROM KnowledgeBaseAccess 
            WHERE kb_id = %s AND subject_type = 'department' AND subject_id = %s
        """
        dept_access = local_doc_qa.milvus_summary.execute_query_(query, (kb_id, dept_id), fetch=True)
        if dept_access:
            dept_level = level_map.get(dept_access[0][0], 0)
            if dept_level > highest_level:
                highest_level = dept_level
                permission_level = dept_access[0][0]
                permission_source = "department"

    # 检查用户组权限
    for group_id in group_ids:
        query = """
            SELECT permission_type, g.group_name FROM KnowledgeBaseAccess a
            JOIN UserGroup g ON a.subject_id = g.group_id
            WHERE a.kb_id = %s AND a.subject_type = 'group' AND a.subject_id = %s
        """
        group_access = local_doc_qa.milvus_summary.execute_query_(query, (kb_id, group_id), fetch=True)
        if group_access:
            group_level = level_map.get(group_access[0][0], 0)
            if group_level > highest_level:
                highest_level = group_level
                permission_level = group_access[0][0]
                permission_source = f"group:{group_access[0][1]}" if len(group_access[0]) > 1 else "group"

    # 判断用户是否有权限访问该知识库
    has_permission = highest_level > 0
    return has_permission, permission_level, permission_source


@get_time_async
@auth_required("admin")
async def grant_kb_access(req: request):
    """授予知识库访问权限"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    kb_id = safe_get(req, 'kb_id')  # 知识库ID
    subject_type = safe_get(req, 'subject_type')  # 主体类型：user, department, group
    subject_id = safe_get(req, 'subject_id')  # 主体ID
    access_level = safe_get(req, 'access_level', 'read')  # 权限级别：read, write, admin

    if not kb_id or not subject_type or not subject_id:
        return sanic_json({"code": 400, "msg": "知识库ID、主体类型和主体ID不能为空"})
    
    # 验证主体类型
    if subject_type not in ['user', 'department', 'group']:
        return sanic_json({"code": 400, "msg": "主体类型必须是user、department或group"})

    # 验证权限级别
    if access_level not in ['read', 'write', 'admin']:
        return sanic_json({"code": 400, "msg": "权限级别必须是read、write或admin"})

    # 检查知识库是否存在
    if not _check_kb_exists(local_doc_qa, kb_id):
        return sanic_json({"code": 404, "msg": "知识库不存在"})

    # 检查主体是否存在
    if not _check_subject_exists(local_doc_qa, subject_type, subject_id):
        return sanic_json({"code": 404, "msg": f"{subject_type}不存在或已被禁用"})

    # 检查是否已有权限记录
    existing_access = _get_kb_access(local_doc_qa, kb_id, subject_type, subject_id)

    try:
        if existing_access:
            # 如果已有权限记录，则更新权限级别
            access_id = existing_access[0][0]
            current_level = existing_access[0][1]

            if current_level == access_level:
                return sanic_json({"code": 200, "msg": f"该{subject_type}已具有此权限级别"})

            update_query = """
                UPDATE KnowledgeBaseAccess SET permission_type = %s, granted_by = %s
                WHERE id = %s
            """
            local_doc_qa.milvus_summary.execute_query_(
                update_query, (access_level, user_id, access_id), commit=True
            )
            return sanic_json({"code": 200, "msg": f"权限级别已从{current_level}更新为{access_level}"})
        else:
            # 如果没有权限记录，则创建新记录
            insert_query = """
                INSERT INTO KnowledgeBaseAccess 
                (kb_id, subject_type, subject_id, permission_type, granted_by)
                VALUES (%s, %s, %s, %s, %s)
            """
            local_doc_qa.milvus_summary.execute_query_(
                insert_query, (kb_id, subject_type, subject_id, access_level, user_id), commit=True
            )
            return sanic_json({"code": 200, "msg": "权限授予成功"})
    except Exception as e:
        debug_logger.error(f"授予知识库访问权限失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"授予知识库访问权限失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def revoke_kb_access(req: request):
    """撤销知识库访问权限"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    kb_id = safe_get(req, 'kb_id')  # 知识库ID
    subject_type = safe_get(req, 'subject_type')  # 主体类型：user, department, group
    subject_id = safe_get(req, 'subject_id')  # 主体ID

    if not kb_id or not subject_type or not subject_id:
        return sanic_json({"code": 400, "msg": "知识库ID、主体类型和主体ID不能为空"})
    
    # 验证主体类型
    if subject_type not in ['user', 'department', 'group']:
        return sanic_json({"code": 400, "msg": "主体类型必须是user、department或group"})
    
    # 检查知识库是否存在
    if not _check_kb_exists(local_doc_qa, kb_id):
        return sanic_json({"code": 404, "msg": "知识库不存在"})

    # 检查是否有权限记录
    existing_access = _get_kb_access(local_doc_qa, kb_id, subject_type, subject_id)

    if not existing_access:
        return sanic_json({"code": 404, "msg": f"该{subject_type}没有此知识库的访问权限"})
    
    try:
        # 删除权限记录
        delete_query = """
            DELETE FROM KnowledgeBaseAccess 
            WHERE kb_id = %s AND subject_type = %s AND subject_id = %s
        """
        local_doc_qa.milvus_summary.execute_query_(
            delete_query, (kb_id, subject_type, subject_id), commit=True
        )
        return sanic_json({"code": 200, "msg": "权限撤销成功"})
    except Exception as e:
        debug_logger.error(f"撤销知识库访问权限失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"撤销知识库访问权限失败: {str(e)}"})


@get_time_async
@auth_required("admin")
async def get_kb_access_list(req: request):
    """获取知识库的所有访问权限记录"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    kb_id = safe_get(req, 'kb_id')  # 知识库ID
    
    debug_logger.info(f"获取知识库访问权限列表 - 操作用户: {user_id}, 知识库ID: {kb_id}")
    
    # 检查参数
    if not kb_id:
        debug_logger.warning(f"获取知识库访问权限列表失败 - 知识库ID为空")
        return sanic_json({"code": 400, "msg": "知识库ID不能为空"})

    # 检查知识库是否存在
    query = "SELECT kb_id, kb_name, user_id FROM KnowledgeBase WHERE kb_id = %s AND deleted = 0"
    debug_logger.info(f"执行查询: {query} 参数: {kb_id}")
    kb_info = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    
    if not kb_info:
        debug_logger.warning(f"获取知识库访问权限列表失败 - 知识库 {kb_id} 不存在")
        return sanic_json({"code": 404, "msg": "知识库不存在"})

    kb_name = kb_info[0][1]
    owner_id = kb_info[0][2]  # 使用user_id作为owner_id
    debug_logger.info(f"知识库信息 - 名称: {kb_name}, 所有者ID: {owner_id}")

    # 获取所有者信息
    owner_name = _get_subject_name(local_doc_qa, 'user', owner_id)
    debug_logger.info(f"知识库所有者: {owner_name} (ID: {owner_id})")

    # 获取所有权限记录
    query = """
        SELECT id, subject_type, subject_id, permission_type
        FROM KnowledgeBaseAccess 
        WHERE kb_id = %s
        ORDER BY subject_type, permission_type
    """
    debug_logger.info(f"查询知识库权限记录: {query} 参数: {kb_id}")
    access_records = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    debug_logger.info(f"找到 {len(access_records) if access_records else 0} 条权限记录")

    # 处理权限记录
    access_list = []
    for record in access_records:
        access_id, subject_type, subject_id, access_level = record
        debug_logger.info(f"处理权限记录 - ID: {access_id}, 类型: {subject_type}, 主体ID: {subject_id}, 权限级别: {access_level}")
        
        subject_name = _get_subject_name(local_doc_qa, subject_type, subject_id)
        debug_logger.info(f"主体名称: {subject_name}")

        access_list.append({
            "access_id": access_id,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "subject_name": subject_name,
            "access_level": access_level
        })

    # 构建返回结果
    result = {
        "kb_id": kb_id,
        "kb_name": kb_name,
        "owner_id": owner_id,
        "owner_name": owner_name,
        "access_list": access_list
    }
    
    debug_logger.info(f"获取知识库访问权限列表成功 - 知识库: {kb_name} (ID: {kb_id}), 权限记录数: {len(access_list)}")
    return sanic_json({"code": 200, "msg": "获取知识库访问权限列表成功", "data": result})


@get_time_async
@auth_required("read")
async def check_kb_permission(req: request):
    """检查当前用户对知识库的权限"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前用户
    kb_id = safe_get(req, 'kb_id')  # 知识库ID
    
    if not kb_id:
        return sanic_json({"code": 400, "msg": "知识库ID不能为空"})

    # 获取用户角色和部门
    role = req.ctx.user.get("role", "user")
    dept_id = req.ctx.user.get("dept_id")
    
    # 检查知识库是否存在
    query = "SELECT kb_id, kb_name, user_id FROM KnowledgeBase WHERE kb_id = %s AND deleted = 0"
    kb_info = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    if not kb_info:
        return sanic_json({"code": 404, "msg": "知识库不存在"})

    kb_name = kb_info[0][1]
    owner_id = kb_info[0][2]  # 使用user_id作为owner_id

    # 获取用户权限
    has_permission, permission_level, permission_source = _get_user_permission(
        local_doc_qa, kb_id, user_id, role, dept_id, owner_id
    )

    return sanic_json({
        "code": 200 if has_permission else 403,
        "msg": "获取权限信息成功" if has_permission else "您没有权限访问此知识库",
        "data": {
            "kb_id": kb_id,
            "kb_name": kb_name,
            "has_permission": has_permission,
            "permission_level": permission_level,
            "permission_source": permission_source
        }
    })


@get_time_async
@auth_required("admin")
async def batch_set_kb_access(req: request):
    """批量设置知识库访问权限"""
    local_doc_qa: LocalDocQA = req.app.ctx.access_listlocal_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    kb_id = safe_get(req, 'kb_id')  # 知识库ID
    access_list = safe_get(req, 'access_list', [])  # 权限列表，格式为[{subject_type, subject_id, access_level}]

    if not kb_id or not access_list:
        return sanic_json({"code": 400, "msg": "知识库ID和权限列表不能为空"})
    
    # 检查知识库是否存在
    if not _check_kb_exists(local_doc_qa, kb_id):
        return sanic_json({"code": 404, "msg": "知识库不存在"})
    
    success_count = 0
    failed_list = []

    for access_item in access_list:
        subject_type = access_item.get('subject_type')
        subject_id = access_item.get('subject_id')
        access_level = access_item.get('access_level', 'read')

        if not subject_type or not subject_id:
            failed_list.append({
                "subject_type": subject_type,
                "subject_id": subject_id,
                "reason": "主体类型和主体ID不能为空"
            })
            continue
        
        # 验证主体类型
        if subject_type not in ['user', 'department', 'group']:
            failed_list.append({
                "subject_type": subject_type,
                "subject_id": subject_id,
                "reason": "主体类型必须是user、department或group"
            })
            continue

        # 验证权限级别
        if access_level not in ['read', 'write', 'admin', 'none']:
            failed_list.append({
                "subject_type": subject_type,
                "subject_id": subject_id,
                "reason": "权限级别必须是read、write、admin或none"
            })
            continue

        # 检查主体是否存在
        if not _check_subject_exists(local_doc_qa, subject_type, subject_id):
            failed_list.append({
                "subject_type": subject_type,
                "subject_id": subject_id,
                "reason": f"{subject_type}不存在或已被禁用"
            })
            continue

        try:
            # 检查是否已有权限记录
            existing_access = _get_kb_access(local_doc_qa, kb_id, subject_type, subject_id)

            if access_level == 'none':
                # 如果设置为none，则删除权限记录
                if existing_access:
                    delete_query = """
                        DELETE FROM KnowledgeBaseAccess 
                        WHERE kb_id = %s AND subject_type = %s AND subject_id = %s
                    """
                    local_doc_qa.milvus_summary.execute_query_(
                        delete_query, (kb_id, subject_type, subject_id), commit=True
                    )
            else:
                if existing_access:
                    # 如果已有权限记录，则更新权限级别
                    access_id = existing_access[0][0]
                    update_query = """
                        UPDATE KnowledgeBaseAccess SET permission_type = %s, granted_by = %s
                        WHERE id = %s
                    """
                    local_doc_qa.milvus_summary.execute_query_(
                        update_query, (access_level, user_id, access_id), commit=True
                    )
                else:
                    # 如果没有权限记录，则创建新记录
                    insert_query = """
                        INSERT INTO KnowledgeBaseAccess 
                        (kb_id, subject_type, subject_id, permission_type, granted_by)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    local_doc_qa.milvus_summary.execute_query_(
                        insert_query, (kb_id, subject_type, subject_id, access_level, user_id), commit=True
                    )
            
            success_count += 1
        except Exception as e:
            debug_logger.error(f"设置知识库访问权限失败: {str(e)}")
            failed_list.append({
                "subject_type": subject_type,
                "subject_id": subject_id,
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
@auth_required("read")
async def get_kb_detail(req: request):
    """获取知识库详细信息，包括访问权限"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前用户
    kb_id = safe_get(req, 'kb_id')  # 知识库ID

    if not kb_id:
        return sanic_json({"code": 400, "msg": "知识库ID不能为空"})

    # 获取用户角色和部门
    role = req.ctx.user.get("role", "user")
    dept_id = req.ctx.user.get("dept_id")

    # 检查知识库是否存在
    query = """
        SELECT kb_id, kb_name, user_id, latest_qa_time, latest_insert_time, deleted
        FROM KnowledgeBase 
        WHERE kb_id = %s AND deleted = 0
    """
    kb_info = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    if not kb_info:
        return sanic_json({"code": 404, "msg": "知识库不存在"})

    kb = kb_info[0]
    owner_id = kb[2]  # 使用user_id作为owner_id

    # 获取所有者信息
    owner_name = _get_subject_name(local_doc_qa, 'user', owner_id)

    # 检查用户是否有权限访问该知识库
    has_access, access_level, access_source = _get_user_permission(
        local_doc_qa, kb_id, user_id, role, dept_id, owner_id
    )

    # 如果用户没有权限访问该知识库，则返回错误
    if not has_access:
        return sanic_json({"code": 403, "msg": "您没有权限访问此知识库"})

    # 获取知识库文件数量
    query = "SELECT COUNT(*) FROM File WHERE kb_id = %s"
    file_count_result = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    file_count = file_count_result[0][0] if file_count_result else 0

    # 如果用户是管理员或知识库所有者，获取知识库的访问权限列表
    access_list = []
    if role == "superadmin" or role == "admin" or user_id == owner_id:
        query = """
            SELECT a.id, a.subject_type, a.subject_id, a.permission_type
            FROM KnowledgeBaseAccess a
            WHERE a.kb_id = %s
            ORDER BY a.subject_type, a.permission_type
        """
        access_records = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)

        for record in access_records:
            access_id, subject_type, subject_id, level = record
            subject_name = _get_subject_name(local_doc_qa, subject_type, subject_id)

            access_list.append({
                "access_id": access_id,
                "subject_type": subject_type,
                "subject_id": subject_id,
                "subject_name": subject_name,
                "access_level": level
            })

    # 构建返回结果
    result = {
        "kb_id": kb[0],
        "kb_name": kb[1],
        "owner_id": owner_id,
        "owner_name": owner_name,
        "latest_qa_time": kb[3].strftime("%Y-%m-%d %H:%M:%S") if kb[3] else None,
        "latest_insert_time": kb[4].strftime("%Y-%m-%d %H:%M:%S") if kb[4] else None,
        "deleted": kb[5],
        "file_count": file_count,
        "user_access": {
            "access_level": access_level,
            "access_source": access_source,
            "is_owner": user_id == owner_id,
            "is_admin": role == "admin" or role == "superadmin"
        }
    }

    # 如果用户是管理员或知识库所有者，添加访问权限列表
    if role == "admin" or user_id == owner_id:
        result["access_list"] = access_list

    return sanic_json({"code": 200, "msg": "获取知识库详细信息成功", "data": result})


@get_time_async
@auth_required(check_kb_access=True)
async def transfer_kb_ownership(req: request):
    """转移知识库所有权"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')  # 当前操作用户
    kb_id = safe_get(req, 'kb_id')  # 知识库ID
    new_owner_id = safe_get(req, 'new_owner_id')  # 新所有者ID

    if not kb_id or not new_owner_id:
        return sanic_json({"code": 400, "msg": "知识库ID和新所有者ID不能为空"})

    # 检查知识库是否存在
    query = "SELECT kb_id, user_id FROM KnowledgeBase WHERE kb_id = %s"
    kb_info = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    if not kb_info:
        return sanic_json({"code": 404, "msg": "知识库不存在"})

    current_owner_id = kb_info[0][1]  # 使用user_id作为owner_id

    # 检查当前用户是否有权限转移所有权（管理员或当前所有者）
    if user_id != current_owner_id and req.ctx.user.get("role") != "admin":
        return sanic_json({"code": 403, "msg": "您没有权限转移此知识库的所有权"})

    # 检查新所有者是否存在
    if not _check_subject_exists(local_doc_qa, 'user', new_owner_id):
        return sanic_json({"code": 404, "msg": "新所有者不存在或已被禁用"})

    # 如果新所有者与当前所有者相同，则无需转移
    if new_owner_id == current_owner_id:
        return sanic_json({"code": 200, "msg": "新所有者与当前所有者相同，无需转移"})

    try:
        # 更新知识库所有者
        update_query = "UPDATE KnowledgeBase SET user_id = %s WHERE kb_id = %s"
        local_doc_qa.milvus_summary.execute_query_(update_query, (new_owner_id, kb_id), commit=True)

        # 确保新所有者有admin权限
        # 先检查是否已有权限记录
        existing_access = _get_kb_access(local_doc_qa, kb_id, 'user', new_owner_id)

        if existing_access:
            # 更新权限级别为admin
            access_id = existing_access[0][0]
            update_query = """
                UPDATE KnowledgeBaseAccess SET permission_type = 'admin'
                WHERE id = %s
            """
            local_doc_qa.milvus_summary.execute_query_(
                update_query, (access_id,), commit=True
            )
        else:
            # 创建新的权限记录
            insert_query = """
                INSERT INTO KnowledgeBaseAccess 
                (kb_id, subject_type, subject_id, permission_type, granted_by)
                VALUES (%s, 'user', %s, 'admin', %s)
            """
            local_doc_qa.milvus_summary.execute_query_(
                insert_query, (kb_id, new_owner_id, user_id), commit=True
            )

        return sanic_json({"code": 200, "msg": "知识库所有权转移成功"})
    except Exception as e:
        debug_logger.error(f"转移知识库所有权失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"转移知识库所有权失败: {str(e)}"})


@get_time_async
@auth_required("write")
async def new_knowledge_base(req: request):
    """创建新的知识库"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info("new_knowledge_base %s", user_id)

    # 获取知识库名称和ID
    kb_name = safe_get(req, 'kb_name')
    debug_logger.info("kb_name: %s", kb_name)

    # 如果未提供知识库ID，则生成一个默认ID
    default_kb_id = 'KB' + uuid.uuid4().hex
    kb_id = safe_get(req, 'kb_id', default_kb_id)
    kb_id = correct_kb_id(kb_id)

    # 验证知识库名称
    if not kb_name:
        return sanic_json({"code": 400, "msg": "知识库名称不能为空"})

    # 检查知识库ID是否已存在
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, [kb_id])
    if not not_exist_kb_ids:
        return sanic_json({"code": 2001, "msg": "知识库ID {} 已经存在".format(kb_id)})

    try:
        # 创建新知识库
        local_doc_qa.milvus_summary.new_milvus_base(kb_id, user_id, kb_name)

        # 生成时间戳
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M")

        # 返回成功响应
        return sanic_json({
            "code": 200,
            "msg": "知识库创建成功",
            "data": {"kb_id": kb_id, "kb_name": kb_name, "timestamp": timestamp}
        })
    except Exception as e:
        # 记录错误并返回错误响应
        debug_logger.error(f"创建知识库失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"创建知识库失败: {str(e)}"})


@get_time_async
@auth_required("write")
async def rename_knowledge_base(req: request):
    """重命名知识库"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取请求参数
    user_id = safe_get(req, 'user_id')
    kb_id = safe_get(req, 'kb_id')
    new_name = safe_get(req, 'new_name')

    # 参数验证
    if not kb_id or not new_name:
        return sanic_json({"code": 400, "msg": "知识库ID和新名称不能为空"})

    # 检查知识库是否存在
    query = "SELECT kb_id, user_id FROM KnowledgeBase WHERE kb_id = %s"
    kb_info = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    if not kb_info:
        return sanic_json({"code": 404, "msg": "知识库不存在"})

    # 权限检查
    owner_id = kb_info[0][1]
    role = req.ctx.user.get("role", "user")

    # 如果不是管理员或所有者，检查是否有写权限
    if user_id != owner_id and role != "admin":
        has_write_access = False

        # 检查用户直接权限
        query = """
            SELECT access_level FROM KnowledgeBaseAccess 
            WHERE kb_id = %s AND subject_type = 'user' AND subject_id = %s
            AND access_level IN ('write', 'admin')
        """
        user_access = local_doc_qa.milvus_summary.execute_query_(query, (kb_id, user_id), fetch=True)
        if user_access:
            has_write_access = True

        if not has_write_access:
            return sanic_json({"code": 403, "msg": "您没有权限修改此知识库"})

    # 检查新名称是否已被使用
    query = "SELECT kb_id FROM KnowledgeBase WHERE kb_name = %s AND kb_id != %s AND deleted = 0"
    if local_doc_qa.milvus_summary.execute_query_(query, (new_name, kb_id), fetch=True):
        return sanic_json({"code": 400, "msg": "该知识库名称已存在"})

    # 更新知识库名称
    try:
        update_query = local_doc_qa.milvus_summary.rename_knowledge_base(user_id, kb_id, new_name)
        return sanic_json({"code": 200, "msg": "知识库重命名成功"})
    except Exception as e:
        debug_logger.error(f"重命名知识库失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"重命名知识库失败: {str(e)}"})


@get_time_async
@auth_required("write", check_kb_access=True)
async def upload_weblink(req: request):
    """上传网页链接到知识库"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info("upload_weblink %s", user_id)

    # 获取并验证知识库ID
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
        return sanic_json({"code": 2001, "msg": msg, "data": [{}]})

    # 处理URL和标题
    url = safe_get(req, 'url')
    if url:
        # 单个URL处理
        urls = [url]
        # 如果URL以/结尾，先去除这个/
        if url.endswith('/'):
            url = url[:-1]
        titles = [safe_get(req, 'title', url.split('/')[-1]) + '.web']
    else:
        # 多个URL处理
        urls = safe_get(req, 'urls')
        titles = safe_get(req, 'titles')
        if len(urls) != len(titles):
            return sanic_json({"code": 2003, "msg": "fail, urls and titles length not equal"})

    # 验证URL格式
    for url in urls:
        # URL必须以http开头
        if not url.startswith('http'):
            return sanic_json({"code": 2001, "msg": "fail, url must start with 'http'"})
        # URL长度不能超过2048
        if len(url) > 2048:
            return sanic_json({"code": 2002, "msg": f"fail, url too long, max length is 2048."})

    # 处理文件名
    file_names = []
    for title in titles:
        debug_logger.info('ori name: %s', title)
        file_name = re.sub(r'[\uFF01-\uFF5E\u3000-\u303F]', '', title)
        debug_logger.info('cleaned name: %s', file_name)
        file_name = truncate_filename(file_name, max_length=110)
        file_names.append(file_name)

    # 获取上传模式和分块大小
    mode = safe_get(req, 'mode', default='soft')  # soft代表不上传同名文件，strong表示强制上传同名文件
    debug_logger.info("mode: %s", mode)
    chunk_size = safe_get(req, 'chunk_size', default=DEFAULT_PARENT_CHUNK_SIZE)
    debug_logger.info("chunk_size: %s", chunk_size)

    # 检查同名文件
    exist_file_names = []
    if mode == 'soft':
        exist_files = local_doc_qa.milvus_summary.check_file_exist_by_name(user_id, kb_id, file_names)
        exist_file_names = [f[1] for f in exist_files]
        for exist_file in exist_files:
            file_id, file_name, file_size, status = exist_file
            debug_logger.info(f"{url}, {status}, existed files, skip upload")

    # 生成时间戳
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")

    # 处理文件上传
    data = []
    for url, file_name in zip(urls, file_names):
        if file_name in exist_file_names:
            continue

        # 创建本地文件对象
        local_file = LocalFile(user_id, kb_id, url, file_name)
        file_id = local_file.file_id
        file_size = len(local_file.file_content)
        file_location = local_file.file_location

        # 添加文件到数据库
        msg = local_doc_qa.milvus_summary.add_file(
            file_id, user_id, kb_id, file_name, file_size, file_location,
            chunk_size, timestamp, url
        )
        debug_logger.info(f"{url}, {file_name}, {file_id}, {msg}")

        # 添加到返回数据
        data.append({
            "file_id": file_id,
            "file_name": file_name,
            "file_url": url,
            "status": "gray",
            "bytes": 0,
            "timestamp": timestamp
        })

    # 生成响应消息
    if exist_file_names:
        msg = f'warning，当前的mode是soft，无法上传同名文件{exist_file_names}，如果想强制上传同名文件，请设置mode：strong'
    else:
        msg = "success，后台正在飞速上传文件，请耐心等待"

    return sanic_json({"code": 200, "msg": msg, "data": data})


@get_time_async
@auth_required("write", check_kb_access=True)
async def upload_files(req: request):
    """上传文件到知识库"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info("upload_files %s", user_id)

    # 获取并验证知识库ID
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    debug_logger.info("kb_id %s", kb_id)

    # 获取上传模式和分块大小
    mode = safe_get(req, 'mode', default='soft')  # soft代表不上传同名文件，strong表示强制上传同名文件
    debug_logger.info("mode: %s", mode)
    chunk_size = safe_get(req, 'chunk_size', default=DEFAULT_PARENT_CHUNK_SIZE)
    debug_logger.info("chunk_size: %s", chunk_size)

    # 获取文件列表
    use_local_file = safe_get(req, 'use_local_file', 'false')
    if use_local_file == 'true':
        files = read_files_with_extensions()
    else:
        files = req.files.getlist('files')
    debug_logger.info(f"{user_id} upload files number: {len(files)}")

    # 验证知识库是否存在
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
        return sanic_json({"code": 2001, "msg": msg, "data": [{}]})

    # 检查文件数量限制
    exist_files = local_doc_qa.milvus_summary.get_files(user_id, kb_id)
    if len(exist_files) + len(files) > 10000:
        return sanic_json({
            "code": 2002,
            "msg": f"fail, exist files is {len(exist_files)}, upload files is {len(files)}, total files is {len(exist_files) + len(files)}, max length is 10000."
        })

    # 处理文件名
    data = []
    local_files = []
    file_names = []
    for file in files:
        if isinstance(file, str):
            file_name = os.path.basename(file)
        else:
            debug_logger.info('ori name: %s', file.name)
            file_name = urllib.parse.unquote(file.name, encoding='UTF-8')
            debug_logger.info('decode name: %s', file_name)

        # 删除掉全角字符
        file_name = re.sub(r'[\uFF01-\uFF5E\u3000-\u303F]', '', file_name)
        debug_logger.info('cleaned name: %s', file_name)
        file_name = truncate_filename(file_name, max_length=110)
        file_names.append(file_name)

    # 检查同名文件
    exist_file_names = []
    if mode == 'soft':
        exist_files = local_doc_qa.milvus_summary.check_file_exist_by_name(user_id, kb_id, file_names)
        exist_file_names = [f[1] for f in exist_files]
        for exist_file in exist_files:
            file_id, file_name, file_size, status = exist_file
            debug_logger.info(f"{file_name}, {status}, existed files, skip upload")

    # 生成时间戳
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")

    # 处理文件上传
    failed_files = []
    for file, file_name in zip(files, file_names):
        # 跳过同名文件
        if file_name in exist_file_names:
            continue

        # 创建本地文件对象
        local_file = LocalFile(user_id, kb_id, file, file_name)

        # 检查文件字符数
        chars = fast_estimate_file_char_count(local_file.file_location)
        debug_logger.info(f"{file_name} char_size: {chars}")
        if chars and chars > MAX_CHARS:
            debug_logger.warning(f"fail, file {file_name} chars is {chars}, max length is {MAX_CHARS}.")
            failed_files.append(file_name)
            continue

        # 获取文件信息
        file_id = local_file.file_id
        file_size = len(local_file.file_content)
        file_location = local_file.file_location
        local_files.append(local_file)

        # 添加文件到数据库
        msg = local_doc_qa.milvus_summary.add_file(
            file_id, user_id, kb_id, file_name, file_size, file_location,
            chunk_size, timestamp
        )
        debug_logger.info(f"{file_name}, {file_id}, {msg}")

        # 添加到返回数据
        data.append({
            "file_id": file_id,
            "file_name": file_name,
            "status": "gray",
            "bytes": len(local_file.file_content),
            "timestamp": timestamp,
            "estimated_chars": chars
        })

    # 生成响应消息
    if exist_file_names:
        msg = f'warning，当前的mode是soft，无法上传同名文件{exist_file_names}，如果想强制上传同名文件，请设置mode：strong'
    elif failed_files:
        msg = f"warning, {failed_files} chars is too much, max characters length is {MAX_CHARS}, skip upload."
    else:
        msg = "success，后台正在飞速上传文件，请耐心等待"

    return sanic_json({"code": 200, "msg": msg, "data": data})


@get_time_async
@auth_required("write", check_kb_access=True)
async def upload_faqs(req: request):
    """上传FAQ到知识库"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取基本参数
    user_id = safe_get(req, 'user_id')
    debug_logger.info("upload_faqs %s", user_id)

    # 获取并验证知识库ID
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    debug_logger.info("kb_id %s", kb_id)

    # 获取分块大小
    chunk_size = safe_get(req, 'chunk_size', default=DEFAULT_PARENT_CHUNK_SIZE)
    debug_logger.info("chunk_size: %s", chunk_size)

    # 获取FAQ数据
    faqs = safe_get(req, 'faqs')
    file_status = {}

    # 如果没有直接提供FAQ数据，则从上传的文件中解析
    if faqs is None:
        files = req.files.getlist('files')
        faqs = []

        # 处理每个上传的文件
        for file in files:
            debug_logger.info('ori name: %s', file.name)
            file_name = urllib.parse.unquote(file.name, encoding='UTF-8')
            debug_logger.info('decode name: %s', file_name)

            # 清理文件名
            file_name = re.sub(r'[\uFF01-\uFF5E\u3000-\u303F]', '', file_name)
            file_name = file_name.replace("/", "_")
            debug_logger.info('cleaned name: %s', file_name)
            file_name = truncate_filename(file_name)

            # 解析Excel文件内容
            file_faqs = check_and_transform_excel(file.body)
            if isinstance(file_faqs, str):
                # 如果返回字符串，表示解析出错
                file_status[file_name] = file_faqs
            else:
                # 解析成功，添加到FAQ列表
                faqs.extend(file_faqs)
                file_status[file_name] = "success"

    # 验证FAQ数量
    if len(faqs) > 1000:
        return sanic_json({"code": 2002, "msg": f"fail, faqs too many, max length is 1000."})

    # 验证知识库是否存在
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
        return sanic_json({"code": 2001, "msg": msg})

    # 准备数据
    data = []
    local_files = []
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")

    # 开始处理FAQ
    debug_logger.info(f"start insert {len(faqs)} faqs to mysql, user_id: {user_id}, kb_id: {kb_id}")
    for faq in tqdm(faqs):
        # 获取问题和答案
        ques = faq['question']

        # 验证问题和答案长度
        if len(ques) > 512 or len(faq['answer']) > 2048:
            return sanic_json(
                {"code": 2003, "msg": f"fail, faq too long, max length of question is 512, answer is 2048."})

        # 处理文件名
        file_name = f"FAQ_{ques}.faq"
        file_name = file_name.replace("/", "_").replace(":", "_")  # 文件名中的/和：会导致写入时出错
        file_name = simplify_filename(file_name)

        # 计算文件大小
        file_size = len(ques) + len(faq['answer'])

        # 创建本地文件对象
        local_file = LocalFile(user_id, kb_id, faq, file_name)
        file_id = local_file.file_id
        file_location = local_file.file_location
        local_files.append(local_file)

        # 添加FAQ到数据库
        local_doc_qa.milvus_summary.add_faq(
            file_id, user_id, kb_id, faq['question'], faq['answer'],
            faq.get('nos_keys', '')
        )

        # 添加文件记录
        local_doc_qa.milvus_summary.add_file(
            file_id, user_id, kb_id, file_name, file_size, file_location,
            chunk_size, timestamp
        )

        # 添加到返回数据
        data.append({
            "file_id": file_id,
            "file_name": file_name,
            "status": "gray",
            "length": file_size,
            "timestamp": timestamp
        })
    
    debug_logger.info(f"end insert {len(faqs)} faqs to mysql, user_id: {user_id}, kb_id: {kb_id}")

    # 返回成功响应
    msg = "success，后台正在飞速上传文件，请耐心等待"
    return sanic_json({"code": 200, "msg": msg, "data": data})


@get_time_async
@auth_required("read", check_kb_access=True)
async def list_docs(req: request):
    """获取知识库文档列表"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取请求参数
    user_id = safe_get(req, 'user_id')
    debug_logger.info("list_docs %s", user_id)

    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    debug_logger.info("kb_id: {}".format(kb_id))

    file_id = safe_get(req, 'file_id')
    page_id = safe_get(req, 'page_id', 1)  # 默认为第一页
    page_limit = safe_get(req, 'page_limit', 10)  # 默认每页显示10条记录

    # 获取文件信息
    data = []
    if file_id is None:
        file_infos = local_doc_qa.milvus_summary.get_files(user_id, kb_id)
    else:
        file_infos = local_doc_qa.milvus_summary.get_files(user_id, kb_id, file_id)

    # 统计各状态文件数量
    status_count = {}

    # 处理文件信息
    for file_info in file_infos:
        # 统计状态
        status = file_info[2]
        if status not in status_count:
            status_count[status] = 1
        else:
            status_count[status] += 1

        # 构建文件数据
        file_data = {
            "file_id": file_info[0],
            "file_name": file_info[1],
            "status": file_info[2],
            "bytes": file_info[3],
            "content_length": file_info[4],
            "timestamp": file_info[5],
            "file_location": file_info[6],
            "file_url": file_info[7],
            "chunks_number": file_info[8],
            "msg": file_info[9]
        }

        # 如果是FAQ文件，添加问题和答案
        if file_info[1].endswith('.faq'):
            faq_info = local_doc_qa.milvus_summary.get_faq(file_info[0])
            user_id, kb_id, question, answer, nos_keys = faq_info
            file_data['question'] = question
            file_data['answer'] = answer

        data.append(file_data)

    # 按时间戳排序，时间越新的越靠前
    data = sorted(data, key=lambda x: int(x['timestamp']), reverse=True)

    # 分页处理
    total_count = len(data)
    total_pages = (total_count + page_limit - 1) // page_limit

    # 验证页码是否有效
    if page_id > total_pages and total_count != 0:
        return sanic_json({
            "code": 2002,
            "msg": f'输入非法！page_id超过最大值，page_id: {page_id}，最大值：{total_pages}，请检查！'
        })

    # 计算当前页的数据范围
    start_index = (page_id - 1) * page_limit
    end_index = start_index + page_limit
    current_page_data = data[start_index:end_index]

    # 返回结果
    return sanic_json({
        "code": 200,
        "msg": "success",
        "data": {
            'total_page': total_pages,  # 总页数
            "total": total_count,  # 总文件数
            "status_count": status_count,  # 各状态的文件数
            "details": current_page_data,  # 当前页码下的文件目录
            "page_id": page_id,  # 当前页码,
            "page_limit": page_limit  # 每页显示的文件数
        }
    })


@get_time_async
@auth_required("write", check_kb_access=True)
async def delete_docs(req: request):
    """删除知识库中的文档"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取请求参数
    user_id = safe_get(req, 'user_id')
    debug_logger.info("delete_docs %s", user_id)

    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    file_ids = safe_get(req, "file_ids")

    # 验证知识库是否存在
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        return sanic_json({
            "code": 2003,
            "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids[0])
        })

    # 验证文件是否存在
    valid_file_infos = local_doc_qa.milvus_summary.check_file_exist(user_id, kb_id, file_ids)
    if len(valid_file_infos) == 0:
        return sanic_json({
            "code": 2004,
            "msg": "fail, files {} not found".format(file_ids)
        })

    # 获取有效的文件ID
    valid_file_ids = [file_info[0] for file_info in valid_file_infos]
    debug_logger.info("delete_docs valid_file_ids %s", valid_file_ids)

    # 从Milvus中删除数据
    expr = f"""kb_id == "{kb_id}" and file_id in {valid_file_ids}"""
    asyncio.create_task(run_in_background(local_doc_qa.milvus_kb.delete_expr, expr))

    # 从ES中删除数据
    file_chunks = local_doc_qa.milvus_summary.get_chunk_size(valid_file_ids)
    asyncio.create_task(run_in_background(local_doc_qa.es_client.delete_files, valid_file_ids, file_chunks))

    # 从数据库中删除相关记录
    local_doc_qa.milvus_summary.delete_files(kb_id, valid_file_ids)
    local_doc_qa.milvus_summary.delete_documents(valid_file_ids)
    local_doc_qa.milvus_summary.delete_faqs(valid_file_ids)

    # 删除文件系统中的文件
    for file_id in file_ids:
        try:
            # 删除上传目录
            upload_path = os.path.join(UPLOAD_ROOT_PATH, user_id)
            file_dir = os.path.join(upload_path, kb_id, file_id)
            debug_logger.info("delete_docs file_dir %s", file_dir)
            shutil.rmtree(file_dir)

            # 删除图片目录
            images_dir = os.path.join(IMAGES_ROOT_PATH, file_id)
            debug_logger.info("delete_docs images_dir %s", images_dir)
            shutil.rmtree(images_dir)
        except Exception as e:
            debug_logger.error("An error occurred while constructing file paths: %s", str(e))

    return sanic_json({
        "code": 200,
        "msg": "documents {} delete success".format(valid_file_ids)
    })
    

@get_time_async
@auth_required("admin", check_kb_access=True)
async def delete_knowledge_base(req: request):
    """删除知识库"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取请求参数
    user_id = safe_get(req, 'user_id')
    debug_logger.info("delete_knowledge_base %s", user_id)

    # 获取并处理知识库ID
    kb_ids = safe_get(req, 'kb_ids')
    kb_ids = [correct_kb_id(kb_id) for kb_id in kb_ids]

    # 验证知识库是否存在
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, kb_ids)
    if not_exist_kb_ids:
        return sanic_json({
            "code": 2003,
            "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids)
        })

    # 从Milvus中删除数据
    for kb_id in kb_ids:
        expr = f"kb_id == \"{kb_id}\""
        asyncio.create_task(run_in_background(local_doc_qa.milvus_kb.delete_expr, expr))

    # 处理每个知识库
    for kb_id in kb_ids:
        # 获取知识库中的文件
        file_infos = local_doc_qa.milvus_summary.get_files(user_id, kb_id)
        file_ids = [file_info[0] for file_info in file_infos]
        file_chunks = [file_info[8] for file_info in file_infos]

        # 从ES中删除文件
        asyncio.create_task(run_in_background(local_doc_qa.es_client.delete_files, file_ids, file_chunks))

        # 从数据库中删除文档和FAQ
        local_doc_qa.milvus_summary.delete_documents(file_ids)
        local_doc_qa.milvus_summary.delete_faqs(file_ids)

        # 删除文件系统中的知识库目录
        try:
            upload_path = os.path.join(UPLOAD_ROOT_PATH, user_id)
            file_dir = os.path.join(upload_path, kb_id)
            debug_logger.info("delete_knowledge_base file dir : %s", file_dir)
            shutil.rmtree(file_dir)
        except Exception as e:
            debug_logger.error("An error occurred while constructing file paths: %s", str(e))

        debug_logger.info(f"""delete knowledge base {kb_id} success""")

    # 从数据库中删除知识库
    local_doc_qa.milvus_summary.delete_knowledge_base(user_id, kb_ids)

    return sanic_json({
        "code": 200,
        "msg": "Knowledge Base {} delete success".format(kb_ids)
    })


@get_time_async
@auth_required("read", check_kb_access=True)
async def get_total_status(req: request):
    """获取知识库文件状态统计"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取请求参数
    user_id = safe_get(req, 'user_id')
    debug_logger.info('get_total_status %s', user_id)
    by_date = safe_get(req, 'by_date', False)

    # 确定要处理的用户列表
    if not user_id:
        users = local_doc_qa.milvus_summary.get_users()
        users = [user[0] for user in users]
    else:
        users = [user_id]

    # 初始化结果
    res = {}

    # 处理每个用户
    for user in users:
        res[user] = {}

        # 如果按日期统计
        if by_date:
            res[user] = local_doc_qa.milvus_summary.get_total_status_by_date(user)
            continue

        # 获取用户的所有知识库
        kbs = local_doc_qa.milvus_summary.get_knowledge_bases(user)

        # 统计每个知识库的文件状态
        for kb_id, kb_name in kbs:
            # 获取各状态的文件信息
            gray_file_infos = local_doc_qa.milvus_summary.get_file_by_status([kb_id], 'gray')
            red_file_infos = local_doc_qa.milvus_summary.get_file_by_status([kb_id], 'red')
            yellow_file_infos = local_doc_qa.milvus_summary.get_file_by_status([kb_id], 'yellow')
            green_file_infos = local_doc_qa.milvus_summary.get_file_by_status([kb_id], 'green')

            # 统计各状态的文件数量
            res[user][kb_name + kb_id] = {
                'green': len(green_file_infos),
                'yellow': len(yellow_file_infos),
                'red': len(red_file_infos),
                'gray': len(gray_file_infos)
            }

    return sanic_json({"code": 200, "status": res})


@get_time_async
@auth_required("admin", check_kb_access=True)
async def clean_files_by_status(req: request):
    """根据状态清理文件"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取请求参数
    user_id = safe_get(req, 'user_id')
    debug_logger.info('clean_files_by_status %s', user_id)

    # 获取并验证状态参数
    status = safe_get(req, 'status', default='gray')
    if status not in ['gray', 'red', 'yellow']:
        return sanic_json({
            "code": 2003,
            "msg": "fail, status {} must be in ['gray', 'red', 'yellow']".format(status)
        })

    # 获取知识库ID列表
    kb_ids = safe_get(req, 'kb_ids')
    kb_ids = [correct_kb_id(kb_id) for kb_id in kb_ids] if kb_ids else []

    # 如果未提供知识库ID，则获取用户的所有知识库
    if not kb_ids:
        kbs = local_doc_qa.milvus_summary.get_knowledge_bases(user_id)
        kb_ids = [kb[0] for kb in kbs]
    else:
        # 验证知识库是否存在
        not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, kb_ids)
        if not_exist_kb_ids:
            return sanic_json({
                "code": 2003,
                "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids)
            })

    # 获取指定状态的文件
    files_to_clean = local_doc_qa.milvus_summary.get_file_by_status(kb_ids, status)
    file_ids = [f[0] for f in files_to_clean]
    file_names = [f[1] for f in files_to_clean]
    debug_logger.info(f'{status} files number: {len(file_names)}')

    # 删除数据库中的文件记录
    if file_ids:
        for kb_id in kb_ids:
            local_doc_qa.milvus_summary.delete_files(kb_id, file_ids)

    # 返回成功响应
    return sanic_json({
        "code": 200,
        "msg": f"delete {status} files success",
        "data": file_names
    })
    

@get_time_async
@auth_required("read", check_kb_access=True)
async def local_doc_chat(req: request):
    """基于知识库的文档问答"""
    preprocess_start = time.perf_counter()
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取并验证用户信息
    user_id = safe_get(req, 'user_id')

    debug_logger.info('local_doc_chat %s', user_id)
    debug_logger.info('user_info %s', user_info)

    # 处理机器人配置
    bot_id = safe_get(req, 'bot_id')
    if bot_id:
        # 获取机器人配置
        if not local_doc_qa.milvus_summary.check_bot_is_exist(bot_id):
            return sanic_json({"code": 2003, "msg": "fail, Bot {} not found".format(bot_id)})

        bot_info = local_doc_qa.milvus_summary.get_bot(None, bot_id)[0]
        bot_id, bot_name, desc, image, prompt, welcome, kb_ids_str, upload_time, user_id, llm_setting = bot_info

        # 验证知识库绑定
        kb_ids = kb_ids_str.split(',')
        if not kb_ids:
            return sanic_json({"code": 2003, "msg": "fail, Bot {} unbound knowledge base.".format(bot_id)})

        # 设置提示词
        custom_prompt = prompt

        # 解析LLM设置
        if not llm_setting:
            return sanic_json({"code": 2003, "msg": "fail, Bot {} llm_setting is empty.".format(bot_id)})

        llm_setting = json.loads(llm_setting)
        rerank = llm_setting.get('rerank', True)
        only_need_search_results = llm_setting.get('only_need_search_results', False)
        need_web_search = llm_setting.get('networking', False)
        api_base = llm_setting.get('api_base', '')
        api_key = llm_setting.get('api_key', 'ollama')
        api_context_length = llm_setting.get('api_context_length', 4096)
        top_p = llm_setting.get('top_p', 0.99)
        temperature = llm_setting.get('temperature', 0.5)
        top_k = llm_setting.get('top_k', VECTOR_SEARCH_TOP_K)
        model = llm_setting.get('model', 'gpt-4o-mini')
        max_token = llm_setting.get('max_token')
        hybrid_search = llm_setting.get('hybrid_search', False)
        chunk_size = llm_setting.get('chunk_size', DEFAULT_PARENT_CHUNK_SIZE)
    else:
        # 从请求中获取参数
        kb_ids = safe_get(req, 'kb_ids')
        custom_prompt = safe_get(req, 'custom_prompt', None)
        rerank = safe_get(req, 'rerank', default=True)
        only_need_search_results = safe_get(req, 'only_need_search_results', False)
        need_web_search = safe_get(req, 'networking', False)

        # 处理API基础URL
        api_base = safe_get(req, 'api_base', '')
        api_base = api_base.replace('0.0.0.0', GATEWAY_IP).replace('127.0.0.1', GATEWAY_IP).replace('localhost',
                                                                                                    GATEWAY_IP)

        # 获取其他LLM参数
        api_key = safe_get(req, 'api_key', 'ollama')
        api_context_length = safe_get(req, 'api_context_length', 4096)
        top_p = safe_get(req, 'top_p', 0.99)
        temperature = safe_get(req, 'temperature', 0.5)
        top_k = safe_get(req, 'top_k', VECTOR_SEARCH_TOP_K)
        model = safe_get(req, 'model', 'gpt-4o-mini')
        max_token = safe_get(req, 'max_token')
        hybrid_search = safe_get(req, 'hybrid_search', False)
        chunk_size = safe_get(req, 'chunk_size', DEFAULT_PARENT_CHUNK_SIZE)

    debug_logger.info('rerank %s', rerank)

    # 验证知识库数量
    if len(kb_ids) > 20:
        return sanic_json({"code": 2005, "msg": "fail, kb_ids length should less than or equal to 20"})

    # 处理知识库ID
    kb_ids = [correct_kb_id(kb_id) for kb_id in kb_ids]

    # 获取问题和历史记录
    question = safe_get(req, 'question')
    streaming = safe_get(req, 'streaming', False)
    history = safe_get(req, 'history', [])

    # 验证top_k参数
    if top_k > 100:
        return sanic_json({"code": 2003, "msg": "fail, top_k should less than or equal to 100"})

    # 验证必要参数
    missing_params = []
    if not api_base:
        missing_params.append('api_base')
    if not api_key:
        missing_params.append('api_key')
    if not api_context_length:
        missing_params.append('api_context_length')
    if not top_p:
        missing_params.append('top_p')
    if not top_k:
        missing_params.append('top_k')
    if top_p == 1.0:
        top_p = 0.99
    if not temperature:
        missing_params.append('temperature')

    if missing_params:
        missing_params_str = " and ".join(missing_params) if len(missing_params) > 1 else missing_params[0]
        return sanic_json({"code": 2003, "msg": f"fail, {missing_params_str} is required"})

    # 验证流式响应和搜索结果模式不能同时开启
    if only_need_search_results and streaming:
        return sanic_json(
            {"code": 2006, "msg": "fail, only_need_search_results and streaming can't be True at the same time"})

    # 获取请求来源
    request_source = safe_get(req, 'source', 'unknown')

    # 记录请求参数
    debug_logger.info("history: %s ", history)
    debug_logger.info("question: %s", question)
    debug_logger.info("kb_ids: %s", kb_ids)
    debug_logger.info("user_id: %s", user_id)
    debug_logger.info("custom_prompt: %s", custom_prompt)
    debug_logger.info("model: %s", model)
    debug_logger.info("max_token: %s", max_token)
    debug_logger.info("request_source: %s", request_source)
    debug_logger.info("only_need_search_results: %s", only_need_search_results)
    debug_logger.info("bot_id: %s", bot_id)
    debug_logger.info("need_web_search: %s", need_web_search)
    debug_logger.info("api_base: %s", api_base)
    debug_logger.info("api_key: %s", api_key)
    debug_logger.info("api_context_length: %s", api_context_length)
    debug_logger.info("top_p: %s", top_p)
    debug_logger.info("top_k: %s", top_k)
    debug_logger.info("temperature: %s", temperature)
    debug_logger.info("hybrid_search: %s", hybrid_search)
    debug_logger.info("chunk_size: %s", chunk_size)

    # 初始化时间记录
    time_record = {}

    # 验证知识库
    if kb_ids:
        # 检查知识库是否存在
        not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, kb_ids)
        if not_exist_kb_ids:
            return sanic_json({"code": 2003, "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids)})

        # 添加FAQ知识库
        faq_kb_ids = [kb + '_FAQ' for kb in kb_ids]
        not_exist_faq_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, faq_kb_ids)
        exist_faq_kb_ids = [kb for kb in faq_kb_ids if kb not in not_exist_faq_kb_ids]
        debug_logger.info("exist_faq_kb_ids: %s", exist_faq_kb_ids)
        kb_ids += exist_faq_kb_ids

    # 检查知识库中是否有有效文件
    file_infos = []
    for kb_id in kb_ids:
        file_infos.extend(local_doc_qa.milvus_summary.get_files(user_id, kb_id))
    valid_files = [fi for fi in file_infos if fi[2] == 'green']
    if len(valid_files) == 0:
        debug_logger.info("valid_files is empty, use only chat mode.")
        kb_ids = []

    # 记录预处理时间
    preprocess_end = time.perf_counter()
    time_record['preprocess'] = round(preprocess_end - preprocess_start, 2)

    # 更新知识库最近访问时间
    qa_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    for kb_id in kb_ids:
        local_doc_qa.milvus_summary.update_knowledge_base_latest_qa_time(kb_id, qa_timestamp)

    debug_logger.info("streaming: %s", streaming)

    # 处理流式响应
    if streaming:
        debug_logger.info("start generate answer")

        async def generate_answer(response):
            """生成流式回答"""
            debug_logger.info("start generate...")
            async for resp, next_history in local_doc_qa.get_knowledge_based_answer(
                    model=model,
                    max_token=max_token,
                    kb_ids=kb_ids,
                    query=question,
                    retriever=local_doc_qa.retriever,
                    chat_history=history,
                    streaming=True,
                    rerank=rerank,
                    custom_prompt=custom_prompt,
                    time_record=time_record,
                    need_web_search=need_web_search,
                    hybrid_search=hybrid_search,
                    web_chunk_size=chunk_size,
                    temperature=temperature,
                    api_base=api_base,
                    api_key=api_key,
                    api_context_length=api_context_length,
                    top_p=top_p,
                    top_k=top_k
            ):
                chunk_data = resp["result"]
                if not chunk_data:
                    continue

                chunk_str = chunk_data[6:]
                if chunk_str.startswith("[DONE]"):
                    # 处理完成响应
                    retrieval_documents = format_source_documents(resp["retrieval_documents"])
                    source_documents = format_source_documents(resp["source_documents"])
                    result = next_history[-1][1]

                    # 记录完成时间
                    time_record['chat_completed'] = round(time.perf_counter() - preprocess_start, 2)
                    if time_record.get('llm_completed', 0) > 0:
                        time_record['tokens_per_second'] = round(
                            len(result) / time_record['llm_completed'], 2)

                    formatted_time_record = format_time_record(time_record)

                    # 保存问答记录
                    chat_data = {
                        'user_id': user_id,
                        'kb_ids': kb_ids,
                        'query': question,
                        "model": model,
                        "product_source": request_source,
                        'time_record': formatted_time_record,
                        'history': history,
                        'condense_question': resp['condense_question'],
                        'prompt': resp['prompt'],
                        'result': result,
                        'retrieval_documents': retrieval_documents,
                        'source_documents': source_documents,
                        'bot_id': bot_id
                    }
                    local_doc_qa.milvus_summary.add_qalog(**chat_data)
                    qa_logger.info("chat_data: %s", chat_data)
                    debug_logger.info("response: %s", chat_data['result'])

                    # 构建完成响应
                    stream_res = {
                        "code": 200,
                        "msg": "success stream chat",
                        "question": question,
                        "response": result,
                        "model": model,
                        "history": next_history,
                        "condense_question": resp['condense_question'],
                        "source_documents": source_documents,
                        "retrieval_documents": retrieval_documents,
                        "time_record": formatted_time_record,
                        "show_images": resp.get('show_images', [])
                    }
                else:
                    # 处理中间响应
                    time_record['rollback_length'] = resp.get('rollback_length', 0)
                    if 'first_return' not in time_record:
                        time_record['first_return'] = round(time.perf_counter() - preprocess_start, 2)

                    chunk_js = json.loads(chunk_str)
                    delta_answer = chunk_js["answer"]

                    # 构建中间响应
                    stream_res = {
                        "code": 200,
                        "msg": "success",
                        "question": "",
                        "response": delta_answer,
                        "history": [],
                        "source_documents": [],
                        "retrieval_documents": [],
                        "time_record": format_time_record(time_record),
                    }

                # 发送响应
                await response.write(f"data: {json.dumps(stream_res, ensure_ascii=False)}\n\n")
                if chunk_str.startswith("[DONE]"):
                    await response.eof()
                await asyncio.sleep(0.001)

        response_stream = ResponseStream(generate_answer, content_type='text/event-stream')
        return response_stream

    else:
        # 处理非流式响应
        debug_logger.info("start non-streaming answer generation")
        try:
            async for resp, history in local_doc_qa.get_knowledge_based_answer(
                    model=model,
                    max_token=max_token,
                    kb_ids=kb_ids,
                    query=question,
                    retriever=local_doc_qa.retriever,
                    chat_history=history,
                    streaming=False,
                    rerank=rerank,
                    custom_prompt=custom_prompt,
                    time_record=time_record,
                    only_need_search_results=only_need_search_results,
                    need_web_search=need_web_search,
                    hybrid_search=hybrid_search,
                    web_chunk_size=chunk_size,
                    temperature=temperature,
                    api_base=api_base,
                    api_key=api_key,
                    api_context_length=api_context_length,
                    top_p=top_p,
                    top_k=top_k
            ):
                pass

            # 如果只需要搜索结果，则直接返回
            if only_need_search_results:
                return sanic_json({
                    "code": 200,
                    "question": question,
                    "source_documents": format_source_documents(resp)
                })

            # 处理文档和检索结果
            retrieval_documents = format_source_documents(resp["retrieval_documents"])
            source_documents = format_source_documents(resp["source_documents"])
            formatted_time_record = format_time_record(time_record)

            # 构建聊天数据并保存
            chat_data = {
                'user_id': user_id,
                'kb_ids': kb_ids,
                'query': question,
                'time_record': formatted_time_record,
                'history': history,
                "condense_question": resp['condense_question'],
                "model": model,
                "product_source": request_source,
                'retrieval_documents': retrieval_documents,
                'prompt': resp['prompt'],
                'result': resp['result'],
                'source_documents': source_documents,
                'bot_id': bot_id
            }

            # 保存问答记录
            local_doc_qa.milvus_summary.add_qalog(**chat_data)
            qa_logger.info("chat_data: %s", chat_data)
            debug_logger.info("response: %s", chat_data['result'])

            # 返回响应
            return sanic_json({
                "code": 200,
                "msg": "success no stream chat",
                "question": question,
                "response": resp["result"],
                "model": model,
                "history": history,
                "condense_question": resp['condense_question'],
                "source_documents": source_documents,
                "retrieval_documents": retrieval_documents,
                "time_record": formatted_time_record
            })

        except Exception as e:
            debug_logger.error(f"Error in non-streaming answer generation: {str(e)}")
            return sanic_json({
                "code": 5000,
                "msg": f"Internal server error: {str(e)}"
            })


@get_time_async
@auth_required("read", check_kb_access=True)
async def get_doc_completed(req: request):
    """获取文档的分块内容"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取并验证用户信息
    user_id = safe_get(req, 'user_id')
    debug_logger.info("get_doc_chunks %s", user_id)

    # 获取知识库ID和文件ID
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    debug_logger.info("kb_id: {}".format(kb_id))

    file_id = safe_get(req, 'file_id')
    if not file_id:
        return sanic_json({"code": 2005, "msg": "fail, file_id is None"})
    debug_logger.info("file_id: {}".format(file_id))

    # 获取分页参数
    page_id = safe_get(req, 'page_id', 1)  # 默认为第一页
    page_limit = safe_get(req, 'page_limit', 10)  # 默认每页显示10条记录

    try:
        # 获取文档分块数据
        sorted_json_datas = local_doc_qa.milvus_summary.get_document_by_file_id(file_id)
        chunks = [json_data['kwargs'] for json_data in sorted_json_datas]

        # 计算分页信息
        total_count = len(chunks)
        total_pages = (total_count + page_limit - 1) // page_limit

        # 验证页码是否有效
        if page_id > total_pages and total_count != 0:
            return sanic_json({
                "code": 2002,
                "msg": f'输入非法！page_id超过最大值，page_id: {page_id}，最大值：{total_pages}，请检查！'
            })

        # 获取当前页数据
        start_index = (page_id - 1) * page_limit
        end_index = start_index + page_limit
        current_page_chunks = chunks[start_index:end_index]

        # 处理图片引用
        for chunk in current_page_chunks:
            chunk['page_content'] = replace_image_references(chunk['page_content'], file_id)

        # 获取文件路径
        file_location = local_doc_qa.milvus_summary.get_file_location(file_id)
        file_path = os.path.dirname(file_location) if file_location else ""

        # 返回成功响应
        return sanic_json({
            "code": 200,
            "msg": "success",
            "chunks": current_page_chunks,
            "file_path": file_path,
            "page_id": page_id,
            "page_limit": page_limit,
            "total_count": total_count
        })

    except Exception as e:
        debug_logger.error(f"Error in get_doc_completed: {str(e)}")
        return sanic_json({
            "code": 5000,
            "msg": f"Internal server error: {str(e)}"
        })


@get_time_async
@auth_required("read", check_kb_access=True)
async def get_qa_info(req: request):
    """获取问答记录信息"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取基本参数
    any_kb_id = safe_get(req, 'any_kb_id')
    user_id = safe_get(req, 'user_id')

    # 验证必要参数
    if user_id is None and not any_kb_id:
        return sanic_json({"code": 2005, "msg": "fail, user_id and any_kb_id is None"})

    # 处理知识库ID
    if any_kb_id:
        any_kb_id = correct_kb_id(any_kb_id)
        debug_logger.info("get_qa_info %s", any_kb_id)

    # 验证用户信息
    if user_id:
        user_info = safe_get(req, 'user_info', "1234")
        passed, msg = check_user_id_and_user_info(user_id, user_info)
        if not passed:
            return sanic_json({"code": 2001, "msg": msg})
        debug_logger.info("get_qa_info %s", user_id)

    # 获取查询参数
    query = safe_get(req, 'query')
    bot_id = safe_get(req, 'bot_id')
    qa_ids = safe_get(req, "qa_ids")
    time_start = safe_get(req, 'time_start')
    time_end = safe_get(req, 'time_end')

    # 处理时间范围
    time_range = get_time_range(time_start, time_end)
    if not time_range:
        return sanic_json({
            "code": 2002,
            "msg": f'输入非法！time_start格式错误，time_start: {time_start}，示例：2024-10-05，请检查！'
        })

    # 处理仅需计数的情况
    only_need_count = safe_get(req, 'only_need_count', False)
    debug_logger.info(f"only_need_count: {only_need_count}")

    if only_need_count:
        try:
            need_info = ["timestamp"]
            qa_infos = local_doc_qa.milvus_summary.get_qalog_by_filter(
                need_info=need_info,
                user_id=user_id,
                time_range=time_range
            )

            # 按天统计问答数量
            qa_infos = sorted(qa_infos, key=lambda x: x['timestamp'])
            qa_infos = [qa_info['timestamp'] for qa_info in qa_infos]
            qa_infos = [qa_info[:10] for qa_info in qa_infos]
            qa_infos_by_day = dict(Counter(qa_infos))

            return sanic_json({
                "code": 200,
                "msg": "success",
                "qa_infos_by_day": qa_infos_by_day
            })
        except Exception as e:
            debug_logger.error(f"Error in get_qa_info (count only): {str(e)}")
            return sanic_json({
                "code": 5000,
                "msg": f"Internal server error: {str(e)}"
            })

    # 处理分页和导出
    try:
        page_id = safe_get(req, 'page_id', 1)
        page_limit = safe_get(req, 'page_limit', 10)

        default_need_info = [
            "qa_id", "user_id", "bot_id", "kb_ids", "query", "model",
            "product_source", "time_record", "history", "condense_question",
            "prompt", "result", "retrieval_documents", "source_documents", "timestamp"
        ]
        need_info = safe_get(req, 'need_info', default_need_info)
        save_to_excel = safe_get(req, 'save_to_excel', False)

        # 获取问答记录
        qa_infos = local_doc_qa.milvus_summary.get_qalog_by_filter(
            need_info=need_info,
            user_id=user_id,
            query=query,
            bot_id=bot_id,
            time_range=time_range,
            any_kb_id=any_kb_id,
            qa_ids=qa_ids
        )

        # 处理导出到Excel的情况
        if save_to_excel:
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            file_name = f"QAnything_QA_{timestamp}.xlsx"
            file_path = export_qalogs_to_excel(qa_infos, need_info, file_name)
            return await response.file(
                file_path,
                filename=file_name,
                mime_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename="{file_name}"'}
            )

        # 处理分页
        total_count = len(qa_infos)
        total_pages = (total_count + page_limit - 1) // page_limit

        if page_id > total_pages and total_count != 0:
            return sanic_json({
                "code": 2002,
                "msg": f'输入非法！page_id超过最大值，page_id: {page_id}，最大值：{total_pages}，请检查！'
            })

        # 获取当前页数据
        start_index = (page_id - 1) * page_limit
        end_index = start_index + page_limit
        current_qa_infos = qa_infos[start_index:end_index]

        msg = f"检测到的Log总数为{total_count}, 本次返回page_id为{page_id}的数据，每页显示{page_limit}条"

        return sanic_json({
            "code": 200,
            "msg": msg,
            "page_id": page_id,
            "page_limit": page_limit,
            "qa_infos": current_qa_infos,
            "total_count": total_count
        })

    except Exception as e:
        debug_logger.error(f"Error in get_qa_info: {str(e)}")
        return sanic_json({
            "code": 5000,
            "msg": f"Internal server error: {str(e)}"
        })


@get_time_async
@auth_required("read", check_kb_access=True)
async def get_random_qa(req: request):
    """获取随机问答记录"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取请求参数
    limit = safe_get(req, 'limit', 10)
    time_start = safe_get(req, 'time_start')
    time_end = safe_get(req, 'time_end')
    need_info = safe_get(req, 'need_info')

    # 处理时间范围
    time_range = get_time_range(time_start, time_end)
    if not time_range:
        return sanic_json({
            "code": 2002,
            "msg": f'输入非法！time_start格式错误，time_start: {time_start}，示例：2024-10-05，请检查！'
        })

    try:
        debug_logger.info(f"get_random_qa limit: {limit}, time_range: {time_range}")

        # 获取随机问答记录
        qa_infos = local_doc_qa.milvus_summary.get_random_qa_infos(
            limit=limit,
            time_range=time_range,
            need_info=need_info
        )

        # 获取统计信息
        counts = local_doc_qa.milvus_summary.get_statistic(time_range=time_range)

        return sanic_json({
            "code": 200,
            "msg": "success",
            "total_users": counts["total_users"],
            "total_queries": counts["total_queries"],
            "qa_infos": qa_infos
        })

    except Exception as e:
        debug_logger.error(f"Error in get_random_qa: {str(e)}")
        return sanic_json({
            "code": 5000,
            "msg": f"Internal server error: {str(e)}"
        })


@get_time_async
@auth_required("read", check_kb_access=True)
async def get_related_qa(req: request):
    """获取相关问答记录"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取并验证问答ID
    qa_id = safe_get(req, 'qa_id')
    if not qa_id:
        return sanic_json({"code": 2005, "msg": "fail, qa_id is None"})

    # 获取其他参数
    need_info = safe_get(req, 'need_info')
    need_more = safe_get(req, 'need_more', False)
    debug_logger.info("get_related_qa %s", qa_id)

    try:
        # 获取相关问答记录
        qa_log, recent_logs, older_logs = local_doc_qa.milvus_summary.get_related_qa_infos(
            qa_id,
            need_info,
            need_more
        )

        # 处理最近的问答记录
        recent_sections = defaultdict(list)
        for log in recent_logs:
            recent_sections[log['kb_ids']].append(log)

        # 为最近的问答记录添加知识库名称
        for i, kb_ids in enumerate(list(recent_sections.keys())):
            try:
                kb_names = local_doc_qa.milvus_summary.get_knowledge_base_name(json.loads(kb_ids))
                kb_names = [kb_name for user_id, kb_id, kb_name in kb_names]
                kb_names = ','.join(kb_names)
                recent_sections[i] = recent_sections.pop(kb_ids)
                for log in recent_sections[i]:
                    log['kb_names'] = kb_names
            except Exception as e:
                debug_logger.error(f"Error processing recent kb_ids {kb_ids}: {str(e)}")
                recent_sections[i] = recent_sections.pop(kb_ids)
                for log in recent_sections[i]:
                    log['kb_names'] = "未知知识库"

        # 处理较早的问答记录
        older_sections = defaultdict(list)
        for log in older_logs:
            older_sections[log['kb_ids']].append(log)

        # 为较早的问答记录添加知识库名称
        for i, kb_ids in enumerate(list(older_sections.keys())):
            try:
                kb_names = local_doc_qa.milvus_summary.get_knowledge_base_name(json.loads(kb_ids))
                kb_names = [kb_name for user_id, kb_id, kb_name in kb_names]
                kb_names = ','.join(kb_names)
                older_sections[i] = older_sections.pop(kb_ids)
                for log in older_sections[i]:
                    log['kb_names'] = kb_names
            except Exception as e:
                debug_logger.error(f"Error processing older kb_ids {kb_ids}: {str(e)}")
                older_sections[i] = older_sections.pop(kb_ids)
                for log in older_sections[i]:
                    log['kb_names'] = "未知知识库"

        return sanic_json({
            "code": 200,
            "msg": "success",
            "qa_info": qa_log,
            "recent_sections": recent_sections,
            "older_sections": older_sections
        })

    except Exception as e:
        debug_logger.error(f"Error in get_related_qa: {str(e)}")
        return sanic_json({
            "code": 5000,
            "msg": f"Internal server error: {str(e)}"
        })


@get_time_async
@auth_required("read", check_kb_access=True)
async def get_user_id(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    debug_logger.info("kb_id: {}".format(kb_id))
    user_id = local_doc_qa.milvus_summary.get_user_by_kb_id(kb_id)
    if not user_id:
        return sanic_json({"code": 2003, "msg": "fail, knowledge Base {} not found".format(kb_id)})
    else:
        return sanic_json({"code": 200, "msg": "success", "user_id": user_id})


@get_time_async
@auth_required("read", check_kb_access=True)
async def get_doc(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    doc_id = safe_get(req, 'doc_id')
    debug_logger.info("get_doc %s", doc_id)
    if not doc_id:
        return sanic_json({"code": 2005, "msg": "fail, doc_id is None"})
    doc_json_data = local_doc_qa.milvus_summary.get_document_by_doc_id(doc_id)
    return sanic_json({"code": 200, "msg": "success", "doc_text": doc_json_data['kwargs']})


@get_time_async
@auth_required("read", check_kb_access=True)
async def get_rerank_results(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    query = safe_get(req, 'query')
    if not query:
        return sanic_json({"code": 2005, "msg": "fail, query is None"})
    doc_ids = safe_get(req, 'doc_ids')
    doc_strs = safe_get(req, 'doc_strs')
    if not doc_ids and not doc_strs:
        return sanic_json({"code": 2005, "msg": "fail, doc_ids is None and doc_strs is None"})
    if doc_ids:
        rerank_results = await local_doc_qa.get_rerank_results(query, doc_ids=doc_ids)
    else:
        rerank_results = await local_doc_qa.get_rerank_results(query, doc_strs=doc_strs)

    return sanic_json({"code": 200, "msg": "success", "rerank_results": format_source_documents(rerank_results)})


@get_time_async
@auth_required("read", check_kb_access=True)
async def get_user_status(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info("get_user_status %s", user_id)
    user_status = local_doc_qa.milvus_summary.get_user_status(user_id)
    if user_status is None:
        return sanic_json({"code": 2003, "msg": "fail, user {} not found".format(user_id)})
    if user_status == 0:
        status = 'green'
    else:
        status = 'red'
    return sanic_json({"code": 200, "msg": "success", "status": status})


@get_time_async
@auth_required("write", check_kb_access=True)
async def update_chunks(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info("update_chunks %s", user_id)
    doc_id = safe_get(req, 'doc_id')
    debug_logger.info(f"doc_id: {doc_id}")
    
    # 检查是否有正在处理的文件
    yellow_files = local_doc_qa.milvus_summary.get_files_by_status("yellow")
    if len(yellow_files) > 0:
        return sanic_json({"code": 2002,
                           "msg": f"fail, currently, there are {len(yellow_files)} files being parsed, please wait for all files to finish parsing before updating the chunk."})
    
    # 获取更新内容和分块大小
    update_content = safe_get(req, 'update_content')
    debug_logger.info(f"update_content: {update_content}")
    chunk_size = safe_get(req, 'chunk_size', DEFAULT_PARENT_CHUNK_SIZE)
    debug_logger.info(f"chunk_size: {chunk_size}")
    
    # 检查内容长度
    update_content_tokens = num_tokens_embed(update_content)
    if update_content_tokens > chunk_size:
        return sanic_json({"code": 2003, "msg": f"fail, update_content too long, please reduce the length, "
                                                f"your update_content tokens is {update_content_tokens}, "
                                                f"the max tokens is {chunk_size}"})
    
    # 获取文档信息
    doc_json = local_doc_qa.milvus_summary.get_document_by_doc_id(doc_id)
    if not doc_json:
        return sanic_json({"code": 2004, "msg": "fail, DocId {} not found".format(doc_id)})
    
    # 创建新文档对象
    doc = Document(page_content=update_content, metadata=doc_json['kwargs']['metadata'])
    doc.metadata['doc_id'] = doc_id
    
    # 更新数据库中的文档
    local_doc_qa.milvus_summary.update_document(doc_id, update_content)
    
    # 从向量库中删除旧文档
    try:
        expr = f'doc_id == "{doc_id}"'
        debug_logger.info(f"删除向量库中的文档，表达式: {expr}")
        
        # 检查milvus_kb是否已初始化
        if not hasattr(local_doc_qa, 'milvus_kb') or local_doc_qa.milvus_kb is None:
            debug_logger.error("milvus_kb未初始化")
            return sanic_json({"code": 5000, "msg": "Internal error: milvus_kb not initialized"})
        
        # 尝试获取匹配的文档
        chunks = local_doc_qa.milvus_kb.get_local_chunks(expr)
        if chunks is None:
            debug_logger.warning(f"未找到匹配表达式 '{expr}' 的文档")
        else:
            debug_logger.info(f"找到 {len(chunks)} 个匹配的文档")
            local_doc_qa.milvus_kb.delete_expr(expr)
    except Exception as e:
        debug_logger.error(f"删除向量库文档时出错: {str(e)}")
        # 继续执行，不中断流程
    
    # 插入新文档到向量库
    try:
        await local_doc_qa.retriever.insert_documents([doc], chunk_size, True)
    except Exception as e:
        debug_logger.error(f"插入新文档到向量库时出错: {str(e)}")
        return sanic_json({"code": 5000, "msg": f"Failed to insert document: {str(e)}"})
    
    return sanic_json({"code": 200, "msg": "success update doc_id {}".format(doc_id)})


@get_time_async
@auth_required("read", check_kb_access=True)
async def get_file_base64(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    file_id = safe_get(req, 'file_id')
    debug_logger.info("get_file_base64 %s", file_id)
    file_location = local_doc_qa.milvus_summary.get_file_location(file_id)
    debug_logger.info("file_location %s", file_location)
    # file_location = '/home/liujx/Downloads/2021-08-01 00:00:00.pdf'
    if not file_location:
        return sanic_json({"code": 2005, "msg": "fail, file_id is Invalid"})
    with open(file_location, "rb") as f:
        file_base64 = base64.b64encode(f.read()).decode()
    return sanic_json({"code": 200, "msg": "success", "file_base64": file_base64})
