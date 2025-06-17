import json
import json
import re
import urllib.parse
from collections import Counter
from collections import defaultdict
from datetime import datetime

from sanic import request, response
from sanic.response import json as sanic_json
from tqdm import tqdm

from qanything_kernel.configs.model_config import (DEFAULT_PARENT_CHUNK_SIZE)
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.core.local_file import LocalFile
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.utils.general_utils import *


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
        if kb_names:  # 添加安全检查
            kb_names = [kb_name for user_id, kb_id, kb_name in kb_names]
            kb_names = ','.join(kb_names)
        else:
            kb_names = "未知知识库"
        recent_sections[i] = recent_sections.pop(kb_ids)
        for log in recent_sections[i]:
            log['kb_names'] = kb_names

    older_sections = defaultdict(list)
    for log in older_logs:
        older_sections[log['kb_ids']].append(log)
    # 把older_sections的key改为自增的正整数，且每个log都新增kb_name
    for i, kb_ids in enumerate(list(older_sections.keys())):
        kb_names = local_doc_qa.milvus_summary.get_knowledge_base_name(json.loads(kb_ids))
        if kb_names:  # 添加安全检查
            kb_names = [kb_name for user_id, kb_id, kb_name in kb_names]
            kb_names = ','.join(kb_names)
        else:
            kb_names = "未知知识库"
        older_sections[i] = older_sections.pop(kb_ids)
        for log in older_sections[i]:
            log['kb_names'] = kb_names

    return sanic_json({"code": 200, "msg": "success", "qa_info": qa_log, "recent_sections": recent_sections,
                       "older_sections": older_sections})


@get_time_async
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

    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist([kb_id])
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
