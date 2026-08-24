# ALL_PLANS_INTEGRATED

## 一、项目任务执行规划

# 项目任务执行规划

## 1. 任务目标

- [x] 建立基于 Flask + 原生 HTML/JavaScript + 本地 LM Studio 的本地 AI 聊天 Web 应用。
- [x] 提供移动端优先的聊天界面、多会话历史、参数设置、Markdown/LaTeX 展示和流式回答。
- [x] 通过 Flask 代理 LM Studio OpenAI-compatible API，支持模型列表、文本聊天、SSE 转发和中文 UTF-8 解码。
- [x] 支持联网搜索、搜索结果引用、深层详情页过滤和搜索失败降级。
- [x] 支持图片上传、压缩、预览、剪贴板粘贴、Base64 传输和多模态模型请求。
- [x] 支持用户消息图片缩略图、原图打开/下载，以及 assistant `[image_n]` 图片引用跳转。
- [x] 保持停止生成、上下文隔离、代码展示与运行、会话持久化等现有交互能力。

## 2. 执行步骤拆解

- [x] 初始化 Flask 应用、候选模板目录和本地 LM Studio 配置。
  - 已实现 `GET /` 页面渲染及非 API 404 回退。
  - 已支持 `LM_STUDIO_BASE`、`DEFAULT_MODEL`、`DEFAULT_SYSTEM_PROMPT` 环境变量。
  - 已启用 CORS，并设置 12MB 请求体上限和 413 错误提示。
- [x] 实现模型列表 API 与容错处理。
  - 已实现 `GET /api/models`，规范化 LM Studio 模型响应；服务不可用时返回 `local-model` 占位模型。
- [x] 实现文本聊天和 SSE 流式代理。
  - 已实现消息校验、上下文字符数限制、系统提示词、Temperature 边界、UTF-8 解码、`[DONE]` 和异常处理。
  - 已对图片请求设置连接/读取超时，并在多模态错误时给出视觉输入提示。
- [x] 实现联网搜索和搜索结果引用。
  - 已使用 `ddgs`、代理环境变量、线程池超时、一次重试和安全降级。
  - 已过滤搜索页、分类页、标签页和跳转链接，仅保留深层详情链接。
  - 已实现代码/数学/问答语境控制、搜索结果注入、SSE 状态与 citations 事件、前端来源查看。
- [x] 实现前端聊天布局与交互状态。
  - 已实现响应式布局、历史抽屉、新对话、会话切换/删除、参数设置、Enter 发送、Escape 关闭和加载/停止状态。
  - 已实现消息复制、assistant 重新生成和历史版本折叠展示。
- [x] 实现多会话持久化和上下文管理。
  - 已通过 `localStorage` 保存会话、消息、模型、提示词、Temperature、图片压缩比例和更新时间。
  - 已恢复历史会话、按更新时间排序、过滤 `excludeFromContext`，并维护 `turnId`、版本和 citations 元数据。
- [x] 实现 Markdown、代码高亮、公式和代码运行展示。
  - 已使用 marked.js、KaTeX auto-render、highlight.js；支持代码复制以及 JavaScript/HTML/XML 沙箱运行。
- [x] 实现图片输入和多模态消息处理。
  - 已支持图片选择、压缩、预览、移除、剪贴板粘贴和 `data:image/...` Base64 转换。
  - 已通过 `image_base64` 构造 OpenAI-compatible `text + image_url` 消息，并按会话保留 `image_1`、`image_2` 等编号。
  - 已改为记录请求摘要而非完整 Base64，并避免最终回复前强制执行额外视觉识别。
- [x] 实现图片展示和图片引用跳转。
  - 已在用户气泡顶部显示可点击缩略图，支持新标签页打开和下载保存。
  - 已将 assistant 的 `[image_n]` 转换为对应图片链接，并兼容历史消息和流式更新。
- [x] 实现停止生成和错误反馈。
  - 已通过 `AbortController` 停止请求、保留半截回答、追加停止标记并隔离停止轮次上下文。
  - 已解析 SSE 的 `error/detail` 并显示系统错误气泡。
- [x] 完成基础语法和结构验证。
  - 已通过 `python -m py_compile WebProject1/app.py`、Node `--check` 和后端多模态消息结构验证。
- [ ] 补充项目依赖清单和版本锁定文件。
- [ ] 增加后端单元测试、SSE 转发测试、前端上下文过滤测试和多模态回归测试。
- [ ] 增强后端消息角色/content 规范化和未知字段校验。
- [ ] 完善浏览器断开后的上游 LM Studio 请求取消策略。
- [ ] 评估公网部署时的鉴权、日志脱敏、生产模式和访问控制。

## 3. 变更日志

- [2026-08-15/项目现状整理]: 根据当前 `WebProject1/app.py`、`templates/index.html`、项目配置和交互文档，建立项目功能与完成状态清单，并覆盖本文件。
- [2026-08-15/后端能力]: 记录 Flask 页面/API、LM Studio 模型查询、SSE 流式代理、联网搜索、深层过滤、请求限制和多模态图片处理。
- [2026-08-15/前端能力]: 记录多会话持久化、参数设置、Markdown/KaTeX、代码高亮运行、图片上传压缩预览、图片引用跳转和停止生成逻辑。
- [2026-08-15/后续事项]: 保留依赖清单、自动化测试、输入校验、断开取消和公网安全等尚未实现的改进项。
- [2026-08-15/上下文 Token 用量]: 在 `templates/index.html` 增加默认 8192 的最大上下文配置、轻量 Token 估算、动态百分比进度条及会话切换/SSE 完成时刷新逻辑，并兼容旧会话数据。
- [2026-08-15/模型动态 Max Tokens]: 在 `WebProject1/app.py` 增加 `/api/model-info`，从 LM Studio 模型元数据读取 `context_length` 等上下文字段并以 8192 兜底；前端新增模型切换同步和手动 Override 持久化。
- [2026-08-15/上下文滑动窗口]: 前端改为按 LM Studio 实际 Context Length 的 80% Token 预算倒序保留最新历史，超长最新用户消息按 Token 截断，并让进度条统计实际发送窗口。后端模型信息兼容多种 context length 元数据字段。

---

## 二、上下文交接报告

# WebProject1 项目上下文交接报告

> 生成时间：2026 年
> 适用目录：`C:\Users\Wzm06\source\repos\WebProject1\`
> 文档用途：用于新 AI 对话、开发环境迁移和项目维护交接。

---

## ① 项目概况与技术栈（Overview & Tech Stack）

### 1.1 核心功能与应用场景

WebProject1 是一个本地 AI 对话助手 Web 应用，面向以下场景：

- 通过浏览器访问移动端优先的聊天界面。
- 使用本机 LM Studio 中加载的本地大语言模型进行对话。
- 通过 Flask 后端作为浏览器与 LM Studio OpenAI 兼容 API 之间的代理。
- 支持流式输出，降低长回复等待时间，并避免一次性响应导致的网关超时。
- 在浏览器 `localStorage` 中保存多会话历史，适合个人本地使用。
- 支持 Markdown、代码块和 LaTeX/KaTeX 公式显示。

### 1.2 整体架构

```text
浏览器（templates/index.html）
		│
		│ GET /
		│ GET /api/models
		│ POST /api/chat
		▼
Flask 应用（WebProject1/app.py）
		│
		│ HTTP / SSE 代理
		▼
LM Studio 本地服务（默认 127.0.0.1:1234）
		│
		▼
本地加载的 LLM 模型
```

当前代码中没有实际配置公网映射服务。历史上曾排查过 Cloudflare 524 等公网网关超时问题，但当前仓库内的正式运行路径仍是本机 Flask `127.0.0.1:5000` 加本机 LM Studio `127.0.0.1:1234`。

### 1.3 技术栈

| 层次 | 技术 | 用途 |
|---|---|---|
| 前端页面 | HTML、CSS、原生 JavaScript | 单文件聊天 SPA 和状态管理 |
| Markdown | marked.js CDN | assistant 回复 Markdown 解析 |
| 数学公式 | KaTeX 0.16.9 CDN、auto-render | LaTeX 公式渲染 |
| 后端 | Python 3.x、Flask | 页面服务和 API 代理 |
| 跨域 | flask-cors | Flask 应用启用 CORS |
| HTTP 客户端 | requests、urllib | `requests` 用于流式聊天，`urllib` 用于 JSON 请求和模型查询 |
| 推送协议 | SSE（Server-Sent Events） | LM Studio 流式结果转发到浏览器 |
| 本地存储 | 浏览器 localStorage | 保存会话数组和消息历史 |
| IDE 项目 | Visual Studio Python Web Project | 启动文件、工作目录和浏览器地址配置 |

---

## ② 已实现功能清单（Completed Features）

### 2.1 后端/API

#### `GET /`

- 使用 Flask `render_template("index.html")` 返回前端页面。
- 通过候选模板目录兼容两种目录布局：
  - `WebProject1/templates`
  - 项目上一级的 `templates`
- 非 API 路径的 404 会回退渲染前端页面。

#### `GET /api/models`

- 请求 LM Studio 的 `/v1/models`。
- 支持从响应的 `data` 数组中提取模型 `id`，也兼容 `name` 字段。
- 失败时返回可供前端继续工作的占位模型：

```json
[{"id": "local-model"}]
```

#### `POST /api/chat`

- 接收前端 JSON：
  - `messages`
  - `system_prompt`
  - `temperature`
  - `model`
- 校验 `messages` 必须为数组。
- 将系统提示词放在消息列表最前面。
- 将 temperature 转为浮点数，并限制在 `0.0` 到 `1.0`。
- 调用 LM Studio OpenAI 兼容接口：
  - 默认地址：`http://127.0.0.1:1234/v1/chat/completions`
- 向 LM Studio 请求 `stream: true`。
- 使用 `requests.post(..., stream=True, timeout=120)` 转发响应。
- 逐行读取 LM Studio SSE/兼容流式响应，并重新包装为浏览器可读取的 SSE。
- 对原始 bytes 使用 UTF-8 解码并设置 `errors="replace"`，避免中文流式输出乱码。
- 最终发送 `data: [DONE]`。
- 后端返回类型显式设置为：

```text
text/event-stream; charset=utf-8
```

#### 错误处理

- API 404 返回可读 JSON。
- 捕获 LM Studio HTTP 错误、连接错误、超时和一般异常。
- 前端可读取 `error`、`detail` 等字段显示中文错误信息。
- 常见错误包括：无法连接本地 LM Studio、接口 404、请求超时和后端处理失败。

### 2.2 前端/UI

#### 页面布局和响应式设计

- 移动端优先的单页面布局。
- 固定顶部导航栏、滚动聊天区和固定底部输入区。
- 顶部包含：历史、新对话、参数设置。
- 宽屏时聊天主轴最大宽度为 `1200px` 并居中。
- assistant 气泡使用全宽布局，便于阅读长公式和代码。
- 顶栏按钮统一高度，避免中文按钮折叠变形。
- 使用安全区环境变量适配移动端刘海屏和底部手势区域。

#### 多会话和持久化

- localStorage 键名：`ai_chat_sessions`。
- 支持创建、切换和删除会话。
- 会话包含：
  - `id`
  - `title`
  - `messages`
  - `system_prompt`
  - `temperature`
  - `model`
  - `updatedAt`
- 页面刷新后恢复会话、消息和参数。
- 历史抽屉按更新时间倒序显示。

#### 流式聊天

- 使用 `fetch('/api/chat')` 发起 POST 请求。
- 使用 `ReadableStream` 和 `getReader()` 读取 SSE。
- 使用 `TextDecoder('utf-8')` 的流式模式解决中文 UTF-8 多字节截断问题。
- 使用行缓冲解析 `data:` 内容。
- 每收到一段 assistant 内容就更新当前气泡。
- 流式结束后持久化完整 assistant 消息。

#### 停止生成和上下文隔离

- 发送按钮在生成期间变为“⏹️ 停止”。
- 点击停止调用 `AbortController.abort()`。
- 停止时保留已经生成的半截回复。
- assistant 回复末尾追加：

```markdown
*[已停止生成]*
```

- 被停止轮次的用户消息和 assistant 消息都设置：

```json
{"excludeFromContext": true}
```

- 后续请求发送前过滤所有 `excludeFromContext` 消息，只发送 `role` 和 `content`。
- 停止后的消息仍展示在界面并保存到 localStorage，但不会继续影响后续 LM Studio 上下文。

#### Markdown、LaTeX 与 KaTeX

- 使用 marked.js 解析 Markdown。
- 引入 KaTeX 0.16.9 CSS、核心脚本和 auto-render 脚本。
- 对 LaTeX 公式片段进行占位保护，减少 marked 对反斜杠和下划线的破坏。
- 支持常见分隔符：
  - `$...$`
  - `$$...$$`
  - `\(...\)`
  - `\[...\]`
- `renderMathInElement` 配置 `throwOnError: false`，流式接收半截公式时不会阻断整个气泡更新。
- 历史消息渲染、正常 assistant 消息和 SSE 流式更新都调用统一公式渲染入口。

#### 参数设置

- 模型下拉选择。
- 系统提示词编辑。
- Temperature 滑块，范围 `0` 到 `1`，步长 `0.1`。
- 参数按会话保存。

#### 错误和交互状态

- 请求失败时删除空 assistant 气泡并显示系统错误气泡。
- 发送期间禁用新建会话、历史和设置按钮。
- 支持 Enter 发送、Shift+Enter 换行。
- 支持 Escape 关闭设置和历史抽屉。

> 当前代码中没有发现已实现的一键复制或重新生成功能，因此这两项不应被视为已完成特性。

---

## ③ 文件结构与关键指令约束（Project Structure & Rules）

### 3.1 核心文件结构

```text
WebProject1/
├─ WebProject1.slnx
├─ PROJECT_HANDOFF.md                 # 本交接报告
├─ templates/
│  └─ index.html                       # 单文件前端页面、CSS、JavaScript
└─ WebProject1/
   ├─ app.py                           # Flask 后端和 LM Studio 代理
   ├─ WebProject1.pyproj               # Visual Studio Python Web 项目配置
   ├─ WebProject1.pyproj.user          # Visual Studio 用户调试状态
   └─ .github/
	  └─ copilot-instructions.md       # 增量修改和最小干预规范
```

此外存在 `__pycache__`、`obj` 等 Python/Visual Studio 生成的缓存或构建产物，不属于手工维护的运行源文件。

### 3.2 `app.py` 职责

- 定义 Flask 应用和模板目录。
- 定义 LM Studio 地址、默认模型和默认系统提示词。
- 实现 `/`、`/api/models`、`/api/chat`。
- 负责请求参数处理、LM Studio 调用、SSE 转发和错误转换。
- 支持通过环境变量覆盖：
  - `LM_STUDIO_BASE`
  - `DEFAULT_MODEL`
  - `DEFAULT_SYSTEM_PROMPT`

### 3.3 `templates/index.html` 职责

- 包含完整 HTML、CSS 和原生 JavaScript。
- 管理 DOM、会话数组、当前会话、发送状态和 AbortController。
- 处理 localStorage、历史抽屉、设置弹窗、SSE 解码和 Markdown/KaTeX 渲染。

### 3.4 强制开发约束

这些约束来自 `.github/copilot-instructions.md`：

1. **最小干预原则**
   - 禁止无必要的整体重构。
   - 保留现有 HTML 主结构、CSS 根变量和顶层容器布局。
2. **定位修改**
   - 只修改本次需求涉及的局部 CSS、DOM 或 JavaScript 函数。
   - 新功能优先通过增量逻辑或独立辅助函数实现。
3. **不得破坏已有状态逻辑**
   - 不得擅自删除或重命名全局变量、初始化函数、localStorage 逻辑和后端路由。
4. **样式隔离**
   - 不得随意重置 `body`、`*`、全局 CSS 变量或原有盒模型。
   - 新增样式使用局部选择器、独立类名或必要的高优先级规则，避免污染现有组件。
5. **保持未涉及代码原貌**
   - 不做无意义的缩进重排、清理或结构重构。
6. **完整回归**
   - 修改后必须保留原有布局、事件监听和交互功能。
   - 前端改动至少进行 JavaScript 语法检查；后端改动至少运行 Python 编译检查。

### 3.5 当前路径和目录注意事项

- 当前实际模板位于项目根目录：`templates/index.html`。
- 后端位于：`WebProject1/app.py`。
- `app.py` 使用候选模板目录，因此同时兼容后端目录下的 `templates` 和项目上一级的 `templates`。
- 不要因为 `WebProject1.pyproj` 的项目目录而误将模板路径改成不存在的 `WebProject1/templates`。

### 3.6 当前未发现的项目文件

当前扫描未发现：

- `requirements.txt`
- `pyproject.toml`
- `Pipfile`
- `README.md`
- 独立前端构建配置
- 自动化测试项目
- 公网隧道/映射配置文件

因此依赖安装和测试流程目前主要依赖运行环境，而不是项目清单文件。

---

## ④ 待办事项与下一步计划（Pending Tasks / Roadmap）

以下按优先级排序。内容分为“代码中已明确需要关注的事项”和“工程化建议”，避免把建议误认为已存在故障。

### P0：验证当前关键链路

1. **实机验证 LaTeX 渲染**
	  - 测试 `$\\rightarrow$`、`$\\frac{a}{b}$`、`$$...$$`、`\\(...\\)` 和 `\\[...\\]`。
   - 分别验证新消息、流式消息、刷新后的历史消息。
   - 观察 marked 公式保护占位符在列表、代码块和表格中的表现。
2. **验证停止生成隔离**
   - 生成中点击停止。
   - 确认半截 assistant 回复和用户问题均保存。
   - 确认后续 `/api/chat` 请求 payload 不包含 `excludeFromContext` 消息。
3. **验证 LM Studio 兼容性**
   - 确认当前 LM Studio 版本支持 `/v1/models` 和 `/v1/chat/completions`。
   - 确认模型 ID 与前端下拉值一致。

### P1：补充可靠性和安全性

1. **增加后端消息规范化**
   - 当前后端只校验 `messages` 是数组，随后直接拼接到系统消息后发送。

```text
（原文后续内容保持不变）
```

---

## ⑤ 快速运行指南（Quick Run Guide）

### 5.1 必需环境

- Windows。
- Python 3.x；当前开发环境使用 Python 3.13。
- Visual Studio Python Web Project 工具，或可直接使用命令行启动 Flask。
- 已安装 Python 包：
  - `flask`
  - `flask-cors`
  - `requests`
- 浏览器需要能够访问以下 CDN 资源，除非以后改为本地静态资源：
  - marked.js
  - KaTeX CSS
  - KaTeX JS
  - KaTeX auto-render JS

由于仓库没有依赖清单，建议在新环境手动安装：

```powershell
python -m pip install Flask flask-cors requests
```

### 5.2 启动 LM Studio

1. 启动 LM Studio。
2. 加载一个可用模型。
3. 启动本地 OpenAI 兼容服务器。
4. 默认监听：

```text
http://127.0.0.1:1234
```

5. 确认以下接口可访问：

```text
GET  http://127.0.0.1:1234/v1/models
POST http://127.0.0.1:1234/v1/chat/completions
```

如端口不同，可设置环境变量：

```powershell
$env:LM_STUDIO_BASE = "http://127.0.0.1:1234"
```

### 5.3 启动 Flask

从项目根目录执行：

```powershell
python WebProject1/app.py
```

应用默认监听：

```text
http://127.0.0.1:5000/
```

也可以在 Visual Studio 中启动项目。项目配置已经指定：

- 启动文件：`app.py`
- 工作目录：项目配置目录
- 浏览器地址：`http://127.0.0.1:5000/`
- Web launcher：启用

### 5.4 可选环境变量

```powershell
$env:LM_STUDIO_BASE = "http://127.0.0.1:1234"
$env:DEFAULT_MODEL = "local-model"
$env:DEFAULT_SYSTEM_PROMPT = "你是一个严谨的学术与通用助手。"
python WebProject1/app.py
```

### 5.5 基础检查

检查后端语法：

```powershell
python -m py_compile WebProject1/app.py
```

检查页面内联 JavaScript 语法，可使用 PowerShell 提取最后一个内联脚本后运行 Node：

```powershell
$html = Get-Content -Raw 'templates/index.html'
$scripts = [regex]::Matches($html, '<script(?:\s[^>]*)?>([\s\S]*?)</script>') | ForEach-Object { $_.Groups[1].Value } | Where-Object { $_.Trim() }
$scripts[-1] | Set-Content -Encoding utf8 "$env:TEMP\index-inline.js"
node --check "$env:TEMP\index-inline.js"
```

### 5.6 浏览器验证顺序

1. 打开 `http://127.0.0.1:5000/`。
2. 确认模型下拉列表已加载，或显示 `local-model` 占位模型。
3. 发送普通中文消息，确认 SSE 流式输出正常。
4. 输入 Markdown、代码块和 LaTeX 公式，确认渲染正常。
5. 生成中点击“停止”，确认半截消息带有“已停止生成”。
6. 刷新页面，确认会话仍存在。
7. 再次发送消息，确认停止轮次未进入请求上下文。
8. 打开历史抽屉，确认会话切换和删除正常。

---

## 结论

当前项目已经形成“单文件前端 + Flask 代理 + 本地 LM Studio”的可运行原型，核心聊天、流式输出、中文解码、多会话持久化、停止生成隔离、Markdown 和 KaTeX 公式显示均已实现。下一阶段重点应放在实机回归验证、依赖清单、自动化测试、后端输入校验和公网暴露安全性，而不是继续进行大范围结构重构。
