
# Local AI Assistant

A lightweight, mobile-first local AI assistant built on **Flask + LM Studio + ComfyUI**. Supports multi-session management, real-time LLM parameter tuning, Markdown/LaTeX rendering, and text-to-video API extensions.

---

## ✨ Core Features

* 🤖 **Seamless Local LLM Integration**: Compatible with LM Studio and standard OpenAI REST API endpoints, supporting Server-Sent Events (SSE) streaming responses with typewriter effects.
* 🎬 **ComfyUI Generative Extensions**: Acts as a control hub for local ComfyUI backends, submitting workflows via API for offline text-to-image/video rendering and real-time status polling.
* 📱 **Mobile-First Design**: Built with fully responsive layouts and native long-screen interactions, featuring gesture-driven sidebars and independent overlays.
* 💾 **Local Offline Persistence**: No remote database required; all session history, parameter configurations, and version histories are securely stored locally via browser `localStorage`.
* 📐 **Markdown & LaTeX Rendering**: Integrated with `marked.js` and `KaTeX` math libraries, providing full support for academic derivations, code syntax highlighting, and formula rendering.
* 🎛️ **Real-Time Parameter Tuning**: Dynamically adjust System Prompts, Temperature (randomness), and active model versions per session on the fly.
* 🔄 **Version Tracking & Regeneration**: Collapse or expand historical responses per node, copy code blocks with one click, and regenerate outputs on demand.

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (index.html)                    │
│     (State Management / UI Component / Math & MD Render)    │
└──────────────┬──────────────────────────────▲───────────────┘
               │                              │
               │ HTTP / SSE                   │ JSON / Stream
               ▼                              │
┌─────────────────────────────────────────────────────────────┐
│                    Backend (app.py)                         │
│         (Flask Proxy / Stream Forwarder / API Engine)       │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼ HTTP                         ▼ HTTP
┌─────────────────────────────┐┌─────────────────────────────┐
│    LM Studio (Port 1234)    ││     ComfyUI (Port 8188)     │
│    (Local LLM Inference)    ││  (Image / Video Generation) │
└─────────────────────────────┘└─────────────────────────────┘

```

---

## 🛠️ Prerequisites

1. **Python 3.10+** environment.
2. **[LM Studio](https://lmstudio.ai/)**: Ensure the Local Server is running and listening on `http://127.0.0.1:1234`.

---

## 🚀 Quick Start

### 1. Clone Repository & Install Dependencies

```bash
git clone [https://github.com/SpaceK-W/Local-AI-Assistant-on-LMstudio.git](https://github.com/SpaceK-W/Local-AI-Assistant-on-LMstudio.git)
cd Local-AI-Assistant-on-LMstudio

# Install Python dependencies
pip install -r requirements.txt

```

### 2. Configure Environment Variables (Optional)

Copy `.env.example` to `.env` and adjust the configurations according to your local services:

```bash
cp .env.example .env

```

### 3. Launch Application

Run the Flask backend in your development environment:

```bash
python app.py

```

Once started successfully, open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**
### Windows 一键启动
下载项目后直接双击根目录下的 `start.bat`，脚本会自动检测环境、创建 `.venv`、安装第三方依赖并打开浏览器页面。
*(Or run via Docker container with port 5000 mapped)*

---

## 📂 Project Structure

```text
.
├── app.py                 # Flask backend service (handles forwarding & proxying)
├── templates/
│   └── index.html         # Single-file HTML5 client (styles & frontend logic)
├── requirements.txt       # Python project dependency list
├── .env.example           # Environment variable example file
├── .gitignore             # Git ignore rules
├── LICENSE                # Open-source license (MIT)
└── README.md              # Project documentation

```

---

## ⚙️ Production Deployment Suggestions

To deploy this application across a local network or public domain for multi-device access:

1. **Replace WSGI Server** (`waitress` recommended on Windows):

```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app

```

2. **Port Forwarding & Tunnels**: Map port 5000 via Cloudflare Tunnel or FRP, protected with access tokens to secure local compute resources.

---

## 📄 License

This project is open-sourced under the [MIT License](https://www.google.com/search?q=LICENSE).

```

```
