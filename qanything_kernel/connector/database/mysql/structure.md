# MySQL 数据库连接器重构

## 文件结构
```
mysql/
├── __init__.py              # 导出模块接口
├── connection.py            # 数据库连接管理
├── models/                  # 数据模型
│   ├── __init__.py          
│   ├── user.py              # 用户相关模型
│   ├── knowledge_base.py    # 知识库相关模型
│   ├── file.py              # 文件相关模型
│   ├── qa.py                # 问答相关模型
│   ├── bot.py               # 机器人相关模型
│   └── department.py        # 部门相关模型
├── daos/                    # 数据访问对象
│   ├── __init__.py
│   ├── base_dao.py          # 基础DAO类
│   ├── user_dao.py          # 用户相关DAO
│   ├── knowledge_base_dao.py # 知识库相关DAO
│   ├── file_dao.py          # 文件相关DAO
│   ├── document_dao.py      # 文档相关DAO
│   ├── faq_dao.py           # FAQ相关DAO
│   ├── qa_log_dao.py        # 问答日志相关DAO
│   ├── bot_dao.py           # 机器人相关DAO
│   └── department_dao.py    # 部门相关DAO
└── manager.py               # 数据库管理器，集成所有DAO
```

## 重构原则

1. **单一职责原则**：每个类只负责一个功能领域
2. **开闭原则**：对扩展开放，对修改关闭
3. **依赖倒置原则**：高层模块不应该依赖低层模块，都应该依赖抽象

## 主要组件

### 连接管理
- `connection.py` - 管理数据库连接池和基本查询执行

### 数据模型
- 为每个表创建对应的数据模型类
- 模型类负责数据验证和格式转换

### 数据访问对象
- 每个DAO类负责一个业务领域的数据操作
- 所有SQL语句应当在DAO类中定义
- DAO类继承自基础DAO类，共享通用功能

### 数据库管理器
- 集成所有DAO，提供统一的接口
- 对外暴露的API应保持与原始类似，以减少迁移成本 