# <div align="center">NovAnything</div>

<div align="center">

<img src="https://novagrid-1315164445.cos.ap-beijing.myqcloud.com/novagrid/novagrid_纯logo.png" 
     alt="NovAnything Logo" 
     width="200">

<p>
    <strong>基于QAnything的企业级知识库管理与问答系统</strong>
</p>

<p>
    <a href="./README.md">简体中文</a> |
    <a href="./README_en.md">English</a>
</p>

<p>
    <a href="./LICENSE">
        <img src="https://img.shields.io/badge/license-AGPL--3.0-yellow" alt="License">
    </a>
    <a href="https://github.com/NovagridAI/NovAnything/pulls">
        <img src="https://img.shields.io/badge/PRs-welcome-red" alt="PRs Welcome">
    </a>
</p>

</div>

<div align="center">

---

</div>

## ✨ 项目简介

NovAnything 是由 Novagrid 开发的企业级知识库管理与问答系统，基于 [QAnything](https://github.com/netease-youdao/QAnything) 进行二次开发。我们在保留原有系统强大的文档解析和智能问答能力的基础上，增加了用户权限控制和知识库权限管理功能，并对前端界面进行了全面重构优化，使其更适合企业级应用场景。

<div align="center">

---

</div>

## 🌟 核心特性

### 🔐 权限控制
- **用户体系**
  - 三级角色管理
  - 动态权限继承
- **知识库体系**
  - 分级控制
  - 权限转移

### 🎨 交互体验
- **界面设计**
  - 响应式布局
  - 更现代的UI
- **交互优化**
  - 优化交互逻辑
  - 实时反馈机制

### 📄 文档处理
- **格式支持**
  - Office全系
  - PDF/图片
  - 网页/多媒体
- **智能处理**
  - 语义搜索
  - 智能问答

<div align="center">

---

</div>

## 🔧 系统架构

### 🏗️ 架构演进
基于QAnything核心架构，新增权限控制层：

- 🔑 **用户认证系统**
  - RBAC 权限模型支持
- 🔒 **权限管理模块**
  - 部门/角色/用户三级控制
- 📊 **前端交互优化**
  - 更加现代的UI与交互逻辑

### ⚙️ 基础架构
- QAnything
- Milvus
- MySQL
- ElasticSearch

<div align="center">

---

</div>

## 📢 版本演进

### v0.0.1 (2025-03-14)
- **权限管理系统**
  - 支持角色/部门/用户三级控制与知识库权限管理
- **前端优化**
  - 基于QAnything页面结构进行了UI优化

### 开发进程 (预计 2025-Q2)
- **前端重构与优化** (10%)
  - 重构大部分的交互逻辑与界面
- **后端功能完善** (15%)
  - 持久化当前用户的配置

<div align="center">

---

</div>

## 🚀 快速开始

### 📋 环境要求

| 系统 | 依赖项 | 最低要求 | 说明 |
|------|--------|----------|------|
| 🐧 Linux | 内存 | ≥20GB | 物理内存或SWAP交换空间 |
| 🍎 macOS | Docker | 20.10.5+ | [安装指南](https://docs.docker.com/engine/install/) |
| 🪟 Windows | Docker Desktop | 4.26.1+ | [安装指南](https://docs.docker.com/desktop/) |
| 🐳 通用 | Docker Compose | 2.23.3+ | [安装指南](https://docs.docker.com/compose/install/) |

### 📥 安装步骤

1. **获取代码**
```bash
git clone https://github.com/NovagridAI/NovAnything.git && cd NovAnything
```

2. **启动服务**
```bash
# Linux 系统
docker compose -f docker-compose-linux.yaml up -d

# macOS 系统
docker compose -f docker-compose-mac.yaml up -d

# Windows 系统
docker compose -f docker-compose-win.yaml up -d
```

3. **访问入口**
- Web界面：http://localhost:8777/novanything/
- API服务：http://localhost:8777/api/

<div align="center">

---

</div>

## ❓ 常见问题

📚 完整文档请访问 [FAQ文档](docs/FAQ.md)（最近更新：2025-03-15）

<div align="center">

---

</div>

## 🤝 参与贡献

### 贡献方式
- 💡 **问题反馈**：提交Bug或功能建议
- 📖 **文档改进**：完善使用手册与API文档
- 💻 **代码贡献**：提交Pull Request

### 联系我们
- [GitHub Issues](https://github.com/NovagridAI/NovAnything/issues)：问题追踪与功能请求
- [GitHub Discussions](https://github.com/NovagridAI/NovAnything/discussions)：技术讨论与经验分享
- 📧 邮箱：contact@novagrid.ai

<div align="center">

---

</div>

## 📄 许可证书

采用 [AGPL-3.0 许可证](./LICENSE)

<div align="center">

---

</div>

## 👥 贡献者

### 🌟 核心贡献者

<table>
<tr>
<td align="center">
<a href="https://github.com/Mangosata">
<img src="https://github.com/Mangosata.png" width="100px;" alt="Mangosata"/>
<br />
<sub><b>Mangosata</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/Sshrimp">
<img src="https://github.com/Sshrimp.png" width="100px;" alt="Shrimp"/>
<br />
<sub><b>Shrimp</b></sub>
</a>
</td>
</tr>
</table>

<div align="center">

---

</div>

## 🙏 致谢

特别鸣谢：
- [QAnything](https://github.com/netease-youdao/QAnything)

<div align="center">

---

</div>

<div align="center">
<p>由 Novagrid 倾力打造</p>
<p>Copyright © 2025 Novagrid AI. All rights reserved.</p>
</div>
