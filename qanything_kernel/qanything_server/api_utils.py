"""
API工具函数模块 - 为API接口提供通用辅助函数
"""
import os
import re
import urllib.parse

from sanic.response import json as sanic_json

from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.utils.general_utils import safe_get, correct_kb_id, truncate_filename


def create_error_response(code, msg, data=None):
    """创建统一格式的错误响应"""
    response = {"code": code, "msg": msg}
    if data is not None:
        response["data"] = data
    return sanic_json(response)


def create_success_response(msg="success", data=None):
    """创建统一格式的成功响应"""
    response = {"code": 200, "msg": msg}
    if data is not None:
        response["data"] = data
    return sanic_json(response)


def get_user_kb_info(req):
    """获取用户ID和知识库ID并进行验证"""
    user_id = safe_get(req, 'user_id')
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)
    
    return user_id, kb_id


def validate_kb_exists(local_doc_qa, user_id, kb_id):
    """验证知识库是否存在"""
    # 确保kb_id是字符串类型，如果是列表则取第一个元素
    if isinstance(kb_id, list):
        kb_id = kb_id[0] if kb_id else None
    
    # 将单个kb_id包装成列表后传递
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist([kb_id])
    if not_exist_kb_ids:
        msg = f"invalid kb_id: {not_exist_kb_ids}, please check..."
        return False, create_error_response(2001, msg, [{}])
    return True, None


def process_file_names(files, max_length=110):
    """统一处理文件名称"""
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
        file_name = truncate_filename(file_name, max_length=max_length)
        file_names.append(file_name)
    
    return file_names


def paginate_results(data, page_id, page_limit):
    """对结果进行分页处理"""
    total_count = len(data)
    total_pages = (total_count + page_limit - 1) // page_limit if total_count > 0 else 1
    
    if page_id > total_pages and total_count != 0:
        return None, None, None, create_error_response(
            2002, f'输入非法！page_id超过最大值，page_id: {page_id}，最大值：{total_pages}，请检查！')
    
    start_index = (page_id - 1) * page_limit
    end_index = start_index + page_limit
    current_page_data = data[start_index:end_index]
    
    return current_page_data, total_count, total_pages, None 