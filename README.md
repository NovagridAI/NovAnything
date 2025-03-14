<div align="center">

<img src="https://novagrid-1315164445.cos.ap-beijing.myqcloud.com/novagrid/novagrid_纯logo.png" alt="Logo" width="200">

<h1>NovAnything</h1>
<p style="font-size: 1.2em">基于QAnything的企业级知识库管理与问答系统</p>

<p align="center">
  <a href="./README.md">简体中文</a> |
  <a href="./README_en.md">English</a>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0-yellow"></a>
  <a href="https://github.com/NovagridAI/NovAnything/pulls"><img src="https://img.shields.io/badge/PRs-welcome-red"></a>
</p>

</div>

<details open="open">
<summary><h2>📑 目录</h2></summary>

- [✨ 项目简介](#-项目简介)
  - [🌟 核心特性](#-核心特性)
  - [🔧 系统架构](#-系统架构)
- [📢 最近更新](#-最近更新)
- [🚀 开始使用](#-开始使用)
  - [📋 环境要求](#-环境要求)
  - [📥 安装步骤](#-安装步骤)
  - [🔌 API接口](#-api接口)
- [💡 功能特点](#-功能特点)
  - [🔒 权限管理系统](#-权限管理系统)
  - [📚 知识库管理](#-知识库管理)
  - [📝 文档解析能力](#-文档解析能力)
- [❓ 常见问题](#-常见问题)
- [🤝 参与贡献](#-参与贡献)
- [👥 开源社区](#-开源社区)
- [📄 许可证](#-许可证)
- [🙏 致谢](#-致谢)

</details>

# ✨ 项目简介

NovAnything 是由 Novagrid 开发的企业级知识库管理与问答系统，基于 [QAnything](https://github.com/netease-youdao/QAnything) 进行二次开发。我们在保留原有系统强大的文档解析和智能问答能力的基础上，增加了用户权限控制和知识库权限管理功能，并对前端界面进行了全面重构优化，使其更适合企业级应用场景。

## 🌟 核心特性

<div align="center" style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px; margin: 20px 0;">

<div style="flex: 1; min-width: 250px; max-width: 400px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; margin: 10px;">

### 🔐 完整的权限控制

#### 用户管理
- 多级角色体系
- 灵活的权限分配
- 细粒度访问控制

#### 安全保障
- 数据访问审计
- 操作日志记录
- 敏感信息保护

</div>

<div style="flex: 1; min-width: 250px; max-width: 400px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; margin: 10px;">

### 🎨 优化的用户界面

#### 现代化设计
- 简洁美观的界面
- 响应式布局设计
- 深色模式支持

#### 交互优化
- 直观的操作流程
- 便捷的快捷操作
- 实时反馈机制

</div>

<div style="flex: 1; min-width: 250px; max-width: 400px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; margin: 10px;">

### 📄 强大的文档处理

#### 全面的格式支持
- PDF 和 Office 文档
- 图片和网页内容
- 多媒体资源处理

#### 智能化功能
- 精准的文档解析
- 高效的语义搜索
- 智能问答系统
- 实时协作能力

</div>

</div>

## 🔧 系统架构

<div align="center">
<img src="docs/images/novanything_arch.png" width="600" alt="系统架构图">
</div>

NovAnything在QAnything的基础架构上增加了权限控制层，主要包括：

- 🔑 用户认证与授权系统
- 🔒 知识库权限管理模块
- 📝 文档访问控制层
- 📊 操作日志记录系统

# 📢 最近更新

- 🌟 ***2025-03-14***: **发布NovAnything 0.0.1版本，增加完整的权限管理系统**
- 🚧 ***正在进行中...*** **优化前端界面，提升用户体验**

# 🚀 开始使用

## 📋 环境要求

| **系统**    | **依赖项**           | **最低要求**    | **说明**                                                                              |
|-----------|------------------|-------------|-----------------------------------------------------------------------------------|
|           | 内存               | >= 20GB     |                                                                                   |
| Linux/Mac | Docker          | >= 20.10.5  | [安装指南](https://docs.docker.com/engine/install/)                                  |
| Linux/Mac | Docker Compose  | >= 2.23.3   | [安装指南](https://docs.docker.com/compose/install/)                                 |
| Windows   | Docker Desktop  | >= 4.26.1   | [安装指南](https://docs.docker.com/desktop/install/windows-install/)                |

## 📥 安装步骤

1️⃣ 克隆项目
```bash
git clone https://github.com/NovagridAI/NovAnything.git
```

2️⃣ 进入项目目录
```bash
cd NovAnything
```

3️⃣ 启动服务
```bash
# Linux环境
docker compose -f docker-compose-linux.yaml up

# Mac环境
docker compose -f docker-compose-mac.yaml up

# Windows环境
docker compose -f docker-compose-win.yaml up
```

4️⃣ 访问系统
- 🌐 前端界面：http://localhost:8777/novanything/
- 🔌 API接口：http://localhost:8777/api/

# 💡 功能特点

## 🔒 权限管理系统

- **用户角色管理**
  - 多级角色定义
  - 灵活的权限分配
  - 细粒度的操作权限

- **知识库权限控制**
  - 私有知识库
  - 共享知识库
  - 公共知识库

## 📚 知识库管理

- **知识库组织**
  - 多级目录结构
  - 智能标签系统
  - 快速检索功能

## 📝 文档解析能力

- **多格式支持**
  - PDF文档
  - Office套件
  - 图片识别
  - 网页解析

- **智能解析**
  - 表格识别
  - 图文混排
  - 多栏布局

# ❓ 常见问题

详细信息请参考我们的 [FAQ文档](docs/FAQ.md)。

# 🤝 参与贡献

我们欢迎各种形式的贡献，包括但不限于：

- 💡 提交问题和建议
- 📖 改进文档
- 💻 提交代码修改
- 🎯 分享使用经验

# 👥 开源社区

- 📢 [GitHub Issues](https://github.com/NovagridAI/NovAnything/issues)
- 💬 [GitHub Discussions](https://github.com/NovagridAI/NovAnything/discussions)
- 📧 邮箱：contact@novagrid.ai

# 📄 许可证

本项目采用 [AGPL-3.0](./LICENSE) 许可证。

# 🙏 致谢

- [QAnything](https://github.com/netease-youdao/QAnything) - 本项目的基础框架
- 所有为这个项目做出贡献的开发者

---

<div align="center">
<p>由 Novagrid 倾力打造</p>
<p>Copyright © 2025 Novagrid AI. All rights reserved.</p>
</div>
