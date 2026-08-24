\ Local AI Assistant



一个轻量级、移动端优先的本地大模型与生成式 AI 助手。基于 \*\*Flask + LM Studio + ComfyUI\*\* 构建，支持多会话管理、大模型参数实时调节、Markdown/LaTeX 渲染及文生视频 API 拓展。



\---



\## ✨ 核心特性



\* 🤖 \*\*本地 LLM 无缝接入\*\*：兼容 LM Studio 及标准 OpenAI REST API 接口，支持 Server-Sent Events (SSE) 流式响应与打字机效果。

\* 🎬 \*\*ComfyUI 生成式拓展\*\*：可作为本地 ComfyUI 后台的调度中枢，通过 API 方式提交工作流，实现文生图/文生视频的离线渲染与实时轮询。

\* 📱 \*\*移动端优先设计\*\*：采用全响应式布局与原生长屏交互体验，支持手势 drawer 侧边栏与独立遮罩。

\* 💾 \*\*本地离线持久化\*\*：不依赖远程数据库，所有会话记录、参数配置与历史版本均通过浏览器 `localStorage` 保护在本地。

\* 📐 \*\*Markdown \& LaTeX 渲染\*\*：集成 `marked.js` 与 `KaTeX` 数学公式库，完美支持学术推导、代码高亮与公式渲染。

\* 🎛️ \*\*实时参数重置\*\*：支持基于当前会话实时调整 System Prompt、Temperature 随机性及加载的模型版本。

\* 🔄 \*\*多版本追踪与重生成\*\*：支持单节点历史回答折叠收起、一键复制代码块与按需重新生成。



\---



\## 🏗️ 系统架构



```text

┌─────────────────────────────────────────────────────────────┐

│                      前端 (index.html)                       │

│     (State Management / UI Component / Math \& MD Render)    │

└──────────────┬──────────────────────────────▲───────────────┘

&#x20;              │                              │

&#x20;              │ HTTP / SSE                   │ JSON / Stream

&#x20;              ▼                              │

┌─────────────────────────────────────────────────────────────┐

│                      后端 (app.py)                           │

│        (Flask Proxy / Stream Forwarder / API Engine)        │

└──────────────┬──────────────────────────────┬───────────────┘

&#x20;              │                            

&#x20;              ▼ HTTP                       

┌─────────────────────────────┐

│   LM Studio (Port 1234)     ││   (Local LLM Inference)     │

└─────────────────────────────┘



```



\---



\## 🛠️ 前置要求



1\. \*\*Python 3.10+\*\* 环境。

2\. \*\*\[LM Studio](https://lmstudio.ai/)\*\*：确保已启动 Local Server 并监听在 `\[http://127.0.0.1:1234](http://127.0.0.1:1234)`。




\---



\## 🚀 快速开始



\### 1. 克隆仓库与安装依赖



```bash

git clone https://github.com/你的用户名/你的项目名.git

cd 你的项目名



\# 安装 Python 依赖包

pip install -r requirements.txt



```



\### 2. 环境变量配置 (可选)



复制 `.env.example` 为 `.env` 并根据本地服务修改配置：



```bash

cp .env.example .env



```



\### 3. 启动应用



在开发环境中运行 Flask 后端：



```bash

python app.py



```



终端提示启动成功后，在浏览器访问：

👉 \*\*`\[http://127.0.0.1:5000](http://127.0.0.1:5000)`\*\*

或者：运行image并配置5000端口

\---



\## 📂 项目结构



```text

.

├── app.py                 # Flask 后端服务（处理转发与代理）

├── templates/

│   └── index.html         # 单文件 HTML5 客户端（包含样式与前端逻辑）

├── requirements.txt       # Python 项目依赖清单

├── .env.example           # 环境变量示例文件

├── .gitignore             # Git 忽略配置

├── LICENSE                # 开源协议 (MIT)

└── README.md              # 项目文档



```



\---



\## ⚙️ 生产部署建议



若需将应用部署到公网或局域网供多设备访问：



1\. \*\*替换 WSGI 服务器\*\*（Windows 环境推荐 `waitress`）：

```bash

pip install waitress

waitress-serve --host=0.0.0.0 --port=5000 app:app



```





2\. \*\*端口与网络穿透\*\*：可通过 Cloudflare Tunnel 或 FRP 将 5000 端口映射，配合访问令牌（Token）以保护本地算力资源。



\---



\## 📄 授权协议



本项目基于 \[MIT License](https://www.google.com/search?q=LICENSE) 开源。

