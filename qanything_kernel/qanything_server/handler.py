import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

from sanic import request
from sanic.response import ResponseStream
from sanic.response import json as sanic_json
from sanic.response import text as sanic_text

from qanything_kernel.configs.model_config import (DEFAULT_PARENT_CHUNK_SIZE, VECTOR_SEARCH_TOP_K)
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.utils.custom_log import debug_logger, qa_logger
from qanything_kernel.utils.general_utils import *

INVALID_USER_ID = f"fail, Invalid user_id: . user_id 必须只含有字母，数字和下划线且字母开头"

# 获取环境变量GATEWAY_IP
GATEWAY_IP = os.getenv("GATEWAY_IP", "localhost")
debug_logger.info(f"GATEWAY_IP: {GATEWAY_IP}")

# 异步包装器，用于在后台执行带有参数的同步函数
async def run_in_background(func, *args):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=4) as pool:
        await loop.run_in_executor(pool, func, *args)


# 使用aiohttp异步请求另一个API
async def fetch(session, url, input_json):
    headers = {'Content-Type': 'application/json'}
    async with session.post(url, json=input_json, headers=headers) as response:
        return await response.json()


# 定义一个需要参数的同步函数
def sync_function_with_args(arg1, arg2):
    # 模拟耗时操作
    import time
    time.sleep(5)
    print(f"同步函数执行完毕，参数值：arg1={arg1}, arg2={arg2}")
    


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
        if not local_doc_qa.milvus_summary.check_bot_exist(bot_id):
            return sanic_json({"code": 2003, "msg": "fail, Bot {} not found".format(bot_id)})
        bot_info = local_doc_qa.milvus_summary.get_bot_by_id(bot_id)
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
        local_doc_qa.milvus_summary.add_qa_log(**chat_data)
        qa_logger.info("chat_data: %s", chat_data)
        debug_logger.info("response: %s", chat_data['result'])
        return sanic_json({"code": 200, "msg": "success no stream chat", "question": question,
                           "response": resp["result"], "model": model,
                           "history": history, "condense_question": resp['condense_question'],
                           "source_documents": source_documents, "retrieval_documents": retrieval_documents,
                           "time_record": formatted_time_record})


@get_time_async
async def document(req: request):
    description = """
# QAnything 介绍
[戳我看视频>>>>>【有道QAnything介绍视频.mp4】](https://docs.popo.netease.com/docs/7e512e48fcb645adadddcf3107c97e7c)

**QAnything** (**Q**uestion and **A**nswer based on **Anything**) 是支持任意格式的本地知识库问答系统。

您的任何格式的本地文件都可以往里扔，即可获得准确、快速、靠谱的问答体验。

**目前已支持格式:**
* PDF
* Word(doc/docx)
* PPT
* TXT
* 图片
* 网页链接
* ...更多格式，敬请期待

# API 调用指南

## API Base URL

https://qanything.youdao.com

## 鉴权
目前使用微信鉴权,步骤如下:
1. 客户端通过扫码微信二维码(首次登录需要关注公众号)
2. 获取token
3. 调用下面所有API都需要通过authorization参数传入这个token

注意：authorization参数使用Bearer auth认证方式

生成微信二维码以及获取token的示例代码下载地址：[微信鉴权示例代码](https://docs.popo.netease.com/docs/66652d1a967e4f779594aef3306f6097)

## API 接口说明
    {
        "api": "/api/local_doc_qa/upload_files"
        "name": "上传文件",
        "description": "上传文件接口，支持多个文件同时上传，需要指定知识库名称",
    },
    {
        "api": "/api/local_doc_qa/upload_weblink"
        "name": "上传网页链接",
        "description": "上传网页链接，自动爬取网页内容，需要指定知识库名称",
    },
    {
        "api": "/api/local_doc_qa/local_doc_chat" 
        "name": "问答接口",
        "description": "知识库问答接口，指定知识库名称，上传用户问题，通过传入history支持多轮对话",
    },
    {
        "api": "/api/local_doc_qa/list_files" 
        "name": "文件列表",
        "description": "列出指定知识库下的所有文件名，需要指定知识库名称",
    },
    {
        "api": "/api/local_doc_qa/delete_files" 
        "name": "删除文件",
        "description": "删除指定知识库下的指定文件，需要指定知识库名称",
    },

"""
    return sanic_text(description)



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
async def health_check(req: request):
    # 实现一个服务健康检查的逻辑，正常就返回200，不正常就返回500
    return sanic_json({"code": 200, "msg": "success"})
