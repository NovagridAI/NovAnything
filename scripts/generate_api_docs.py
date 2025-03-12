import json
import os
from pathlib import Path

# 定义API文档基本信息
api_doc = {
    "openapi": "3.0.0",
    "info": {
        "title": "NovAnything API",
        "description": "NovAnything系统API接口文档",
        "version": "0.0.1"
    },
    "servers": [
        {
            "url": "http://localhost:8777",
            "description": "本地开发服务器"
        }
    ],
    "paths": {},
    "components": {
        "schemas": {
            "Error": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "msg": {"type": "string"}
                }
            },
            "SuccessResponse": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer", "example": 200},
                    "msg": {"type": "string", "example": "操作成功"},
                    "data": {"type": "object"}
                }
            }
        },
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    },
    "tags": [
        {
            "name": "知识库管理",
            "description": "知识库的创建、删除、重命名等管理操作"
        },
        {
            "name": "知识库问答",
            "description": "基于知识库的问答功能"
        },
        {
            "name": "用户认证",
            "description": "用户登录、令牌刷新等认证操作"
        },
        {
            "name": "用户管理",
            "description": "用户的创建、删除、更新等管理操作"
        }
    ]
}

# 定义通用响应
common_responses = {
    "200": {
        "description": "操作成功",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/SuccessResponse"}
            }
        }
    },
    "400": {
        "description": "请求参数错误",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 400},
                        "msg": {"type": "string", "example": "请求参数错误"}
                    }
                }
            }
        }
    },
    "401": {
        "description": "未授权",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 401},
                        "msg": {"type": "string", "example": "未授权或令牌已过期"}
                    }
                }
            }
        }
    },
    "403": {
        "description": "权限不足",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 403},
                        "msg": {"type": "string", "example": "权限不足"}
                    }
                }
            }
        }
    },
    "500": {
        "description": "服务器内部错误",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 500},
                        "msg": {"type": "string", "example": "服务器内部错误"}
                    }
                }
            }
        }
    }
}

# 定义local_doc_qa_bp蓝图中的路由
local_doc_qa_routes = [
    {
        "path": "/api/local_doc_qa/new_knowledge_base",
        "method": "post",
        "tag": "知识库管理",
        "summary": "新建知识库",
        "description": "创建一个新的知识库",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_name": {"type": "string", "description": "知识库名称"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "description": {"type": "string", "description": "知识库描述"}
                        },
                        "required": ["kb_name", "user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/upload_weblink",
        "method": "post",
        "tag": "知识库管理",
        "summary": "上传网页链接",
        "description": "上传网页链接到知识库",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "url": {"type": "string", "description": "网页链接"}
                        },
                        "required": ["kb_id", "user_id", "url"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/upload_files",
        "method": "post",
        "tag": "知识库管理",
        "summary": "上传文件",
        "description": "上传文件到知识库",
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "files": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "format": "binary"
                                },
                                "description": "上传的文件"
                            }
                        },
                        "required": ["kb_id", "user_id", "files"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/upload_faqs",
        "method": "post",
        "tag": "知识库管理",
        "summary": "上传FAQ",
        "description": "上传FAQ到知识库",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "faqs": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "question": {"type": "string", "description": "问题"},
                                        "answer": {"type": "string", "description": "答案"}
                                    }
                                },
                                "description": "FAQ列表"
                            }
                        },
                        "required": ["kb_id", "user_id", "faqs"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/local_doc_chat",
        "method": "post",
        "tag": "知识库问答",
        "summary": "知识库问答",
        "description": "基于知识库进行问答",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "query": {"type": "string", "description": "用户问题"},
                            "history": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "role": {"type": "string", "description": "角色(user/assistant)"},
                                        "content": {"type": "string", "description": "内容"}
                                    }
                                },
                                "description": "历史对话"
                            }
                        },
                        "required": ["kb_id", "user_id", "query"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/list_files",
        "method": "post",
        "tag": "知识库管理",
        "summary": "文件列表",
        "description": "获取知识库中的文件列表",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"}
                        },
                        "required": ["kb_id", "user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/get_total_status",
        "method": "post",
        "tag": "知识库管理",
        "summary": "获取知识库状态",
        "description": "获取知识库的总体状态",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"}
                        },
                        "required": ["kb_id", "user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/clean_files_by_status",
        "method": "post",
        "tag": "知识库管理",
        "summary": "清理文件",
        "description": "根据状态清理知识库中的文件",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "status": {"type": "string", "description": "文件状态"}
                        },
                        "required": ["kb_id", "user_id", "status"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/delete_files",
        "method": "post",
        "tag": "知识库管理",
        "summary": "删除文件",
        "description": "删除知识库中的文件",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "file_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "文件ID列表"
                            }
                        },
                        "required": ["kb_id", "user_id", "file_ids"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/delete_knowledge_base",
        "method": "post",
        "tag": "知识库管理",
        "summary": "删除知识库",
        "description": "删除指定的知识库",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"}
                        },
                        "required": ["kb_id", "user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/rename_knowledge_base",
        "method": "post",
        "tag": "知识库管理",
        "summary": "重命名知识库",
        "description": "重命名指定的知识库",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "kb_name": {"type": "string", "description": "新的知识库名称"}
                        },
                        "required": ["kb_id", "user_id", "kb_name"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/get_doc_completed",
        "method": "post",
        "tag": "知识库管理",
        "summary": "获取文档完整内容",
        "description": "获取知识库中文档的完整内容",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "doc_id": {"type": "string", "description": "文档ID"}
                        },
                        "required": ["kb_id", "user_id", "doc_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
        {
        "path": "/api/local_doc_qa/get_qa_info",
        "method": "post",
        "tag": "知识库问答",
        "summary": "获取QA信息",
        "description": "获取问答相关信息",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"}
                        },
                        "required": ["kb_id", "user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/get_user_id",
        "method": "post",
        "tag": "用户管理",
        "summary": "获取用户ID",
        "description": "获取当前用户的ID",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/get_doc",
        "method": "post",
        "tag": "知识库管理",
        "summary": "获取文档详情",
        "description": "获取知识库中文档的详细信息",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "doc_id": {"type": "string", "description": "文档ID"}
                        },
                        "required": ["kb_id", "user_id", "doc_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/get_rerank_results",
        "method": "post",
        "tag": "知识库问答",
        "summary": "获取重排结果",
        "description": "获取问答重排序的结果",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "query": {"type": "string", "description": "查询内容"}
                        },
                        "required": ["kb_id", "user_id", "query"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/get_user_status",
        "method": "post",
        "tag": "用户管理",
        "summary": "获取用户状态",
        "description": "获取用户的当前状态",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "用户ID"}
                        },
                        "required": ["user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/get_random_qa",
        "method": "post",
        "tag": "知识库问答",
        "summary": "获取随机QA",
        "description": "获取随机的问答对",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"}
                        },
                        "required": ["kb_id", "user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/get_related_qa",
        "method": "post",
        "tag": "知识库问答",
        "summary": "获取相关QA",
        "description": "获取与当前问题相关的问答对",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "query": {"type": "string", "description": "查询内容"}
                        },
                        "required": ["kb_id", "user_id", "query"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/update_chunks",
        "method": "post",
        "tag": "知识库管理",
        "summary": "更新文档块",
        "description": "更新知识库中的文档块",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "doc_id": {"type": "string", "description": "文档ID"},
                            "chunks": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "chunk_id": {"type": "string", "description": "文档块ID"},
                                        "content": {"type": "string", "description": "文档块内容"}
                                    }
                                },
                                "description": "文档块列表"
                            }
                        },
                        "required": ["kb_id", "user_id", "doc_id", "chunks"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/local_doc_qa/get_file_base64",
        "method": "post",
        "tag": "知识库管理",
        "summary": "获取文件Base64",
        "description": "获取文件的Base64编码",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "file_id": {"type": "string", "description": "文件ID"}
                        },
                        "required": ["kb_id", "user_id", "file_id"]
                    }
                }
            }
        },
        "responses": common_responses
    }
]

# 将路由信息添加到API文档中
for route in local_doc_qa_routes:
    path = route["path"]
    method = route["method"].lower()
    
    if path not in api_doc["paths"]:
        api_doc["paths"][path] = {}
    
    api_doc["paths"][path][method] = {
        "tags": [route["tag"]],
        "summary": route["summary"],
        "description": route["description"],
        "security": [{"bearerAuth": []}],
        "responses": route["responses"]
    }
    
    if "requestBody" in route:
        api_doc["paths"][path][method]["requestBody"] = route["requestBody"]

# 定义auth_bp蓝图中的路由
auth_routes = [
    {
        "path": "/api/auth/login",
        "method": "post",
        "tag": "用户认证",
        "summary": "用户登录",
        "description": "用户登录并获取访问令牌",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string", "description": "用户名"},
                            "password": {"type": "string", "description": "密码"}
                        },
                        "required": ["username", "password"]
                    }
                }
            }
        },
        "responses": {
            "200": {
                "description": "登录成功",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer", "example": 200},
                                "msg": {"type": "string", "example": "登录成功"},
                                "data": {
                                    "type": "object",
                                    "properties": {
                                        "access_token": {"type": "string", "description": "访问令牌"},
                                        "refresh_token": {"type": "string", "description": "刷新令牌"},
                                        "token_type": {"type": "string", "example": "bearer", "description": "令牌类型"},
                                        "expires_in": {"type": "integer", "description": "令牌有效期（秒）"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "400": {
                "description": "请求参数错误",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer", "example": 400},
                                "msg": {"type": "string", "example": "请求参数错误"}
                            }
                        }
                    }
                }
            },
            "401": {
                "description": "用户名或密码错误",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer", "example": 401},
                                "msg": {"type": "string", "example": "用户名或密码错误"}
                            }
                        }
                    }
                }
            },
            "500": {
                "description": "服务器内部错误",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer", "example": 500},
                                "msg": {"type": "string", "example": "服务器内部错误"}
                            }
                        }
                    }
                }
            }
        }
    },
    {
        "path": "/api/auth/refresh_token",
        "method": "post",
        "tag": "用户认证",
        "summary": "刷新令牌",
        "description": "使用刷新令牌获取新的访问令牌",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "refresh_token": {"type": "string", "description": "刷新令牌"}
                        },
                        "required": ["refresh_token"]
                    }
                }
            }
        },
        "responses": {
            "200": {
                "description": "刷新成功",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer", "example": 200},
                                "msg": {"type": "string", "example": "刷新成功"},
                                "data": {
                                    "type": "object",
                                    "properties": {
                                        "access_token": {"type": "string", "description": "新的访问令牌"},
                                        "refresh_token": {"type": "string", "description": "新的刷新令牌"},
                                        "token_type": {"type": "string", "example": "bearer", "description": "令牌类型"},
                                        "expires_in": {"type": "integer", "description": "令牌有效期（秒）"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "400": {
                "description": "请求参数错误",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer", "example": 400},
                                "msg": {"type": "string", "example": "请求参数错误"}
                            }
                        }
                    }
                }
            },
            "401": {
                "description": "刷新令牌无效或已过期",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer", "example": 401},
                                "msg": {"type": "string", "example": "刷新令牌无效或已过期"}
                            }
                        }
                    }
                }
            },
            "500": {
                "description": "服务器内部错误",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer", "example": 500},
                                "msg": {"type": "string", "example": "服务器内部错误"}
                            }
                        }
                    }
                }
            }
        }
    }
]

# 将local_doc_qa_bp路由信息添加到API文档中
for route in auth_routes:
    path = route["path"]
    method = route["method"].lower()
    
    if path not in api_doc["paths"]:
        api_doc["paths"][path] = {}
    
    api_doc["paths"][path][method] = {
        "tags": [route["tag"]],
        "summary": route["summary"],
        "description": route["description"],
        "responses": route["responses"]
    }
    
    if "requestBody" in route:
        api_doc["paths"][path][method]["requestBody"] = route["requestBody"]
    
    # 登录和刷新令牌接口不需要认证
    if path != "/api/auth/login" and path != "/api/auth/refresh_token":
        api_doc["paths"][path][method]["security"] = [{"bearerAuth": []}]

# 定义user_bp蓝图中的路由
user_routes = [
    {
        "path": "/api/user/create",
        "method": "post",
        "tag": "用户管理",
        "summary": "创建用户",
        "description": "创建新用户",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string", "description": "用户名"},
                            "password": {"type": "string", "description": "密码"},
                            "name": {"type": "string", "description": "姓名"},
                            "email": {"type": "string", "description": "邮箱"},
                            "phone": {"type": "string", "description": "电话"},
                            "dept_id": {"type": "string", "description": "部门ID"},
                            "role": {"type": "string", "description": "角色"}
                        },
                        "required": ["username", "password", "name"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/user/list",
        "method": "get",
        "tag": "用户管理",
        "summary": "用户列表",
        "description": "获取用户列表",
        "parameters": [
            {
                "name": "page",
                "in": "query",
                "description": "页码",
                "schema": {"type": "integer", "default": 1}
            },
            {
                "name": "size",
                "in": "query",
                "description": "每页数量",
                "schema": {"type": "integer", "default": 10}
            },
            {
                "name": "keyword",
                "in": "query",
                "description": "搜索关键词",
                "schema": {"type": "string"}
            }
        ],
        "responses": common_responses
    },
    {
        "path": "/api/user/delete",
        "method": "post",
        "tag": "用户管理",
        "summary": "删除用户",
        "description": "删除指定用户",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "用户ID"}
                        },
                        "required": ["user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/user/update",
        "method": "post",
        "tag": "用户管理",
        "summary": "更新用户",
        "description": "更新用户信息",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "用户ID"},
                            "name": {"type": "string", "description": "姓名"},
                            "email": {"type": "string", "description": "邮箱"},
                            "phone": {"type": "string", "description": "电话"},
                            "dept_id": {"type": "string", "description": "部门ID"},
                            "role": {"type": "string", "description": "角色"}
                        },
                        "required": ["user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/user/reset_password",
        "method": "post",
        "tag": "用户管理",
        "summary": "重置密码",
        "description": "管理员重置用户密码",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "用户ID"},
                            "password": {"type": "string", "description": "新密码"}
                        },
                        "required": ["user_id", "password"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/user/change_password",
        "method": "post",
        "tag": "用户管理",
        "summary": "修改密码",
        "description": "用户修改自己的密码",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "old_password": {"type": "string", "description": "旧密码"},
                            "new_password": {"type": "string", "description": "新密码"}
                        },
                        "required": ["old_password", "new_password"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/user/set_kb_access",
        "method": "post",
        "tag": "用户管理",
        "summary": "设置用户知识库权限",
        "description": "设置用户对知识库的访问权限",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "用户ID"},
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "access_type": {"type": "string", "description": "权限类型", "enum": ["read", "write", "admin", "none"]}
                        },
                        "required": ["user_id", "kb_id", "access_type"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/user/batch_set_kb_access",
        "method": "post",
        "tag": "用户管理",
        "summary": "批量设置用户知识库权限",
        "description": "批量设置用户对知识库的访问权限",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "用户ID"},
                            "kb_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "知识库ID列表"
                            },
                            "access_type": {"type": "string", "description": "权限类型", "enum": ["read", "write", "admin", "none"]}
                        },
                        "required": ["user_id", "kb_ids", "access_type"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/user/get_kb_access",
        "method": "get",
        "tag": "用户管理",
        "summary": "获取用户知识库权限",
        "description": "获取用户对知识库的访问权限",
        "parameters": [
            {
                "name": "user_id",
                "in": "query",
                "description": "用户ID",
                "schema": {"type": "string"},
                "required": ["user_id"]
            }
        ],
        "responses": common_responses
    },
    {
        "path": "/api/user/update_user_profile",
        "method": "post",
        "tag": "用户管理",
        "summary": "更新用户信息",
        "description": "用户更新自己的个人信息",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "姓名"},
                            "email": {"type": "string", "description": "邮箱"},
                            "phone": {"type": "string", "description": "电话"},
                            "avatar": {"type": "string", "description": "头像URL"}
                        }
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/user/get_user_profile",
        "method": "get",
        "tag": "用户管理",
        "summary": "获取用户信息",
        "description": "获取当前用户的个人信息",
        "responses": common_responses
    },
    {
        "path": "/api/user/list_knowledge_base",
        "method": "post",
        "tag": "用户管理",
        "summary": "获取可访问知识库",
        "description": "获取用户可访问的知识库列表",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "用户ID"}
                        },
                        "required": ["user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    }
]

# 将user_bp路由信息添加到API文档中
for route in user_routes:
    path = route["path"]
    method = route["method"].lower()
    
    if path not in api_doc["paths"]:
        api_doc["paths"][path] = {}
    
    api_doc["paths"][path][method] = {
        "tags": [route["tag"]],
        "summary": route["summary"],
        "description": route["description"],
        "security": [{"bearerAuth": []}],
        "responses": route["responses"]
    }
    
    if "requestBody" in route:
        api_doc["paths"][path][method]["requestBody"] = route["requestBody"]
    
    if "parameters" in route:
        api_doc["paths"][path][method]["parameters"] = route["parameters"]

# 定义kb_bp蓝图中的路由
kb_routes = [
    {
        "path": "/api/kb/grant_access",
        "method": "post",
        "tag": "知识库权限管理",
        "summary": "授予知识库访问权限",
        "description": "授予用户或用户组对知识库的访问权限",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"},
                            "access_type": {"type": "string", "description": "权限类型", "enum": ["read", "write", "admin"]}
                        },
                        "required": ["kb_id", "user_id", "access_type"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/kb/revoke_access",
        "method": "post",
        "tag": "知识库权限管理",
        "summary": "撤销知识库访问权限",
        "description": "撤销用户或用户组对知识库的访问权限",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_id": {"type": "string", "description": "用户ID"}
                        },
                        "required": ["kb_id", "user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/kb/access_list",
        "method": "get",
        "tag": "知识库权限管理",
        "summary": "获取知识库访问权限列表",
        "description": "获取知识库的访问权限列表",
        "parameters": [
            {
                "name": "kb_id",
                "in": "query",
                "description": "知识库ID",
                "schema": {"type": "string"},
                "required": ["kb_id"]
            }
        ],
        "responses": common_responses
    },
    {
        "path": "/api/kb/check_access",
        "method": "get",
        "tag": "知识库权限管理",
        "summary": "检查知识库权限",
        "description": "检查用户对知识库的访问权限",
        "parameters": [
            {
                "name": "kb_id",
                "in": "query",
                "description": "知识库ID",
                "schema": {"type": "string"},
                "required": ["kb_id"]
            },
            {
                "name": "user_id",
                "in": "query",
                "description": "用户ID",
                "schema": {"type": "string"},
                "required": ["user_id"]
            }
        ],
        "responses": common_responses
    },
    {
        "path": "/api/kb/batch_set_access",
        "method": "post",
        "tag": "知识库权限管理",
        "summary": "批量设置知识库访问权限",
        "description": "批量设置用户对知识库的访问权限",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "user_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "用户ID列表"
                            },
                            "access_type": {"type": "string", "description": "权限类型", "enum": ["read", "write", "admin", "none"]}
                        },
                        "required": ["kb_id", "user_ids", "access_type"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/kb/detail",
        "method": "get",
        "tag": "知识库管理",
        "summary": "获取知识库详情",
        "description": "获取知识库的详细信息",
        "parameters": [
            {
                "name": "kb_id",
                "in": "query",
                "description": "知识库ID",
                "schema": {"type": "string"},
                "required": ["kb_id"]
            }
        ],
        "responses": common_responses
    },
    {
        "path": "/api/kb/transfer_kb_ownership",
        "method": "post",
        "tag": "知识库管理",
        "summary": "转移知识库所有权",
        "description": "将知识库的所有权转移给其他用户",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string", "description": "知识库ID"},
                            "new_owner_id": {"type": "string", "description": "新所有者用户ID"}
                        },
                        "required": ["kb_id", "new_owner_id"]
                    }
                }
            }
        },
        "responses": common_responses
    }
]

# 将kb_bp路由信息添加到API文档中
for route in kb_routes:
    path = route["path"]
    method = route["method"].lower()
    
    if path not in api_doc["paths"]:
        api_doc["paths"][path] = {}
    
    api_doc["paths"][path][method] = {
        "tags": [route["tag"]],
        "summary": route["summary"],
        "description": route["description"],
        "security": [{"bearerAuth": []}],
        "responses": route["responses"]
    }
    
    if "requestBody" in route:
        api_doc["paths"][path][method]["requestBody"] = route["requestBody"]
    
    if "parameters" in route:
        api_doc["paths"][path][method]["parameters"] = route["parameters"]


# 定义group_bp蓝图中的路由
group_routes = [
    {
        "path": "/api/group/create",
        "method": "post",
        "tag": "用户组管理",
        "summary": "创建用户组",
        "description": "创建新的用户组",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "用户组名称"},
                            "description": {"type": "string", "description": "用户组描述"}
                        },
                        "required": ["name"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/group/list",
        "method": "get",
        "tag": "用户组管理",
        "summary": "用户组列表",
        "description": "获取所有用户组列表",
        "parameters": [
            {
                "name": "page",
                "in": "query",
                "description": "页码",
                "schema": {"type": "integer", "default": 1}
            },
            {
                "name": "size",
                "in": "query",
                "description": "每页数量",
                "schema": {"type": "integer", "default": 10}
            },
            {
                "name": "keyword",
                "in": "query",
                "description": "搜索关键词",
                "schema": {"type": "string"}
            }
        ],
        "responses": common_responses
    },
    {
        "path": "/api/group/update",
        "method": "post",
        "tag": "用户组管理",
        "summary": "更新用户组",
        "description": "更新用户组信息",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "用户组ID"},
                            "name": {"type": "string", "description": "用户组名称"},
                            "description": {"type": "string", "description": "用户组描述"}
                        },
                        "required": ["group_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/group/delete",
        "method": "post",
        "tag": "用户组管理",
        "summary": "删除用户组",
        "description": "删除指定的用户组",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "用户组ID"}
                        },
                        "required": ["group_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/group/add_user",
        "method": "post",
        "tag": "用户组管理",
        "summary": "添加用户到用户组",
        "description": "将用户添加到指定用户组",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "用户组ID"},
                            "user_id": {"type": "string", "description": "用户ID"}
                        },
                        "required": ["group_id", "user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/group/remove_user",
        "method": "post",
        "tag": "用户组管理",
        "summary": "从用户组移除用户",
        "description": "从指定用户组中移除用户",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "用户组ID"},
                            "user_id": {"type": "string", "description": "用户ID"}
                        },
                        "required": ["group_id", "user_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/group/members",
        "method": "get",
        "tag": "用户组管理",
        "summary": "用户组成员列表",
        "description": "获取指定用户组的成员列表",
        "parameters": [
            {
                "name": "group_id",
                "in": "query",
                "description": "用户组ID",
                "schema": {"type": "string"},
                "required": True
            },
            {
                "name": "page",
                "in": "query",
                "description": "页码",
                "schema": {"type": "integer", "default": 1}
            },
            {
                "name": "size",
                "in": "query",
                "description": "每页数量",
                "schema": {"type": "integer", "default": 10}
            }
        ],
        "responses": common_responses
    }
]

# 将group_bp路由信息添加到API文档中
for route in group_routes:
    path = route["path"]
    method = route["method"].lower()
    
    if path not in api_doc["paths"]:
        api_doc["paths"][path] = {}
    
    api_doc["paths"][path][method] = {
        "tags": [route["tag"]],
        "summary": route["summary"],
        "description": route["description"],
        "security": [{"bearerAuth": []}],
        "responses": route["responses"]
    }
    
    if "requestBody" in route:
        api_doc["paths"][path][method]["requestBody"] = route["requestBody"]
    
    if "parameters" in route:
        api_doc["paths"][path][method]["parameters"] = route["parameters"]


# 定义dept_bp蓝图中的路由
dept_routes = [
    {
        "path": "/api/department/create",
        "method": "post",
        "tag": "部门管理",
        "summary": "创建部门",
        "description": "创建新的部门",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "部门名称"},
                            "parent_id": {"type": "string", "description": "父部门ID"},
                            "description": {"type": "string", "description": "部门描述"}
                        },
                        "required": ["name"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/department/list",
        "method": "get",
        "tag": "部门管理",
        "summary": "部门列表",
        "description": "获取所有部门列表",
        "parameters": [
            {
                "name": "page",
                "in": "query",
                "description": "页码",
                "schema": {"type": "integer", "default": 1}
            },
            {
                "name": "size",
                "in": "query",
                "description": "每页数量",
                "schema": {"type": "integer", "default": 10}
            },
            {
                "name": "keyword",
                "in": "query",
                "description": "搜索关键词",
                "schema": {"type": "string"}
            }
        ],
        "responses": common_responses
    },
    {
        "path": "/api/department/update",
        "method": "post",
        "tag": "部门管理",
        "summary": "更新部门",
        "description": "更新部门信息",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "dept_id": {"type": "string", "description": "部门ID"},
                            "name": {"type": "string", "description": "部门名称"},
                            "parent_id": {"type": "string", "description": "父部门ID"},
                            "description": {"type": "string", "description": "部门描述"}
                        },
                        "required": ["dept_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/department/delete",
        "method": "post",
        "tag": "部门管理",
        "summary": "删除部门",
        "description": "删除指定的部门",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "dept_id": {"type": "string", "description": "部门ID"}
                        },
                        "required": ["dept_id"]
                    }
                }
            }
        },
        "responses": common_responses
    }
]

# 将dept_bp路由信息添加到API文档中
for route in dept_routes:
    path = route["path"]
    method = route["method"].lower()
    
    if path not in api_doc["paths"]:
        api_doc["paths"][path] = {}
    
    api_doc["paths"][path][method] = {
        "tags": [route["tag"]],
        "summary": route["summary"],
        "description": route["description"],
        "security": [{"bearerAuth": []}],
        "responses": route["responses"]
    }
    
    if "requestBody" in route:
        api_doc["paths"][path][method]["requestBody"] = route["requestBody"]
    
    if "parameters" in route:
        api_doc["paths"][path][method]["parameters"] = route["parameters"]

# 定义bot_bp蓝图中的路由
bot_routes = [
    {
        "path": "/api/bot/new_bot",
        "method": "post",
        "tag": "机器人管理",
        "summary": "创建机器人",
        "description": "创建新的机器人",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "机器人名称"},
                            "description": {"type": "string", "description": "机器人描述"},
                            "kb_id": {"type": "string", "description": "关联的知识库ID"},
                            "avatar": {"type": "string", "description": "机器人头像URL"},
                            "prompt_template": {"type": "string", "description": "提示词模板"}
                        },
                        "required": ["name", "kb_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/bot/delete_bot",
        "method": "post",
        "tag": "机器人管理",
        "summary": "删除机器人",
        "description": "删除指定的机器人",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "bot_id": {"type": "string", "description": "机器人ID"}
                        },
                        "required": ["bot_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/bot/update_bot",
        "method": "post",
        "tag": "机器人管理",
        "summary": "更新机器人",
        "description": "更新机器人信息",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "bot_id": {"type": "string", "description": "机器人ID"},
                            "name": {"type": "string", "description": "机器人名称"},
                            "description": {"type": "string", "description": "机器人描述"},
                            "kb_id": {"type": "string", "description": "关联的知识库ID"},
                            "avatar": {"type": "string", "description": "机器人头像URL"},
                            "prompt_template": {"type": "string", "description": "提示词模板"}
                        },
                        "required": ["bot_id"]
                    }
                }
            }
        },
        "responses": common_responses
    },
    {
        "path": "/api/bot/get_bot_info",
        "method": "post",
        "tag": "机器人管理",
        "summary": "获取机器人信息",
        "description": "获取机器人详细信息",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "bot_id": {"type": "string", "description": "机器人ID"}
                        },
                        "required": ["bot_id"]
                    }
                }
            }
        },
        "responses": common_responses
    }
]

# 将bot_bp路由信息添加到API文档中
for route in bot_routes:
    path = route["path"]
    method = route["method"].lower()
    
    if path not in api_doc["paths"]:
        api_doc["paths"][path] = {}
    
    api_doc["paths"][path][method] = {
        "tags": [route["tag"]],
        "summary": route["summary"],
        "description": route["description"],
        "security": [{"bearerAuth": []}],
        "responses": route["responses"]
    }
    
    if "requestBody" in route:
        api_doc["paths"][path][method]["requestBody"] = route["requestBody"]
    
    if "parameters" in route:
        api_doc["paths"][path][method]["parameters"] = route["parameters"]

# 生成API文档JSON文件
output_path = "/Users/qqcapitalmax3/opensource/QAnything/scripts/api_docs.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(api_doc, f, ensure_ascii=False, indent=2)

print(f"API文档已生成: {output_path}")
