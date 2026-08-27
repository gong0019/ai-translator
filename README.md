<div align="center">

# 🌐 AI Terminal Translator (AI 终端翻译器)

**A lightning-fast, local-first universal AI terminal translator powered by llama.cpp and any GGUF model (Qwen2.5, DeepSeek-R1, Llama-3.2, Mistral, etc.).**  
*Featuring Claude Code CLI aesthetic, dynamic multi-language skill routing, instant clipboard OCR, dynamic model auto-discovery, and 1-minute auto-idle memory release (0 MB idle footprint).*

---

[English](README.md) | [简体中文](README_zh.md)

---

</div>

## 🌟 Highlights

- ⚡ **Local & Privacy-First**: 100% runs on your local CPU or GPU using optimized C++ inference (`llama.cpp`). Zero cloud API fees, zero data tracking.
- 🧩 **Universal GGUF Engine**: Auto-discovers and hot-switches between **any GGUF model** (Qwen2.5, DeepSeek, Llama-3, Gemma-2, Mistral) simply by dropping them into `models/`.
- 🧠 **Document-Aware News Translation**: Uses compact language skills, a shared document glossary, paragraph-safe chunking, truncation confirmation, and targeted retry of only the defective chunk.
- 📷 **Smart Screenshot OCR (`Ctrl+V`)**: Press `Ctrl+V` to automatically capture clipboard images, detect the page script with Tesseract and load only the matching language packs, extract text while preserving spatial layouts, and translate line-by-line.
- 💤 **1-Minute Auto-Sleep (0 MB Footprint)**: Automatically unloads model weights after 60 seconds of inactivity to keep your system memory clean (0 MB RAM). Instantly wakes up in ~0.3s on new input, with active-lock protection during long text translations.
- 📋 **Clipboard-Friendly Input**: `Ctrl+V` pastes text normally or detects clipboard images for local OCR. Translation output is not copied automatically.
- 🧼 **Clean Output**: Borderless horizontal rule dividers—no side pipe `│` characters. Copy text cleanly without formatting artifacts.
- 🚀 **One-Click Automated Installer & Uninstaller**: Includes TUI model selection, domestic/global mirror routing, anti-sudo permission isolation, and clean uninstallation.

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
> 1. Lets you choose **Global Direct**, **China Mirrors**, or **Auto Detect** for both Python packages and model downloads. Installer downloads ignore stale local proxy variables.
> 2. Installs required system packages (`tesseract-ocr`, `cmake`, `xclip`/`wl-clipboard`).
> 3. Sets up an isolated Python virtual environment (`.venv/`) with anti-sudo privilege separation.
> 4. Supports comma-separated multi-selection of Qwen2.5 1.5B/3B/7B and Tencent Hy-MT2-1.8B, with either resumable installer download or link-only manual download.
> 5. Validates the selected source and remote file identity before resuming. If the source changes, stale partial data is discarded instead of being mixed with the new download.
> 6. Creates a native macOS `.app` launcher with icon, a Linux `.desktop` launcher with icon, or the Windows/WSL launcher as appropriate.
> 7. Adds `ai-trans` (and `qwen-trans`) to your system terminal `$PATH`.

The selected source controls Python packages and model files. Homebrew, APT, DNF, and Pacman continue to use the repositories configured on the operating system; on macOS, Homebrew is not invoked when all required commands and language packs are already installed.

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
ai-trans
# or
qwen-trans
# or directly run
./run.sh
```

### Interactive CLI Interface

```text
╭───────────────────────────────────────────────────────────────────────╮
│  🌐 AI Terminal Translator (Universal GGUF Engine)                    │
│  Input: 🔍 Auto Language Sniffer ➔ Target: 🇨🇳 Simplified Chinese      │
│  Model: Qwen2.5 3B (Q4_K_M) [2.0GB] | AutoSleep: 1m                   │
╰───────────────────────────────────────────────────────────────────────╯
Shortcuts: Ctrl+V (Smart Image/Text Paste) | /lang | /model | /sleep | /quit

[auto➔zh] > Missing one day of practice is less discouraging when the goal is to continue over a long period rather than to perform perfectly every day.

──────────────────── Translation ➔ Simplified Chinese ────────────────────
当目标是长期坚持而不是每天都完美表现时，一天不练习并不会让人感到那么沮丧。
─────────────────────────────────── END ──────────────────────────────────
(Elapsed: 0.42s | Auto-sleeps in 1 min)
```

### Slash Commands

| Command | Action |
| :--- | :--- |
| **`Ctrl+V`** | **Smart Paste**: Automatically extracts image text via OCR if clipboard contains a screenshot; pastes text otherwise. |
| **`/lang`** | Change target language (1: Chinese, 2: English, 3: Japanese, 4: Korean, 5: German, 6: French, etc.). |
| **`/model`** | **Hot-switch Models**: Re-scans `models/` every time and lists all complete GGUF files. In-progress downloads are hidden until complete. |
| **`/sleep`** or **`/unload`** | Manually unload model from RAM immediately (0 MB memory). |
| **`/clear`** | Clear terminal screen and redraw status header. |
| **`/quit`** or **`:q`** | Exit the program. |

---

## 🧩 How to Add Any Custom Model (Zero-Code Dynamic Discovery)

This tool supports **any GGUF quantized model** (Qwen, DeepSeek-R1, Llama-3, Gemma-2, Mistral, etc.).

1. **Simply download any `.gguf` file** into the `models/` directory:
   ```bash
   # Example: Download DeepSeek-R1-Distill-Qwen-7B
   wget -c -P models/ "https://hf-mirror.com/bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"

   # Or download Llama-3.2-3B
   wget -c -P models/ "https://hf-mirror.com/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
   ```

2. **That's it!** Launch the translator and type **`/model`**—the new model will be automatically discovered and listed for one-click switching!

---

## 📝 Customizing Translation Skills

Prompts and linguistic rules are modularized as standalone files under `skills/`:

- `skills/base.md`: The shared contract carrying coverage, structure, terminology, and output rules for every language pair. Pair files keep only their own grammar, instead of 23 copies of the same boilerplate.
- `skills/ja_to_zh.md`: Japanese-to-Chinese grammar (sentence-final negation, both sides of a contrast, omitted-subject recovery).
- `skills/en_to_zh.md`: English-to-Chinese grammar (modifier splitting to avoid stacked 的, adverbial fronting, agentless passive to active, denominalization, pronoun dropping, long-sentence splitting, magnitude and date conversion).
- `skills/zh_to_en.md`: Chinese-to-English grammar (subject recovery, run-on splitting, topic-comment recasting, 了/着/过 to tense-aspect, category-noun deletion, idiom rendering, 万/亿 arithmetic conversion, article and number choice, measure-word constructions).
- `skills/news_terms.json`: Curated news proper nouns in a nine-language bidirectional format (en/zh/ja/ko/de/fr/es/ru/it), usable by any pair. It holds only names with a single standard rendering: curated entries are enforced, so an ambiguous common noun would trigger false repairs.
- `skills/finance_terms.json`, `stocks_terms.json`, `tech_terms.json`, `blockchain_terms.json`: Finance, equity, computing, and blockchain terminology. The runtime selects only terms that occur in the document; ambiguous blockchain words require a blockchain context marker.
- `skills/crossborder_ecommerce_terms.json`, `trade_terms.json`: Marketplace-operations and international-trade terminology, including fulfilment, bills of lading, Incoterms®, customs declarations, and HS codes.
- `skills/hardware_terms.json`, `materials_terms.json`: Hardware/manufacturing and polymer/packaging terminology, including air/water cooling, PCB/PCBA, PP, PE, PET, PVC, ABS, PC, and PA. Context markers prevent generic uses from forcing a specialist translation.

The source and maintenance policy for these catalogs is documented in [`After editing a catalogue, run `python3 scripts/build_comprehensive_terms.py` to check required languages and duplicate source terms. The maintenance scripts merge new records and keep existing source terms; read the terminology sources document before running them.

docs/terminology-sources.md`](docs/terminology-sources.md).

You can edit any `.md` file in `skills/` directly with your preferred editor. Changes take effect on the very next translation without restarting the program.

### Translation Quality Validation

For news and other multi-paragraph input, every paragraph is translated, checked, and displayed before the next one begins. A paragraph over the source-token limit is split at sentence boundaries first, then at safe token boundaries if needed. A document glossary is planned once and shared across every chunk; full personal names also create surname aliases for later paragraphs. The translator detects accidental large-scale reuse of the preceding translation and retries only the current chunk. It also detects likely truncated input and asks for confirmation instead of silently inventing an ending.

Each response is checked for observable defects such as omitted structure, changed quantities, missing terms, and inappropriate source-language residue. Only a defective chunk is retried, at most once and at temperature `0.0`. The final translation is always shown; validator codes and review warnings stay out of normal terminal output. These safeguards improve accuracy but may make long-document translation roughly 1.5–2× slower, and they cannot mathematically prove semantic equivalence.

Configure the behavior in `config.json` or `~/.config/ai-translator/config.json`:

```json
{
  "quality_validation": true,
  "quality_retry_limit": 1,
  "repeat_penalty_latin": 1.02,
  "adaptive_quality_mode": true,
  "adaptive_quality_min_chunks": 5
}
```

`quality_validation` accepts only `true` or `false`. `quality_retry_limit` accepts only `0` or `1`. Invalid values resolve to `true` and `1`. Automatic clipboard copying remains disabled.

`retry_max_source_tokens` limits repairs to units no larger than this, since a repair is a second full generation and the number check is least reliable on number-dense text. Default 800.

With `adaptive_quality_mode` on, a document of at least `adaptive_quality_min_chunks` units is redone only for objective defects — empty output, truncation, lost structure, changed numbers, or a repeated chunk. Short text keeps strict retries. Residue and glossary misses are excluded because in testing they almost always flagged correct text: brand names, acronyms, statistical notation, units.

Generation is bounded by the source it translates (about 1.8x the source tokens) rather than always using `max_tokens`. Terminology planning runs only when the document splits into more than one unit — its sole purpose is holding one rendering steady across separate calls.

`repeat_penalty_latin` applies only when the target is English, German, French, Spanish, Italian, or Russian. Those languages build sentences by repeating function words such as `the`, `of`, and `a`, and the main `repeat_penalty` of 1.08 pushes the model to drop articles and prepositions. Chinese, Japanese, and Korean targets keep 1.08. A lower configured value is never raised.

The config file accepts only keys the program knows; stale keys are dropped on the next save.

---

## 📂 Project Structure

```text
ai-translator/
├── install.sh              # Cross-platform automated installer
├── uninstall.sh            # Clean uninstaller (removes shortcuts, venv, cache)
├── run.sh                  # Application launcher (.venv aware)
├── run.bat                 # Windows native launcher
├── requirements.txt        # Python dependency manifest
├── translator_cli.py       # Core CLI application (Universal GGUF)
├── document_translation.py # Document glossary, truncation check, paragraph chunk planning
├── translation_quality.py  # Deterministic quality validation and one-retry policy
├── assets/icons/           # macOS ICNS and cross-platform PNG launcher icons
├── models/                 # Dynamic model storage (drop any .gguf file here)
│   └── .gitkeep
├── skills/                 # Dynamic linguistic rule prompts
│   ├── base.md             # Base translation rules
│   ├── ja_to_zh.md         # Japanese -> Chinese skill
│   ├── en_to_zh.md         # English -> Chinese skill
│   ├── zh_to_en.md         # Chinese -> English skill
│   └── news_terms.json     # Curated news terminology
├── docs/terminology-sources.md # Public terminology references and contribution format
├── README.md               # English documentation
├── README_zh.md            # Chinese documentation
└── LICENSE                 # Apache-2.0 license
```

---

## 📄 License

This project is licensed under the [Apache-2.0 License](LICENSE).
