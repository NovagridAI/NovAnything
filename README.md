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
<p style="color: #7f8c8d; font-size: 1.2em; margin: 0.5rem 0;">基于QAnything的企业级知识库管理与问答系统</p>

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
        <span style="color: #3498db;">📑</span> 目录
    </h2>
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

<!-- 主目录项 -->
<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#-项目简介" style="color: #2c3e50; text-decoration: none;">✨ 项目简介</a>
</div>

<!-- 子目录项 -->
<div style="display: grid; gap: 0.6rem; margin-left: 1.8rem;">
    <div style="display: flex; align-items: center; gap: 8px;">
        <a href="#-核心特性" style="color: #7f8c8d; text-decoration: none;">🌟 核心特性</a>
    </div>
    <div style="display: flex; align-items: center; gap: 8px;">
        <a href="#-系统架构" style="color: #7f8c8d; text-decoration: none;">🔧 系统架构</a>
    </div>
</div>

<!-- 其他主目录项模板 -->
<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#-版本演进" style="color: #2c3e50; text-decoration: none;">📢 版本演进</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#-快速开始" style="color: #2c3e50; text-decoration: none;">🚀 快速开始</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#-常见问题" style="color: #2c3e50; text-decoration: none;">❓ 常见问题</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#-参与贡献" style="color: #2c3e50; text-decoration: none;">🤝 参与贡献</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#-许可证书" style="color: #2c3e50; text-decoration: none;">📄 许可证书</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#-贡献者" style="color: #2c3e50; text-decoration: none;">👥 贡献者</a>
</div>

<div style="display: flex; align-items: center; gap: 8px;">
    <a href="#-致谢" style="color: #2c3e50; text-decoration: none;">🙏 致谢</a>
</div>

<!-- 更多目录项... -->

</div>

</div>
</details>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# ✨ 项目简介
<div style="margin: 2rem 0; padding-left: 16px; border-left: 3px solid #3498db;">

NovAnything 是由 Novagrid 开发的企业级知识库管理与问答系统，基于 [QAnything](https://github.com/netease-youdao/QAnything) 进行二次开发。我们在保留原有系统强大的文档解析和智能问答能力的基础上，增加了用户权限控制和知识库权限管理功能，并对前端界面进行了全面重构优化，使其更适合企业级应用场景。

</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

## 🌟 核心特性

<div class="features-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin: 2rem 0;">

<!-- 权限控制系统 -->
<div style="padding: 22px; background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 14px; box-shadow: 0 6px 12px rgba(0,0,0,0.08);">
    <h3 style="margin: 0 0 1rem; color: #2c3e50;">🔐 权限控制</h3>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px;">▸ 用户体系</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 0.95em;">
                <li>三级角色管理</li>
                <li>动态权限继承</li>
            </ul>
        </div>
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px;">▸ 知识库体系</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 0.95em;">
                <li>分级控制</li>
                <li>权限转移</li>
            </ul>
        </div>
    </div>
</div>

<!-- 用户界面优化 -->
<div style="padding: 22px; background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 14px; box-shadow: 0 6px 12px rgba(0,0,0,0.08);">
    <h3 style="margin: 0 0 1rem; color: #2c3e50;">🎨 交互体验</h3>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px;">▸ 界面设计</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 0.95em;">
                <li>响应式布局</li>
                <li>更现代的UI</li>
            </ul>
        </div>
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px;">▸ 交互优化</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 0.95em;">
                <li>优化交互逻辑</li>
                <li>实时反馈机制</li>
            </ul>
        </div>
    </div>
</div>

<!-- 文档处理能力 -->
<div style="padding: 22px; background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 14px; box-shadow: 0 6px 12px rgba(0,0,0,0.08);">
    <h3 style="margin: 0 0 1rem; color: #2c3e50;">📄 文档处理</h3>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px;">▸ 格式支持</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 0.95em;">
                <li>Office全系</li>
                <li>PDF/图片</li>
                <li>网页/多媒体</li>
            </ul>
        </div>
        <div>
            <h4 style="color: #34495e; margin: 0 0 8px;">▸ 智能处理</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 0.95em;">
                <li>语义搜索</li>
                <li>智能问答</li>
            </ul>
        </div>
    </div>
</div>

</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

## 🔧 系统架构

<div style="margin: 2rem 0 2.5rem; padding: 0 1.5rem;">

### 🏗️ 架构演进
**基于QAnything核心架构，新增权限控制层：**

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.5rem; margin-top: 1.2rem;">

<div style="position: relative; padding-left: 2.5rem;">
    <div style="position: absolute; left: 0; top: 0.2em; width: 1.8em; height: 1.8em; background: #f8f9fa; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
        <span style="color: #3498db; font-size: 1.1em;">🔑</span>
    </div>
    <h4 style="color: #2c3e50; margin: 0 0 0.4rem;">用户认证系统</h4>
    <div style="color: #7f8c8d; font-size: 0.95em;">RBAC 权限模型支持</div>
</div>

<div style="position: relative; padding-left: 2.5rem;">
    <div style="position: absolute; left: 0; top: 0.2em; width: 1.8em; height: 1.8em; background: #f8f9fa; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
        <span style="color: #e67e22; font-size: 1.1em;">🔒</span>
    </div>
    <h4 style="color: #2c3e50; margin: 0 0 0.4rem;">权限管理模块</h4>
    <div style="color: #7f8c8d; font-size: 0.95em;">部门/角色/用户三级控制</div>
</div>

<div style="position: relative; padding-left: 2.5rem;">
    <div style="position: absolute; left: 0; top: 0.2em; width: 1.8em; height: 1.8em; background: #f8f9fa; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
        <span style="color: #9b59b6; font-size: 1.1em;">📊</span>
    </div>
    <h4 style="color: #2c3e50; margin: 0 0 0.4rem;">前端交互优化</h4>
    <div style="color: #7f8c8d; font-size: 0.95em;">更加现代的UI与交互逻辑</div>
</div>

</div>

<div style="margin-top: 2rem; padding: 1.2rem; background: #f8f9fa; border-radius: 8px;">
    <div style="display: flex; align-items: center; gap: 0.8rem; color: #34495e;">
        <span style="font-size: 1.2em;">⚙️</span>
        <div style="font-size: 0.95em;">
            <strong>基础架构：</strong>
            QAnything + Milvus + MySQL + ElasticSearch
        </div>
    </div>
</div>

</div>


<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

## 📢 版本演进

<div style="display: flex; flex-direction: column; gap: 28px; margin: 2.5rem 0;">

<!-- 已发布版本 -->
<div style="padding: 24px; background: linear-gradient(152deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 16px; box-shadow: 0 8px 16px rgba(0,0,0,0.06);">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
        <div style="width: 36px; height: 36px; background: #3498db; border-radius: 8px; display: grid; place-items: center;">
            <span style="color: white; font-size: 1.2em;">✓</span>
        </div>
        <div>
            <h3 style="color: #2c3e50; margin: 0;">已发布版本 - v0.0.1</h3>
            <span style="font-size: 0.9em; color: #7f8c8d;">2025-03-14</span>
        </div>
    </div>
    <ul style="margin: 0; font-size: 0.95em; line-height: 1.6;">
        <li style="margin-bottom: 1.2rem;">
            <strong style="color: #2c3e50; display: block;">权限管理系统</strong>
            <div style="font-size: 0.9em; color: #7f8c8d;">支持角色/部门/用户三级控制与知识库权限管理</div>
        </li>
        <li>
            <strong style="color: #2c3e50; display: block;">前端优化</strong>
            <div style="font-size: 0.9em; color: #7f8c8d;">基于QAnything页面结构进行了UI优化</div>
        </li>
    </ul>
</div>

<!-- 开发进程 -->
<div style="padding: 24px; background: linear-gradient(152deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 16px; box-shadow: 0 8px 16px rgba(0,0,0,0.06);">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
        <div style="width: 36px; height: 36px; background: #e67e22; border-radius: 8px; display: grid; place-items: center;">
            <span style="color: white; font-size: 1.2em;">⌛</span>
        </div>
        <div>
            <h3 style="color: #2c3e50; margin: 0;">开发进程</h3>
            <span style="font-size: 0.9em; color: #7f8c8d;">预计 2025-Q2 完成</span>
        </div>
    </div>
    <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-size: 0.9em;">前端重构与优化</span>
            <span style="color: #3498db; font-size: 0.9em;">10%</span>
        </div>
        <div style="height: 6px; background: #f1f2f6; border-radius: 3px;">
            <div style="width: 10%; height: 100%; background: #3498db; border-radius: 3px;"></div>
        </div>
    </div>
    <ul style="margin: 0; font-size: 0.95em; line-height: 1.6;">
        <li>
            <strong style="color: #2c3e50; display: block;">交互升级</strong>
            <div style="font-size: 0.9em; color: #7f8c8d;">重构大部分的交互逻辑与界面</div>
        </li>
    </ul>
    <div style="margin: 1.2rem 0 1.5rem; height: 1px; background: rgba(0,0,0,0.08); position: relative;">
    <div style="position: absolute; width: 40px; height: 1px; left: 0; top: 0;"></div>
    </div>
    <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-size: 0.9em;">后端功能完善</span>
            <span style="color: #3498db; font-size: 0.9em;">15%</span>
        </div>
        <div style="height: 6px; background: #f1f2f6; border-radius: 3px;">
            <div style="width: 15%; height: 100%; background:rgb(234, 174, 22); border-radius: 3px;"></div>
        </div>
    </div>
    <ul style="margin: 0; font-size: 0.95em; line-height: 1.6;">
        <li>
            <strong style="color: #2c3e50; display: block;">模型配置存储</strong>
            <div style="font-size: 0.9em; color: #7f8c8d;">持久化当前用户的配置</div>
        </li>
    </ul>
</div>

</div>


<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# 🚀 快速开始

## 📋 环境要求
<div style="margin: 1.5rem 0 2rem;">

| 系统        | 依赖项             | 最低要求     | 说明                                                                 |
|-------------|--------------------|--------------|---------------------------------------------------------------------|
| 🐧 Linux    | 内存           | ≥20GB        | 物理内存或SWAP交换空间                                               |
| 🍎 macOS    | Docker             | 20.10.5+     | [安装指南](https://docs.docker.com/engine/install/)                  |
| 🪟 Windows  | Docker Desktop     | 4.26.1+      | [安装指南](https://docs.docker.com/desktop/)                        |
| 🐳 通用     | Docker Compose     | 2.23.3+      | [安装指南](https://docs.docker.com/compose/install/)                |

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

## 📥 安装步骤
<div style="margin: 2rem 0;">

### 1️⃣ 获取代码
```bash
git clone https://github.com/NovagridAI/NovAnything.git && cd NovAnything
```

### 2️⃣ 启动服务
<div style="margin: 1.2rem 0 1.8rem;">

```bash
# Linux 系统
docker compose -f docker-compose-linux.yaml up -d

# macOS 系统
docker compose -f docker-compose-mac.yaml up -d

# Windows 系统
docker compose -f docker-compose-win.yaml up -d
```

</div>

### 3️⃣ 访问入口
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">

<div style="padding: 12px; border-left: 4px solid #3498db;">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="color: #3498db;">🌐</span>
        <strong>Web 界面</strong>
    </div>
    <div style="margin-top: 6px;">
        <a href="http://localhost:8777/novanything/" target="_blank">http://localhost:8777/novanything/</a>
    </div>
</div>

<div style="padding: 12px; border-left: 4px solid #e67e22;">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="color: #e67e22;">🔌</span>
        <strong>API 服务</strong>
    </div>
    <div style="margin-top: 6px;">
        <a href="http://localhost:8777/api/" target="_blank">http://localhost:8777/api/</a>
    </div>
</div>

</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# ❓ 常见问题
<div style="margin: 1.5rem 0 2rem; padding: 16px; background: #f8f9fa; border-radius: 8px;">
📚 完整文档请访问 
<a href="docs/FAQ.md" style="color: #3498db; text-decoration: none; border-bottom: 1px dashed #3498db;">FAQ文档</a> 
<span style="color: #7f8c8d; font-size: 0.9em;">（最近更新：2025-03-15）</span>
</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# 🤝 参与贡献
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem; margin: 2rem 0;">

<div style="padding: 12px; border-left: 3px solid #3498db;">
    <div style="display: flex; gap: 8px; align-items: center;">
        <span style="color: #3498db;">💡</span>
        <strong>问题反馈</strong>
    </div>
    <div style="color: #7f8c8d; font-size: 0.9em; margin-top: 6px;">提交Bug或功能建议</div>
</div>

<div style="padding: 12px; border-left: 3px solid #8e44ad;">
    <div style="display: flex; gap: 8px; align-items: center;">
        <span style="color: #8e44ad;">📖</span>
        <strong>文档改进</strong>
    </div>
    <div style="color: #7f8c8d; font-size: 0.9em; margin-top: 6px;">完善使用手册与API文档</div>
</div>

<div style="padding: 12px; border-left: 3px solid #e67e22;">
    <div style="display: flex; gap: 8px; align-items: center;">
        <span style="color: #e67e22;">💻</span>
        <strong>代码贡献</strong>
    </div>
    <div style="color: #7f8c8d; font-size: 0.9em; margin-top: 6px;">提交Pull Request</div>
</div>

</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.2rem; margin: 2rem 0;">

<a href="https://github.com/NovagridAI/NovAnything/issues" target="_blank" style="padding: 12px; border: 1px solid #e9ecef; border-radius: 6px; text-decoration: none;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="color: #3498db;">📢</span>
        <div>
            <div style="color: #2c3e50; font-weight: 500;">GitHub Issues</div>
            <div style="color: #7f8c8d; font-size: 0.9em;">问题追踪与功能请求</div>
        </div>
    </div>
</a>

<a href="https://github.com/NovagridAI/NovAnything/discussions" target="_blank" style="padding: 12px; border: 1px solid #e9ecef; border-radius: 6px; text-decoration: none;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="color: #8e44ad;">💬</span>
        <div>
            <div style="color: #2c3e50; font-weight: 500;">GitHub Discussions</div>
            <div style="color: #7f8c8d; font-size: 0.9em;">技术讨论与经验分享</div>
        </div>
    </div>
</a>

<div style="padding: 12px; border: 1px solid #e9ecef; border-radius: 6px;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="color: #e67e22;">📧</span>
        <div>
            <div style="color: #2c3e50; font-weight: 500;">联系邮箱</div>
            <a href="mailto:contact@novagrid.ai" style="color: #3498db; text-decoration: none;">contact@novagrid.ai</a>
        </div>
    </div>
</div>

</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# 📄 许可证书
<div style="margin: 2rem 0; padding: 16px; background: #f8f9fa; border-radius: 8px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 1.2em;">⚖️</span>
        <div>
            采用 <a href="./LICENSE" style="color: #3498db; text-decoration: none;">AGPL-3.0 许可证</a>
            <div style="color: #7f8c8d; font-size: 0.9em; margin-top: 4px;">开源自由，共同成长</div>
        </div>
    </div>
</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

# 👥 贡献者

## 🌟 核心贡献者
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem; margin: 2rem 0;">

<!-- 贡献者模板 -->
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

<!-- 更多贡献者... -->

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

# 🙏 致谢
<div style="margin: 2rem 0; padding-left: 16px; border-left: 3px solid #3498db;">
    <div style="color: #2c3e50; margin-bottom: 12px;">特别鸣谢：</div>
    <a href="https://github.com/netease-youdao/QAnything" target="_blank" style="text-decoration: none; color: #3498db; margin: 8px 0;">
        • QAnything
    </a>
</div>

<div style="height: 1px; background: rgba(0,0,0,0.1); margin: 2rem 0; box-shadow: 0 1px 2px rgba(52,152,219,0.2);"></div>

<div style="text-align: center; color: #7f8c8d; margin-top: 3rem;">
    <p style="margin: 0.5rem 0; font-size: 0.95em;">由 Novagrid 倾力打造</p>
    <p style="margin: 0.5rem 0; font-size: 0.9em;">Copyright © 2025 Novagrid AI. All rights reserved.</p>
</div>
