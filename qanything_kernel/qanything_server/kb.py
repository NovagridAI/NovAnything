import asyncio
import os
import shutil
import uuid
from datetime import datetime

from sanic import request
from sanic.response import json as sanic_json

from qanything_kernel.configs.model_config import UPLOAD_ROOT_PATH
from qanything_kernel.qanything_server.auth import auth_required, ROLE_USER
from qanything_kernel.qanything_server.handler import run_in_background
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.utils.general_utils import get_time_async, safe_get, correct_kb_id


def _verify_subject_exists(local_doc_qa, subject_id, subject_type):
    """验证授权主体是否存在"""
    if subject_type == 'user':
        # 使用user_dao检查用户是否存在
        user_exists = local_doc_qa.milvus_summary.user_dao.check_user_exists(subject_id)
        if not user_exists:
            return False, "用户不存在或未激活"
    elif subject_type == 'department':
        # 使用department_dao检查部门是否存在
        dept_exists = local_doc_qa.milvus_summary.department_dao.check_department_exists(subject_id)
        if not dept_exists:
            return False, "部门不存在"
    elif subject_type == 'group':
        # 使用user_group_dao检查用户组是否存在
        group_exists = local_doc_qa.milvus_summary.user_group_dao.check_group_exists(subject_id)
        if not group_exists:
            return False, "用户组不存在"
    else:
        return False, "无效的主体类型"
    return True, "验证通过"


def _set_permission(local_doc_qa, kb_id, subject_id, subject_type, permission_type, user_id):
    """设置权限的通用函数"""
    try:
        if permission_type == 'remove':
            # 删除权限 - 通过kb_dao设置为空权限来实现删除
            debug_logger.info(f"删除权限 - 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}")
            success = local_doc_qa.milvus_summary.kb_dao.remove_subject_access(subject_type, subject_id)
            if success:
                return True, "权限已删除"
            else:
                return False, "删除权限失败"
        else:
            # 设置权限
            debug_logger.info(f"设置权限 - 知识库: {kb_id}, 主体: {subject_id}, 类型: {subject_type}, 权限: {permission_type}")
            success = local_doc_qa.milvus_summary.kb_dao.set_kb_access(kb_id, subject_id, subject_type, permission_type, user_id)
            if success:
                return True, "权限设置成功"
            else:
                return False, "设置权限失败"
    except Exception as e:
        debug_logger.error(f"设置知识库权限失败: {str(e)}")
        return False, f"设置知识库权限失败: {str(e)}"


@get_time_async
@auth_required()
async def new_knowledge_base(req: request):
    """创建新知识库
    
    支持创建三种类型的知识库：
    - personal: 个人知识库，默认类型，只有创建者可访问
    - team: 团队知识库，可以共享给其他用户或部门, 仅admin和superadmin可创建
    - temporary: 临时知识库，用于临时使用场景
    
    请求参数:
    - kb_name: 知识库名称
    - kb_id: (可选) 知识库ID，如不提供则自动生成
    - kb_type: (可选) 知识库类型，可选值：'personal', 'team', 'temporary'，默认为'personal'
    """
    local_doc_qa = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    kb_name = safe_get(req, 'kb_name')
    description = safe_get(req, 'description')
    
    # 验证知识库名称
    if not kb_name:
        return sanic_json({"code": 400, "msg": "知识库名称不能为空"})
    
    # 获取知识库类型
    valid_kb_types = ['personal', 'team', 'temporary']
    kb_type = safe_get(req, 'kb_type', 'personal')
    if kb_type not in valid_kb_types:
        return sanic_json({"code": 400, "msg": f"无效的知识库类型，可选值: {', '.join(valid_kb_types)}"})
    
    # 检查创建团队知识库的权限
    if kb_type == 'team':
        # 获取用户角色
        user_role = req.ctx.user.get('role', 'user') if hasattr(req, 'ctx') and hasattr(req.ctx, 'user') else 'user'
        if user_role != 'superadmin':
            return sanic_json({
                "code": 403, 
                "msg": "您没有创建团队知识库的权限，只有超级管理员可以创建团队知识库"
            })
    
    # 获取或生成知识库ID
    default_kb_id = 'KB' + uuid.uuid4().hex
    kb_id = safe_get(req, 'kb_id', default_kb_id)
    kb_id = correct_kb_id(kb_id)
    
    # 检查知识库ID格式
    if kb_id[:2] != 'KB':
        return sanic_json({"code": 400, "msg": "知识库ID必须以'KB'开头"})
    
    # 检查知识库是否已存在
    not_exist_kb_ids = local_doc_qa.milvus_summary.kb_dao.check_kb_exist([kb_id])
    if not not_exist_kb_ids:
        return sanic_json({"code": 400, "msg": f"知识库 {kb_id} 已存在"})
    
    # 创建知识库
    debug_logger.info(f"创建{kb_type}知识库 - ID: {kb_id}, 名称: {kb_name}, 用户: {user_id}")
    
    try:
        # 使用kb_dao创建知识库，对不同类型的知识库进行处理
        kb_id, status = local_doc_qa.milvus_summary.kb_dao.new_knowledge_base(kb_id, user_id, kb_name, kb_type, description)
        
        # 根据知识库类型设置不同的权限策略
        if kb_type == 'team':
            # 团队知识库默认创建者拥有admin权限，其他人需要专门设置
            debug_logger.info(f"团队知识库创建成功，所有者 {user_id} 拥有管理权限")
        elif kb_type == 'personal':
            # 个人知识库默认只有创建者可访问
            debug_logger.info(f"个人知识库创建成功，仅所有者 {user_id} 可访问")
        elif kb_type == 'temporary':
            # 临时知识库也只有创建者可访问
            debug_logger.info(f"临时知识库创建成功，仅所有者 {user_id} 可访问")
        
        debug_logger.info(f"知识库创建成功 - ID: {kb_id}, 名称: {kb_name}, 类型: {kb_type}, 状态: {status}")
    except Exception as e:
        debug_logger.error(f"创建知识库失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"创建知识库失败: {str(e)}"})
    
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")
    
    return sanic_json({
        "code": 200,
        "msg": f"成功创建{kb_type}知识库: {kb_id}",
        "data": {
            "kb_id": kb_id, 
            "kb_name": kb_name, 
            "kb_type": kb_type,
            "description": description,
            "timestamp": timestamp
        }
    })


@get_time_async
@auth_required("read", check_kb_access=False)
async def list_kbs(req: request):
    """列出用户的所有知识库
    
    请求参数:
    - kb_type: (可选) 知识库类型筛选，可选值：'personal', 'team', 'temporary', 'all'，默认为'all'
    
    返回:
    - 知识库列表，包含kb_id、kb_name和kb_type
    """
    local_doc_qa = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    
    # 获取筛选条件
    kb_type = safe_get(req, 'kb_type', None)  # 默认不筛选类型，返回所有类型
    
    try:
        # 使用kb_dao获取知识库列表
        kb_infos = local_doc_qa.milvus_summary.kb_dao.get_knowledge_bases(user_id, kb_type)
        
        # 格式化结果
        data = []
        for kb in kb_infos:
            kb_dict = {
                "kb_id": kb[0],              # kb_id
                "kb_name": kb[1],            # kb_name
                "kb_type": kb[2] or 'personal',  # 如果kb_type为空，默认为'personal'
                "description": kb[3] if len(kb) > 3 else None,  # description
                "is_owner": True  # 暂时标记为True，后续可以根据需要调整
            }
            data.append(kb_dict)
        
        # 按知识库类型进行分类计数
        type_counts = {
            "personal": len([kb for kb in data if kb["kb_type"] == "personal"]),
            "team": len([kb for kb in data if kb["kb_type"] == "team"]),
            "temporary": len([kb for kb in data if kb["kb_type"] == "temporary"]),
            "total": len(data)
        }
        
        debug_logger.info(f"获取知识库列表 - 用户: {user_id}, 类型过滤: {kb_type}, 找到: {len(data)}个")
        return sanic_json({
            "code": 200, 
            "msg": "获取知识库列表成功", 
            "data": data,
            "counts": type_counts
        })
    except Exception as e:
        debug_logger.error(f"获取知识库列表失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"获取知识库列表失败: {str(e)}"})


@get_time_async
@auth_required(required_role=ROLE_USER)
async def delete_knowledge_base(req: request):
    """删除知识库
    
    请求参数:
    - kb_ids: 要删除的知识库ID列表
    
    注意：
    - 团队知识库只有管理员或拥有者可以删除
    - 个人知识库和临时知识库只有拥有者可以删除
    """
    local_doc_qa = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')

    kb_ids = safe_get(req, 'kb_ids')
    
    if not kb_ids or not isinstance(kb_ids, list):
        return sanic_json({"code": 400, "msg": "请提供有效的知识库ID列表"})
    
    kb_ids = [correct_kb_id(kb_id) for kb_id in kb_ids]
    
    try:
        # 检查知识库是否存在
        not_exist_kb_ids = local_doc_qa.milvus_summary.kb_dao.check_kb_exist(kb_ids)
        if not_exist_kb_ids:
            return sanic_json({"code": 404, "msg": f"知识库不存在: {not_exist_kb_ids}"})
        
        # 获取知识库信息（记录日志用）
        kb_info_list = local_doc_qa.milvus_summary.kb_dao.get_knowledge_base_name(kb_ids)
        
        # 验证权限 - 确保用户有权删除这些知识库
        unauthorized_kbs = []
        for kb_info in kb_info_list:
            kb_owner = kb_info[0]  # user_id
            kb_id = kb_info[1]     # kb_id
            
            # 获取知识库详细信息以检查类型
            kb = local_doc_qa.milvus_summary.kb_dao.get_knowledge_base_by_id(kb_id)
            if not kb:
                unauthorized_kbs.append(kb_id)
                continue
                
            kb_type = getattr(kb, 'kb_type', 'personal')
            
            # 检查是否为拥有者
            is_owner = kb_owner == user_id
            
            # 个人知识库：只有拥有者可以删除
            if kb_type == 'personal':
                if not is_owner:
                    unauthorized_kbs.append(kb_id)
            # 团队知识库：只有拥有者或超级管理员可以删除
            elif kb_type == 'team':
                if not is_owner:
                    # 检查是否为超级管理员
                    try:
                        user_role = req.ctx.user.get('role', 'user') if hasattr(req, 'ctx') and hasattr(req.ctx, 'user') else 'user'
                        if user_role != 'superadmin':
                            unauthorized_kbs.append(kb_id)
                    except:
                        # 如果检查权限失败，认为没有权限
                        unauthorized_kbs.append(kb_id)
            # 临时知识库：只有拥有者可以删除
            elif kb_type == 'temporary':
                if not is_owner:
                    unauthorized_kbs.append(kb_id)
        
        if unauthorized_kbs:
            return sanic_json({"code": 403, "msg": f"无权删除以下知识库: {unauthorized_kbs}"})
        
        debug_logger.info(f"准备删除知识库: {kb_info_list}")

        # 删除Milvus中的数据
        for kb_id in kb_ids:
            expr = f"kb_id == \"{kb_id}\""
            asyncio.create_task(run_in_background(local_doc_qa.milvus_kb.delete_expr, expr))

        # 删除文件和相关数据
        for kb_id in kb_ids:
            # 删除ES和数据库中的文件记录
            file_infos = local_doc_qa.milvus_summary.get_files(user_id, kb_id)
            if file_infos:
                file_ids = [file_info[0] for file_info in file_infos]
                file_chunks = [file_info[8] for file_info in file_infos]
                asyncio.create_task(run_in_background(local_doc_qa.es_client.delete_files, file_ids, file_chunks))
                local_doc_qa.milvus_summary.delete_documents(file_ids)
                local_doc_qa.milvus_summary.delete_faqs(file_ids)

            # 删除知识库文件目录
            try:
                file_dir = os.path.join(UPLOAD_ROOT_PATH, user_id, kb_id)
                if os.path.exists(file_dir):
                    shutil.rmtree(file_dir)
            except Exception as e:
                debug_logger.error(f"删除文件目录失败: {str(e)}")

        # 从数据库中标记知识库为删除状态
        local_doc_qa.milvus_summary.kb_dao.delete_knowledge_base(user_id, kb_ids)
        return sanic_json({
            "code": 200, 
            "msg": f"成功删除知识库: {kb_ids}",
            "data": {"deleted_kb_ids": kb_ids}
        })
    except Exception as e:
        debug_logger.error(f"删除知识库失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"删除知识库失败: {str(e)}"})


@get_time_async
@auth_required("write", check_kb_access=True)
async def update_knowledge_base(req: request):
    """更新知识库信息
    
    请求参数:
    - kb_id: 知识库ID
    - new_kb_name: 新的知识库名称（可选）
    - description: 知识库描述（可选）
    
    注意:
    - 对于个人知识库和临时知识库，只有拥有者可以更新
    - 对于团队知识库，拥有者和有写权限的用户可以更新
    - 名称和描述至少提供一个进行更新
    """
    local_doc_qa = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')

    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    new_kb_name = safe_get(req, 'new_kb_name')
    description = safe_get(req, 'description')
    
    if not kb_id:
        return sanic_json({"code": 400, "msg": "知识库ID不能为空"})
        
    if not new_kb_name and description is None:
        return sanic_json({"code": 400, "msg": "新知识库名称或描述至少提供一个"})

    try:
        # 检查知识库是否存在
        not_exist_kb_ids = local_doc_qa.milvus_summary.kb_dao.check_kb_exist([kb_id])
        if not_exist_kb_ids:
            return sanic_json({"code": 404, "msg": f"知识库不存在: {kb_id}"})
            
        # 获取知识库信息，检查拥有者和类型
        kb = local_doc_qa.milvus_summary.kb_dao.get_knowledge_base_by_id(kb_id)
        if not kb:
            return sanic_json({"code": 404, "msg": f"知识库不存在: {kb_id}"})
            
        # 检查权限
        is_owner = kb.user_id == user_id
        kb_type = kb.kb_type or 'personal'
        
        # 个人知识库和临时知识库只有拥有者可以更新
        if kb_type in ['personal', 'temporary'] and not is_owner:
            return sanic_json({"code": 403, "msg": f"没有权限更新该知识库: {kb_id}"})
            
        # 团队知识库，不是拥有者需要检查是否有写权限
        if kb_type == 'team' and not is_owner:
            has_write = local_doc_qa.milvus_summary.kb_dao.check_kb_access(user_id, kb_id, 'write')
            if not has_write:
                return sanic_json({"code": 403, "msg": f"没有权限更新该知识库: {kb_id}"})

        # 更新知识库信息
        response_data = {
            "kb_id": kb_id,
            "kb_type": kb_type
        }
        
        # 更新知识库名称
        if new_kb_name:
            local_doc_qa.milvus_summary.kb_dao.rename_knowledge_base(user_id, kb_id, new_kb_name)
            response_data["kb_name"] = new_kb_name
            debug_logger.info(f"知识库重命名成功 - ID: {kb_id}, 新名称: {new_kb_name}, 用户: {user_id}, 类型: {kb_type}")
        else:
            response_data["kb_name"] = kb.kb_name
            
        # 更新知识库描述
        if description is not None:
            local_doc_qa.milvus_summary.kb_dao.update_knowledge_base_description(user_id, kb_id, description)
            response_data["description"] = description
            debug_logger.info(f"知识库描述更新成功 - ID: {kb_id}, 描述: {description}, 用户: {user_id}, 类型: {kb_type}")
        else:
            response_data["description"] = kb.description
        
        return sanic_json({
            "code": 200, 
            "msg": "知识库更新成功", 
            "data": response_data
        })
    except Exception as e:
        debug_logger.error(f"知识库更新失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"知识库更新失败: {str(e)}"})


@get_time_async
@auth_required(check_kb_access=True, kb_permission='admin')
async def get_kb_permission_data(req: request):
    """获取知识库权限分配数据
    
    用于权限管理界面，提供部门、用户数据，以及当前权限设置
    
    请求参数:
    - kb_id: 知识库ID
    """
    local_doc_qa = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    kb_id = safe_get(req, 'kb_id')

    if not kb_id:
        return sanic_json({"code": 400, "msg": "请提供知识库ID"})
        
    try:
        # 检查知识库是否存在并验证权限
        kb = local_doc_qa.milvus_summary.kb_dao.get_knowledge_base_by_id(kb_id)
        if not kb:
            return sanic_json({"code": 404, "msg": f"知识库不存在: {kb_id}"})
            
        is_owner = kb.user_id == user_id
        if not is_owner and not local_doc_qa.milvus_summary.kb_dao.check_kb_access(user_id, kb_id, 'admin'):
            return sanic_json({"code": 403, "msg": "没有权限管理此知识库的权限"})

        # 获取数据和构建结构
        kb_data = await _get_kb_permission_detailed_data(local_doc_qa, kb_id, user_id, req.ctx.user.get('role', 'user'))
            
        debug_logger.info(f"获取知识库权限分配数据成功 - KB: {kb_id}, 用户: {user_id}")
        return sanic_json({
            "code": 200,
            "msg": "获取知识库权限分配数据成功",
            "data": {
                "kb_info": {
                    "kb_id": kb.kb_id,
                    "kb_name": kb.kb_name,
                    "kb_type": kb.kb_type,
                    "owner_id": kb.user_id
                },
                "departments": kb_data["departments"],
                "unassigned_users": kb_data["unassigned_users"],
                "user_groups": [],  # 暂时隐藏用户组
                "permissions": kb_data["permissions"]
            }
        })
    except Exception as e:
        debug_logger.error(f"获取知识库权限分配数据失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"获取知识库权限分配数据失败: {str(e)}"})


@get_time_async
@auth_required(check_kb_access=True, kb_permission='admin')
async def update_kb_permissions(req: request):
    """设置知识库权限 - 统一的权限管理接口
    
    使用树形结构进行完整的权限更新:
    kb_id, permissions_data={
        user_permissions: [{user_id, permission_type}, ...],
        department_permissions: [{dept_id, permission_type}, ...]
    }
    
    说明:
    - 此接口会更新整个知识库的权限设置，删除未明确指定的权限
    - 会自动跳过未发生变化的权限设置，以提高性能
    - 适用于前端树形界面的整体权限管理模式
    
    不同类型知识库的权限说明：
    - 个人知识库：只有所有者可以设置权限，默认不共享
    - 团队知识库：所有者和管理员可以设置权限，适合团队协作
    - 临时知识库：只有所有者可以设置权限，临时用途
    """
    local_doc_qa = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    kb_id = safe_get(req, 'kb_id')
    permissions_data = safe_get(req, 'permissions_data')

    if not kb_id:
        return sanic_json({"code": 400, "msg": "知识库ID不能为空"})

    if not permissions_data:
        return sanic_json({"code": 400, "msg": "请提供权限数据"})
        
    try:
        # 检查知识库是否存在
        kb = local_doc_qa.milvus_summary.kb_dao.get_knowledge_base_by_id(kb_id)
        if not kb:
            return sanic_json({"code": 404, "msg": f"知识库不存在: {kb_id}"})
            
        # 检查权限
        is_owner = kb.user_id == user_id
        kb_type = kb.kb_type or 'personal'
        
        # 个人知识库和临时知识库只有所有者可以设置权限
        if kb_type in ['personal', 'temporary'] and not is_owner:
            return sanic_json({"code": 403, "msg": "只有知识库所有者可以设置权限"})
            
        # 团队知识库需要所有者或管理员权限
        if kb_type == 'team' and not is_owner:
            has_admin = local_doc_qa.milvus_summary.kb_dao.check_kb_access(user_id, kb_id, 'admin')
            if not has_admin:
                return sanic_json({"code": 403, "msg": "没有权限设置此知识库的权限"})

        debug_logger.info(f"更新知识库权限 - 操作用户: {user_id}, 知识库: {kb_id}, 类型: {kb_type}")

        # 提取当前权限数据进行比较
        current_permissions = await _get_current_kb_permissions(local_doc_qa, kb_id)
        
        # 对于管理员，需要验证操作的用户和部门是否在其管辖范围内
        user_role = req.ctx.user.get('role', 'user') if hasattr(req, 'ctx') and hasattr(req.ctx, 'user') else 'user'
        if user_role == 'admin':
            # 只验证发生变化的权限，而不是所有权限
            validation_result = await _validate_admin_permission_changes(local_doc_qa, user_id, permissions_data, current_permissions)
            if not validation_result['valid']:
                return sanic_json({"code": 403, "msg": validation_result['message']})
        
        # 处理新的权限数据
        response_data = await _process_permissions_update(local_doc_qa, kb_id, permissions_data, current_permissions, user_id)
        
        # 返回结果
        debug_logger.info(f"知识库权限更新完成 - KB: {kb_id}, 成功: {response_data['success_count']}, 失败: {response_data['failed_count']}")
        return sanic_json({
            "code": 200,
            "msg": "知识库权限更新完成", 
            "data": {
                "kb_id": kb_id,
                "kb_type": kb_type,
                **response_data
            }
        })
    except Exception as e:
        debug_logger.error(f"更新知识库权限失败: {str(e)}")
        return sanic_json({"code": 500, "msg": f"更新知识库权限失败: {str(e)}"})


async def _get_kb_permission_detailed_data(local_doc_qa, kb_id, user_id=None, user_role=None):
    """获取知识库权限详细数据（辅助函数）
    
    将权限数据获取和处理逻辑抽离为独立函数，便于维护
    
    Args:
        local_doc_qa: 本地文档问答对象
        kb_id: 知识库ID
        user_id: 当前用户ID
        user_role: 当前用户角色
        
    Returns:
        包含部门、用户和权限数据的字典
    """
    # 初始化DAO对象
    dept_dao = local_doc_qa.milvus_summary.department_dao
    user_dao = local_doc_qa.milvus_summary.user_dao
    
    # 获取部门数据
    departments = []
    try:
        if user_role == 'superadmin':
            # 超级管理员可以看到所有部门
            dept_objects = dept_dao.get_all_departments()
        elif user_role == 'admin':
            # 管理员只能看到自己管辖的部门
            user_info = user_dao.get_user_by_id(user_id)
            if user_info and user_info.dept_id:
                # 获取管理员所属部门及其所有子部门
                dept_objects = []
                
                # 添加用户所属部门
                user_dept = dept_dao.get_department_by_id(user_info.dept_id)
                if user_dept:
                    dept_objects.append(user_dept)
                
                # 递归获取所有子部门
                def get_child_departments_recursive(parent_dept_id):
                    child_depts = dept_dao.get_child_departments(parent_dept_id)
                    for child_dept in child_depts:
                        dept_objects.append(child_dept)
                        # 递归获取子部门的子部门
                        get_child_departments_recursive(child_dept.dept_id)
                
                get_child_departments_recursive(user_info.dept_id)
            else:
                dept_objects = []
        else:
            # 普通用户不能管理权限，但为了兼容性返回空列表
            dept_objects = []
            
        for dept in dept_objects:
            departments.append({
                "dept_id": dept.dept_id,
                "dept_name": dept.dept_name,
                "parent_dept_id": dept.parent_dept_id
            })
    except Exception as e:
        debug_logger.error(f"获取部门数据失败: {str(e)}")
        departments = []

    # 获取用户数据 - 根据用户角色过滤
    users = []
    try:
        if user_role == 'superadmin':
            # 超级管理员可以看到所有用户
            user_objects = user_dao.get_active_users()
        elif user_role == 'admin':
            # 管理员只能看到自己管辖部门内的用户，且排除其他管理员
            user_info = user_dao.get_user_by_id(user_id)
            if user_info and user_info.dept_id:
                # 获取管理员管辖范围内的所有部门ID
                dept_ids = [dept['dept_id'] for dept in departments]
                if dept_ids:
                    # 构建SQL查询，只获取这些部门的普通用户
                    dept_ids_str = ','.join(['%s'] * len(dept_ids))
                    query = f"""
                        SELECT user_id, username, role, dept_id, email, status 
                        FROM User 
                        WHERE dept_id IN ({dept_ids_str}) 
                        AND status = 'active' 
                        AND role = 'user'
                        ORDER BY username
                    """
                    user_data = user_dao.execute_query(query, tuple(dept_ids), fetch=True)
                    user_objects = []
                    for user_row in user_data:
                        from qanything_kernel.connector.database.mysql.models.user import User
                        user = User(
                            user_id=user_row[0],
                            username=user_row[1],
                            role=user_row[2],
                            dept_id=user_row[3],
                            email=user_row[4] if len(user_row) > 4 else None,
                            status=user_row[5] if len(user_row) > 5 else 'active'
                        )
                        user_objects.append(user)
                else:
                    user_objects = []
            else:
                user_objects = []
        else:
            # 普通用户不能管理权限
            user_objects = []
            
        for user in user_objects:
            users.append({
                "user_id": user.user_id,
                "username": user.username,
                "role": user.role,
                "dept_id": user.dept_id
            })
    except Exception as e:
        debug_logger.error(f"获取用户数据失败: {str(e)}")
        users = []

    # 将用户按部门分组
    users_by_dept = {}
    for user in users:
        dept_id = user.get("dept_id")
        if dept_id not in users_by_dept:
            users_by_dept[dept_id] = []
        users_by_dept[dept_id].append({
            "user_id": user.get("user_id"), 
            "username": user.get("username"), 
            "role": user.get("role")
        })

    # 构建部门树
    dept_dict = {}
    for dept in departments:
        dept_id = dept.get("dept_id")
        dept_dict[dept_id] = {
            "dept_id": dept_id, 
            "dept_name": dept.get("dept_name"), 
            "parent_dept_id": dept.get("parent_dept_id"),
            "children": [], 
            "users": users_by_dept.get(dept_id, [])
        }

    # 构建部门树结构
    tree = []
    for dept_id, dept in dept_dict.items():
        parent_id = dept.get("parent_dept_id")
        if parent_id is None:
            tree.append(dept)
        elif parent_id in dept_dict:
            dept_dict[parent_id]["children"].append(dept)

    # 获取权限数据
    permissions = {'user': {}, 'department': {}, 'group': {}}
    try:
        # 获取用户权限
        user_permissions = local_doc_qa.milvus_summary.kb_dao.get_kb_access_by_type(kb_id, 'user')
        for perm in user_permissions:
            user_info = user_dao.get_user_by_id(perm['subject_id'])
            if user_info:
                permissions['user'][perm['subject_id']] = {
                    "name": user_info.username,
                    "permission_type": perm['permission_type']
                }
        
        # 获取部门权限
        dept_permissions = local_doc_qa.milvus_summary.kb_dao.get_kb_access_by_type(kb_id, 'department')
        for perm in dept_permissions:
            dept_info = dept_dao.get_department_by_id(perm['subject_id'])
            if dept_info:
                permissions['department'][perm['subject_id']] = {
                    "name": dept_info.dept_name,
                    "permission_type": perm['permission_type']
                }
        
    except Exception as e:
        debug_logger.error(f"获取权限数据失败: {str(e)}")
    
    return {
        "departments": tree,
        "unassigned_users": users_by_dept.get(None, []),
        "permissions": permissions
    }

async def _get_current_kb_permissions(local_doc_qa, kb_id):
    """获取当前知识库的权限设置
    
    Args:
        local_doc_qa: 本地文档问答对象
        kb_id: 知识库ID
        
    Returns:
        权限字典，格式为 {subject_id:subject_type: permission_type}
    """
    kb_dao = local_doc_qa.milvus_summary.kb_dao
    query = """
        SELECT subject_id, subject_type, permission_type 
        FROM KnowledgeBaseAccess 
        WHERE kb_id = %s
    """
    current_permissions = kb_dao.execute_query(query, (kb_id,), fetch=True)
    return {f"{perm[0]}:{perm[1]}": perm[2] for perm in current_permissions}

async def _process_permissions_update(local_doc_qa, kb_id, permissions_data, current_perm_dict, user_id):
    """处理权限更新请求
    
    Args:
        local_doc_qa: 本地文档问答对象
        kb_id: 知识库ID
        permissions_data: 新的权限数据
        current_perm_dict: 当前权限字典
        user_id: 操作用户ID
        
    Returns:
        包含处理结果统计的字典
    """
    new_permissions = []
    try:
        # 处理不同类型的权限，不包括用户组
        for key, subject_type, id_field in [
            ('user_permissions', 'user', 'user_id'),
            ('department_permissions', 'department', 'dept_id')
        ]:
            for perm in permissions_data.get(key, []):
                subject_id = perm.get(id_field)
                permission_type = perm.get('permission_type')
                if subject_id and permission_type:
                    new_permissions.append({
                        'subject_id': subject_id,
                        'subject_type': subject_type,
                        'permission_type': permission_type
                    })
    except Exception as e:
        debug_logger.error(f"权限数据格式错误: {str(e)}")
        raise ValueError(f"权限数据格式错误: {str(e)}")

    # 验证和过滤权限设置
    validated_permissions = []
    invalid_count = 0
    skipped_count = 0

    # 构建新权限字典
    new_perm_dict = {}
    for perm in new_permissions:
        subject_id = perm.get('subject_id')
        subject_type = perm.get('subject_type')
        permission_type = perm.get('permission_type')

        # 基本参数验证
        if not all([subject_id, subject_type, permission_type]):
            invalid_count += 1
            continue
        
        if subject_type not in ['user', 'department']:  # 排除group
            invalid_count += 1
            continue

        if permission_type not in ['read', 'write', 'admin', 'remove']:
            invalid_count += 1
            continue

        # 生成权限字典键值
        key = f"{subject_id}:{subject_type}"
        new_perm_dict[key] = permission_type

        # 检查权限是否已存在且相同（跳过未变更的权限）
        if key in current_perm_dict and current_perm_dict[key] == permission_type:
            skipped_count += 1
            continue

        # 验证主体是否存在
        exists, error_msg = _verify_subject_exists(local_doc_qa, subject_id, subject_type)
        if not exists:
            debug_logger.warning(f"主体验证失败 - ID: {subject_id}, 类型: {subject_type}, 错误: {error_msg}")
            invalid_count += 1
            continue

        # 添加到已验证的权限列表
        validated_permissions.append(perm)

    # 处理需要删除的权限（只处理用户和部门权限，保留用户组权限）
    for key, _ in current_perm_dict.items():
        subject_id, subject_type = key.split(':')
        if subject_type != 'group' and key not in new_perm_dict:  # 跳过用户组权限
            validated_permissions.append({
                'subject_id': subject_id,
                'subject_type': subject_type,
                'permission_type': 'remove'
            })

    # 应用变更
    success_count = 0
    failed_count = 0

    for perm in validated_permissions:
        success, msg = _set_permission(
            local_doc_qa, kb_id, perm['subject_id'],
            perm['subject_type'], perm['permission_type'], user_id
        )
        if success:
            success_count += 1
            debug_logger.info(f"权限设置成功 - KB: {kb_id}, 主体: {perm['subject_id']}, 类型: {perm['subject_type']}, 权限: {perm['permission_type']}")
        else:
            failed_count += 1
            debug_logger.error(f"权限设置失败 - KB: {kb_id}, 主体: {perm['subject_id']}, 类型: {perm['subject_type']}, 权限: {perm['permission_type']}, 原因: {msg}")

    # 计算未变更权限数量
    unchanged_count = 0
    for key in current_perm_dict:
        subject_id, subject_type = key.split(':')
        if subject_type != 'group' and key in new_perm_dict and current_perm_dict[key] == new_perm_dict[key]:
            unchanged_count += 1

    return {
        "success_count": success_count,  # 成功更新的权限数量
        "failed_count": failed_count,  # 更新失败的权限数量
        "skipped_count": skipped_count,  # 跳过的未变更权限数量
        "invalid_count": invalid_count,  # 无效的权限数量
        "total_processed": len(validated_permissions),  # 总共处理的权限数量
        "unchanged_count": unchanged_count  # 未变更的权限数量
    }

async def _validate_admin_permission_changes(local_doc_qa, admin_user_id, permissions_data, current_permissions):
    """验证管理员的权限变化是否合法（只验证发生变化的权限）
    
    Args:
        local_doc_qa: 本地文档问答对象
        admin_user_id: 管理员用户ID
        permissions_data: 新的权限数据
        current_permissions: 当前权限字典
        
    Returns:
        验证结果字典，包含 valid 和 message 字段
    """
    try:
        debug_logger.info(f"开始验证管理员权限变化 - 管理员: {admin_user_id}")
        
        user_dao = local_doc_qa.milvus_summary.user_dao
        dept_dao = local_doc_qa.milvus_summary.department_dao
        
        # 获取管理员信息
        admin_info = user_dao.get_user_by_id(admin_user_id)
        if not admin_info or not admin_info.dept_id:
            debug_logger.error(f"管理员 {admin_user_id} 没有被分配到任何部门")
            return {"valid": False, "message": "您没有被分配到任何部门"}
        
        admin_dept_id = admin_info.dept_id
        debug_logger.info(f"管理员 {admin_user_id} 所属部门: {admin_dept_id}")
        
        # 获取管理员管辖的所有部门ID
        try:
            from qanything_kernel.qanything_server.dept import _get_departments_in_scope
            managed_dept_ids = _get_departments_in_scope(dept_dao, admin_dept_id)
            debug_logger.info(f"管理员 {admin_user_id} 管辖的部门ID: {managed_dept_ids}")
        except Exception as e:
            debug_logger.error(f"获取管理员管辖部门失败: {str(e)}")
            return {"valid": False, "message": f"获取管辖范围失败: {str(e)}"}
        
        # 构建新权限字典
        new_perm_dict = {}
        
        # 处理用户权限
        for user_perm in permissions_data.get('user_permissions', []):
            user_id = user_perm.get('user_id')
            permission_type = user_perm.get('permission_type')
            if user_id and permission_type:
                key = f"{user_id}:user"
                new_perm_dict[key] = permission_type
        
        # 处理部门权限
        for dept_perm in permissions_data.get('department_permissions', []):
            dept_id = dept_perm.get('dept_id')
            permission_type = dept_perm.get('permission_type')
            if dept_id and permission_type:
                key = f"{dept_id}:department"
                new_perm_dict[key] = permission_type
        
        # 找出发生变化的权限（新增、修改、删除）
        changed_permissions = []
        
        # 检查新增和修改的权限
        for key, new_perm in new_perm_dict.items():
            subject_id, subject_type = key.split(':')
            if key not in current_permissions or current_permissions[key] != new_perm:
                changed_permissions.append({
                    'subject_id': subject_id,
                    'subject_type': subject_type,
                    'permission_type': new_perm,
                    'change_type': 'add' if key not in current_permissions else 'modify'
                })
        
        # 检查删除的权限
        for key in current_permissions:
            subject_id, subject_type = key.split(':')
            if subject_type != 'group' and key not in new_perm_dict:  # 跳过用户组权限
                changed_permissions.append({
                    'subject_id': subject_id,
                    'subject_type': subject_type,
                    'permission_type': 'remove',
                    'change_type': 'remove'
                })
        
        debug_logger.info(f"检测到 {len(changed_permissions)} 个权限变化")
        
        # 验证发生变化的用户权限
        changed_user_perms = [p for p in changed_permissions if p['subject_type'] == 'user']
        if changed_user_perms:
            debug_logger.info(f"验证用户权限变化，共 {len(changed_user_perms)} 项")
            for user_perm in changed_user_perms:
                target_user_id = user_perm['subject_id']
                change_type = user_perm['change_type']
                debug_logger.info(f"检查用户权限变化: {target_user_id} ({change_type})")
                
                # 检查目标用户是否存在且为普通用户
                target_user = user_dao.get_user_by_id(target_user_id)
                if not target_user:
                    debug_logger.error(f"用户 {target_user_id} 不存在")
                    return {"valid": False, "message": f"用户 {target_user_id} 不存在"}
                
                # 管理员不能操作其他管理员或超级管理员
                if target_user.role in ['admin', 'superadmin']:
                    debug_logger.error(f"管理员 {admin_user_id} 尝试{change_type}管理员账号 {target_user.username} 的权限")
                    return {"valid": False, "message": f"您不能设置管理员账号 {target_user.username} 的权限"}
                
                # 检查目标用户是否在管理员管辖范围内
                if target_user.dept_id not in managed_dept_ids:
                    debug_logger.error(f"用户 {target_user.username} (部门: {target_user.dept_id}) 不在管理员 {admin_user_id} 的管辖范围内")
                    return {"valid": False, "message": f"用户 {target_user.username} 不在您的管辖范围内"}
                
                debug_logger.info(f"用户权限变化 {target_user.username} 验证通过")
        
        # 验证发生变化的部门权限
        changed_dept_perms = [p for p in changed_permissions if p['subject_type'] == 'department']
        if changed_dept_perms:
            debug_logger.info(f"验证部门权限变化，共 {len(changed_dept_perms)} 项")
            for dept_perm in changed_dept_perms:
                dept_id = dept_perm['subject_id']
                change_type = dept_perm['change_type']
                if dept_id not in managed_dept_ids:
                    dept_info = dept_dao.get_department_by_id(dept_id)
                    dept_name = dept_info.dept_name if dept_info else dept_id
                    debug_logger.error(f"部门 {dept_name} (ID: {dept_id}) 不在管理员 {admin_user_id} 的管辖范围内")
                    return {"valid": False, "message": f"部门 {dept_name} 不在您的管辖范围内"}
                debug_logger.info(f"部门权限变化 {dept_id} ({change_type}) 验证通过")
        
        debug_logger.info(f"管理员 {admin_user_id} 权限变化验证全部通过")
        return {"valid": True, "message": "验证通过"}
        
    except Exception as e:
        debug_logger.error(f"验证管理员权限变化失败: {str(e)}")
        return {"valid": False, "message": f"权限验证失败: {str(e)}"}

# 保留原来的函数作为备用（可以在需要时删除）
async def _validate_admin_permission_operations_backup(local_doc_qa, admin_user_id, permissions_data):
    """原始的权限验证函数（备用）"""
    pass
