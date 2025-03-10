import json
import uuid
from datetime import datetime

from sanic import request
from sanic.response import json as sanic_json

from qanything_kernel.configs.model_config import BOT_DESC, BOT_IMAGE, BOT_PROMPT, BOT_WELCOME
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.utils.custom_log import debug_logger
from qanything_kernel.utils.general_utils import get_time_async, safe_get, check_user_id_and_user_info


@get_time_async
async def get_bot_info(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    user_info = safe_get(req, 'user_info', "1234")
    passed, msg = check_user_id_and_user_info(user_id, user_info)
    if not passed:
        return sanic_json({"code": 2001, "msg": msg})
    # user_id = user_id + '__' + user_info
    bot_id = safe_get(req, 'bot_id')
    if bot_id:
        if not local_doc_qa.milvus_summary.check_bot_is_exist(bot_id):
            return sanic_json({"code": 2003, "msg": "fail, Bot {} not found".format(bot_id)})
    debug_logger.info("get_bot_info %s", user_id)
    bot_infos = local_doc_qa.milvus_summary.get_bot(user_id, bot_id)
    data = []
    for bot_info in bot_infos:
        if bot_info[6] != "":
            kb_ids = bot_info[6].split(',')
            kb_infos = local_doc_qa.milvus_summary.get_knowledge_base_name(kb_ids)
            kb_names = []
            for kb_id in kb_ids:
                for kb_info in kb_infos:
                    if kb_id == kb_info[1]:
                        kb_names.append(kb_info[2])
                        break
        else:
            kb_ids = []
            kb_names = []
        info = {"bot_id": bot_info[0], "user_id": user_id, "bot_name": bot_info[1], "description": bot_info[2],
                "head_image": bot_info[3], "prompt_setting": bot_info[4], "welcome_message": bot_info[5],
                "kb_ids": kb_ids, "kb_names": kb_names,
                "update_time": bot_info[7].strftime("%Y-%m-%d %H:%M:%S"), "llm_setting": bot_info[9]}
        data.append(info)
    return sanic_json({"code": 200, "msg": "success", "data": data})


@get_time_async
async def new_bot(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    user_info = safe_get(req, 'user_info', "1234")
    passed, msg = check_user_id_and_user_info(user_id, user_info)
    if not passed:
        return sanic_json({"code": 2001, "msg": msg})
    # user_id = user_id + '__' + user_info
    bot_name = safe_get(req, "bot_name")
    desc = safe_get(req, "description", BOT_DESC)
    head_image = safe_get(req, "head_image", BOT_IMAGE)
    prompt_setting = safe_get(req, "prompt_setting", BOT_PROMPT)
    welcome_message = safe_get(req, "welcome_message", BOT_WELCOME)
    kb_ids = safe_get(req, "kb_ids", [])
    kb_ids_str = ",".join(kb_ids)

    not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, kb_ids)
    if not_exist_kb_ids:
        msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
        return sanic_json({"code": 2001, "msg": msg, "data": [{}]})
    debug_logger.info("new_bot %s", user_id)
    bot_id = 'BOT' + uuid.uuid4().hex
    local_doc_qa.milvus_summary.new_qanything_bot(bot_id, user_id, bot_name, desc, head_image, prompt_setting,
                                                  welcome_message, kb_ids_str)
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return sanic_json({"code": 200, "msg": "success create qanything bot {}".format(bot_id),
                       "data": {"bot_id": bot_id, "bot_name": bot_name, "create_time": create_time}})


@get_time_async
async def delete_bot(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    user_info = safe_get(req, 'user_info', "1234")
    passed, msg = check_user_id_and_user_info(user_id, user_info)
    if not passed:
        return sanic_json({"code": 2001, "msg": msg})
    # user_id = user_id + '__' + user_info
    debug_logger.info("delete_bot %s", user_id)
    bot_id = safe_get(req, 'bot_id')
    if not local_doc_qa.milvus_summary.check_bot_is_exist(bot_id):
        return sanic_json({"code": 2003, "msg": "fail, Bot {} not found".format(bot_id)})
    local_doc_qa.milvus_summary.delete_bot(user_id, bot_id)
    return sanic_json({"code": 200, "msg": "Bot {} delete success".format(bot_id)})


@get_time_async
async def update_bot(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    user_info = safe_get(req, 'user_info', "1234")
    passed, msg = check_user_id_and_user_info(user_id, user_info)
    if not passed:
        return sanic_json({"code": 2001, "msg": msg})
    # user_id = user_id + '__' + user_info
    debug_logger.info("update_bot %s", user_id)
    bot_id = safe_get(req, 'bot_id')
    if not local_doc_qa.milvus_summary.check_bot_is_exist(bot_id):
        return sanic_json({"code": 2003, "msg": "fail, Bot {} not found".format(bot_id)})
    bot_info = local_doc_qa.milvus_summary.get_bot(user_id, bot_id)[0]
    bot_name = safe_get(req, "bot_name", bot_info[1])
    description = safe_get(req, "description", bot_info[2])
    head_image = safe_get(req, "head_image", bot_info[3])
    prompt_setting = safe_get(req, "prompt_setting", bot_info[4])
    welcome_message = safe_get(req, "welcome_message", bot_info[5])
    kb_ids = safe_get(req, "kb_ids")
    if kb_ids is not None:
        not_exist_kb_ids = local_doc_qa.milvus_summary.check_kb_exist(user_id, kb_ids)
        if not_exist_kb_ids:
            msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
            return sanic_json({"code": 2001, "msg": msg, "data": [{}]})
        kb_ids_str = ",".join(kb_ids)
    else:
        kb_ids_str = bot_info[6]

    llm_setting = json.loads(bot_info[9])
    if api_base := safe_get(req, "api_base"):
        llm_setting["api_base"] = api_base
    if api_key := safe_get(req, "api_key"):
        llm_setting["api_key"] = api_key
    if api_context_length := safe_get(req, "api_context_length"):
        llm_setting["api_context_length"] = api_context_length
    if top_p := safe_get(req, "top_p"):
        llm_setting["top_p"] = top_p
    if top_k := safe_get(req, "top_k"):
        llm_setting["top_k"] = top_k
    if chunk_size := safe_get(req, "chunk_size"):
        llm_setting["chunk_size"] = chunk_size
    if temperature := safe_get(req, "temperature"):
        llm_setting["temperature"] = temperature
    if model := safe_get(req, "model"):
        llm_setting["model"] = model
    if max_token := safe_get(req, "max_token"):
        llm_setting["max_token"] = max_token
    # 如果rerank不是None，赋值，false也可以
    rerank = safe_get(req, "rerank")
    if rerank is not None:
        llm_setting["rerank"] = rerank
    hybrid_search = safe_get(req, "hybrid_search")
    if hybrid_search is not None:
        llm_setting["hybrid_search"] = hybrid_search
    networking = safe_get(req, "networking")
    if networking is not None:
        llm_setting["networking"] = networking
    only_need_search_results = safe_get(req, "only_need_search_results")
    if only_need_search_results is not None:
        llm_setting["only_need_search_results"] = only_need_search_results

    debug_logger.info(f"update llm_setting: {llm_setting}")

    # 判断哪些项修改了
    if bot_name != bot_info[1]:
        debug_logger.info(f"update bot name from {bot_info[1]} to {bot_name}")
    if description != bot_info[2]:
        debug_logger.info(f"update bot description from {bot_info[2]} to {description}")
    if head_image != bot_info[3]:
        debug_logger.info(f"update bot head_image from {bot_info[3]} to {head_image}")
    if prompt_setting != bot_info[4]:
        debug_logger.info(f"update bot prompt_setting from {bot_info[4]} to {prompt_setting}")
    if welcome_message != bot_info[5]:
        debug_logger.info(f"update bot welcome_message from {bot_info[5]} to {welcome_message}")
    if kb_ids_str != bot_info[6]:
        debug_logger.info(f"update bot kb_ids from {bot_info[6]} to {kb_ids_str}")
    #  update_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP 根据这个mysql的格式获取现在的时间
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    debug_logger.info(f"update_time: {update_time}")
    local_doc_qa.milvus_summary.update_bot(user_id, bot_id, bot_name, description, head_image, prompt_setting,
                                           welcome_message, kb_ids_str, update_time, llm_setting)
    return sanic_json({"code": 200, "msg": "Bot {} update success".format(bot_id)})
