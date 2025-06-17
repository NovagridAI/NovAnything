import asyncio
import base64
import os
import re
import shutil
from datetime import datetime

from langchain.schema import Document
from sanic import request

from qanything_kernel.configs.model_config import (DEFAULT_PARENT_CHUNK_SIZE, MAX_CHARS, UPLOAD_ROOT_PATH,
                                                   IMAGES_ROOT_PATH)
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.core.local_file import LocalFile
from qanything_kernel.qanything_server.api_utils import (
    create_error_response, create_success_response,
    get_user_kb_info, validate_kb_exists,
    process_file_names, paginate_results
)
from qanything_kernel.qanything_server.auth import (
    KB_PERM_ADMIN, auth_required, KB_PERM_WRITE, KB_PERM_READ
)
from qanything_kernel.qanything_server.handler import run_in_background
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.utils.general_utils import *


@get_time_async
@auth_required(check_kb_access=True, kb_permission=KB_PERM_WRITE)
async def upload_files(req: request):
    """处理文件上传请求"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    kb_id = safe_get(req, 'kb_id')
    kb_id = correct_kb_id(kb_id)

    debug_logger.info(f"upload_files user_id: {user_id}, kb_id: {kb_id}")

    # 参数获取与验证
    mode = safe_get(req, 'mode', default='soft')  # soft代表不上传同名文件，strong表示强制上传同名文件
    chunk_size = safe_get(req, 'chunk_size', default=DEFAULT_PARENT_CHUNK_SIZE)

    # 验证知识库是否存在
    valid, response = validate_kb_exists(local_doc_qa, user_id, [kb_id])
    if not valid:
        return response

    # 获取文件列表
    use_local_file = safe_get(req, 'use_local_file', 'false')
    files = read_files_with_extensions() if use_local_file == 'true' else req.files.getlist('files')
    debug_logger.info(f"upload files number: {len(files)}")

    # 检查文件数量限制
    exist_files = local_doc_qa.milvus_summary.get_files(user_id, kb_id)
    if len(exist_files) + len(files) > 10000:
        return create_error_response(2002,
                                     f"已有文件{len(exist_files)}个，上传文件{len(files)}个，总数{len(exist_files) + len(files)}个，超过最大限制10000个。")

    # 处理文件名
    file_names = process_file_names(files)

    # 检查同名文件
    exist_file_names = []
    if mode == 'soft':
        exist_files = local_doc_qa.milvus_summary.check_file_exist_by_name(user_id, kb_id, file_names)
        exist_file_names = [f[1] for f in exist_files]
        debug_logger.info(f"检测到{len(exist_file_names)}个同名文件，mode为soft将跳过上传")

    # 获取当前时间戳
    timestamp = datetime.now().strftime("%Y%m%d%H%M")

    # 处理文件上传
    data = []
    failed_files = []
    failed_reasons = {}  # 记录文件失败的具体原因
    local_files = []

    for file, file_name in zip(files, file_names):
        # 跳过同名文件
        if file_name in exist_file_names:
            continue

        try:
            # 创建本地文件对象
            local_file = LocalFile(user_id, kb_id, file, file_name)

            # 检查文件大小 - 0字节文件检查
            file_size = len(local_file.file_content)
            if file_size == 0:
                debug_logger.warning(f"文件 {file_name} 大小为0字节，跳过上传")
                failed_files.append(file_name)
                failed_reasons[file_name] = "文件大小为0字节"
                continue

            # 检查文件是否过大（30MB限制）
            max_file_size = 30 * 1024 * 1024  # 30MB
            if file_size > max_file_size:
                debug_logger.warning(f"文件 {file_name} 大小 {file_size/1024/1024:.2f}MB 超过30MB限制")
                failed_files.append(file_name)
                failed_reasons[file_name] = f"文件大小{file_size/1024/1024:.2f}MB超过30MB限制"
                continue

            # 检查文件扩展名
            file_extension = os.path.splitext(file_name)[1].lower()
            supported_extensions = ['.md', '.txt', '.pdf', '.jpg', '.png', '.jpeg', '.docx', '.xlsx', '.pptx', '.eml', '.csv']
            if file_extension not in supported_extensions:
                debug_logger.warning(f"文件 {file_name} 格式 {file_extension} 不受支持")
                failed_files.append(file_name)
                failed_reasons[file_name] = f"不支持的文件格式{file_extension}"
                continue

            # 检查文件字符数
            chars = fast_estimate_file_char_count(local_file.file_location)
            debug_logger.info(f"{file_name} char_size: {chars}")

            # 检查字符数是否有效（非图片文件）
            if file_extension not in ['.jpg', '.png', '.jpeg']:
                if chars is None:
                    debug_logger.warning(f"文件 {file_name} 字符数统计失败，可能文件损坏或格式有问题")
                    failed_files.append(file_name)
                    failed_reasons[file_name] = "文件损坏或格式有问题，无法解析"
                    continue
                elif chars == 0:
                    debug_logger.warning(f"文件 {file_name} 字符数为0，文件内容为空")
                    failed_files.append(file_name)
                    failed_reasons[file_name] = "文件内容为空"
                    continue
                elif chars > MAX_CHARS:
                    debug_logger.warning(f"文件 {file_name} 字符数 {chars} 超过最大限制 {MAX_CHARS}")
                    failed_files.append(file_name)
                    failed_reasons[file_name] = f"文件字符数{chars}超过最大限制{MAX_CHARS}"
                    continue

            # 添加文件记录
            file_id = local_file.file_id
            file_location = local_file.file_location
            local_files.append(local_file)

            # 添加到数据库
            msg = local_doc_qa.milvus_summary.add_file(
                file_id, user_id, kb_id, file_name, file_size, file_location, chunk_size, timestamp
            )
            debug_logger.info(f"添加文件: {file_name}, {file_id}, {msg}")

            # 添加到响应数据
            data.append({
                "file_id": file_id,
                "file_name": file_name,
                "status": "gray",
                "bytes": file_size,
                "timestamp": timestamp,
                "estimated_chars": chars
            })

        except Exception as e:
            debug_logger.error(f"处理文件 {file_name} 时发生错误: {str(e)}")
            failed_files.append(file_name)
            failed_reasons[file_name] = f"处理文件时发生错误: {str(e)}"
            continue

    # 为失败的文件创建失败条目
    failed_data = []
    for file_name in failed_files:
        reason = failed_reasons.get(file_name, "未知原因")
        failed_data.append({
            "file_id": None,
            "file_name": file_name,
            "status": "error",
            "bytes": 0,
            "timestamp": timestamp,
            "estimated_chars": None,
            "error_reason": reason
        })
    
    # 为跳过的同名文件创建跳过条目
    for file_name in exist_file_names:
        failed_data.append({
            "file_id": None,
            "file_name": file_name,
            "status": "skipped",
            "bytes": 0,
            "timestamp": timestamp,
            "estimated_chars": None,
            "error_reason": "文件已存在，当前mode为soft"
        })
    
    # 合并成功和失败的数据
    all_data = data + failed_data
    
    # 生成响应消息
    msg_parts = []
    
    if data:  # 有成功上传的文件
        msg_parts.append(f"成功上传{len(data)}个文件")
    
    if exist_file_names:
        msg_parts.append(f"跳过{len(exist_file_names)}个同名文件")
    
    if failed_files:
        msg_parts.append(f"上传失败{len(failed_files)}个文件")
    
    if not msg_parts:
        msg = "没有文件被上传"
    else:
        msg = "；".join(msg_parts)
        if data:  # 只有当有成功文件时才显示处理提示
            msg += "。系统正在处理文件，请耐心等待。"
    
    return create_success_response(msg, all_data)


@get_time_async
@auth_required(check_kb_access=True, kb_permission=KB_PERM_READ)
async def list_docs(req: request):
    """获取文档列表"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取用户和知识库信息
    user_id, kb_id = get_user_kb_info(req)

    debug_logger.info(f"list_docs user_id: {user_id}, kb_id: {kb_id}")

    # 获取分页参数
    file_id = safe_get(req, 'file_id')
    page_id = safe_get(req, 'page_id', 1)  # 默认为第一页
    page_limit = safe_get(req, 'page_limit', 10)  # 默认每页显示10条记录

    # 获取文件信息
    file_infos = local_doc_qa.milvus_summary.get_files(user_id, kb_id, file_id)

    # 处理文件状态统计和文件信息
    status_count = {}
    data = []

    for file_info in file_infos:
        status = file_info[2]
        status_count[status] = status_count.get(status, 0) + 1

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

        # 处理FAQ文件
        if file_info[1].endswith('.faq'):
            faq_info = local_doc_qa.milvus_summary.get_faq(file_info[0])
            if faq_info:
                file_data['question'] = faq_info.question
                file_data['answer'] = faq_info.answer

        data.append(file_data)

    # 按时间戳排序，最新的文件在前面
    data = sorted(data, key=lambda x: int(x['timestamp']), reverse=True)

    # 分页处理
    current_page_data, total_count, total_pages, error_response = paginate_results(data, page_id, page_limit)
    if error_response:
        return error_response

    # 返回结果
    return create_success_response("success", {
        'total_page': total_pages,
        "total": total_count,
        "status_count": status_count,
        "details": current_page_data,
        "page_id": page_id,
        "page_limit": page_limit
    })


@get_time_async
@auth_required(check_kb_access=True, kb_permission=KB_PERM_WRITE)
async def delete_docs(req: request):
    """删除文档"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取用户和知识库信息
    user_id, kb_id = get_user_kb_info(req)

    # 获取文件ID
    file_ids = safe_get(req, "file_ids")
    if not file_ids:
        return create_error_response(2004, "文件ID不能为空")

    debug_logger.info(f"delete_docs user_id: {user_id}, kb_id: {kb_id}, file_ids: {file_ids}")

    # 验证知识库是否存在
    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist([kb_id])
    if not_exist_kb_ids:
        return create_error_response(2003, f"知识库 {not_exist_kb_ids[0]} 不存在")

    # 检查文件是否存在
    valid_file_infos = local_doc_qa.milvus_summary.check_file_exist(user_id, kb_id, file_ids)
    if len(valid_file_infos) == 0:
        return create_error_response(2004, f"文件 {file_ids} 不存在")

    valid_file_ids = [file_info[0] for file_info in valid_file_infos]
    debug_logger.info(f"有效文件ID: {valid_file_ids}")

    # 删除Milvus中的记录
    expr = f"""kb_id == "{kb_id}" and file_id in {valid_file_ids}"""
    asyncio.create_task(run_in_background(local_doc_qa.milvus_kb.delete_expr, expr))

    # 删除ES中的记录
    file_chunks = local_doc_qa.milvus_summary.get_chunk_size(valid_file_ids)
    asyncio.create_task(run_in_background(local_doc_qa.es_client.delete_files, valid_file_ids, file_chunks))

    # 删除数据库中的记录
    local_doc_qa.milvus_summary.delete_files(kb_id, valid_file_ids)
    local_doc_qa.milvus_summary.delete_documents(valid_file_ids)
    local_doc_qa.milvus_summary.delete_faqs(valid_file_ids)

    # 删除本地文件
    delete_errors = []
    for file_id in file_ids:
        try:
            # 删除上传目录
            upload_path = os.path.join(UPLOAD_ROOT_PATH, user_id)
            file_dir = os.path.join(upload_path, kb_id, file_id)
            if os.path.exists(file_dir):
                shutil.rmtree(file_dir)
                debug_logger.info(f"已删除文件目录: {file_dir}")

            # 删除图片目录
            images_dir = os.path.join(IMAGES_ROOT_PATH, file_id)
            if os.path.exists(images_dir):
                shutil.rmtree(images_dir)
                debug_logger.info(f"已删除图片目录: {images_dir}")
        except Exception as e:
            delete_errors.append(str(e))
            debug_logger.error(f"删除文件时发生错误: {str(e)}")

    msg = f"文档 {valid_file_ids} 删除成功"
    if delete_errors:
        msg += f"，但删除本地文件时发生错误: {delete_errors}"

    return create_success_response(msg)


@get_time_async
@auth_required(check_kb_access=True, kb_permission=KB_PERM_ADMIN)
async def get_total_status(req: request):
    """获取文档状态统计 - 需要管理员角色"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    by_date = safe_get(req, 'by_date', False)

    debug_logger.info(f"get_total_status user_id: {user_id}, by_date: {by_date}")

    # 如果没有指定用户ID，则获取所有用户
    if not user_id:
        users = [user[0] for user in local_doc_qa.milvus_summary.get_users()]
    else:
        users = [user_id]

    # 状态统计结果
    status_data = {}

    for user in users:
        # 如果按日期统计
        if by_date:
            status_data[user] = local_doc_qa.milvus_summary.get_total_status_by_date(user)
            continue

        # 按知识库统计
        status_data[user] = {}
        kbs = local_doc_qa.milvus_summary.get_knowledge_bases(user)

        for kb_id, kb_name, _ in kbs:
            # 获取各状态文件数量
            status_counts = {}
            for status in ['gray', 'red', 'yellow', 'green']:
                files = local_doc_qa.milvus_summary.get_file_by_status([kb_id], status)
                status_counts[status] = len(files)

            status_data[user][kb_name + kb_id] = status_counts

    return create_success_response("success", {"status": status_data})


@get_time_async
@auth_required(check_kb_access=True, kb_permission=KB_PERM_ADMIN)
async def clean_files_by_status(req: request):
    """清理指定状态的文件 - 需要管理员角色"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取用户和知识库信息
    user_id, _ = get_user_kb_info(req)

    # 获取要清理的状态
    status = safe_get(req, 'status', default='gray')
    if status not in ['gray', 'red', 'yellow']:
        return create_error_response(2003, f"状态 {status} 必须是 ['gray', 'red', 'yellow'] 之一")

    # 获取知识库ID列表
    kb_ids = safe_get(req, 'kb_ids', [])
    kb_ids = [correct_kb_id(kb_id) for kb_id in kb_ids]

    # 如果没有指定知识库，则获取用户的所有知识库
    if not kb_ids:
        kbs = local_doc_qa.milvus_summary.get_knowledge_bases(user_id)
        kb_ids = [kb[0] for kb in kbs]
    else:
        # 验证知识库是否存在
        not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(kb_ids)
        if not_exist_kb_ids:
            return create_error_response(2003, f"知识库 {not_exist_kb_ids} 不存在")

    # 获取要删除的文件
    files_to_clean = local_doc_qa.milvus_summary.get_file_by_status(kb_ids, status)
    file_ids = [f[0] for f in files_to_clean]
    file_names = [f[1] for f in files_to_clean]

    debug_logger.info(f"清理 {status} 状态的文件数量: {len(file_names)}")

    # 执行删除操作
    if file_ids:
        for kb_id in kb_ids:
            local_doc_qa.milvus_summary.delete_files(kb_id, file_ids)

    return create_success_response(f"删除 {status} 状态的文件成功", file_names)


@get_time_async
@auth_required(check_kb_access=True, kb_permission=KB_PERM_READ)
async def get_doc_completed(req: request):
    """获取完整文档块内容"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取用户和知识库信息
    user_id, kb_id = get_user_kb_info(req)

    # 获取文件ID
    file_id = safe_get(req, 'file_id')
    if not file_id:
        return create_error_response(2005, "文件ID不能为空")

    # 获取分页参数
    page_id = safe_get(req, 'page_id', 1)
    page_limit = safe_get(req, 'page_limit', 10)

    debug_logger.info(f"get_doc_completed user_id: {user_id}, kb_id: {kb_id}, file_id: {file_id}")

    # 获取文档块
    sorted_json_datas = local_doc_qa.milvus_summary.get_document_by_file_id(file_id)
    chunks = [json_data['kwargs'] for json_data in sorted_json_datas]

    # 分页处理
    current_page_chunks, total_count, total_pages, error_response = paginate_results(chunks, page_id, page_limit)
    if error_response:
        return error_response

    # 处理图片引用
    for chunk in current_page_chunks:
        chunk['page_content'] = replace_image_references(chunk['page_content'], file_id)

    # 获取文件路径
    file_location = local_doc_qa.milvus_summary.get_file_location(file_id)
    file_path = os.path.dirname(file_location) if file_location else ""

    return create_success_response("success", {
        "chunks": current_page_chunks,
        "file_path": file_path,
        "page_id": page_id,
        "page_limit": page_limit,
        "total_count": total_count
    })


@get_time_async
@auth_required(check_kb_access=True, kb_permission=KB_PERM_READ)
async def get_doc(req: request):
    """获取单个文档块"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    doc_id = safe_get(req, 'doc_id')

    debug_logger.info(f"get_doc doc_id: {doc_id}")

    if not doc_id:
        return create_error_response(2005, "文档ID不能为空")

    doc = local_doc_qa.milvus_summary.get_document_by_doc_id(doc_id)
    if not doc:
        return create_error_response(2004, f"文档 {doc_id} 不存在")

    return create_success_response("success", {"doc_text": doc.json_data})


@get_time_async
@auth_required(check_kb_access=True, kb_permission=KB_PERM_WRITE)
async def update_chunks(req: request):
    """更新文档块内容"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取用户信息
    user_id, _ = get_user_kb_info(req)

    # 获取文档ID和更新内容
    doc_id = safe_get(req, 'doc_id')
    if not doc_id:
        return create_error_response(2005, "文档ID不能为空")

    debug_logger.info(f"update_chunks user_id: {user_id}, doc_id: {doc_id}")

    # 检查是否有文件正在解析中
    yellow_files = local_doc_qa.milvus_summary.get_files_by_status("yellow")
    if yellow_files:
        return create_error_response(2002,
                                     f"当前有 {len(yellow_files)} 个文件正在解析中，请等待所有文件解析完成后再更新文档块")

    # 获取更新内容和块大小
    update_content = safe_get(req, 'update_content', "")
    chunk_size = safe_get(req, 'chunk_size', DEFAULT_PARENT_CHUNK_SIZE)

    # 检查内容长度
    update_content_tokens = num_tokens_embed(update_content)
    if update_content_tokens > chunk_size:
        return create_error_response(2003,
                                     f"更新内容过长，当前token数 {update_content_tokens}，最大允许 {chunk_size}")

    # 检查文档是否存在
    doc_obj = local_doc_qa.milvus_summary.get_document_by_doc_id(doc_id)
    if not doc_obj:
        return create_error_response(2004, f"文档 {doc_id} 不存在")

    # 从Document对象中获取元数据
    doc_data = doc_obj.json_data
    metadata = doc_data.get('kwargs', {}).get('metadata', {})
    
    # 更新文档
    doc = Document(page_content=update_content, metadata=metadata)
    doc.metadata['doc_id'] = doc_id

    # 更新数据库
    local_doc_qa.milvus_summary.update_document(doc_id, update_content)

    # 删除向量库中的旧记录
    expr = f'doc_id == "{doc_id}"'
    local_doc_qa.milvus_kb.delete_expr(expr)

    # 插入新记录
    await local_doc_qa.retriever.insert_documents([doc], chunk_size, True)

    return create_success_response(f"文档 {doc_id} 更新成功")


@get_time_async
@auth_required(check_kb_access=True, kb_permission=KB_PERM_READ)
async def get_file_base64(req: request):
    """获取文件的Base64编码"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    file_id = safe_get(req, 'file_id')

    debug_logger.info(f"get_file_base64 file_id: {file_id}")

    if not file_id:
        return create_error_response(2005, "文件ID不能为空")

    # 获取文件位置
    file_location = local_doc_qa.milvus_summary.get_file_location(file_id)
    debug_logger.info(f"file_location: {file_location}")

    if not file_location or not os.path.exists(file_location):
        return create_error_response(2005, "文件ID无效或文件不存在")

    # 读取文件并转为Base64
    try:
        with open(file_location, "rb") as f:
            file_base64 = base64.b64encode(f.read()).decode()
        return create_success_response("success", {"file_base64": file_base64})
    except Exception as e:
        debug_logger.error(f"读取文件时发生错误: {str(e)}")
        return create_error_response(2006, f"读取文件时发生错误: {str(e)}")


@get_time_async
@auth_required(check_kb_access=True, kb_permission=KB_PERM_WRITE)
async def upload_weblink(req: request):
    """上传网页链接"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取用户和知识库信息
    user_id, kb_id = get_user_kb_info(req)

    debug_logger.info(f"upload_weblink user_id: {user_id}, kb_id: {kb_id}")

    # 验证知识库是否存在
    valid, response = validate_kb_exists(local_doc_qa, user_id, [kb_id])
    if not valid:
        return response

    # 获取URL和标题
    url = safe_get(req, 'url')
    if url:
        # 处理单个URL
        if url.endswith('/'):
            url = url[:-1]
        urls = [url]
        titles = [safe_get(req, 'title', url.split('/')[-1]) + '.web']
    else:
        # 处理多个URL
        urls = safe_get(req, 'urls', [])
        titles = safe_get(req, 'titles', [])
        if len(urls) != len(titles):
            return create_error_response(2003, "URL和标题数量不匹配")

    # 验证URL
    for url in urls:
        if not url.startswith('http'):
            return create_error_response(2001, "URL必须以'http'开头")
        if len(url) > 2048:
            return create_error_response(2002, f"URL过长，最大长度为2048")

    # 处理文件名
    file_names = []
    for title in titles:
        file_name = re.sub(r'[\uFF01-\uFF5E\u3000-\u303F]', '', title)
        file_name = truncate_filename(file_name, max_length=110)
        file_names.append(file_name)

    # 获取参数
    mode = safe_get(req, 'mode', 'soft')
    chunk_size = safe_get(req, 'chunk_size', DEFAULT_PARENT_CHUNK_SIZE)

    # 检查同名文件
    exist_file_names = []
    if mode == 'soft':
        exist_files = local_doc_qa.milvus_summary.check_file_exist_by_name(user_id, kb_id, file_names)
        exist_file_names = [f[1] for f in exist_files]

    # 获取当前时间戳
    timestamp = datetime.now().strftime("%Y%m%d%H%M")

    # 上传文件
    data = []
    for url, file_name in zip(urls, file_names):
        if file_name in exist_file_names:
            continue

        local_file = LocalFile(user_id, kb_id, url, file_name)
        file_id = local_file.file_id
        file_size = len(local_file.file_content)
        file_location = local_file.file_location

        msg = local_doc_qa.milvus_summary.add_file(
            file_id, user_id, kb_id, file_name, file_size, file_location,
            chunk_size, timestamp, url
        )

        debug_logger.info(f"添加网页: {url}, {file_name}, {file_id}, {msg}")
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
        msg = f'警告：当前mode为soft，无法上传同名文件{exist_file_names}，如需上传请设置mode=strong'
    else:
        msg = "上传成功，系统正在处理网页，请耐心等待"

    return create_success_response(msg, data)


@get_time_async
@auth_required(check_kb_access=True, kb_permission=KB_PERM_READ)
async def get_rerank_results(req: request):
    """获取重排序结果 - 基本用户权限即可"""
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa

    # 获取查询和文档ID/文本
    query = safe_get(req, 'query')
    if not query:
        return create_error_response(2005, "查询内容不能为空")

    doc_ids = safe_get(req, 'doc_ids')
    doc_strs = safe_get(req, 'doc_strs')

    if not doc_ids and not doc_strs:
        return create_error_response(2005, "文档ID或文档内容不能同时为空")

    # 获取重排序结果
    try:
        if doc_ids:
            rerank_results = await local_doc_qa.get_rerank_results(query, doc_ids=doc_ids)
        else:
            rerank_results = await local_doc_qa.get_rerank_results(query, doc_strs=doc_strs)

        formatted_results = format_source_documents(rerank_results)

        return create_success_response("success", {"rerank_results": formatted_results})
    except Exception as e:
        debug_logger.error(f"获取重排序结果时发生错误: {str(e)}")
        return create_error_response(2006, f"获取重排序结果时发生错误: {str(e)}")
