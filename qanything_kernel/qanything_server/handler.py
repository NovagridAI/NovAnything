import functools
import shutil

from qanything_kernel.core.local_file import LocalFile
from qanything_kernel.core.local_doc_qa import LocalDocQA
from qanything_kernel.utils.custom_log import debug_logger, qa_logger
from qanything_kernel.configs.model_config import (BOT_DESC, BOT_IMAGE, BOT_PROMPT, BOT_WELCOME,
                                                   DEFAULT_PARENT_CHUNK_SIZE, MAX_CHARS, VECTOR_SEARCH_TOP_K,
                                                   UPLOAD_ROOT_PATH, IMAGES_ROOT_PATH)
from qanything_kernel.utils.general_utils import *
from langchain.schema import Document
from sanic.response import ResponseStream
from sanic.response import json as sanic_json
from sanic.response import text as sanic_text
from sanic import request, response
import uuid
import json
import asyncio
import urllib.parse
import re
from datetime import datetime
from collections import defaultdict
import os
from tqdm import tqdm
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import base64
import jwt
from datetime import timedelta
import bcrypt
from qanything_kernel.qanything_server.auth import auth_required

__all__ = ["new_knowledge_base", "upload_files", "list_kbs", "list_docs", "delete_knowledge_base", "delete_docs",
           "rename_knowledge_base", "get_total_status", "clean_files_by_status", "upload_weblink", "local_doc_chat",
           "document", "upload_faqs", "get_doc_completed", "get_qa_info", "get_user_id", "get_doc",
           "get_rerank_results", "get_user_status", "health_check", "update_chunks", "get_file_base64",
           "get_random_qa", "get_related_qa", "new_bot", "delete_bot", "update_bot", "get_bot_info", "login",
           "refresh_token"]

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
