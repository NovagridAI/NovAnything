from doctest import debug
import json

from sanic import response, request

from qanything_kernel.connector.database.mysql.models.qa_log import QaLog
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.qanything_server.auth import ROLE_USER, auth_required
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.utils.general_utils import get_time_async, safe_get


def ensure_json_serializable(data):
    """确保数据可以被JSON序列化，处理所有可能的复杂类型"""
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            try:
                result[k] = ensure_json_serializable(v)
            except Exception as e:
                if isinstance(v, (list, dict)):
                    result[k] = str(v)
                else:
                    result[k] = str(v) if v is not None else ""
        return result
    elif isinstance(data, list):
        result = []
        for i, item in enumerate(data):
            try:
                result.append(ensure_json_serializable(item))
            except Exception as e:
                result.append(str(item) if item is not None else "")
        return result
    elif isinstance(data, (str, int, float, bool, type(None))):
        return data
    else:
        # 对于其他类型，转为字符串
        return str(data)


@get_time_async
@auth_required(required_role=ROLE_USER)
async def get_qa_logs(req: request):
    """获取问答日志列表
    
    请求参数:
        user_id (str): 用户ID
        is_favorite (bool, 可选): 是否只获取收藏的问答记录
        page (int, 可选): 页码，默认为1
        page_size (int, 可选): 每页数量，默认为20
    
    返回:
        问答日志列表和总数，包含每条记录的完整信息
    """
    try:
        debug_logger.info("收到获取问答日志列表请求")
        local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

        user_id = safe_get(req, 'user_id')
        if not user_id:
            return response.json({
                "code": 400,
                "msg": "user_id不能为空",
                "data": None
            })

        # 获取可选参数
        is_favorite = safe_get(req, 'is_favorite')
        page = int(safe_get(req, 'page', 1))
        page_size = int(safe_get(req, 'page_size', 20))

        # 验证分页参数
        if page < 1:
            return response.json({
                "code": 400,
                "msg": "页码必须大于0",
                "data": None
            })

        if page_size < 1 or page_size > 100:
            return response.json({
                "code": 400,
                "msg": "每页数量必须在1-100之间",
                "data": None
            })

        # 计算偏移量
        offset = (page - 1) * page_size

        # 获取问答日志列表，不指定need_info以获取全部字段
        debug_logger.info(f"准备从数据库获取问答日志，参数: user_id={user_id}, limit={page_size}, offset={offset}, is_favorite={is_favorite}")
        
        qa_logs = local_doc_qa.milvus_summary.get_qa_logs(
            user_id=user_id,
            limit=page_size,
            offset=offset,
            need_info=None,  # 不指定need_info，获取全部字段
            is_favorite=is_favorite
        )
        debug_logger.info(f"从数据库获取到 {len(qa_logs)} 条问答日志")
        
        try:
            # 确保数据可以被JSON序列化
            qa_logs = ensure_json_serializable(qa_logs)
            
        except Exception as e:
            debug_logger.error(f"数据处理过程中出错: {e}")
            raise

        debug_logger.info("获取总记录数")
        total_logs = local_doc_qa.milvus_summary.get_qa_logs(
            user_id=user_id,
            need_info=["qa_id"],
            is_favorite=is_favorite
        )
        total_count = len(total_logs)
        debug_logger.info(f"总记录数: {total_count}")

        debug_logger.info("准备返回结果")
        return response.json({
            "code": 200,
            "msg": "获取问答日志列表成功",
            "data": {
                "qa_logs": qa_logs,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        })
    except Exception as e:
        debug_logger.error(f"获取问答日志列表失败: {e}")
        return response.json({
            "code": 500,
            "msg": f"获取问答日志列表失败: {str(e)}",
            "data": None
        })


@get_time_async
@auth_required(required_role=ROLE_USER)
async def get_qa_log(req: request):
    """获取问答日志详情
    
    请求参数:
        qa_id (str): 问答ID
    
    返回:
        问答日志详情的全部数据
    """
    try:
        debug_logger.info(f"收到获取问答日志详情请求, req: {req}")
        local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

        qa_id = safe_get(req, 'qa_id')
        if not qa_id:
            return response.json({
                "code": 400,
                "msg": "qa_id不能为空",
                "data": None
            })
        
        # 不指定need_info参数，获取全部字段数据
        qa_log = local_doc_qa.milvus_summary.get_qa_log_by_id(qa_id)

        if not qa_log:
            return response.json({
                "code": 404,
                "msg": "问答日志不存在",
                "data": None
            })
            
        # 确保数据可以被JSON序列化
        qa_log = ensure_json_serializable(qa_log)

        return response.json({
            "code": 200,
            "msg": "获取问答日志详情成功",
            "data": qa_log
        })
    except Exception as e:
        debug_logger.error(f"获取问答日志详情失败: {e}")
        return response.json({
            "code": 500,
            "msg": f"获取问答日志详情失败: {str(e)}",
            "data": None
        })


@get_time_async
@auth_required(required_role=ROLE_USER)
async def update_qa_log(req: request):
    """更新问答日志
    
    请求参数:
        qa_id (str): 问答ID
        update_data (dict): 要更新的数据，可包含以下字段：
            - query (str, 可选): 问题内容
            - result (str, 可选): 回答内容
            - model (str, 可选): 使用的模型名称
            - product_source (str, 可选): 产品来源
            - time_record (dict, 可选): 时间记录
            - history (list, 可选): 历史记录
            - condense_question (str, 可选): 压缩后的问题
            - prompt (str, 可选): 提示词
            - retrieval_documents (list, 可选): 检索文档
            - source_documents (list, 可选): 源文档
            - is_favorite (bool, 可选): 是否收藏
            - kb_ids (list, 可选): 知识库ID列表
    
    返回:
        更新结果
    """
    try:
        debug_logger.info("收到更新问答日志请求")
        local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

        qa_id = safe_get(req, 'qa_id')
        if not qa_id:
            return response.json({
                "code": 400,
                "msg": "qa_id不能为空",
                "data": None
            })

        update_data = safe_get(req, 'update_data', {})
        if not update_data:
            return response.json({
                "code": 400,
                "msg": "更新数据不能为空",
                "data": None
            })
            
        debug_logger.info("update_qa_log received update_data: %s", update_data)
        
        # 获取当前QA日志
        current_qa_log = local_doc_qa.milvus_summary.get_qa_log_by_id(qa_id)
        if not current_qa_log:
            return response.json({
                "code": 404,
                "msg": "问答日志不存在",
                "data": None
            })
        
        # 处理kb_ids的更新，确保临时知识库不被丢失
        if 'kb_ids' in update_data:
            new_kb_ids = update_data['kb_ids']
            debug_logger.info("update_qa_log received kb_ids: %s", new_kb_ids)
            
            # 处理kb_ids，确保其为列表
            if isinstance(new_kb_ids, str):
                if new_kb_ids:
                    new_kb_ids = new_kb_ids.split(',')
                else:
                    new_kb_ids = []
            
            # 确保kb_ids中的元素都是字符串
            new_kb_ids = [str(kb_id) for kb_id in new_kb_ids]
            debug_logger.info("update_qa_log processed kb_ids: %s", new_kb_ids)
            
            # 检查当前QA日志中的临时知识库
            current_temp_kb_ids = []
            if 'kb_ids' in current_qa_log and current_qa_log['kb_ids']:
                for kb_id in current_qa_log['kb_ids']:
                    # 获取知识库信息
                    kb_info = local_doc_qa.milvus_summary.kb_dao.get_knowledge_base_by_id(kb_id)
                    if kb_info and kb_info.kb_type == 'temporary':
                        current_temp_kb_ids.append(kb_id)
            
            # 将现有的临时知识库添加到新的kb_ids中
            for temp_kb_id in current_temp_kb_ids:
                if temp_kb_id not in new_kb_ids:
                    debug_logger.info(f"保留临时知识库关联: {temp_kb_id}")
                    new_kb_ids.append(temp_kb_id)
            
            # 更新kb_ids
            update_data['kb_ids'] = new_kb_ids
            debug_logger.info("update_qa_log final kb_ids: %s", update_data['kb_ids'])

        # 确保更新数据可以被JSON序列化
        update_data = ensure_json_serializable(update_data)

        # 更新问答日志
        success = local_doc_qa.milvus_summary.update_qa_log(qa_id, update_data)
        if success:
            return response.json({
                "code": 200,
                "msg": "更新问答日志成功",
                "data": {
                    "kb_ids": update_data.get('kb_ids', current_qa_log.get('kb_ids', []))
                }
            })
        else:
            return response.json({
                "code": 500,
                "msg": "更新问答日志失败",
                "data": None
            })
    except Exception as e:
        debug_logger.error(f"更新问答日志失败: {e}")
        return response.json({
            "code": 500,
            "msg": f"更新问答日志失败: {str(e)}",
            "data": None
        })


@get_time_async
@auth_required(required_role=ROLE_USER)
async def delete_qa_log(req: request):
    """删除问答日志
    
    请求参数:
        qa_id (str): 问答ID
    
    返回:
        删除结果
    """
    try:
        debug_logger.info("收到删除问答日志请求")
        local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

        qa_id = safe_get(req, 'qa_id')
        if not qa_id:
            return response.json({
                "code": 400,
                "msg": "qa_id不能为空",
                "data": None
            })

        # 检查问答日志是否存在
        qa_log = local_doc_qa.milvus_summary.get_qa_log_by_id(qa_id)
        if not qa_log:
            return response.json({
                "code": 404,
                "msg": "问答日志不存在",
                "data": None
            })
            
        # 检查是否有关联的临时知识库
        temp_kb_ids = []
        if 'kb_ids' in qa_log and qa_log['kb_ids']:
            for kb_id in qa_log['kb_ids']:
                # 获取知识库信息
                kb_info = local_doc_qa.milvus_summary.kb_dao.get_knowledge_base_by_id(kb_id)
                if kb_info and kb_info.kb_type == 'temporary':
                    debug_logger.info(f"发现关联的临时知识库: {kb_id}")
                    temp_kb_ids.append(kb_id)

        # 删除问答日志
        success = local_doc_qa.milvus_summary.delete_qa_log(qa_id)
        
        # 如果有关联的临时知识库，一并删除
        deleted_kb_count = 0
        if temp_kb_ids and success:
            debug_logger.info(f"尝试删除关联的临时知识库: {temp_kb_ids}")
            deleted_kb_count = local_doc_qa.milvus_summary.kb_dao.physically_delete_temporary_knowledge_base(temp_kb_ids)
            debug_logger.info(f"成功删除 {deleted_kb_count} 个临时知识库")

        if success:
            return response.json({
                "code": 200,
                "msg": f"删除问答日志成功，同时删除了 {deleted_kb_count} 个关联的临时知识库",
                "data": {
                    "deleted_temp_kb_count": deleted_kb_count,
                    "deleted_temp_kb_ids": temp_kb_ids
                }
            })
        else:
            return response.json({
                "code": 500,
                "msg": "删除问答日志失败",
                "data": None
            })
    except Exception as e:
        debug_logger.error(f"删除问答日志失败: {e}")
        return response.json({
            "code": 500,
            "msg": f"删除问答日志失败: {str(e)}",
            "data": None
        })


@get_time_async
@auth_required(required_role=ROLE_USER)
async def toggle_qa_favorite(req: request):
    """切换问答日志收藏状态
    
    请求参数:
        qa_id (str): 问答ID
        is_favorite (bool, 可选): 是否收藏，如果不提供则自动切换当前状态
    
    返回:
        切换结果和新状态
    """
    try:
        debug_logger.info("收到切换问答日志收藏状态请求")
        local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

        qa_id = safe_get(req, 'qa_id')
        if not qa_id:
            return response.json({
                "code": 400,
                "msg": "qa_id不能为空",
                "data": None
            })

        # 检查问答日志是否存在
        qa_log = local_doc_qa.milvus_summary.get_qa_log_by_id(qa_id)
        if not qa_log:
            return response.json({
                "code": 404,
                "msg": "问答日志不存在",
                "data": None
            })

        is_favorite = safe_get(req, 'is_favorite')

        # 切换收藏状态
        success, new_status = local_doc_qa.milvus_summary.toggle_favorite(qa_id, is_favorite)

        if success:
            return response.json({
                "code": 200,
                "msg": "切换收藏状态成功",
                "data": {
                    "is_favorite": new_status
                }
            })
        else:
            return response.json({
                "code": 500,
                "msg": "切换收藏状态失败",
                "data": None
            })
    except Exception as e:
        debug_logger.error(f"切换收藏状态失败: {e}")
        return response.json({
            "code": 500,
            "msg": f"切换收藏状态失败: {str(e)}",
            "data": None
        })


@get_time_async
@auth_required(required_role=ROLE_USER)
async def create_qa_log(req: request):
    """创建问答日志
    
    请求参数:
        user_id (str): 用户ID
        kb_ids (str或list): 知识库ID列表，多个ID用逗号分隔或直接传递列表
        query (str): 问题内容
        result (str): 回答内容
        model (str): 使用的模型名称
        product_source (str, 可选): 产品来源，默认为'unknown'
        bot_id (str, 可选): 机器人ID
        is_favorite (bool, 可选): 是否收藏，默认为False
        time_record (dict, 可选): 时间记录，默认为空字典
        history (list, 可选): 历史记录，默认为空列表
        condense_question (str, 可选): 压缩后的问题，默认为空字符串
        prompt (str, 可选): 提示词，默认为空字符串
        retrieval_documents (list, 可选): 检索文档，默认为空列表
        source_documents (list, 可选): 源文档，默认为空列表
    
    返回:
        创建结果
    """
    try:
        debug_logger.info("收到创建问答日志请求")
        local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

        # 获取必填参数
        user_id = safe_get(req, 'user_id')
        kb_ids = safe_get(req, 'kb_ids', [])
        query = safe_get(req, 'query')
        result = safe_get(req, 'result')
        model = safe_get(req, 'model')
        
        # 参数验证
        if not user_id:
            return response.json({"code": 400, "msg": "user_id不能为空", "data": None})
        if not query:
            return response.json({"code": 400, "msg": "问题内容不能为空", "data": None})
        # if not result:
        #     return response.json({"code": 400, "msg": "回答内容不能为空", "data": None})
        if not model:
            return response.json({"code": 400, "msg": "模型名称不能为空", "data": None})
        
        # 获取可选参数
        product_source = safe_get(req, 'product_source', 'unknown')
        bot_id = safe_get(req, 'bot_id')
        is_favorite = safe_get(req, 'is_favorite', False)
        
        # 处理kb_ids，确保其为列表
        if isinstance(kb_ids, str):
            if kb_ids:
                kb_ids = kb_ids.split(',')
            else:
                kb_ids = []
        
        # 确保kb_ids中的元素都是字符串
        kb_ids = [str(kb_id) for kb_id in kb_ids]
        
        # 获取其他可选参数
        time_record = safe_get(req, 'time_record', {})
        history = safe_get(req, 'history', [])
        condense_question = safe_get(req, 'condense_question', '')
        prompt = safe_get(req, 'prompt', '')
        retrieval_documents = safe_get(req, 'retrieval_documents', [])
        source_documents = safe_get(req, 'source_documents', [])

        # 确保所有数据都是可序列化的
        time_record = ensure_json_serializable(time_record)
        history = ensure_json_serializable(history)
        retrieval_documents = ensure_json_serializable(retrieval_documents)
        source_documents = ensure_json_serializable(source_documents)

        # 创建问答日志
        qa_log = QaLog(
            qa_id="",
            user_id=user_id,
            kb_ids=kb_ids,
            query=query,
            result=result,
            model=model,
            product_source=product_source,
            time_record=time_record,
            history=history,
            condense_question=condense_question,
            prompt=prompt,
            retrieval_documents=retrieval_documents,
            source_documents=source_documents,
            bot_id=bot_id,
            is_favorite=is_favorite
        )

        qa_id = local_doc_qa.milvus_summary.add_qa_log(qa_log)

        if qa_id:
            return response.json({
                "code": 200,
                "msg": "创建问答日志成功",
                "data": {"qa_id": qa_id}
            })
        else:
            return response.json({
                "code": 500,
                "msg": "创建问答日志失败",
                "data": None
            })
    except Exception as e:
        debug_logger.error(f"创建问答日志失败: {e}")
        return response.json({
            "code": 500,
            "msg": f"创建问答日志失败: {str(e)}",
            "data": None
        })
