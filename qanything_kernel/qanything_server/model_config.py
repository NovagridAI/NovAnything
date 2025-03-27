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
        creativity = float(safe_get(request, 'creativity', 1.0))
        thinking_depth = float(safe_get(request, 'thinking_depth', 1.0))
        expression_style = float(safe_get(request, 'expression_style', 1.0))
        vocabulary_richness = float(safe_get(request, 'vocabulary_richness', 1.0))
        token_limit = float(safe_get(request, 'token_limit', 1.0))
        reasoning_strength = safe_get(request, 'reasoning_strength', "中")
        is_global = bool(safe_get(request, 'is_global', False))

        # 检查必需字段
        required_fields = [service_id, service_name, request_format, api_key, api_proxy, model_endpoint]
        if not all(required_fields):
            missing_fields = []
            field_names = ["service_id", "service_name", "request_format", "api_key", "api_proxy", "model_endpoint"]
            for i, field in enumerate(required_fields):
                if not field:
                    missing_fields.append(field_names[i])
            return create_error_response(400, f"缺少必需字段: {', '.join(missing_fields)}")

        # 检查全局模型创建权限
        if is_global and role not in [ROLE_ADMIN, ROLE_SUPERADMIN]:
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
            creativity=creativity,
            thinking_depth=thinking_depth,
            expression_style=expression_style,
            vocabulary_richness=vocabulary_richness,
            token_limit=token_limit,
            reasoning_strength=reasoning_strength,
            is_global=is_global,
            is_deleted=False
        )

        # 保存到数据库
        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        success = model_config_dao.add_model_config(model_config)

        if success:
            return create_success_response("创建模型配置成功", {"config_id": config_id})
        else:
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

        # 从请求上下文获取用户信息
        user_id = request.ctx.user["user_id"]
        role = request.ctx.user["role"]

        # 使用safe_get获取必需字段
        config_id = safe_get(request, 'config_id')

        if not config_id:
            return create_error_response(400, "缺少必需字段: config_id")

        # 使用safe_get获取可选字段
        service_name = safe_get(request, 'service_name')
        api_key = safe_get(request, 'api_key')
        api_proxy = safe_get(request, 'api_proxy')
        model_endpoint = safe_get(request, 'model_endpoint')
        creativity = safe_get(request, 'creativity')
        thinking_depth = safe_get(request, 'thinking_depth')
        expression_style = safe_get(request, 'expression_style')
        vocabulary_richness = safe_get(request, 'vocabulary_richness')
        token_limit = safe_get(request, 'token_limit')
        reasoning_strength = safe_get(request, 'reasoning_strength')
        is_global = safe_get(request, 'is_global')

        # 获取原配置
        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        existing_config = model_config_dao.get_model_config(config_id)

        if not existing_config:
            return create_error_response(404, "模型配置不存在")

        # 检查权限
        if role not in [ROLE_ADMIN, ROLE_SUPERADMIN] and existing_config.user_id != user_id:
            return create_error_response(403, "无权修改此模型配置")

        # 如果是全局模型，检查修改权限
        if existing_config.is_global and role not in [ROLE_ADMIN, ROLE_SUPERADMIN]:
            # 普通用户只能修改某些参数，不能修改全局模型的基本信息
            allowed_fields = [
                "creativity", "thinking_depth", "expression_style",
                "vocabulary_richness", "token_limit", "reasoning_strength"
            ]

            # 检查是否尝试修改不允许的字段
            for field_name, field_value in [
                ("service_name", service_name),
                ("api_key", api_key),
                ("api_proxy", api_proxy),
                ("model_endpoint", model_endpoint),
                ("is_global", is_global)
            ]:
                if field_value is not None:
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
        if creativity is not None:
            update_data["creativity"] = float(creativity)
        if thinking_depth is not None:
            update_data["thinking_depth"] = float(thinking_depth)
        if expression_style is not None:
            update_data["expression_style"] = float(expression_style)
        if vocabulary_richness is not None:
            update_data["vocabulary_richness"] = float(vocabulary_richness)
        if token_limit is not None:
            update_data["token_limit"] = float(token_limit)
        if reasoning_strength is not None:
            update_data["reasoning_strength"] = reasoning_strength

        # 更新数据库
        if update_data:
            success = model_config_dao.update_model_config(config_id, update_data)

            if success:
                return create_success_response("更新模型配置成功")
            else:
                return create_error_response(500, "更新模型配置失败")
        else:
            return create_error_response(400, "无有效更新字段")

    except Exception as e:
        debug_logger.error(f"更新模型配置错误: {str(e)}")
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

        # 从请求上下文获取用户信息
        user_id = request.ctx.user["user_id"]
        role = request.ctx.user["role"]

        # 使用safe_get获取请求参数
        config_id = safe_get(request, 'config_id')

        if not config_id:
            return create_error_response(400, "缺少必需参数: config_id")

        # 获取配置
        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        config = model_config_dao.get_model_config(config_id)

        if not config:
            return create_error_response(404, "模型配置不存在")

        # 检查权限
        if role not in [ROLE_ADMIN, ROLE_SUPERADMIN] and config.user_id != user_id and not config.is_global:
            return create_error_response(403, "无权查看此模型配置")

        # 脱敏敏感信息
        config_data = config.to_dict()
        if role not in [ROLE_ADMIN, ROLE_SUPERADMIN] and config.user_id != user_id:
            config_data["api_key"] = "******"  # 对其他用户的配置隐藏API密钥

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

        # 从请求上下文获取用户信息
        user_id = request.ctx.user["user_id"]
        role = request.ctx.user["role"]

        # 获取查询参数，使用safe_get
        only_global = bool(safe_get(request, 'only_global', False))

        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        configs = []

        # 根据查询条件获取配置
        if only_global:
            # 仅获取全局配置
            configs = model_config_dao.get_global_model_configs()
        else:
            # 获取用户有权限的所有配置（包括全局配置）
            configs = model_config_dao.get_model_configs_by_user(user_id)

        # 处理结果
        config_list = []
        for config in configs:
            config_data = config.to_dict()
            # 脱敏非当前用户创建的配置，且当前用户不是管理员
            if config.user_id != user_id and role not in [ROLE_ADMIN, ROLE_SUPERADMIN]:
                config_data["api_key"] = "******"
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

        # 从请求上下文获取用户信息
        user_id = request.ctx.user["user_id"]
        role = request.ctx.user["role"]

        # 使用safe_get获取参数
        config_id = safe_get(request, 'config_id')

        if not config_id:
            return create_error_response(400, "缺少必需字段: config_id")

        # 获取配置
        model_config_dao = ModelConfigDAO(local_doc_qa.milvus_summary.db_connection)
        config = model_config_dao.get_model_config(config_id)

        if not config:
            return create_error_response(404, "模型配置不存在")

        # 检查权限：普通用户只能删除自己的配置，管理员可以删除所有配置
        if role not in [ROLE_ADMIN, ROLE_SUPERADMIN] and config.user_id != user_id:
            return create_error_response(403, "无权删除此模型配置")

        # 检查全局配置的删除权限
        if config.is_global and role not in [ROLE_ADMIN, ROLE_SUPERADMIN]:
            return create_error_response(403, "普通用户不能删除全局模型配置")

        # 执行删除（逻辑删除）
        success = model_config_dao.delete_model_config(config_id)

        if success:
            return create_success_response("删除模型配置成功")
        else:
            return create_error_response(500, "删除模型配置失败")

    except Exception as e:
        debug_logger.error(f"删除模型配置错误: {str(e)}")
        return create_error_response(500, f"服务器错误: {str(e)}")
