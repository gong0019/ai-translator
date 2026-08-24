<div align="center">

# 🌐 Qwen Terminal Translator (AI Translator)

**A lightning-fast, local-first AI terminal translator powered by Qwen2.5 (3B / 1.5B) and llama.cpp.**  
*Featuring Claude Code CLI aesthetic, dynamic multi-language skill routing, instant clipboard OCR, and 1-minute auto-idle memory release (0 MB idle footprint).*

---

[English](README.md) | [简体中文](README_zh.md)

---

</div>

## 🌟 Highlights

- ⚡ **Local & Privacy-First**: 100% runs on your local CPU or GPU using optimized C++ inference (`llama.cpp`). Zero cloud API fees, zero data tracking.
- 🧠 **Dynamic Skill-Based Routing**: Python detects source language instantly and dynamically injects specialized translation rules (e.g., Japanese negation protection, English clause de-inversion, Chinese subject recovery).
- 📷 **Smart Screenshot OCR (`Ctrl+V`)**: Press `Ctrl+V` to automatically capture clipboard images, extract text via local Tesseract OCR while preserving spatial layouts, and translate line-by-line.
- 💤 **1-Minute Auto-Sleep (0 MB Footprint)**: Automatically unloads model weights after 60 seconds of inactivity to keep your system memory clean (0 MB RAM). Instantly wakes up in ~0.3s on new input, with active-lock protection during long text translations.
- 📋 **Auto Clipboard Sync**: Translations are automatically synced to the system clipboard upon completion.
- 🧼 **Clean Output**: Borderless horizontal rule dividers—no side pipe `│` characters. Copy text cleanly without formatting artifacts.
- 🚀 **One-Click Automated Installer & Uninstaller**: Includes TUI model multi-selection, domestic/global mirror routing, anti-sudo permission isolation, and clean uninstallation.

---

## 🛠️ Quick Start

### 1. Automated Installation (Linux / macOS / Windows WSL)

Clone the repository and run the automated installer:

```bash
git clone git@github.com:gong0019/ai-translator.git
cd ai-translator
chmod +x install.sh
./install.sh
```

> **What `install.sh` does automatically:**
> 1. Detects network region and auto-switches between global PyPI/HuggingFace and domestic mirrors (Aliyun / HF-Mirror).
> 2. Installs required system packages (`tesseract-ocr`, `cmake`, `xclip`/`wl-clipboard`).
> 3. Sets up an isolated Python virtual environment (`.venv/`) with anti-sudo privilege separation.
> 4. Launches an interactive TUI checklist for model selection (`[Space]` to select, `[Enter]` to confirm).
> 5. Detects your OS desktop directory (`~/Desktop`, `~/桌面`, Windows WSL desktop) and creates double-clickable launchers.
> 6. Optionally adds `qwen-trans` to your system terminal `$PATH`.

### 2. Clean Uninstallation

To remove desktop shortcuts, global commands, and virtual environments:

```bash
chmod +x uninstall.sh
./uninstall.sh
```

---

## 🎮 Usage & Commands

Start the translator from anywhere:

```bash
qwen-trans
# or directly run
./run.sh
```

### Interactive CLI Interface

```text
╭───────────────────────────────────────────────────────────────────╮
│  🌐 Qwen Terminal Translator (Skill-Based Architecture)           │
│  Input: 🔍 Auto Language Sniffer ➔ Target: 🇨🇳 Simplified Chinese  │
│  Model: Qwen2.5-3B (High Accuracy) | AutoSleep: 1m | AutoCopy: ON │
╰───────────────────────────────────────────────────────────────────╯
Shortcuts: Ctrl+V (Smart Image/Text Paste) | /lang | /model | /sleep | /copy | /quit

[auto➔zh] > Missing one day of practice is less discouraging when the goal is to continue over a long period rather than to perform perfectly every day.

──────────────────── Translation ➔ Simplified Chinese ────────────────────
当目标是长期坚持而不是每天都完美表现时，一天不练习并不会让人感到那么沮丧。
─────────────────────────────────── END ──────────────────────────────────
(Elapsed: 0.42s | Copied to clipboard 📋 | Auto-sleeps in 1 min)
```

### Slash Commands

| Command | Action |
| :--- | :--- |
| **`Ctrl+V`** | **Smart Paste**: Automatically extracts image text via OCR if clipboard contains a screenshot; pastes text otherwise. |
| **`/lang`** | Change target language (1: Chinese, 2: English, 3: Japanese, 4: Korean, 5: German, 6: French, etc.). |
| **`/model`** | Hot-switch between local models (e.g. `3B` High-Accuracy vs `1.5B` Fast). |
| **`/sleep`** or **`/unload`** | Manually unload model from RAM immediately (0 MB memory). |
| **`/copy`** | Toggle auto-syncing translation results to system clipboard. |
| **`/clear`** | Clear terminal screen and redraw status header. |
| **`/quit`** or **`:q`** | Exit the program. |

---

## 🧩 How to Add Custom Models

You can download any GGUF quantized model (e.g., Qwen2.5-7B, DeepSeek-R1-Distill-Qwen, Llama-3.1) and use it with the translator.

1. **Download GGUF model** into the `models/` directory:
   ```bash
   # Example: Download Qwen2.5-7B-Instruct GGUF
   wget -c -P models/ "https://hf-mirror.com/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
   ```

2. **Register the model** in `translator_cli.py`:
   Open `translator_cli.py` and add your model to the `MODELS` dictionary:
   ```python
   MODELS = {
       "1": ("Qwen2.5-3B (Recommended)", "qwen2.5-3b-instruct-q4_k_m.gguf", 3),
       "2": ("Qwen2.5-1.5B (Lightweight)", "qwen2.5-1.5b-instruct-q4_k_m.gguf", 1.5),
       "3": ("Qwen2.5-7B (Flagship Quality)", "qwen2.5-7b-instruct-q4_k_m.gguf", 7), # <- Add here
   }
   ```

3. Launch the translator and type `/model` to switch to your new model!

---

## 📝 Customizing Translation Skills

Prompts and linguistic rules are modularized as standalone Markdown files under `skills/`:

- `skills/base.md`: Universal base prompt (format preservation, URL protection, translatables).
- `skills/ja_to_zh.md`: Japanese-to-Chinese skill (negation preservation, anti-semantic compression, SOV restructuring).
- `skills/en_to_zh.md`: English-to-Chinese skill (clause restructuring, temporal/conditional pre-positioning).
- `skills/zh_to_en.md`: Chinese-to-English skill (subject recovery, idiom meaning adaptation).

You can edit any `.md` file in `skills/` directly with your preferred editor. Changes take effect on the very next translation without restarting the program.

---

## 📂 Project Structure

```text
ai-translator/
├── install.sh              # Cross-platform automated installer
├── uninstall.sh            # Clean uninstaller (removes shortcuts, venv, cache)
├── run.sh                  # Application launcher (.venv aware)
├── run.bat                 # Windows native launcher
├── requirements.txt        # Python dependency manifest
├── translator_cli.py       # Core CLI application
├── models/                 # Model storage (.gguf files, ignored by git)
│   └── .gitkeep
├── skills/                 # Dynamic linguistic rule prompts
│   ├── base.md             # Base translation rules
│   ├── ja_to_zh.md         # Japanese -> Chinese skill
│   ├── en_to_zh.md         # English -> Chinese skill
│   └── zh_to_en.md         # Chinese -> English skill
├── README.md               # English documentation
├── README_zh.md            # Chinese documentation
└── LICENSE                 # Apache-2.0 license
```

---

## 📄 License

This project is licensed under the [Apache-2.0 License](LICENSE).
