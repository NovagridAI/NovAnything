# <div align="center">NovAnything</div>

<div align="center">

<img src="https://novagrid-1315164445.cos.ap-beijing.myqcloud.com/novagrid/novagrid_纯logo.png" 
     alt="NovAnything Logo" 
     width="200">

<p>
    <strong>Enterprise-level knowledge base management and question-answering system based on QAnything</strong>
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

## ✨ Project Introduction

NovAnything is an enterprise-level knowledge base management and question-answering system developed by Novagrid, based on secondary development of [QAnything](https://github.com/netease-youdao/QAnything). While retaining the original system's robust document parsing and intelligent question-answering capabilities, we have added user access control and knowledge base permission management features. Additionally, the front-end interface has been completely redesigned and optimized to better suit enterprise application scenarios.

<div align="center">

---

</div>

## 🌟 Core Features

### 🔐 Access Control
- **User System**
  - Three-tier role management
  - Dynamic permission inheritance
- **Knowledge Base System**
  - Hierarchical control
  - Permission transfer

### 🎨 User Experience
- **Interface Design**
  - Responsive layout
  - More modern UI
- **Interaction Optimization**
  - Optimize interaction logic
  - Real-time feedback

### 📄 Document Process
- **Format Support**
  - All Office suites
  - PDF/Picture
  - Web/Multimedia
- **Intelligent Process**
  - Semantic search
  - Intelligent Q&A

<div align="center">

---

</div>

## 🔧 System Architecture

### 🏗️ Version Evolution
**Based on QAnything's core architecture, with added access control layer:**

- 🔑 **User Authentication System**
  - RBAC Permission Model Support
- 🔒 **Permission Management Module**
  - Department/Role/User Three-level Control
- 📊 **Frontend Interaction Optimization**
  - More Modern UI and Interaction Logic

### ⚙️ Base Architecture
- QAnything
- Milvus
- MySQL
- ElasticSearch

<div align="center">

---

</div>

## 📢 Version Evolution

### v0.0.1 (2025-03-14)
- **Permission Management System**
  - Support for role/department/user three-level control and knowledge base permission management
- **Frontend Optimization**
  - UI optimization based on QAnything's page structure

### Development Progress (Expected 2025-Q2)
- **Frontend Refactoring and Optimization** (10%)
  - Refactoring most of the interaction logic and interface
- **Backend Function Enhancement** (15%)
  - Persistent storage of current user configurations

<div align="center">

---

</div>

## 🚀 Quick Start

### 📋 Environment Requirements

| System | Dependency | Minimum Requirement | Description |
|--------|------------|---------------------|-------------|
| 🐧 Linux | Memory | ≥20GB | Physical memory or SWAP space |
| 🍎 macOS | Docker | 20.10.5+ | [Installation Guide](https://docs.docker.com/engine/install/) |
| 🪟 Windows | Docker Desktop | 4.26.1+ | [Installation Guide](https://docs.docker.com/desktop/) |
| 🐳 General | Docker Compose | 2.23.3+ | [Installation Guide](https://docs.docker.com/compose/install/) |

### 📥 Installation Steps

1. **Get the Code**
```bash
git clone https://github.com/NovagridAI/NovAnything.git && cd NovAnything
```

2. **Start Services**
```bash
# Linux System
docker compose -f docker-compose-linux.yaml up -d

# macOS System
docker compose -f docker-compose-mac.yaml up -d

# Windows System
docker compose -f docker-compose-win.yaml up -d
```

3. **Access**
- Web Interface: http://localhost:8777/novanything/
- API Service: http://localhost:8777/api/

<div align="center">

---

</div>

## ❓ FAQ

📚 Complete documentation available at [FAQ Documentation](docs/FAQ.md) (Last updated: 2025-03-15)

<div align="center">

---

</div>

## 🤝 Contribution Guide

### Contribution Methods
- 💡 **Issue Reporting**: Submit bugs or feature suggestions
- 📖 **Documentation Improvement**: Enhance user manual and API documentation
- 💻 **Code Contribution**: Submit Pull Requests

### Contact Us
- [GitHub Issues](https://github.com/NovagridAI/NovAnything/issues): Issue tracking and feature requests
- [GitHub Discussions](https://github.com/NovagridAI/NovAnything/discussions): Technical discussions and experience sharing
- 📧 Email: contact@novagrid.ai

<div align="center">

---

</div>

## 📄 License

Licensed under [AGPL-3.0 License](./LICENSE)

<div align="center">

---

</div>

## 👥 Contributors

### 🌟 Core Contributors

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

## 🙏 Acknowledgments

Special Thanks:
- [QAnything](https://github.com/netease-youdao/QAnything)

<div align="center">

---

</div>

<div align="center">
<p>Crafted with ❤️ by Novagrid</p>
<p>Copyright © 2025 Novagrid AI. All rights reserved.</p>
</div>

