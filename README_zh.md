<div align="center">

# 🌐 Qwen 终端翻译器 (AI Translator)

**基于 Qwen2.5 (3B / 1.5B) 与 llama.cpp 的极速本地 AI 终端翻译工具。**  
*具备 Claude Code CLI 审美、动态多语种 Skill 路由、截图智能 OCR 即贴即译与 1 分钟闲置自动休眠（0 MB 内存常驻）。*

---

[English](README.md) | [简体中文](README_zh.md)

---

</div>

## 🌟 核心亮点

- ⚡ **本地运行 · 隐私安全**：基于底层 C++ 优化推理（`llama.cpp`），100% 运行于本地 CPU/核显/显卡。零 API 费用、零数据上云。
- 🧠 **动态 Skill 专项语种路由**：Python 层毫秒级嗅探源语言，动态注入专属翻译策略（日译中否定防漏、英译中破除从句倒装、中译英主语补齐）。
- 📷 **截图智能 OCR 即译 (`Ctrl+V`)**：按下 `Ctrl+V` 自动捕获剪贴板截图，调用本地 Tesseract 提取文字并保留空间排版，逐行对照翻译。
- 💤 **1 分钟闲置自动休眠（0 MB 内存占用）**：翻译完成后 60 秒无操作，自动释放 1.8GB 模型权重（平时 0 MB 负载）；新任务时 0.3 秒瞬间从固态硬盘唤醒，长文翻译期间具备任务执行锁保护。
- 📋 **自动剪贴板同步**：翻译完毕自动写回系统剪贴板，无缝衔接粘贴使用。
- 🧼 **纯净输出**：上下水平分割线渲染，彻底移除左右竖线 `│` 字符，鼠标划词复制 100% 纯文本无污染。
- 🚀 **一键自动化安装**：内置 TUI 模型多选菜单、国内外镜像智能测速分流、防 Sudo 权限污染与跨平台桌面启动器自动生成。

---

## 🛠️ 快速开始

### 1. 一键自动化安装 (Linux / macOS / Windows WSL)

克隆本仓库并执行安装向导：

```bash
git clone git@github.com:gong0019/ai-translator.git
cd ai-translator
chmod +x install.sh
./install.sh
```

> **`install.sh` 自动完成的工作：**
> 1. 自动探测网络环境，国内自动切换阿里云 PyPI 镜像与 HF-Mirror 高速节点。
> 2. 自动安装系统底层依赖（`tesseract-ocr`、`cmake`、`xclip`/`wl-clipboard`）。
> 3. 初始化隔离的私有虚拟环境（`.venv/`），并使用真实用户权限隔离 Sudo。
> 4. 弹出 TUI 交互式菜单（按 `空格键` 选择下载 3B 推荐高精度 / 1.5B 极速模型）。
> 5. 自动探测系统桌面（Linux 中英文桌面、macOS `~/Desktop`、Windows WSL 宿主桌面）并生成双击图标。
> 6. 可选将 `qwen-trans` 软链接至系统终端 `$PATH`。

---

## 🎮 使用方法与快捷指令

在终端输入 `qwen-trans` 或双击桌面图标即可启动：

```bash
qwen-trans
# 或在项目根目录运行
./run.sh
```

### 终端交互界面

```text
╭───────────────────────────────────────────────────────────────────╮
│  🌐 Qwen Terminal Translator (Skill-Based Architecture)           │
│  Input: 🔍 智能语种嗅探 ➔ Target: 🇨🇳 中文 (Simplified Chinese)     │
│  Model: Qwen2.5-3B (高精度·推荐) | AutoSleep: 1m | AutoCopy: ON   │
╰───────────────────────────────────────────────────────────────────╯
Shortcuts: Ctrl+V (智能粘图/文本) | /lang (语言) | /model (模型) | /sleep | /quit

[auto➔zh] > Missing one day of practice is less discouraging when the goal is to continue over a long period rather than to perform perfectly every day.

──────────────────── Translation ➔ Simplified Chinese ────────────────────
当目标是长期坚持而不是每天都完美表现时，一天不练习并不会让人感到那么沮丧。
─────────────────────────────────── END ──────────────────────────────────
(耗时: 0.42s | 已复制到剪贴板 📋 | 闲置 1 分钟后将自动释放内存)
```

### 斜杠指令 (Slash Commands)

| 指令 | 说明 |
| :--- | :--- |
| **`Ctrl+V`** | **智能粘贴**：剪贴板为图片时自动本地 OCR 排版识别并翻译，为文本时正常粘贴。 |
| **`/lang`** | 切换目标输出语言（1: 中文, 2: 英语, 3: 日语, 4: 韩语, 5: 德语, 6: 法语 等 9 大语种）。 |
| **`/model`** | 实时热切换本地模型（3B 高精度 / 1.5B 极速）。 |
| **`/sleep`** 或 **`/unload`** | 立即手动休眠并释放模型内存（0 MB 占用）。 |
| **`/copy`** | 开启 / 关闭自动同步写入系统剪贴板。 |
| **`/clear`** | 清屏并重新绘制状态栏。 |
| **`/quit`** 或 **`:q`** | 退出程序。 |

---

## 🧩 如何添加自定义模型

你可以下载任何 GGUF 格式的量化大模型（如 Qwen2.5-7B、DeepSeek-R1-Distill-Qwen、Llama-3 等）放入项目中使用：

1. **下载 GGUF 模型文件** 到 `models/` 目录：
   ```bash
   # 示例：下载 Qwen2.5-7B-Instruct GGUF 模型
   wget -c -P models/ "https://hf-mirror.com/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
   ```

2. **在 `translator_cli.py` 中注册模型**：
   打开 `translator_cli.py`，在顶部的 `MODELS` 字典中追加一行配置：
   ```python
   MODELS = {
       "1": ("Qwen2.5-3B (高精度·推荐)", "qwen2.5-3b-instruct-q4_k_m.gguf", 3),
       "2": ("Qwen2.5-1.5B (极速·轻量)", "qwen2.5-1.5b-instruct-q4_k_m.gguf", 1.5),
       "3": ("Qwen2.5-7B (旗舰画质)", "qwen2.5-7b-instruct-q4_k_m.gguf", 7), # <- 在此添加
   }
   ```

3. 启动翻译器并在终端输入 `/model` 即可切换至新模型！

---

## 📝 自定义与优化翻译 Skill

所有的提示词与语种专项规则均已模块化解耦在 `skills/` 目录下：

- `skills/base.md`：通用底座规则（排版结构保留、代码/URL 免翻保护、语义完整性校验）。
- `skills/ja_to_zh.md`：日译中专属 Skill（从句句尾否定防漏、防对比句截半、禁止语义压缩）。
- `skills/en_to_zh.md`：英译中专属 Skill（从句语法重构、时间与条件前置化、消除欧化倒装）。
- `skills/zh_to_en.md`：中译英专属 Skill（主语智能补齐、成语隐喻意译）。

你可以使用任何文本编辑器随时修改 `skills/` 下的 `.md` 文件，**下次翻译时实时热加载生效，无需重启程序**。

---

## 📂 仓库目录结构

```text
ai-translator/
├── install.sh              # 跨平台一键安装脚本
├── run.sh                  # 启动入口（自动加载虚拟环境）
├── requirements.txt        # Python 依赖清单
├── translator_cli.py       # 核心程序（动态加载 skills/*.md）
├── models/                 # 模型存储目录（.gitignore 忽略权重）
│   └── .gitkeep
├── skills/                 # 核心提示词与多语种专项规则库
│   ├── base.md             # 通用底座
│   ├── ja_to_zh.md         # 日译中专项 Skill
│   ├── en_to_zh.md         # 英译中专项 Skill
│   └── zh_to_en.md         # 中译英专项 Skill
├── README.md               # 英文说明文档
├── README_zh.md            # 中文说明文档
└── LICENSE                 # Apache-2.0 开源协议
```

---

## 📄 开源协议

本项目采用 [Apache-2.0](LICENSE) 协议开源。
