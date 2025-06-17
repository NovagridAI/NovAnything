"""
模型配置API处理模块
"""
import uuid

from sanic.request import Request

from qanything_kernel.connector.database.mysql.daos.model_config_dao import ModelConfigDAO
from qanything_kernel.connector.database.mysql.models.model_config import ModelConfig
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.qanything_server.api_utils import create_success_response, create_error_response
from qanything_kernel.qanything_server.auth import auth_required, ROLE_ADMIN, ROLE_USER, ROLE_SUPERADMIN
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.utils.general_utils import safe_get, get_time_async


@get_time_async
@auth_required(required_role=ROLE_USER)
async def create_model_config(request: Request):
    """创建模型配置
    
    Args:
        request: Sanic请求对象
        
    Returns:
        JSON响应
    """
    try:
        local_doc_qa: LocalDocQA = request.app.ctx.local_doc_qa

        # 确保数据库表存在
        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        model_config_dao.create_table()

        # 从请求上下文获取用户信息
        user_id = request.ctx.user["user_id"]
        role = request.ctx.user["role"]

        # 使用safe_get获取请求字段
        service_id = safe_get(request, 'service_id')
        service_name = safe_get(request, 'service_name')
        request_format = safe_get(request, 'request_format')
        api_key = safe_get(request, 'api_key')
        api_proxy = safe_get(request, 'api_proxy')
        model_endpoint = safe_get(request, 'model_endpoint')

        # 获取可选字段
        temperature = float(safe_get(request, 'temperature', 1.0))
        top_k = int(safe_get(request, 'top_k', 1))
        api_context_length = int(safe_get(request, 'api_context_length', 1024))
        top_p = float(safe_get(request, 'top_p', 1.0))
        max_token = int(safe_get(request, 'max_token', 1024))
        context_length = int(safe_get(request, 'context_length', 10))
        is_global = bool(safe_get(request, 'is_global', False))

        # 检查必需字段
        required_fields = [service_id, service_name, request_format, api_key, api_proxy, model_endpoint]
        if not all(required_fields):
            missing_fields = []
            field_names = ["service_id", "service_name", "request_format", "api_key", "api_proxy", "model_endpoint"]
            for i, field in enumerate(required_fields):
                if not field:
                    missing_fields.append(field_names[i])
            debug_logger.error(f"缺少必需字段: {', '.join(missing_fields)}")
            return create_error_response(400, f"缺少必需字段: {', '.join(missing_fields)}")

        # 检查全局模型创建权限，管理员和超级管理员创建的模型自动设为全局模型
        if role in [ROLE_ADMIN, ROLE_SUPERADMIN]:
            is_global = True  # 管理员创建的模型自动设为全局模型
        elif is_global and role not in [ROLE_ADMIN, ROLE_SUPERADMIN]:
            return create_error_response(403, "非管理员用户不能创建全局模型")

        # 创建模型配置
        config_id = f"model_cfg_{uuid.uuid4().hex[:8]}"
        model_config = ModelConfig(
            config_id=config_id,
            user_id=user_id,
            service_id=service_id,
            service_name=service_name,
            request_format=request_format,
            api_key=api_key,
            api_proxy=api_proxy,
            model_endpoint=model_endpoint,
            temperature=temperature,
            top_k=top_k,
            api_context_length=api_context_length,
            top_p=top_p,
            max_token=max_token,
            context_length=context_length,
            is_global=is_global,
            is_deleted=False
        )

        # 保存到数据库
        success = model_config_dao.add_model_config(model_config)

        if success:
            debug_logger.info(f"创建模型配置成功: {config_id}")
            return create_success_response("创建模型配置成功", {"config_id": config_id})
        else:
            debug_logger.error(f"创建模型配置失败: {config_id}")
            return create_error_response(500, "创建模型配置失败")

    except Exception as e:
        debug_logger.error(f"创建模型配置错误: {str(e)}")
        return create_error_response(500, f"服务器错误: {str(e)}")


@get_time_async
@auth_required(required_role=ROLE_USER)
async def update_model_config(request: Request):
    """更新模型配置
    
    Args:
        request: Sanic请求对象
        
    Returns:
        JSON响应
    """
    try:
        local_doc_qa: LocalDocQA = request.app.ctx.local_doc_qa

        # 确保数据库表存在并检查字段
        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        model_config_dao.create_table()

        # 从请求上下文获取用户信息
        user_id = request.ctx.user["user_id"]
        role = request.ctx.user["role"]
        debug_logger.info(f"更新模型配置开始，用户ID: {user_id}，角色: {role}")

        # 使用safe_get获取必需字段
        config_id = safe_get(request, 'config_id')

        if not config_id:
            debug_logger.warning("缺少必需字段: config_id")
            return create_error_response(400, "缺少必需字段: config_id")

        # 使用safe_get获取可选字段
        service_name = safe_get(request, 'service_name')
        api_key = safe_get(request, 'api_key')
        api_proxy = safe_get(request, 'api_proxy')
        model_endpoint = safe_get(request, 'model_endpoint')
        temperature = safe_get(request, 'temperature')
        top_k = safe_get(request, 'top_k')
        api_context_length = safe_get(request, 'api_context_length')
        top_p = safe_get(request, 'top_p')
        max_token = safe_get(request, 'max_token')
        context_length = safe_get(request, 'context_length')
        is_global = safe_get(request, 'is_global')
        
        # 记录所有请求参数
        debug_logger.info(f"接收到的更新参数: service_name={service_name}, api_key={'已设置' if api_key else '未设置'}, "
                         f"api_proxy={api_proxy}, model_endpoint={model_endpoint}, temperature={temperature}, "
                         f"top_k={top_k}, api_context_length={api_context_length}, top_p={top_p}, "
                         f"max_token={max_token}, context_length={context_length}, is_global={is_global}")

        # 获取原配置
        existing_config = model_config_dao.get_model_config(config_id)

        if not existing_config:
            return create_error_response(404, "模型配置不存在")

        # 检查权限：管理员和超级管理员可以修改所有配置，普通用户只能修改自己的配置
        if role not in [ROLE_ADMIN, ROLE_SUPERADMIN] and existing_config.user_id != user_id:
            debug_logger.warning(f"权限不足，用户{user_id}尝试修改用户{existing_config.user_id}的配置")
            return create_error_response(403, "无权修改此模型配置")

        # 如果是全局模型，检查修改权限
        if existing_config.is_global and role not in [ROLE_ADMIN, ROLE_SUPERADMIN]:
            # 普通用户只能修改某些参数，不能修改全局模型的基本信息
            allowed_fields = [
                "temperature", "top_k", "api_context_length",
                "top_p", "max_token", "context_length", "is_global"
            ]
            debug_logger.info(f"允许修改的字段: {allowed_fields}")

            # 检查是否尝试修改不允许的字段
            for field_name, field_value in [
                ("service_name", service_name),
                ("api_key", api_key),
                ("api_proxy", api_proxy),
                ("model_endpoint", model_endpoint),
                ("is_global", is_global)
            ]:
                if field_value is not None:
                    debug_logger.warning(f"普通用户尝试修改不允许的字段: {field_name}={field_value}")
                    return create_error_response(403, f"普通用户不能修改全局模型的基本信息字段: {field_name}")

        # 准备更新数据
        update_data = {}

        # 根据用户角色和模型类型确定可更新字段
        if role in [ROLE_ADMIN, ROLE_SUPERADMIN]:
            # 管理员可以更新所有字段
            if service_name is not None:
                update_data["service_name"] = service_name
            if api_key is not None:
                update_data["api_key"] = api_key
            if api_proxy is not None:
                update_data["api_proxy"] = api_proxy
            if model_endpoint is not None:
                update_data["model_endpoint"] = model_endpoint
            if is_global is not None:
                update_data["is_global"] = bool(is_global)
        elif not existing_config.is_global:
            # 普通用户更新自己的非全局模型
            if service_name is not None:
                update_data["service_name"] = service_name
            if api_key is not None:
                update_data["api_key"] = api_key
            if api_proxy is not None:
                update_data["api_proxy"] = api_proxy
            if model_endpoint is not None:
                update_data["model_endpoint"] = model_endpoint

        # 所有用户都可以更新的微调参数
        if temperature is not None:
            update_data["temperature"] = float(temperature)
        if top_k is not None:
            update_data["top_k"] = int(top_k)
        if api_context_length is not None:
            update_data["api_context_length"] = int(api_context_length)
        if top_p is not None:
            update_data["top_p"] = float(top_p)
        if max_token is not None:
            update_data["max_token"] = int(max_token)
        if context_length is not None:
            update_data["context_length"] = int(context_length)

        # 更新数据库
        if update_data:
            debug_logger.info(f"执行数据库更新操作，更新字段: {list(update_data.keys())}")
            success = model_config_dao.update_model_config(config_id, update_data)

            if success:
                debug_logger.info(f"保存模型配置成功，config_id: {config_id}")
                return create_success_response("保存模型配置成功")
            else:
                debug_logger.error(f"保存模型配置失败，config_id: {config_id}")
                return create_error_response(500, "保存模型配置失败")
        else:
            debug_logger.warning("没有有效的更新字段")
            return create_error_response(400, "无有效更新字段")

    except Exception as e:
        return create_error_response(500, f"服务器错误: {str(e)}")


@get_time_async
@auth_required(required_role=ROLE_USER)
async def get_model_config(request: Request):
    """获取模型配置详情
    
    Args:
        request: Sanic请求对象
        
    Returns:
        JSON响应
    """
    try:
        local_doc_qa: LocalDocQA = request.app.ctx.local_doc_qa

        # 确保数据库表存在并检查字段
        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        model_config_dao.create_table()

        # 从请求上下文获取用户信息
        user_id = request.ctx.user["user_id"]
        role = request.ctx.user["role"]

        # 使用safe_get获取请求参数
        config_id = safe_get(request, 'config_id')
        debug_logger.info(f"从请求中获取的config_id: {config_id}, type: {type(config_id)}")

        # 如果config_id是列表，取第一个元素
        if isinstance(config_id, list) and len(config_id) > 0:
            config_id = config_id[0]
            debug_logger.info(f"config_id是列表，使用第一个元素: {config_id}")

        if not config_id:
            return create_error_response(400, "缺少必需参数: config_id")

        # 获取配置
        debug_logger.info(f"开始查询模型配置: config_id={config_id}")
        config = model_config_dao.get_model_config(config_id)
        debug_logger.info(f"获取模型配置结果: {config}")

        if not config:
            debug_logger.warning(f"模型配置不存在: {config_id}")
            return create_error_response(404, "模型配置不存在")

        # 检查权限
        if role not in [ROLE_ADMIN, ROLE_SUPERADMIN] and config.user_id != user_id and not config.is_global:
            debug_logger.warning(f"无权查看模型配置: config_id={config_id}, user_id={user_id}, config.user_id={config.user_id}, config.is_global={config.is_global}")
            return create_error_response(403, "无权查看此模型配置")

        # 脱敏敏感信息
        config_data = config.to_dict()
        debug_logger.info(f"返回模型配置数据: {config_data}")

        return create_success_response("获取模型配置成功", config_data)

    except Exception as e:
        debug_logger.error(f"获取模型配置错误: {str(e)}")
        return create_error_response(500, f"服务器错误: {str(e)}")


@get_time_async
@auth_required(required_role=ROLE_USER)
async def list_model_configs(request: Request):
    """获取模型配置列表
    
    Args:
        request: Sanic请求对象
        
    Returns:
        JSON响应
    """
    try:
        local_doc_qa: LocalDocQA = request.app.ctx.local_doc_qa

        # 确保数据库表存在并检查字段
        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        model_config_dao.create_table()

        # 从请求上下文获取用户信息
        user_id = request.ctx.user["user_id"]
        role = request.ctx.user["role"]

        # 获取查询参数，使用safe_get
        only_global = bool(safe_get(request, 'only_global', False))

        configs = []

        # 根据查询条件和用户角色获取配置
        if only_global:
            # 仅获取全局配置
            configs = model_config_dao.get_global_model_configs()
        else:
            # 管理员和超级管理员可以看到所有模型配置，普通用户只能看到自己的和全局的
            if role in [ROLE_ADMIN, ROLE_SUPERADMIN]:
                configs = model_config_dao.get_all_model_configs()
            else:
                configs = model_config_dao.get_model_configs_by_user(user_id)

        # 处理结果
        config_list = []
        for config in configs:
            config_data = config.to_dict()
            config_list.append(config_data)

        return create_success_response("获取模型配置列表成功", {
            "configs": config_list,
            "total": len(config_list)
        })

    except Exception as e:
        debug_logger.error(f"获取模型配置列表错误: {str(e)}")
        return create_error_response(500, f"服务器错误: {str(e)}")


@get_time_async
@auth_required(required_role=ROLE_USER)
async def delete_model_config(request: Request):
    """删除模型配置
    
    Args:
        request: Sanic请求对象
        
    Returns:
        JSON响应
    """
    try:
        local_doc_qa: LocalDocQA = request.app.ctx.local_doc_qa

        # 确保数据库表存在并检查字段
        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        model_config_dao.create_table()

        # 从请求上下文获取用户信息
        user_id = request.ctx.user["user_id"]
        role = request.ctx.user["role"]

        # 使用safe_get获取参数
        config_id = safe_get(request, 'config_id')
        
        # 如果config_id是列表，取第一个元素
        if isinstance(config_id, list) and len(config_id) > 0:
            config_id = config_id[0]

        if not config_id:
            return create_error_response(400, "缺少必需字段: config_id")

        # 获取配置
        config = model_config_dao.get_model_config(config_id)

        if not config:
            return create_error_response(404, "模型配置不存在")

        # 检查权限：管理员和超级管理员可以删除所有配置，普通用户只能删除自己的配置
        if role not in [ROLE_ADMIN, ROLE_SUPERADMIN] and config.user_id != user_id:
            return create_error_response(403, "无权删除此模型配置")

        # 检查全局配置的删除权限
        if config.is_global and role not in [ROLE_ADMIN, ROLE_SUPERADMIN]:
            return create_error_response(403, "普通用户不能删除全局模型配置")

        # 检查是否删除的是活跃模型
        is_deleting_active = config.is_active
        
        # 执行删除（逻辑删除）
        success = model_config_dao.delete_model_config(config_id)

        if success:
            # 如果删除的是活跃模型，需要自动设置下一个可用模型为活跃
            if is_deleting_active:
                debug_logger.info(f"删除了活跃模型 {config_id}，尝试设置备用活跃模型")
                
                # 获取剩余的可用模型
                if role in [ROLE_ADMIN, ROLE_SUPERADMIN]:
                    remaining_configs = model_config_dao.get_all_model_configs()
                else:
                    remaining_configs = model_config_dao.get_model_configs_by_user(user_id)
                
                if remaining_configs:
                    # 选择第一个可用模型作为新的活跃模型
                    new_active_config = remaining_configs[0]
                    set_success = model_config_dao.set_active_model_for_user(user_id, new_active_config.config_id)
                    
                    if set_success:
                        debug_logger.info(f"已自动设置 {new_active_config.service_name} 为新的活跃模型")
                        return create_success_response(f"删除模型配置成功，已自动设置 {new_active_config.service_name} 为活跃模型")
                    else:
                        debug_logger.warning(f"删除成功，但设置备用活跃模型失败")
                        return create_success_response("删除模型配置成功，但未能自动设置新的活跃模型，请手动设置")
                else:
                    debug_logger.warning(f"删除活跃模型后没有剩余可用模型")
                    return create_success_response("删除模型配置成功，但没有其他可用模型，请添加新的模型配置")
            else:
                return create_success_response("删除模型配置成功")
        else:
            return create_error_response(500, "删除模型配置失败")

    except Exception as e:
        debug_logger.error(f"删除模型配置错误: {str(e)}")
        return create_error_response(500, f"服务器错误: {str(e)}")


@get_time_async
@auth_required(required_role=ROLE_USER)
async def set_active_model_config(request: Request):
    """设置活跃模型配置
    
    Args:
        request: Sanic请求对象
        
    Returns:
        JSON响应
    """
    try:
        local_doc_qa: LocalDocQA = request.app.ctx.local_doc_qa

        # 确保数据库表存在并检查字段
        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        model_config_dao.create_table()

        # 从请求上下文获取用户信息
        user_id = request.ctx.user["user_id"]
        role = request.ctx.user["role"]

        # 使用safe_get获取参数
        config_id = safe_get(request, 'config_id')
        
        # 如果config_id是列表，取第一个元素
        if isinstance(config_id, list) and len(config_id) > 0:
            config_id = config_id[0]

        if not config_id:
            return create_error_response(400, "缺少必需字段: config_id")

        # 获取配置
        config = model_config_dao.get_model_config(config_id)

        if not config:
            return create_error_response(404, "模型配置不存在")

        # 检查权限：管理员和超级管理员可以设置任何配置为活跃，普通用户只能设置自己的和全局的配置为活跃
        if role not in [ROLE_ADMIN, ROLE_SUPERADMIN] and config.user_id != user_id and not config.is_global:
            return create_error_response(403, "无权设置此模型配置为活跃")

        # 设置活跃模型（这里可以根据实际需求实现，比如存储在用户偏好设置中）
        # 目前简单返回成功，实际应用中可能需要在用户表或偏好设置表中记录活跃模型
        success = model_config_dao.set_active_model_for_user(user_id, config_id)

        if success:
            return create_success_response("设置活跃模型成功")
        else:
            return create_error_response(500, "设置活跃模型失败")

    except Exception as e:
        debug_logger.error(f"设置活跃模型错误: {str(e)}")
        return create_error_response(500, f"服务器错误: {str(e)}")


@get_time_async
@auth_required(required_role=ROLE_USER)
async def get_active_model_config(request: Request):
    """获取用户的活跃模型配置
    
    Args:
        request: Sanic请求对象
        
    Returns:
        JSON响应
    """
    try:
        local_doc_qa: LocalDocQA = request.app.ctx.local_doc_qa

        # 确保数据库表存在并检查字段
        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        model_config_dao.create_table()

        # 从请求上下文获取用户信息
        user_id = request.ctx.user["user_id"]
        role = request.ctx.user["role"]

        # 获取用户的活跃模型（DAO层已经实现了完整的fallback逻辑）
        active_config = model_config_dao.get_active_model_for_user(user_id)
        
        if active_config:
            config_data = active_config.to_dict()
            debug_logger.info(f"用户 {user_id} 获取到活跃模型: {config_data.get('service_name', 'Unknown')}")
            return create_success_response("获取活跃模型成功", config_data)
        else:
            debug_logger.warning(f"用户 {user_id} 没有找到任何可用的活跃模型")
            return create_error_response(404, "未找到活跃模型，请联系管理员配置")

    except Exception as e:
        debug_logger.error(f"获取活跃模型错误: {str(e)}")
        return create_error_response(500, f"服务器错误: {str(e)}")
