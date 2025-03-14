<style>
/* 贡献者卡片悬停动画 */
a:hover div[style*="background: #f8f9fa"] {
    transform: translateY(-3px);
    box-shadow: 0 4px 12px rgba(52,152,219,0.15);
}

/* 头像悬浮效果 */
img[alt="Contributor"] {
    transition: transform 0.3s ease-in-out;
}

a:hover img[alt="Contributor"] {
    transform: rotate(8deg) scale(1.05);
}
</style>


<div align="center" style="padding: 2rem 0;">

<img src="https://novagrid-1315164445.cos.ap-beijing.myqcloud.com/novagrid/novagrid_纯logo.png" 
     alt="NovAnything Logo" 
     style="width: 200px; height: auto; margin-bottom: 1.5rem;">

<h1 style="color: #2c3e50; margin: 0.8rem 0; font-size: 2.2em;">NovAnything</h1>
<p style="color: #7f8c8d; font-size: 1.2em; margin: 0.5rem 0;">Enterprise-level knowledge base management and question-answering system based on QAnything</p>

<div style="margin: 1.2rem 0; display: flex; justify-content: center; gap: 1.5rem;">
    <a href="./README.md" style="color: #3498db; text-decoration: none; border-bottom: 1px dashed #3498db;">简体中文</a>
    <span style="color: #e9ecef;">|</span>
    <a href="./README_en.md" style="color: #3498db; text-decoration: none; border-bottom: 1px dashed #3498db;">English</a>
</div>

<div style="margin: 1.2rem 0; display: flex; justify-content: center; gap: 1rem;">
    <a href="./LICENSE" style="text-decoration: none;">
        <img src="https://img.shields.io/badge/license-AGPL--3.0-yellow" 
             alt="License" 
             style="border-radius: 4px;">
    </a>
    <a href="https://github.com/NovagridAI/NovAnything/pulls" style="text-decoration: none;">
        <img src="https://img.shields.io/badge/PRs-welcome-red" 
             alt="PRs Welcome" 
             style="border-radius: 4px;">
    </a>
</div>

</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

<details open="open" style="margin: 2rem 0; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
<summary  style="cursor: pointer; list-style: none; /* 隐藏默认三角 */">
    <h2 style="color: #2c3e50; margin: 0; display: inline-flex; align-items: center; gap: 8px;">
        <span style="color: #3498db;">📑</span> Table of Contents</h2>
</summary>

<style>
    /* 隐藏 Firefox 的默认三角 */
    summary::-webkit-details-marker {
        display: none !important;
    }
    /* 隐藏 Webkit 内核的默认三角 */
    summary::marker {
        display: none !important;
        content: '' !important;
    }
</style>

<div style="margin-top: 1rem; padding-left: 12px;">

<div style="display: grid; gap: 0.8rem;">

<!-- Main directory items -->
<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#project-introduction" style="color: #2c3e50; text-decoration: none;">✨ Project Introduction</a>
</div>

<!-- Subdirectory items -->
<div style="display: grid; gap: 0.6rem; margin-left: 1.8rem;">
    <div style="display: flex; align-items: center; gap: 8px;">
        <a href="#core-features" style="color: #7f8c8d; text-decoration: none;">🌟 Core Features</a>
    </div>
    <div style="display: flex; align-items: center; gap: 8px;">
        <a href="#system-architecture" style="color: #7f8c8d; text-decoration: none;">🔧 System Architecture</a>
    </div>
</div>

<!-- Other main directory items -->
<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#version-evolution" style="color: #2c3e50; text-decoration: none;">📢 Version Evolution</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#quick-start" style="color: #2c3e50; text-decoration: none;">🚀 Quick Start</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#faq" style="color: #2c3e50; text-decoration: none;">❓ FAQ</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#contribution-guide" style="color: #2c3e50; text-decoration: none;">🤝 Contribution Guide</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#license" style="color: #2c3e50; text-decoration: none;">📄 License</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#contributors" style="color: #2c3e50; text-decoration: none;">👥 Contributors</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#acknowledgments" style="color: #2c3e50; text-decoration: none;">🙏 Acknowledgments</a>
</div>

<!-- 更多目录项... -->

</div>

</div>
</details>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# ✨ Project Introduction
<div id="project-introduction" style="margin: 2rem 0; padding-left: 16px; border-left: 3px solid #3498db;">

NovAnything is an enterprise-level knowledge base management and question-answering system developed by Novagrid, based on secondary development of [QAnything](https://github.com/netease-youdao/QAnything). While retaining the original system's robust document parsing and intelligent question-answering capabilities, we have added user access control and knowledge base permission management features. Additionally, the front-end interface has been completely redesigned and optimized to better suit enterprise application scenarios.

</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

## 🌟 Core Features
<div id="core-features">

<div class="features-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin: 2rem 0;">

<!-- Access Control -->
<div style="padding: 20px; background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    <h3 style="margin: 0 0 1rem; color: #2c3e50; font-size: 1.1em;">🔐 Access Control</h3>
    <div style="display: grid; grid-template-columns: 1fr; gap: 12px;">
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px; font-size: 0.95em;">▸ User</h4>
            <ul style="margin: 0; padding-left: 16px; font-size: 0.9em; color: #7f8c8d;">
                <li style="margin-bottom: 8px;">Three-tier role management</li>
                <li>Dynamic permission inheritance</li>
            </ul>
        </div>
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px; font-size: 0.95em;">▸ RAG</h4>
            <ul style="margin: 0; padding-left: 16px; font-size: 0.9em; color: #7f8c8d;">
                <li style="margin-bottom: 8px;">Hierarchical control</li>
                <li>Permission transfer</li>
            </ul>
        </div>
    </div>
</div>

<!-- User Experience -->
<div style="padding: 20px; background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    <h3 style="margin: 0 0 1rem; color: #2c3e50; font-size: 1.1em;">🎨 User Experience</h3>
    <div style="display: grid; grid-template-columns: 1fr; gap: 12px;">
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px; font-size: 0.95em;">▸ Interface</h4>
            <ul style="margin: 0; padding-left: 16px; font-size: 0.9em; color: #7f8c8d;">
                <li style="margin-bottom: 8px;">Responsive layout</li>
                <li>More modern UI</li>
            </ul>
        </div>
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px; font-size: 0.95em;">▸ Interactive</h4>
            <ul style="margin: 0; padding-left: 16px; font-size: 0.9em; color: #7f8c8d;">
                <li style="margin-bottom: 8px;">Optimize interaction logic</li>
                <li>Real-time feedback</li>
            </ul>
        </div>
    </div>
</div>

<!-- Document Process -->
<div style="padding: 20px; background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    <h3 style="margin: 0 0 1rem; color: #2c3e50; font-size: 1.1em;">📄 Document Process</h3>
    <div style="display: grid; grid-template-columns: 1fr; gap: 12px;">
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px; font-size: 0.95em;">▸ Format Support</h4>
            <ul style="margin: 0; padding-left: 16px; font-size: 0.9em; color: #7f8c8d;">
                <li style="margin-bottom: 8px;">All Office suites</li>
                <li style="margin-bottom: 8px;">PDF/Picture</li>
                <li>Web/Multimedia</li>
            </ul>
        </div>
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px; font-size: 0.95em;">▸ Intelligent Process</h4>
            <ul style="margin: 0; padding-left: 16px; font-size: 0.9em; color: #7f8c8d;">
                <li style="margin-bottom: 8px;">Semantic search</li>
                <li>Intelligent Q&A</li>
            </ul>
        </div>
    </div>
</div>

</div>

</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

## 🔧 System Architecture
<div id="system-architecture" style="margin: 2rem 0 2.5rem; padding: 0 1.5rem;">

### 🏗️ Version Evolution
**Based on QAnything's core architecture, with added access control layer:**

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.5rem; margin-top: 1.2rem;">

<div style="position: relative; padding-left: 2.5rem;">
    <div style="position: absolute; left: 0; top: 0.2em; width: 1.8em; height: 1.8em; background: #f8f9fa; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
        <span style="color: #3498db; font-size: 1.1em;">🔑</span>
    </div>
    <h4 style="color: #2c3e50; margin: 0 0 0.4rem;">User Authentication System</h4>
    <div style="color: #7f8c8d; font-size: 0.95em;">RBAC Permission Model Support</div>
</div>

<div style="position: relative; padding-left: 2.5rem;">
    <div style="position: absolute; left: 0; top: 0.2em; width: 1.8em; height: 1.8em; background: #f8f9fa; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
        <span style="color: #e67e22; font-size: 1.1em;">🔒</span>
    </div>
    <h4 style="color: #2c3e50; margin: 0 0 0.4rem;">Permission Management Module</h4>
    <div style="color: #7f8c8d; font-size: 0.95em;">Department/Role/User Three-level Control</div>
</div>

<div style="position: relative; padding-left: 2.5rem;">
    <div style="position: absolute; left: 0; top: 0.2em; width: 1.8em; height: 1.8em; background: #f8f9fa; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
        <span style="color: #9b59b6; font-size: 1.1em;">📊</span>
    </div>
    <h4 style="color: #2c3e50; margin: 0 0 0.4rem;">Frontend Interaction Optimization</h4>
    <div style="color: #7f8c8d; font-size: 0.95em;">More Modern UI and Interaction Logic</div>
</div>

</div>

<div style="margin-top: 2rem; padding: 1.2rem; background: #f8f9fa; border-radius: 8px;">
    <div style="display: flex; align-items: center; gap: 0.8rem; color: #34495e;">
        <span style="font-size: 1.2em;">⚙️</span>
        <div style="font-size: 0.95em;">
            <strong>Base Architecture:</strong>
            QAnything + Milvus + MySQL + ElasticSearch
        </div>
    </div>
</div>

</div>


<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

## �� Version Evolution
<div id="version-evolution" style="display: flex; flex-direction: column; gap: 28px; margin: 2.5rem 0;">

<!-- Released Version -->
<div style="padding: 24px; background: linear-gradient(152deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 16px; box-shadow: 0 8px 16px rgba(0,0,0,0.06);">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
        <div style="width: 36px; height: 36px; background: #3498db; border-radius: 8px; display: grid; place-items: center;">
            <span style="color: white; font-size: 1.2em;">✓</span>
        </div>
        <div>
            <h3 style="color: #2c3e50; margin: 0;">Released Version - v0.0.1</h3>
            <span style="font-size: 0.9em; color: #7f8c8d;">2025-03-14</span>
        </div>
    </div>
    <ul style="margin: 0; font-size: 0.95em; line-height: 1.6;">
        <li style="margin-bottom: 1.2rem;">
            <strong style="color: #2c3e50; display: block;">Permission Management System</strong>
            <div style="font-size: 0.9em; color: #7f8c8d;">Support for role/department/user three-level control and knowledge base permission management</div>
        </li>
        <li>
            <strong style="color: #2c3e50; display: block;">Frontend Optimization</strong>
            <div style="font-size: 0.9em; color: #7f8c8d;">UI optimization based on QAnything's page structure</div>
        </li>
    </ul>
</div>

<!-- Development Progress -->
<div style="padding: 24px; background: linear-gradient(152deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 16px; box-shadow: 0 8px 16px rgba(0,0,0,0.06);">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
        <div style="width: 36px; height: 36px; background: #e67e22; border-radius: 8px; display: grid; place-items: center;">
            <span style="color: white; font-size: 1.2em;">⌛</span>
        </div>
        <div>
            <h3 style="color: #2c3e50; margin: 0;">Development Progress</h3>
            <span style="font-size: 0.9em; color: #7f8c8d;">Expected completion: 2025-Q2</span>
        </div>
    </div>
    <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-size: 0.9em;">Frontend Refactoring and Optimization</span>
            <span style="color: #3498db; font-size: 0.9em;">10%</span>
        </div>
        <div style="height: 6px; background: #f1f2f6; border-radius: 3px;">
            <div style="width: 10%; height: 100%; background: #3498db; border-radius: 3px;"></div>
        </div>
    </div>
    <ul style="margin: 0; font-size: 0.95em; line-height: 1.6;">
        <li>
            <strong style="color: #2c3e50; display: block;">Interaction Upgrade</strong>
            <div style="font-size: 0.9em; color: #7f8c8d;">Refactoring most of the interaction logic and interface</div>
        </li>
    </ul>
    <div style="margin: 1.2rem 0 1.5rem; height: 1px; background: rgba(0,0,0,0.08); position: relative;">
    <div style="position: absolute; width: 40px; height: 1px; left: 0; top: 0;"></div>
    </div>
    <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-size: 0.9em;">Backend Function Enhancement</span>
            <span style="color: #3498db; font-size: 0.9em;">15%</span>
        </div>
        <div style="height: 6px; background: #f1f2f6; border-radius: 3px;">
            <div style="width: 15%; height: 100%; background:rgb(234, 174, 22); border-radius: 3px;"></div>
        </div>
    </div>
    <ul style="margin: 0; font-size: 0.95em; line-height: 1.6;">
        <li>
            <strong style="color: #2c3e50; display: block;">Model Configuration Storage</strong>
            <div style="font-size: 0.9em; color: #7f8c8d;">Persistent storage of current user configurations</div>
        </li>
    </ul>
</div>

</div>


<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# 📢 Quick Start
<div id="quick-start">

## 📋 Environment Requirements
<div style="margin: 1.5rem 0 2rem;">

| System      | Dependency         | Minimum Requirement | Description                                                           |
|-------------|--------------------|---------------------|-----------------------------------------------------------------------|
| 🐧 Linux    | Memory         | ≥20GB              | Physical memory or SWAP space                                         |
| 🍎 macOS    | Docker             | 20.10.5+           | [Installation Guide](https://docs.docker.com/engine/install/)         |
| 🪟 Windows  | Docker Desktop     | 4.26.1+            | [Installation Guide](https://docs.docker.com/desktop/)                |
| 🐳 General  | Docker Compose     | 2.23.3+            | [Installation Guide](https://docs.docker.com/compose/install/)        |

</div>

<style>
table {
    border-collapse: collapse;
    width: 100%;
    background: #f8f9fa;
    border-radius: 8px;
    overflow: hidden;
}
td, th {
    padding: 12px 16px;
    border-bottom: 1px solid #e9ecef;
    text-align: left;
}
th {
    background:rgb(218, 229, 239);
    color: white;
}
a {
    color: #3498db;
    text-decoration: none;
    border-bottom: 1px dashed rgba(190, 190, 190, 0.3);
}
</style>

## 📥 Installation Steps
<div style="margin: 2rem 0;">

### 1️⃣ Get the Code
```bash
git clone https://github.com/NovagridAI/NovAnything.git && cd NovAnything
```

### 2️⃣ Start Services
<div style="margin: 1.2rem 0 1.8rem;">

```bash
# Linux System
docker compose -f docker-compose-linux.yaml up -d

# macOS System
docker compose -f docker-compose-mac.yaml up -d

# Windows System
docker compose -f docker-compose-win.yaml up -d
```

</div>

### 3️⃣ Access
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">

<div style="padding: 12px; border-left: 4px solid #3498db;">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="color: #3498db;">🌐</span>
        <strong>Web Interface</strong>
    </div>
    <div style="margin-top: 6px;">
        <a href="http://localhost:8777/novanything/" target="_blank">http://localhost:8777/novanything/</a>
    </div>
</div>

<div style="padding: 12px; border-left: 4px solid #e67e22;">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="color: #e67e22;">🔌</span>
        <strong>API Service</strong>
    </div>
    <div style="margin-top: 6px;">
        <a href="http://localhost:8777/api/" target="_blank">http://localhost:8777/api/</a>
    </div>
</div>

</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# ❓ FAQ
<div id="faq" style="margin: 1.5rem 0 2rem; padding: 16px; background: #f8f9fa; border-radius: 8px;">
📚 Complete documentation available at 
<a href="docs/FAQ.md" style="color: #3498db; text-decoration: none; border-bottom: 1px dashed #3498db;">FAQ Documentation</a> 
<span style="color: #7f8c8d; font-size: 0.9em;">（Last updated: 2025-03-15）</span>
</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# 🤝 Contribution Guide
<div id="contribution-guide" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem; margin: 2rem 0;">

<div style="padding: 12px; border-left: 3px solid #3498db;">
    <div style="display: flex; gap: 8px; align-items: center;">
        <span style="color: #3498db;">💡</span>
        <strong>Issue Reporting</strong>
    </div>
    <div style="color: #7f8c8d; font-size: 0.9em; margin-top: 6px;">Submit bugs or feature suggestions</div>
</div>

<div style="padding: 12px; border-left: 3px solid #8e44ad;">
    <div style="display: flex; gap: 8px; align-items: center;">
        <span style="color: #8e44ad;">📖</span>
        <strong>Documentation Improvement</strong>
    </div>
    <div style="color: #7f8c8d; font-size: 0.9em; margin-top: 6px;">Enhance user manual and API documentation</div>
</div>

<div style="padding: 12px; border-left: 3px solid #e67e22;">
    <div style="display: flex; gap: 8px; align-items: center;">
        <span style="color: #e67e22;">💻</span>
        <strong>Code Contribution</strong>
    </div>
    <div style="color: #7f8c8d; font-size: 0.9em; margin-top: 6px;">Submit Pull Requests</div>
</div>

</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.2rem; margin: 2rem 0;">

<a href="https://github.com/NovagridAI/NovAnything/issues" target="_blank" style="padding: 12px; border: 1px solid #e9ecef; border-radius: 6px; text-decoration: none;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="color: #3498db;">📢</span>
        <div>
            <div style="color: #2c3e50; font-weight: 500;">GitHub Issues</div>
            <div style="color: #7f8c8d; font-size: 0.9em;">Issue tracking and feature requests</div>
        </div>
    </div>
</a>

<a href="https://github.com/NovagridAI/NovAnything/discussions" target="_blank" style="padding: 12px; border: 1px solid #e9ecef; border-radius: 6px; text-decoration: none;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="color: #8e44ad;">💬</span>
        <div>
            <div style="color: #2c3e50; font-weight: 500;">GitHub Discussions</div>
            <div style="color: #7f8c8d; font-size: 0.9em;">Technical discussions and experience sharing</div>
        </div>
    </div>
</a>

<div style="padding: 12px; border: 1px solid #e9ecef; border-radius: 6px;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="color: #e67e22;">📧</span>
        <div>
            <div style="color: #2c3e50; font-weight: 500;">Contact Email</div>
            <a href="mailto:contact@novagrid.ai" style="color: #3498db; text-decoration: none;">contact@novagrid.ai</a>
        </div>
    </div>
</div>

</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# 📄 License
<div id="license" style="margin: 2rem 0; padding: 16px; background: #f8f9fa; border-radius: 8px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 1.2em;">⚖️</span>
        <div>
            Licensed under <a href="./LICENSE" style="color: #3498db; text-decoration: none;">AGPL-3.0 License</a>
            <div style="color: #7f8c8d; font-size: 0.9em; margin-top: 4px;">Open source, grow together</div>
        </div>
    </div>
</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# 👥 Contributors
<div id="contributors">

## 🌟 Core Contributors
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem; margin: 2rem 0;">

<!-- Contributor template -->
<a href="https://github.com/Mangosata" target="_blank" style="text-decoration: none;">
    <div style="padding: 1rem; background: #f8f9fa; border-radius: 8px; transition: transform 0.2s;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <img src="https://github.com/Mangosata.png" 
                 alt="Contributor" 
                 style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid #3498db;">
            <div>
                <div style="color: #2c3e50; font-weight: 500;">Mangosata</div>
                <div style="color: #7f8c8d; font-size: 0.9em;">@Mangosata</div>
            </div>
        </div>
    </div>
</a>
<a href="https://github.com/Sshrimp" target="_blank" style="text-decoration: none;">
    <div style="padding: 1rem; background: #f8f9fa; border-radius: 8px; transition: transform 0.2s;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <img src="https://github.com/Sshrimp.png" 
                 alt="Contributor" 
                 style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid #3498db;">
            <div>
                <div style="color: #2c3e50; font-weight: 500;">Shrimp</div>
                <div style="color: #7f8c8d; font-size: 0.9em;">@Sshrimp</div>
            </div>
        </div>
    </div>
</a>

</div>

<!-- ## 🤝 所有贡献者
<div style="margin: 1.5rem 0 2rem; padding: 16px; background: #f8f9fa; border-radius: 8px;">
    <div style="display: flex; flex-wrap: wrap; gap: 12px;">
        <a href="https://github.com/user1" target="_blank" style="display: flex; align-items: center; gap: 8px; text-decoration: none;">
            <img src="https://avatars.githubusercontent.com/u/1?s=40" 
                 alt="user1" 
                 style="width: 32px; height: 32px; border-radius: 50%;">
            <span style="color: #3498db;">user1</span>
        </a>
    </div>
    <div style="color: #7f8c8d; margin-top: 1rem; font-size: 0.9em;">
        完整列表详见 <a href="./CONTRIBUTORS.md" style="color: #3498db;">贡献者名单</a>
    </div>
</div> -->

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# 🙏 Acknowledgments
<div id="acknowledgments" style="margin: 2rem 0; padding-left: 16px; border-left: 3px solid #3498db;">
    <div style="color: #2c3e50; margin-bottom: 12px;">Special Thanks:</div>
    <a href="https://github.com/netease-youdao/QAnything" target="_blank" style="text-decoration: none; color: #3498db; margin: 8px 0;">
        • QAnything
    </a>
</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

<div style="text-align: center; color: #7f8c8d; margin-top: 3rem;">
    <p style="margin: 0.5rem 0; font-size: 0.95em;">Crafted with ❤️ by Novagrid</p>
    <p style="margin: 0.5rem 0; font-size: 0.9em;">Copyright © 2025 Novagrid AI. All rights reserved.</p>
</div>

