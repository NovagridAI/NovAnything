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
    if role == "admin" or user_id == owner_id:
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

    if not kb_id:
        return sanic_json({"code": 400, "msg": "知识库ID不能为空"})

    # 检查知识库是否存在
    query = "SELECT kb_id, kb_name, user_id FROM KnowledgeBase WHERE kb_id = %s AND deleted = 0"
    kb_info = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    if not kb_info:
        return sanic_json({"code": 404, "msg": "知识库不存在"})

    kb_name = kb_info[0][1]
    owner_id = kb_info[0][2]  # 使用user_id作为owner_id

    # 获取所有者信息
    owner_name = _get_subject_name(local_doc_qa, 'user', owner_id)

    # 获取所有权限记录
    query = """
        SELECT id, subject_type, subject_id, permission_type
        FROM KnowledgeBaseAccess 
        WHERE kb_id = %s
        ORDER BY subject_type, permission_type
    """
    access_records = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)

    # 处理权限记录
    access_list = []
    for record in access_records:
        access_id, subject_type, subject_id, access_level = record
        subject_name = _get_subject_name(local_doc_qa, subject_type, subject_id)

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
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
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

    # 获取知识库文档数量
    query = "SELECT COUNT(*) FROM Document WHERE kb_id = %s"
    doc_count_result = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    doc_count = doc_count_result[0][0] if doc_count_result else 0

    # 获取知识库最近更新的文档
    query = """
        SELECT doc_id, doc_name, update_time 
        FROM Document 
        WHERE kb_id = %s 
        ORDER BY update_time DESC 
        LIMIT 5
    """
    recent_docs = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    recent_docs_list = []
    for doc in recent_docs:
        recent_docs_list.append({
            "doc_id": doc[0],
            "doc_name": doc[1],
            "update_time": doc[2].strftime("%Y-%m-%d %H:%M:%S") if doc[2] else None
        })

    # 如果用户是管理员或知识库所有者，获取知识库的访问权限列表
    access_list = []
    if role == "admin" or user_id == owner_id:
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
        "doc_count": doc_count,
        "recent_docs": recent_docs_list,
        "user_access": {
            "access_level": access_level,
            "access_source": access_source,
            "is_owner": user_id == owner_id,
            "is_admin": role == "admin"
        }
    }

    # 如果用户是管理员或知识库所有者，添加访问权限列表
    if role == "admin" or user_id == owner_id:
        result["access_list"] = access_list

    return sanic_json({"code": 200, "msg": "获取知识库详细信息成功", "data": result})


@get_time_async
@auth_required("admin")
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
    query = "SELECT user_id FROM User WHERE user_id = %s AND status = 'active'"
    if not local_doc_qa.milvus_summary.execute_query_(query, (new_owner_id,), fetch=True):
        return sanic_json({"code": 404, "msg": "新所有者不存在或已被禁用"})

    # 如果新所有者与当前所有者相同，则无需转移
    if new_owner_id == current_owner_id:
        return sanic_json({"code": 200, "msg": "新所有者与当前所有者相同，无需转移"})

    try:
        # 更新知识库所有者
        update_query = "UPDATE KnowledgeBase SET owner_id = %s WHERE kb_id = %s"
        local_doc_qa.milvus_summary.execute_query_(update_query, (new_owner_id, kb_id), commit=True)

        # 确保新所有者有admin权限
        # 先检查是否已有权限记录
        query = """
            SELECT access_id FROM KnowledgeBaseAccess 
            WHERE kb_id = %s AND subject_type = 'user' AND subject_id = %s
        """
        existing_access = local_doc_qa.milvus_summary.execute_query_(
            query, (kb_id, new_owner_id), fetch=True
        )

        if existing_access:
            # 更新权限级别为admin
            update_query = """
                UPDATE KnowledgeBaseAccess SET access_level = 'admin'
                WHERE kb_id = %s AND subject_type = 'user' AND subject_id = %s
            """
            local_doc_qa.milvus_summary.execute_query_(
                update_query, (kb_id, new_owner_id), commit=True
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
    kb_name = safe_get(req, 'kb_name')
    debug_logger.info("kb_name: %s", kb_name)
    default_kb_id = 'KB' + uuid.uuid4().hex
    kb_id = safe_get(req, 'kb_id', default_kb_id)
    kb_id = correct_kb_id(kb_id)

    if not kb_name:
        return sanic_json({"code": 400, "msg": "知识库名称不能为空"})

    # 检查知识库ID是否已存在
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, [kb_id])
    if not not_exist_kb_ids:
        return sanic_json({"code": 2001, "msg": "知识库ID {} 已经存在".format(kb_id)})

    try:
        local_doc_qa.milvus_summary.new_milvus_base(kb_id, user_id, kb_name)
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M")

        return sanic_json({
            "code": 200,
            "msg": "知识库创建成功",
            "data": {"kb_id": kb_id, "kb_name": kb_name, "timestamp": timestamp}
        })
    except Exception as e:
        debug_logger.error(f"创建知识库失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"创建知识库失败: {str(e)}"})


@get_time_async
@auth_required("write")
async def rename_knowledge_base(req: request):
    """重命名知识库"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    kb_id = safe_get(req, 'kb_id')
    new_name = safe_get(req, 'new_name')

    if not kb_id or not new_name:
        return sanic_json({"code": 400, "msg": "知识库ID和新名称不能为空"})

    # 检查知识库是否存在
    query = "SELECT kb_id, owner_id FROM KnowledgeBase WHERE kb_id = %s"
    kb_info = local_doc_qa.milvus_summary.execute_query_(query, (kb_id,), fetch=True)
    if not kb_info:
        return sanic_json({"code": 404, "msg": "知识库不存在"})

    # 检查用户是否有权限修改（管理员或知识库所有者）
    owner_id = kb_info[0][1]
    if user_id != owner_id and req.ctx.user.get("role") != "admin":
        # 检查用户是否有write权限
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
    query = "UPDATE KnowledgeBase SET kb_name = %s, update_time = NOW() WHERE kb_id = %s"
    try:
        local_doc_qa.milvus_summary.execute_query_(query, (new_name, kb_id), commit=True)
        return sanic_json({"code": 200, "msg": "知识库重命名成功"})
    except Exception as e:
        debug_logger.error(f"重命名知识库失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"重命名知识库失败: {str(e)}"})


@get_time_async
@auth_required("write", check_kb_access=True)
async def upload_weblink(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info("upload_weblink %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
        return sanic_json({"code": 2001, "msg": msg, "data": [{}]})

    url = safe_get(req, 'url')
    if url:
        urls = [url]
        # 如果URL以/结尾，先去除这个/
        if url.endswith('/'):
            url = url[:-1]
        titles = [safe_get(req, 'title', url.split('/')[-1]) + '.web']
    else:
        urls = safe_get(req, 'urls')
        titles = safe_get(req, 'titles')
        if len(urls) != len(titles):
            return sanic_json({"code": 2003, "msg": "fail, urls and titles length not equal"})

    for url in urls:
        # url 需要以http开头
        if not url.startswith('http'):
            return sanic_json({"code": 2001, "msg": "fail, url must start with 'http'"})
        # url 长度不能超过2048
        if len(url) > 2048:
            return sanic_json({"code": 2002, "msg": f"fail, url too long, max length is 2048."})

    file_names = []
    for title in titles:
        debug_logger.info('ori name: %s', title)
        file_name = re.sub(r'[\uFF01-\uFF5E\u3000-\u303F]', '', title)
        debug_logger.info('cleaned name: %s', file_name)
        file_name = truncate_filename(file_name, max_length=110)
        file_names.append(file_name)

    mode = safe_get(req, 'mode', default='soft')  # soft代表不上传同名文件，strong表示强制上传同名文件
    debug_logger.info("mode: %s", mode)
    chunk_size = safe_get(req, 'chunk_size', default=DEFAULT_PARENT_CHUNK_SIZE)
    debug_logger.info("chunk_size: %s", chunk_size)

    exist_file_names = []
    if mode == 'soft':
        exist_files = local_doc_qa.milvus_summary.check_file_exist_by_name(user_id, kb_id, file_names)
        exist_file_names = [f[1] for f in exist_files]
        for exist_file in exist_files:
            file_id, file_name, file_size, status = exist_file
            debug_logger.info(f"{url}, {status}, existed files, skip upload")
            # await post_data(user_id, -1, file_id, status, msg='existed files, skip upload')
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")

    data = []
    for url, file_name in zip(urls, file_names):
        if file_name in exist_file_names:
            continue
        local_file = LocalFile(user_id, kb_id, url, file_name)
        file_id = local_file.file_id
        file_size = len(local_file.file_content)
        file_location = local_file.file_location
        msg = local_doc_qa.milvus_summary.add_file(file_id, user_id, kb_id, file_name, file_size, file_location,
                                                   chunk_size, timestamp, url)
        debug_logger.info(f"{url}, {file_name}, {file_id}, {msg}")
        data.append({"file_id": file_id, "file_name": file_name, "file_url": url, "status": "gray", "bytes": 0,
                     "timestamp": timestamp})
        # asyncio.create_task(local_doc_qa.insert_files_to_milvus(user_id, kb_id, [local_file]))
    if exist_file_names:
        msg = f'warning，当前的mode是soft，无法上传同名文件{exist_file_names}，如果想强制上传同名文件，请设置mode：strong'
    else:
        msg = "success，后台正在飞速上传文件，请耐心等待"
    return sanic_json({"code": 200, "msg": msg, "data": data})


@get_time_async
@auth_required("write", check_kb_access=True)
async def upload_files(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info("upload_files %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    debug_logger.info("kb_id %s", kb_id)
    mode = safe_get(req, 'mode', default='soft')  # soft代表不上传同名文件，strong表示强制上传同名文件
    debug_logger.info("mode: %s", mode)
    chunk_size = safe_get(req, 'chunk_size', default=DEFAULT_PARENT_CHUNK_SIZE)
    debug_logger.info("chunk_size: %s", chunk_size)
    use_local_file = safe_get(req, 'use_local_file', 'false')
    if use_local_file == 'true':
        files = read_files_with_extensions()
    else:
        files = req.files.getlist('files')
    debug_logger.info(f"{user_id} upload files number: {len(files)}")
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
        return sanic_json({"code": 2001, "msg": msg, "data": [{}]})

    exist_files = local_doc_qa.milvus_summary.get_files(user_id, kb_id)
    if len(exist_files) + len(files) > 10000:
        return sanic_json({"code": 2002,
                           "msg": f"fail, exist files is {len(exist_files)}, upload files is {len(files)}, total files is {len(exist_files) + len(files)}, max length is 10000."})

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
        # # 使用正则表达式替换以%开头的字符串
        # file_name = re.sub(r'%\w+', '', file_name)
        # 删除掉全角字符
        file_name = re.sub(r'[\uFF01-\uFF5E\u3000-\u303F]', '', file_name)
        debug_logger.info('cleaned name: %s', file_name)
        # max_length = 255 - len(construct_qanything_local_file_nos_key_prefix(file_id)) == 188
        file_name = truncate_filename(file_name, max_length=110)
        file_names.append(file_name)

    exist_file_names = []
    if mode == 'soft':
        exist_files = local_doc_qa.milvus_summary.check_file_exist_by_name(user_id, kb_id, file_names)
        exist_file_names = [f[1] for f in exist_files]
        for exist_file in exist_files:
            file_id, file_name, file_size, status = exist_file
            debug_logger.info(f"{file_name}, {status}, existed files, skip upload")
            # await post_data(user_id, -1, file_id, status, msg='existed files, skip upload')

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")

    failed_files = []
    for file, file_name in zip(files, file_names):
        if file_name in exist_file_names:
            continue
        local_file = LocalFile(user_id, kb_id, file, file_name)
        chars = fast_estimate_file_char_count(local_file.file_location)
        debug_logger.info(f"{file_name} char_size: {chars}")
        if chars and chars > MAX_CHARS:
            debug_logger.warning(f"fail, file {file_name} chars is {chars}, max length is {MAX_CHARS}.")
            # return sanic_json({"code": 2003, "msg": f"fail, file {file_name} chars is too much, max length is {MAX_CHARS}."})
            failed_files.append(file_name)
            continue
        file_id = local_file.file_id
        file_size = len(local_file.file_content)
        file_location = local_file.file_location
        local_files.append(local_file)
        msg = local_doc_qa.milvus_summary.add_file(file_id, user_id, kb_id, file_name, file_size, file_location,
                                                   chunk_size, timestamp)
        debug_logger.info(f"{file_name}, {file_id}, {msg}")
        data.append(
            {"file_id": file_id, "file_name": file_name, "status": "gray", "bytes": len(local_file.file_content),
             "timestamp": timestamp, "estimated_chars": chars})

    # asyncio.create_task(local_doc_qa.insert_files_to_milvus(user_id, kb_id, local_files))
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
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info("upload_faqs %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    debug_logger.info("kb_id %s", kb_id)
    faqs = safe_get(req, 'faqs')
    chunk_size = safe_get(req, 'chunk_size', default=DEFAULT_PARENT_CHUNK_SIZE)
    debug_logger.info("chunk_size: %s", chunk_size)

    # 增加上传文件的功能和上传文件的检查解析
    file_status = {}
    if faqs is None:
        files = req.files.getlist('files')
        faqs = []
        for file in files:
            debug_logger.info('ori name: %s', file.name)
            file_name = urllib.parse.unquote(file.name, encoding='UTF-8')
            debug_logger.info('decode name: %s', file_name)
            # 删除掉全角字符
            file_name = re.sub(r'[\uFF01-\uFF5E\u3000-\u303F]', '', file_name)
            file_name = file_name.replace("/", "_")
            debug_logger.info('cleaned name: %s', file_name)
            file_name = truncate_filename(file_name)
            file_faqs = check_and_transform_excel(file.body)
            if isinstance(file_faqs, str):
                file_status[file_name] = file_faqs
            else:
                faqs.extend(file_faqs)
                file_status[file_name] = "success"

    if len(faqs) > 1000:
        return sanic_json({"code": 2002, "msg": f"fail, faqs too many, max length is 1000."})

    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
        return sanic_json({"code": 2001, "msg": msg})

    data = []
    local_files = []
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")
    debug_logger.info(f"start insert {len(faqs)} faqs to mysql, user_id: {user_id}, kb_id: {kb_id}")
    for faq in tqdm(faqs):
        ques = faq['question']
        if len(ques) > 512 or len(faq['answer']) > 2048:
            return sanic_json(
                {"code": 2003, "msg": f"fail, faq too long, max length of question is 512, answer is 2048."})
        file_name = f"FAQ_{ques}.faq"
        file_name = file_name.replace("/", "_").replace(":", "_")  # 文件名中的/和：会导致写入时出错
        file_name = simplify_filename(file_name)
        file_size = len(ques) + len(faq['answer'])
        # faq_id = local_doc_qa.milvus_summary.get_faq_by_question(ques, kb_id)
        # if faq_id:
        #     debug_logger.info(f"faq question {ques} already exist, skip")
        #     data.append({
        #         "file_id": faq_id,
        #         "file_name": file_name,
        #         "status": "green",
        #         "length": file_size,
        #         "timestamp": local_doc_qa.milvus_summary.get_file_timestamp(faq_id)
        #     })
        #     continue
        local_file = LocalFile(user_id, kb_id, faq, file_name)
        file_id = local_file.file_id
        file_location = local_file.file_location
        local_files.append(local_file)
        local_doc_qa.milvus_summary.add_faq(file_id, user_id, kb_id, faq['question'], faq['answer'],
                                            faq.get('nos_keys', ''))
        local_doc_qa.milvus_summary.add_file(file_id, user_id, kb_id, file_name, file_size, file_location,
                                             chunk_size, timestamp)
        # debug_logger.info(f"{file_name}, {file_id}, {msg}, {faq}")
        data.append(
            {"file_id": file_id, "file_name": file_name, "status": "gray", "length": file_size,
             "timestamp": timestamp})
    debug_logger.info(f"end insert {len(faqs)} faqs to mysql, user_id: {user_id}, kb_id: {kb_id}")

    msg = "success，后台正在飞速上传文件，请耐心等待"
    return sanic_json({"code": 200, "msg": msg, "data": data})


@get_time_async
@auth_required("read", check_kb_access=True)
async def list_docs(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info("list_docs %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    debug_logger.info("kb_id: {}".format(kb_id))
    file_id = safe_get(req, 'file_id')
    page_id = safe_get(req, 'page_id', 1)  # 默认为第一页
    page_limit = safe_get(req, 'page_limit', 10)  # 默认每页显示10条记录
    data = []
    if file_id is None:
        file_infos = local_doc_qa.milvus_summary.get_files(user_id, kb_id)
    else:
        file_infos = local_doc_qa.milvus_summary.get_files(user_id, kb_id, file_id)
    status_count = {}
    # msg_map = {'gray': "已上传到服务器，进入上传等待队列",
    #            'red': "上传出错，请删除后重试或联系工作人员",
    #            'yellow': "已进入上传队列，请耐心等待", 'green': "上传成功"}
    for file_info in file_infos:
        status = file_info[2]
        if status not in status_count:
            status_count[status] = 1
        else:
            status_count[status] += 1
        data.append({"file_id": file_info[0], "file_name": file_info[1], "status": file_info[2], "bytes": file_info[3],
                     "content_length": file_info[4], "timestamp": file_info[5], "file_location": file_info[6],
                     "file_url": file_info[7], "chunks_number": file_info[8], "msg": file_info[9]})
        if file_info[1].endswith('.faq'):
            faq_info = local_doc_qa.milvus_summary.get_faq(file_info[0])
            user_id, kb_id, question, answer, nos_keys = faq_info
            data[-1]['question'] = question
            data[-1]['answer'] = answer

    # data根据timestamp排序，时间越新的越靠前
    data = sorted(data, key=lambda x: int(x['timestamp']), reverse=True)

    # 计算总记录数
    total_count = len(data)
    # 计算总页数
    total_pages = (total_count + page_limit - 1) // page_limit
    if page_id > total_pages and total_count != 0:
        return sanic_json(
            {"code": 2002, "msg": f'输入非法！page_id超过最大值，page_id: {page_id}，最大值：{total_pages}，请检查！'})
    # 计算当前页的起始和结束索引
    start_index = (page_id - 1) * page_limit
    end_index = start_index + page_limit
    # 截取当前页的数据
    current_page_data = data[start_index:end_index]

    # return sanic_json({"code": 200, "msg": "success", "data": {'total': status_count, 'details': data}})
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
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info("delete_docs %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    file_ids = safe_get(req, "file_ids")
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        return sanic_json({"code": 2003, "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids[0])})
    valid_file_infos = local_doc_qa.milvus_summary.check_file_exist(user_id, kb_id, file_ids)
    if len(valid_file_infos) == 0:
        return sanic_json({"code": 2004, "msg": "fail, files {} not found".format(file_ids)})
    valid_file_ids = [file_info[0] for file_info in valid_file_infos]
    debug_logger.info("delete_docs valid_file_ids %s", valid_file_ids)
    # milvus_kb = local_doc_qa.match_milvus_kb(user_id, [kb_id])
    # milvus_kb.delete_files(file_ids)
    expr = f"""kb_id == "{kb_id}" and file_id in {valid_file_ids}"""  # 删除数据库中的记录
    asyncio.create_task(run_in_background(local_doc_qa.milvus_kb.delete_expr, expr))
    # local_doc_qa.milvus_kb.delete_expr(expr)
    file_chunks = local_doc_qa.milvus_summary.get_chunk_size(valid_file_ids)
    asyncio.create_task(run_in_background(local_doc_qa.es_client.delete_files, valid_file_ids, file_chunks))

    local_doc_qa.milvus_summary.delete_files(kb_id, valid_file_ids)
    local_doc_qa.milvus_summary.delete_documents(valid_file_ids)
    local_doc_qa.milvus_summary.delete_faqs(valid_file_ids)
    # list file_ids
    for file_id in file_ids:
        try:
            upload_path = os.path.join(UPLOAD_ROOT_PATH, user_id)
            file_dir = os.path.join(upload_path, kb_id, file_id)
            debug_logger.info("delete_docs file_dir %s", file_dir)
            # delete file dir
            shutil.rmtree(file_dir)
            # delele images dir
            images_dir = os.path.join(IMAGES_ROOT_PATH, file_id)
            debug_logger.info("delete_docs images_dir %s", images_dir)
            shutil.rmtree(images_dir)
        except Exception as e:
            debug_logger.error("An error occurred while constructing file paths: %s", str(e))

    return sanic_json({"code": 200, "msg": "documents {} delete success".format(valid_file_ids)})


@get_time_async
@auth_required("admin", check_kb_access=True)
async def delete_knowledge_base(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    # TODO: 确认是否支持批量删除知识库
    user_id = safe_get(req, 'user_id')
    user_info = safe_get(req, 'user_info', "1234")
    passed, msg = check_user_id_and_user_info(user_id, user_info)
    if not passed:
        return sanic_json({"code": 2001, "msg": msg})
    # user_id = user_id + '__' + user_info
    debug_logger.info("delete_knowledge_base %s", user_id)
    kb_ids = safe_get(req, 'kb_ids')
    kb_ids = [correct_kb_id(kb_id) for kb_id in kb_ids]
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, kb_ids)
    if not_exist_kb_ids:
        return sanic_json({"code": 2003, "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids)})

    # milvus = local_doc_qa.match_milvus_kb(user_id, kb_ids)
    for kb_id in kb_ids:
        expr = f"kb_id == \"{kb_id}\""
        asyncio.create_task(run_in_background(local_doc_qa.milvus_kb.delete_expr, expr))
        # local_doc_qa.milvus_kb.delete_expr(expr)
        # milvus.delete_partition(kb_id)
    for kb_id in kb_ids:
        file_infos = local_doc_qa.milvus_summary.get_files(user_id, kb_id)
        file_ids = [file_info[0] for file_info in file_infos]
        file_chunks = [file_info[8] for file_info in file_infos]
        asyncio.create_task(run_in_background(local_doc_qa.es_client.delete_files, file_ids, file_chunks))
        local_doc_qa.milvus_summary.delete_documents(file_ids)
        local_doc_qa.milvus_summary.delete_faqs(file_ids)

        # delete kb_id file dir
        try:
            upload_path = os.path.join(UPLOAD_ROOT_PATH, user_id)
            file_dir = os.path.join(upload_path, kb_id)
            debug_logger.info("delete_knowledge_base file dir : %s", file_dir)
            shutil.rmtree(file_dir)
        except Exception as e:
            debug_logger.error("An error occurred while constructing file paths: %s", str(e))

        debug_logger.info(f"""delete knowledge base {kb_id} success""")
    local_doc_qa.milvus_summary.delete_knowledge_base(user_id, kb_ids)
    return sanic_json({"code": 200, "msg": "Knowledge Base {} delete success".format(kb_ids)})


@get_time_async
async def get_total_status(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info('get_total_status %s', user_id)
    by_date = safe_get(req, 'by_date', False)
    if not user_id:
        users = local_doc_qa.milvus_summary.get_users()
        users = [user[0] for user in users]
    else:
        users = [user_id]
    res = {}
    for user in users:
        res[user] = {}
        if by_date:
            res[user] = local_doc_qa.milvus_summary.get_total_status_by_date(user)
            continue
        kbs = local_doc_qa.milvus_summary.get_knowledge_bases(user)
        for kb_id, kb_name in kbs:
            gray_file_infos = local_doc_qa.milvus_summary.get_file_by_status([kb_id], 'gray')
            red_file_infos = local_doc_qa.milvus_summary.get_file_by_status([kb_id], 'red')
            yellow_file_infos = local_doc_qa.milvus_summary.get_file_by_status([kb_id], 'yellow')
            green_file_infos = local_doc_qa.milvus_summary.get_file_by_status([kb_id], 'green')
            res[user][kb_name + kb_id] = {'green': len(green_file_infos), 'yellow': len(yellow_file_infos),
                                          'red': len(red_file_infos),
                                          'gray': len(gray_file_infos)}

    return sanic_json({"code": 200, "status": res})


@get_time_async
async def clean_files_by_status(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    debug_logger.info('clean_files_by_status %s', user_id)
    status = safe_get(req, 'status', default='gray')
    if status not in ['gray', 'red', 'yellow']:
        return sanic_json({"code": 2003, "msg": "fail, status {} must be in ['gray', 'red', 'yellow']".format(status)})
    kb_ids = safe_get(req, 'kb_ids')
    kb_ids = [correct_kb_id(kb_id) for kb_id in kb_ids]
    if not kb_ids:
        kbs = local_doc_qa.milvus_summary.get_knowledge_bases(user_id)
        kb_ids = [kb[0] for kb in kbs]
    else:
        not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, kb_ids)
        if not_exist_kb_ids:
            return sanic_json({"code": 2003, "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids)})

    gray_file_infos = local_doc_qa.milvus_summary.get_file_by_status(kb_ids, status)
    gray_file_ids = [f[0] for f in gray_file_infos]
    gray_file_names = [f[1] for f in gray_file_infos]
    debug_logger.info(f'{status} files number: {len(gray_file_names)}')
    # 删除milvus中的file
    if gray_file_ids:
        # expr = f"file_id in \"{gray_file_ids}\""
        # asyncio.create_task(run_in_background(local_doc_qa.milvus_kb.delete_expr, expr))
        for kb_id in kb_ids:
            local_doc_qa.milvus_summary.delete_files(kb_id, gray_file_ids)
    return sanic_json({"code": 200, "msg": f"delete {status} files success", "data": gray_file_names})


@get_time_async
async def local_doc_chat(req: request):
    preprocess_start = time.perf_counter()
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    user_info = safe_get(req, 'user_info', "1234")
    passed, msg = check_user_id_and_user_info(user_id, user_info)
    if not passed:
        return sanic_json({"code": 2001, "msg": msg})
    # local_cluster = get_milvus_cluster_by_user_info(user_info)
    # user_id = user_id + '__' + user_info
    # local_doc_qa.milvus_summary.update_user_cluster(user_id, [get_milvus_cluster_by_user_info(user_info)])
    debug_logger.info('local_doc_chat %s', user_id)
    debug_logger.info('user_info %s', user_info)
    bot_id = safe_get(req, 'bot_id')
    if bot_id:
        if not local_doc_qa.milvus_summary.check_bot_is_exist(bot_id):
            return sanic_json({"code": 2003, "msg": "fail, Bot {} not found".format(bot_id)})
        bot_info = local_doc_qa.milvus_summary.get_bot(None, bot_id)[0]
        bot_id, bot_name, desc, image, prompt, welcome, kb_ids_str, upload_time, user_id, llm_setting = bot_info
        kb_ids = kb_ids_str.split(',')
        if not kb_ids:
            return sanic_json({"code": 2003, "msg": "fail, Bot {} unbound knowledge base.".format(bot_id)})
        custom_prompt = prompt
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
        kb_ids = safe_get(req, 'kb_ids')
        custom_prompt = safe_get(req, 'custom_prompt', None)
        rerank = safe_get(req, 'rerank', default=True)
        only_need_search_results = safe_get(req, 'only_need_search_results', False)
        need_web_search = safe_get(req, 'networking', False)
        api_base = safe_get(req, 'api_base', '')
        # 如果api_base中包含0.0.0.0或127.0.0.1或localhost，替换为GATEWAY_IP
        api_base = api_base.replace('0.0.0.0', GATEWAY_IP).replace('127.0.0.1', GATEWAY_IP).replace('localhost',
                                                                                                    GATEWAY_IP)
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

    if len(kb_ids) > 20:
        return sanic_json({"code": 2005, "msg": "fail, kb_ids length should less than or equal to 20"})
    kb_ids = [correct_kb_id(kb_id) for kb_id in kb_ids]
    question = safe_get(req, 'question')
    streaming = safe_get(req, 'streaming', False)
    history = safe_get(req, 'history', [])

    if top_k > 100:
        return sanic_json({"code": 2003, "msg": "fail, top_k should less than or equal to 100"})

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

    if only_need_search_results and streaming:
        return sanic_json(
            {"code": 2006, "msg": "fail, only_need_search_results and streaming can't be True at the same time"})
    request_source = safe_get(req, 'source', 'unknown')

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

    time_record = {}
    if kb_ids:
        not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, kb_ids)
        if not_exist_kb_ids:
            return sanic_json({"code": 2003, "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids)})
        faq_kb_ids = [kb + '_FAQ' for kb in kb_ids]
        not_exist_faq_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, faq_kb_ids)
        exist_faq_kb_ids = [kb for kb in faq_kb_ids if kb not in not_exist_faq_kb_ids]
        debug_logger.info("exist_faq_kb_ids: %s", exist_faq_kb_ids)
        kb_ids += exist_faq_kb_ids

    file_infos = []
    for kb_id in kb_ids:
        file_infos.extend(local_doc_qa.milvus_summary.get_files(user_id, kb_id))
    valid_files = [fi for fi in file_infos if fi[2] == 'green']
    if len(valid_files) == 0:
        debug_logger.info("valid_files is empty, use only chat mode.")
        kb_ids = []
    preprocess_end = time.perf_counter()
    time_record['preprocess'] = round(preprocess_end - preprocess_start, 2)
    # 获取格式为'2021-08-01 00:00:00'的时间戳
    qa_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    for kb_id in kb_ids:
        local_doc_qa.milvus_summary.update_knowledge_base_latest_qa_time(kb_id, qa_timestamp)
    debug_logger.info("streaming: %s", streaming)
    if streaming:
        debug_logger.info("start generate answer")

        async def generate_answer(response):
            debug_logger.info("start generate...")
            async for resp, next_history in local_doc_qa.get_knowledge_based_answer(model=model,
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
                    retrieval_documents = format_source_documents(resp["retrieval_documents"])
                    source_documents = format_source_documents(resp["source_documents"])
                    result = next_history[-1][1]
                    # result = resp['result']
                    time_record['chat_completed'] = round(time.perf_counter() - preprocess_start, 2)
                    if time_record.get('llm_completed', 0) > 0:
                        time_record['tokens_per_second'] = round(
                            len(result) / time_record['llm_completed'], 2)
                    formatted_time_record = format_time_record(time_record)
                    chat_data = {'user_id': user_id, 'kb_ids': kb_ids, 'query': question, "model": model,
                                 "product_source": request_source, 'time_record': formatted_time_record,
                                 'history': history,
                                 'condense_question': resp['condense_question'], 'prompt': resp['prompt'],
                                 'result': result, 'retrieval_documents': retrieval_documents,
                                 'source_documents': source_documents, 'bot_id': bot_id}
                    local_doc_qa.milvus_summary.add_qalog(**chat_data)
                    qa_logger.info("chat_data: %s", chat_data)
                    debug_logger.info("response: %s", chat_data['result'])
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
                    time_record['rollback_length'] = resp.get('rollback_length', 0)
                    if 'first_return' not in time_record:
                        time_record['first_return'] = round(time.perf_counter() - preprocess_start, 2)
                    chunk_js = json.loads(chunk_str)
                    delta_answer = chunk_js["answer"]
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
                await response.write(f"data: {json.dumps(stream_res, ensure_ascii=False)}\n\n")
                if chunk_str.startswith("[DONE]"):
                    await response.eof()
                await asyncio.sleep(0.001)

        response_stream = ResponseStream(generate_answer, content_type='text/event-stream')
        return response_stream

    else:
        async for resp, history in local_doc_qa.get_knowledge_based_answer(model=model,
                                                                           max_token=max_token,
                                                                           kb_ids=kb_ids,
                                                                           query=question,
                                                                           retriever=local_doc_qa.retriever,
                                                                           chat_history=history, streaming=False,
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
        if only_need_search_results:
            return sanic_json(
                {"code": 200, "question": question, "source_documents": format_source_documents(resp)})
        retrieval_documents = format_source_documents(resp["retrieval_documents"])
        source_documents = format_source_documents(resp["source_documents"])
        formatted_time_record = format_time_record(time_record)
        chat_data = {'user_id': user_id, 'kb_ids': kb_ids, 'query': question, 'time_record': formatted_time_record,
                     'history': history, "condense_question": resp['condense_question'], "model": model,
                     "product_source": request_source,
                     'retrieval_documents': retrieval_documents, 'prompt': resp['prompt'], 'result': resp['result'],
                     'source_documents': source_documents, 'bot_id': bot_id}
        local_doc_qa.milvus_summary.add_qalog(**chat_data)
        qa_logger.info("chat_data: %s", chat_data)
        debug_logger.info("response: %s", chat_data['result'])
        return sanic_json({"code": 200, "msg": "success no stream chat", "question": question,
                           "response": resp["result"], "model": model,
                           "history": history, "condense_question": resp['condense_question'],
                           "source_documents": source_documents, "retrieval_documents": retrieval_documents,
                           "time_record": formatted_time_record})


@get_time_async
async def get_doc_completed(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    user_info = safe_get(req, 'user_info', "1234")
    passed, msg = check_user_id_and_user_info(user_id, user_info)
    if not passed:
        return sanic_json({"code": 2001, "msg": msg})
    # user_id = user_id + '__' + user_info
    debug_logger.info("get_doc_chunks %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    debug_logger.info("kb_id: {}".format(kb_id))
    file_id = safe_get(req, 'file_id')
    if not file_id:
        return sanic_json({"code": 2005, "msg": "fail, file_id is None"})
    debug_logger.info("file_id: {}".format(file_id))
    page_id = safe_get(req, 'page_id', 1)  # 默认为第一页
    page_limit = safe_get(req, 'page_limit', 10)  # 默认每页显示10条记录

    sorted_json_datas = local_doc_qa.milvus_summary.get_document_by_file_id(file_id)
    # completed_doc = local_doc_qa.get_completed_document(file_id)
    # for json_data in sorted_json_datas:
    #     completed_text += json_data['kwargs']['page_content'] + '\n'
    #     if len(completed_text) > 10000:
    #         return sanic_json({"code": 200, "msg": "failed, completed_text too long, the max length is 10000"})
    chunks = [json_data['kwargs'] for json_data in sorted_json_datas]

    # 计算总记录数
    total_count = len(chunks)
    # 计算总页数
    total_pages = (total_count + page_limit - 1) // page_limit
    if page_id > total_pages and total_count != 0:
        return sanic_json(
            {"code": 2002, "msg": f'输入非法！page_id超过最大值，page_id: {page_id}，最大值：{total_pages}，请检查！'})
    # 计算当前页的起始和结束索引
    start_index = (page_id - 1) * page_limit
    end_index = start_index + page_limit
    # 截取当前页的数据
    current_page_chunks = chunks[start_index:end_index]
    for chunk in current_page_chunks:
        chunk['page_content'] = replace_image_references(chunk['page_content'], file_id)

    # return sanic_json({"code": 200, "msg": "success", "completed_text": completed_doc.page_content,
    #                    "chunks": current_page_chunks, "page_id": page, "total_count": total_count})
    file_location = local_doc_qa.milvus_summary.get_file_location(file_id)
    # 获取file_location的上一级目录
    file_path = os.path.dirname(file_location)
    return sanic_json({"code": 200, "msg": "success", "chunks": current_page_chunks, "file_path": file_path,
                       "page_id": page_id, "page_limit": page_limit, "total_count": total_count})


@get_time_async
async def get_qa_info(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    any_kb_id = safe_get(req, 'any_kb_id')
    user_id = safe_get(req, 'user_id')
    if user_id is None and not any_kb_id:
        return sanic_json({"code": 2005, "msg": "fail, user_id and any_kb_id is None"})
    if any_kb_id:
        any_kb_id = correct_kb_id(any_kb_id)
        debug_logger.info("get_qa_info %s", any_kb_id)
    if user_id:
        user_info = safe_get(req, 'user_info', "1234")
        passed, msg = check_user_id_and_user_info(user_id, user_info)
        if not passed:
            return sanic_json({"code": 2001, "msg": msg})
        # user_id = user_id + '__' + user_info
        debug_logger.info("get_qa_info %s", user_id)
    query = safe_get(req, 'query')
    bot_id = safe_get(req, 'bot_id')
    qa_ids = safe_get(req, "qa_ids")
    time_start = safe_get(req, 'time_start')
    time_end = safe_get(req, 'time_end')
    time_range = get_time_range(time_start, time_end)
    if not time_range:
        return {"code": 2002, "msg": f'输入非法！time_start格式错误，time_start: {time_start}，示例：2024-10-05，请检查！'}
    only_need_count = safe_get(req, 'only_need_count', False)
    debug_logger.info(f"only_need_count: {only_need_count}")
    if only_need_count:
        need_info = ["timestamp"]
        qa_infos = local_doc_qa.milvus_summary.get_qalog_by_filter(need_info=need_info, user_id=user_id,
                                                                   time_range=time_range)
        # timestamp = now.strftime("%Y%m%d%H%M")
        # 按照timestamp，按照天数进行统计，比如20240628，20240629，20240630，计算每天的问答数量
        qa_infos = sorted(qa_infos, key=lambda x: x['timestamp'])
        qa_infos = [qa_info['timestamp'] for qa_info in qa_infos]
        qa_infos = [qa_info[:10] for qa_info in qa_infos]
        qa_infos_by_day = dict(Counter(qa_infos))
        return sanic_json({"code": 200, "msg": "success", "qa_infos_by_day": qa_infos_by_day})

    page_id = safe_get(req, 'page_id', 1)
    page_limit = safe_get(req, 'page_limit', 10)
    default_need_info = ["qa_id", "user_id", "bot_id", "kb_ids", "query", "model", "product_source", "time_record",
                         "history", "condense_question", "prompt", "result", "retrieval_documents", "source_documents",
                         "timestamp"]
    need_info = safe_get(req, 'need_info', default_need_info)
    save_to_excel = safe_get(req, 'save_to_excel', False)
    qa_infos = local_doc_qa.milvus_summary.get_qalog_by_filter(need_info=need_info, user_id=user_id, query=query,
                                                               bot_id=bot_id, time_range=time_range,
                                                               any_kb_id=any_kb_id, qa_ids=qa_ids)
    if save_to_excel:
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        file_name = f"QAnything_QA_{timestamp}.xlsx"
        file_path = export_qalogs_to_excel(qa_infos, need_info, file_name)
        return await response.file(file_path, filename=file_name,
                                   mime_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                   headers={'Content-Disposition': f'attachment; filename="{file_name}"'})

    # 计算总记录数
    total_count = len(qa_infos)
    # 计算总页数
    total_pages = (total_count + page_limit - 1) // page_limit
    if page_id > total_pages and total_count != 0:
        return sanic_json(
            {"code": 2002, "msg": f'输入非法！page_id超过最大值，page_id: {page_id}，最大值：{total_pages}，请检查！'})
    # 计算当前页的起始和结束索引
    start_index = (page_id - 1) * page_limit
    end_index = start_index + page_limit
    # 截取当前页的数据
    current_qa_infos = qa_infos[start_index:end_index]
    msg = f"检测到的Log总数为{total_count}, 本次返回page_id为{page_id}的数据，每页显示{page_limit}条"

    # if len(qa_infos) > 100:
    #     pages = math.ceil(len(qa_infos) // 100)
    #     if page_id is None:
    #         msg = f"检索到的Log数超过100，需要分页返回，总数为{len(qa_infos)}, 请使用page_id参数获取某一页数据，参数范围：[0, {pages - 1}], 本次返回page_id为0的数据"
    #         qa_infos = qa_infos[:100]
    #         page_id = 0
    #     elif page_id >= pages:
    #         return sanic_json(
    #             {"code": 2002, "msg": f'输入非法！page_id超过最大值，page_id: {page_id}，最大值：{pages - 1}，请检查！'})
    #     else:
    #         msg = f"检索到的Log数超过100，需要分页返回，总数为{len(qa_infos)}, page范围：[0, {pages - 1}], 本次返回page_id为{page_id}的数据"
    #         qa_infos = qa_infos[page_id * 100:(page_id + 1) * 100]
    # else:
    #     msg = f"检索到的Log数为{len(qa_infos)}，一次返回所有数据"
    #     page_id = 0
    return sanic_json(
        {"code": 200, "msg": msg, "page_id": page_id, "page_limit": page_limit, "qa_infos": current_qa_infos,
         "total_count": total_count})


@get_time_async
async def get_random_qa(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    limit = safe_get(req, 'limit', 10)
    time_start = safe_get(req, 'time_start')
    time_end = safe_get(req, 'time_end')
    need_info = safe_get(req, 'need_info')
    time_range = get_time_range(time_start, time_end)
    if not time_range:
        return {"code": 2002, "msg": f'输入非法！time_start格式错误，time_start: {time_start}，示例：2024-10-05，请检查！'}

    debug_logger.info(f"get_random_qa limit: {limit}, time_range: {time_range}")
    qa_infos = local_doc_qa.milvus_summary.get_random_qa_infos(limit=limit, time_range=time_range, need_info=need_info)

    counts = local_doc_qa.milvus_summary.get_statistic(time_range=time_range)
    return sanic_json({"code": 200, "msg": "success", "total_users": counts["total_users"],
                       "total_queries": counts["total_queries"], "qa_infos": qa_infos})


@get_time_async
async def get_related_qa(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    qa_id = safe_get(req, 'qa_id')
    if not qa_id:
        return sanic_json({"code": 2005, "msg": "fail, qa_id is None"})
    need_info = safe_get(req, 'need_info')
    need_more = safe_get(req, 'need_more', False)
    debug_logger.info("get_related_qa %s", qa_id)
    qa_log, recent_logs, older_logs = local_doc_qa.milvus_summary.get_related_qa_infos(qa_id, need_info, need_more)
    # 按kb_ids划分sections
    recent_sections = defaultdict(list)
    for log in recent_logs:
        recent_sections[log['kb_ids']].append(log)
    # 把recent_sections的key改为自增的正整数，且每个log都新增kb_name
    for i, kb_ids in enumerate(list(recent_sections.keys())):
        kb_names = local_doc_qa.milvus_summary.get_knowledge_base_name(json.loads(kb_ids))
        kb_names = [kb_name for user_id, kb_id, kb_name in kb_names]
        kb_names = ','.join(kb_names)
        recent_sections[i] = recent_sections.pop(kb_ids)
        for log in recent_sections[i]:
            log['kb_names'] = kb_names

    older_sections = defaultdict(list)
    for log in older_logs:
        older_sections[log['kb_ids']].append(log)
    # 把older_sections的key改为自增的正整数，且每个log都新增kb_name
    for i, kb_ids in enumerate(list(older_sections.keys())):
        kb_names = local_doc_qa.milvus_summary.get_knowledge_base_name(json.loads(kb_ids))
        kb_names = [kb_name for user_id, kb_id, kb_name in kb_names]
        kb_names = ','.join(kb_names)
        older_sections[i] = older_sections.pop(kb_ids)
        for log in older_sections[i]:
            log['kb_names'] = kb_names

    return sanic_json({"code": 200, "msg": "success", "qa_info": qa_log, "recent_sections": recent_sections,
                       "older_sections": older_sections})


@get_time_async
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
async def get_doc(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    doc_id = safe_get(req, 'doc_id')
    debug_logger.info("get_doc %s", doc_id)
    if not doc_id:
        return sanic_json({"code": 2005, "msg": "fail, doc_id is None"})
    doc_json_data = local_doc_qa.milvus_summary.get_document_by_doc_id(doc_id)
    return sanic_json({"code": 200, "msg": "success", "doc_text": doc_json_data['kwargs']})


@get_time_async
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
async def get_user_status(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    user_info = safe_get(req, 'user_info', "1234")
    passed, msg = check_user_id_and_user_info(user_id, user_info)
    if not passed:
        return sanic_json({"code": 2001, "msg": msg})
    # user_id = user_id + '__' + user_info
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
async def health_check(req: request):
    # 实现一个服务健康检查的逻辑，正常就返回200，不正常就返回500
    return sanic_json({"code": 200, "msg": "success"})


@get_time_async
async def update_chunks(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    user_info = safe_get(req, 'user_info', "1234")
    passed, msg = check_user_id_and_user_info(user_id, user_info)
    if not passed:
        return sanic_json({"code": 2001, "msg": msg})
    # user_id = user_id + '__' + user_info
    debug_logger.info("update_chunks %s", user_id)
    doc_id = safe_get(req, 'doc_id')
    debug_logger.info(f"doc_id: {doc_id}")
    yellow_files = local_doc_qa.milvus_summary.get_files_by_status("yellow")
    if len(yellow_files) > 0:
        return sanic_json({"code": 2002,
                           "msg": f"fail, currently, there are {len(yellow_files)} files being parsed, please wait for all files to finish parsing before updating the chunk."})
    update_content = safe_get(req, 'update_content')
    debug_logger.info(f"update_content: {update_content}")
    chunk_size = safe_get(req, 'chunk_size', DEFAULT_PARENT_CHUNK_SIZE)
    debug_logger.info(f"chunk_size: {chunk_size}")
    update_content_tokens = num_tokens_embed(update_content)
    if update_content_tokens > chunk_size:
        return sanic_json({"code": 2003, "msg": f"fail, update_content too long, please reduce the length, "
                                                f"your update_content tokens is {update_content_tokens}, "
                                                f"the max tokens is {chunk_size}"})
    doc_json = local_doc_qa.milvus_summary.get_document_by_doc_id(doc_id)
    if not doc_json:
        return sanic_json({"code": 2004, "msg": "fail, DocId {} not found".format(doc_id)})
    doc = Document(page_content=update_content, metadata=doc_json['kwargs']['metadata'])
    doc.metadata['doc_id'] = doc_id
    local_doc_qa.milvus_summary.update_document(doc_id, update_content)
    expr = f'doc_id == "{doc_id}"'
    local_doc_qa.milvus_kb.delete_expr(expr)
    await local_doc_qa.retriever.insert_documents([doc], chunk_size, True)
    return sanic_json({"code": 200, "msg": "success update doc_id {}".format(doc_id)})


@get_time_async
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
