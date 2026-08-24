#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Terminal Translator (Claude Code CLI Aesthetic)
Powered by Universal GGUF Engine (Qwen2.5, DeepSeek, Llama, Mistral, etc.) via llama.cpp
Architecture: Fast Multi-Language Sniffer + Modular File-based Skill Routing (skills/*.md)
Features: 24 Specialized Linguistic Skills, Chinglish/Mixed Text Auto-Purifier, Physical CPU Thread Optimizer
"""

import os
import re
import sys
import time
import json
import gc
import glob
import tempfile
import threading
import subprocess
import pyperclip
from PIL import Image, ImageGrab
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from llama_cpp import Llama
from translation_quality import (
    CompletionResult,
    normalize_quality_settings,
    normalize_source_structure,
    run_quality_checked_completion,
)

console = Console()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
MODELS_DIR = os.path.join(BASE_DIR, "models")
TEMP_DIR = tempfile.gettempdir()
CLIPBOARD_OCR_PATH = os.path.join(TEMP_DIR, "ai_translator_clipboard_ocr.png")

USER_CONFIG_DIR = os.path.expanduser("~/.config/ai-translator") if os.name != 'nt' else os.path.join(os.environ.get('APPDATA', BASE_DIR), "ai-translator")
USER_CONFIG_FILE = os.path.join(USER_CONFIG_DIR, "config.json")
LOCAL_CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# 9 大支持语种定义
LANGUAGES = {
    "1": {"zh": "中文", "en": "Simplified Chinese (简体中文)", "code": "zh", "flag": "🇨🇳", "ocr": "chi_sim"},
    "2": {"zh": "英语", "en": "English", "code": "en", "flag": "🇬🇧", "ocr": "eng"},
    "3": {"zh": "日语", "en": "Japanese (日本語)", "code": "ja", "flag": "🇯🇵", "ocr": "jpn"},
    "4": {"zh": "韩语", "en": "Korean (한국어)", "code": "ko", "flag": "🇰🇷", "ocr": "kor"},
    "5": {"zh": "德语", "en": "German (Deutsch)", "code": "de", "flag": "🇩🇪", "ocr": "deu"},
    "6": {"zh": "法语", "en": "French (Français)", "code": "fr", "flag": "🇫🇷", "ocr": "fra"},
    "7": {"zh": "西班牙语", "en": "Spanish (Español)", "code": "es", "flag": "🇪🇸", "ocr": "spa"},
    "8": {"zh": "俄语", "en": "Russian (Русский язык)", "code": "ru", "flag": "🇷🇺", "ocr": "rus"},
    "9": {"zh": "意大利语", "en": "Italian (Italiano)", "code": "it", "flag": "🇮🇹", "ocr": "ita"},
}

CODE_TO_LANG = {v["code"]: v for v in LANGUAGES.values()}

LATIN_STOPWORDS = {
    "en": {"the", "is", "this", "that", "are", "was", "were", "for", "with", "have", "has", "not", "you", "all", "any", "can", "will", "an", "a", "in", "on", "at", "to", "from", "by", "about", "as", "into", "like", "through", "after", "over", "between", "out", "against", "during", "without", "before", "under", "around", "among", "people", "often", "believe", "when", "more", "less"},
    "de": {"der", "die", "das", "und", "in", "den", "von", "zu", "mit", "ist", "im", "für", "nicht", "ein", "eine", "als", "auch", "es", "an", "werden", "aus", "er", "hat", "dass", "sie", "nach", "wird", "bei", "einer", "um", "am", "sind", "noch", "wie", "einem", "über", "einen", "war", "haben", "nur", "oder", "aber"},
    "fr": {"le", "la", "les", "de", "des", "un", "une", "du", "et", "en", "dans", "qui", "que", "est", "pour", "pas", "sur", "ce", "il", "sont", "avec", "au", "plus", "par", "je", "son", "ne", "se", "comme", "aux", "nous", "sa", "mais", "ou", "vous", "leur", "ils", "c'est", "d'un"},
    "es": {"el", "la", "los", "las", "un", "una", "de", "del", "y", "en", "que", "es", "por", "para", "con", "no", "su", "al", "lo", "como", "más", "pero", "sus", "le", "ya", "o", "fue", "este", "ha", "si", "sí", "porque", "esta", "son", "entre", "cuando"},
    "it": {"il", "la", "lo", "i", "gli", "le", "un", "uno", "una", "di", "del", "della", "dei", "delle", "e", "ed", "in", "nel", "nella", "a", "al", "alla", "per", "con", "da", "su", "non", "che", "è", "sono", "si", "come", "io", "questo", "questa", "più", "anche", "ma", "se"}
}

DEFAULT_CONFIG = {
    "target_lang_key": "1",
    "selected_model_filename": "",
    "idle_timeout": 60,
    "n_ctx": 8192,
    "temperature": 0.1,
    "repeat_penalty": 1.08,
    "max_tokens": 4096,
    "quality_validation": True,
    "quality_retry_limit": 1,
}

def get_optimal_threads():
    """获取最适合矩阵计算的物理核心数（避免超线程 L1/L2 缓存抖动）"""
    count = os.cpu_count() or 4
    if count >= 8:
        return count // 2
    elif count >= 4:
        return 4
    return count

def load_skill(skill_name: str) -> str:
    """从 skills/ 目录动态读取单独的 skill markdown 文件"""
    skill_file = os.path.join(SKILLS_DIR, f"{skill_name}.md")
    if os.path.exists(skill_file):
        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""

def detect_language(text: str):
    """通过字符集 + 词频投票高效嗅探源语言 (Python 确定性路由层)"""
    chinese_chars = len(re.findall(r'[\u4E00-\u9FFF]', text))
    kana_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', text))
    hangul_chars = len(re.findall(r'[\uAC00-\uD7AF\u1100-\u11FF]', text))
    cyrillic_chars = len(re.findall(r'[\u0400-\u04FF]', text))
    eng_words = re.findall(r'[a-zA-Z]{2,}', text)

    # 1. 混合句判定 (以中文为基础主干，夹杂了英文单词、日文词汇/假名或韩文)
    if chinese_chars > 0 and (len(eng_words) > 0 or (kana_chars > 0 and chinese_chars >= kana_chars)):
        return "mixed", "Mixed / Chinglish"

    # 2. 独立字符集特征 (日、韩、俄)
    if kana_chars > 0:
        return "ja", CODE_TO_LANG["ja"]["en"]
    if hangul_chars > 0:
        return "ko", CODE_TO_LANG["ko"]["en"]
    if cyrillic_chars > 0:
        return "ru", CODE_TO_LANG["ru"]["en"]

    # 3. 纯中文
    if chinese_chars > 0:
        return "zh", CODE_TO_LANG["zh"]["en"]
    
    # 4. 特殊变音/符号特征
    if re.search(r'[äöüßÄÖÜ]', text):
        return "de", CODE_TO_LANG["de"]["en"]
    if re.search(r'[¿¡ñÑ]', text):
        return "es", CODE_TO_LANG["es"]["en"]
    if re.search(r'[œŒçÇ]', text):
        return "fr", CODE_TO_LANG["fr"]["en"]

    # 5. 欧语停用词词频投票 (英、德、法、西、意)
    words = [w.lower() for w in re.findall(r'[a-zA-Zà-öø-ÿÀ-ÖØ-ß\']+', text)]
    if words:
        scores = {"en": 0, "de": 0, "fr": 0, "es": 0, "it": 0}
        for w in words:
            for lang, sw_set in LATIN_STOPWORDS.items():
                if w in sw_set:
                    scores[lang] += 1
        best_lang = max(scores, key=scores.get)
        if scores[best_lang] > 0:
            return best_lang, CODE_TO_LANG[best_lang]["en"]

    return "en", CODE_TO_LANG["en"]["en"]

def grab_clipboard_image():
    """检测并提取剪贴板中的图片保存为跨平台安全临时文件"""
    if os.path.exists(CLIPBOARD_OCR_PATH):
        try:
            os.remove(CLIPBOARD_OCR_PATH)
        except Exception:
            pass

    try:
        im = ImageGrab.grabclipboard()
        if isinstance(im, Image.Image):
            im.save(CLIPBOARD_OCR_PATH)
            return CLIPBOARD_OCR_PATH
    except Exception:
        pass

    if os.name != 'nt':
        try:
            p = subprocess.run(
                ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            if p.returncode == 0 and len(p.stdout) > 0:
                with open(CLIPBOARD_OCR_PATH, "wb") as f:
                    f.write(p.stdout)
                return CLIPBOARD_OCR_PATH
        except Exception:
            pass

        try:
            p = subprocess.run(
                ["wl-paste", "--type", "image/png"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            if p.returncode == 0 and len(p.stdout) > 0:
                with open(CLIPBOARD_OCR_PATH, "wb") as f:
                    f.write(p.stdout)
                return CLIPBOARD_OCR_PATH
        except Exception:
            pass

    return None

def get_installed_tesseract_languages():
    """动态获取本地 Tesseract 实际已安装的所有语言包"""
    try:
        res = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True)
        if res.returncode == 0:
            langs = [line.strip() for line in res.stdout.splitlines() if line.strip() and not line.startswith("List of")]
            return langs
    except Exception:
        pass
    return ["chi_sim", "eng"]

def ocr_extract_text(img_path):
    """调用本地 tesseract 动态加载已安装的多国语言包进行全语种排版识别"""
    try:
        available_langs = get_installed_tesseract_languages()
        active_langs = [l for l in ["chi_sim", "eng", "jpn", "kor", "rus", "deu", "fra", "spa", "ita"] if l in available_langs]
        lang_arg = "+".join(active_langs) if active_langs else "eng"

        cmd = ["tesseract", img_path, "stdout", "-l", lang_arg, "--psm", "3"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception as e:
        console.print(f"[bold red]❌ OCR 执行异常: {str(e)}[/]")
        return ""

def format_model_name(filename: str) -> str:
    """根据文件名自动解析友好的模型显示名称"""
    clean_name = os.path.splitext(filename)[0]
    clean_name = re.sub(r'[-_]instruct', '', clean_name, flags=re.IGNORECASE)
    parts = clean_name.split('-')
    
    quant = ""
    for p in list(parts):
        if re.match(r'^q\d+.*', p, re.IGNORECASE):
            quant = f"({p.upper()})"
            parts.remove(p)
            break
            
    base_title = " ".join(parts).title()
    if quant:
        return f"{base_title} {quant}"
    return base_title

class TranslatorCLI:
    def __init__(self):
        self.config = dict(DEFAULT_CONFIG)
        self.last_active_time = time.time()
        self.is_busy = False
        self.llm = None
        self.lock = threading.Lock()

        # 读取持久化配置
        self.load_config()

        # 动态扫描 models/*.gguf 模型
        self.models_map = {}
        self.active_model_idx = "1"
        self.refresh_available_models()

        # 按键绑定
        self.kb = KeyBindings()
        
        @self.kb.add('enter')
        def _(event):
            event.current_buffer.validate_and_handle()

        @self.kb.add('escape', 'enter')
        @self.kb.add('c-j')
        def _(event):
            event.current_buffer.insert_text('\n')

        @self.kb.add('c-v')
        def _(event):
            img_file = grab_clipboard_image()
            if img_file:
                event.current_buffer.text = f"/img {img_file}"
                event.current_buffer.validate_and_handle()
            else:
                try:
                    text = pyperclip.paste()
                    if text:
                        event.current_buffer.insert_text(text)
                except Exception:
                    pass

        # 底部常驻状态栏
        def get_bottom_toolbar():
            engine_status = "[Active]" if self.llm is not None else "[0 MB Sleep]"
            model_disp = self.get_current_model_name()
            lang_disp = self.target_lang_display
            return HTML(
                f" <style bg='#1a1a24' fg='#00d7af'><b>Target:</b></style> {lang_disp} | "
                f"<style bg='#1a1a24' fg='#00afff'><b>Model:</b></style> {model_disp} {engine_status} | "
                f"<style fg='#777777'>/model /lang /sleep /clear /quit</style> "
            )

        self.session = PromptSession(
            multiline=True,
            key_bindings=self.kb,
            bottom_toolbar=get_bottom_toolbar,
            enable_history_search=True
        )

        # 启动后台看门狗
        self.watchdog = threading.Thread(target=self._idle_watchdog, daemon=True)
        self.watchdog.start()

    @property
    def target_lang_key(self):
        return str(self.config.get("target_lang_key", "1"))

    @target_lang_key.setter
    def target_lang_key(self, val):
        self.config["target_lang_key"] = str(val)

    @property
    def idle_timeout(self):
        return int(self.config.get("idle_timeout", 60))

    def load_config(self):
        """优先从用户主目录读取配置，次选项目目录便携配置"""
        target_file = None
        if os.path.exists(USER_CONFIG_FILE):
            target_file = USER_CONFIG_FILE
        elif os.path.exists(LOCAL_CONFIG_FILE):
            target_file = LOCAL_CONFIG_FILE

        if target_file:
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception:
                pass

        validation_enabled, retry_limit = normalize_quality_settings(
            self.config.get("quality_validation"),
            self.config.get("quality_retry_limit"),
        )
        self.config["quality_validation"] = validation_enabled
        self.config["quality_retry_limit"] = retry_limit

    def save_config(self):
        """双重原子落盘保存配置 (通过 fsync 确保窗口被杀死时依然物理持久化)"""
        current_fn = ""
        if self.active_model_idx in self.models_map:
            current_fn = self.models_map[self.active_model_idx]["filename"]
        self.config["selected_model_filename"] = current_fn

        # 写入用户主目录
        try:
            os.makedirs(USER_CONFIG_DIR, exist_ok=True)
            with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            pass

        # 写入本地便携配置
        try:
            with open(LOCAL_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            pass

    def refresh_available_models(self):
        """动态扫描 models/ 目录下所有 *.gguf 模型并按修改时间与命名构建索引"""
        os.makedirs(MODELS_DIR, exist_ok=True)
        gguf_files = sorted(glob.glob(os.path.join(MODELS_DIR, "*.gguf")))
        
        self.models_map = {}
        idx = 1
        for fpath in gguf_files:
            fname = os.path.basename(fpath)
            fsize_gb = os.path.getsize(fpath) / (1024 * 1024 * 1024)
            display_name = f"{format_model_name(fname)} [{fsize_gb:.1f}GB]"
            self.models_map[str(idx)] = {
                "name": display_name,
                "filename": fname,
                "path": fpath,
                "size_gb": fsize_gb
            }
            idx += 1

        saved_fn = self.config.get("selected_model_filename", "")
        found_saved = False
        if saved_fn:
            for k, info in self.models_map.items():
                if info["filename"] == saved_fn:
                    self.active_model_idx = k
                    found_saved = True
                    break

        if not found_saved and self.models_map:
            for k, info in self.models_map.items():
                if "3b" in info["filename"].lower():
                    self.active_model_idx = k
                    break
            else:
                self.active_model_idx = "1"

    def _idle_watchdog(self):
        """闲置超时自动清空模型内存 (0 MB 负载)"""
        while True:
            time.sleep(3)
            with self.lock:
                if self.is_busy:
                    continue
                if self.llm is not None and (time.time() - self.last_active_time > self.idle_timeout):
                    self.unload_engine()

    def get_current_model_path(self):
        if self.active_model_idx in self.models_map:
            return self.models_map[self.active_model_idx]["path"]
        return None

    def get_current_model_name(self):
        if self.active_model_idx in self.models_map:
            return self.models_map[self.active_model_idx]["name"]
        return "未加载模型 (No Model)"

    def init_engine(self, silent=False):
        model_path = self.get_current_model_path()
        
        if not model_path or not os.path.exists(model_path):
            console.print(f"[bold red]❌ models/ 目录下未检测到任何可用的 .gguf 模型文件！[/]")
            console.print("[yellow]💡 提示：请先运行 ./install.sh 下载模型，或将任意 GGUF 模型文件放入 models/ 目录中。[/]\n")
            sys.exit(1)
        
        model_name = self.get_current_model_name()
        if not silent:
            with console.status(f"[bold cyan]🚀 正在加载 {model_name} 本地引擎...[/]", spinner="dots"):
                self._load_llama(model_path)
        else:
            self._load_llama(model_path)
        
        self.last_active_time = time.time()

    def _load_llama(self, model_path):
        if self.llm is not None:
            del self.llm
            self.llm = None
            gc.collect()
        
        n_ctx = int(self.config.get("n_ctx", 8192))
        optimal_threads = get_optimal_threads()
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=optimal_threads,
            verbose=False
        )

    def unload_engine(self):
        """从内存中释放模型"""
        if self.llm is not None:
            del self.llm
            self.llm = None
            gc.collect()

    def ensure_engine(self):
        """确保模型在内存中，休眠则瞬间唤醒"""
        with self.lock:
            if self.llm is None:
                model_name = self.get_current_model_name()
                model_path = self.get_current_model_path()
                with console.status(f"[dim cyan]⚡ 唤醒 {model_name} (0.3秒从 SSD 加载)...[/]", spinner="dots"):
                    self._load_llama(model_path)
            self.last_active_time = time.time()

    @property
    def target_lang_item(self):
        return LANGUAGES.get(self.target_lang_key, LANGUAGES["1"])

    @property
    def target_lang_display(self):
        item = self.target_lang_item
        return f"{item['flag']} {item['zh']} ({item['code']})"

    def print_header(self):
        model_name = self.get_current_model_name()
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="right")
        grid.add_row(
            f"[bold cyan]Input:[/] [yellow]🔍 智能语种嗅探[/] ➔ [bold cyan]Target:[/] [green]{self.target_lang_display}[/]",
            f"[bold cyan]Model:[/] [green]{model_name}[/] | [dim]AutoSleep: {self.idle_timeout}s[/]"
        )
        console.print(Panel(
            grid,
            title="[bold blue]🌐 AI Terminal Translator (Universal GGUF Engine)[/]",
            subtitle="[dim]Shortcuts: Ctrl+V (智能粘图/文本) | /lang (语言) | /model (换模型) | /sleep | /quit[/]",
            border_style="bright_blue"
        ))

    def build_dynamic_prompt(self, text: str):
        source_code, source_name = detect_language(text)
        target_code = self.target_lang_item["code"]
        target_name = self.target_lang_item["en"]
        pair_key = None

        # 处理中英/中日等混合夹杂句（转换为纯正简体中文）
        if source_code == "mixed":
            if target_code == "zh":
                pair_key = "mixed_to_zh"
                source_name = "Mixed / 混合夹杂"
            else:
                source_code = "zh"
                source_name = CODE_TO_LANG["zh"]["en"]
        
        # 确定性双向互翻（纯中文输入且目标为中文时，自动翻译为英文）
        if source_code == target_code:
            if target_code == "zh":
                target_code = "en"
                target_name = CODE_TO_LANG["en"]["en"]
            else:
                target_code = "zh"
                target_name = CODE_TO_LANG["zh"]["en"]
        
        base_template = load_skill("base")
        if not base_template:
            base_template = "You are a professional {source_name}-to-{target_name} translator.\nTASK: Translate the user's input text into {target_name}."
        
        base_prompt = base_template.replace("{source_name}", source_name).replace("{target_name}", target_name)
        
        # 拼接专属专项 Skill
        if pair_key is None:
            pair_key = f"{source_code}_to_{target_code}"
        skill_prompt = load_skill(pair_key)
        
        if skill_prompt:
            final_prompt = f"{base_prompt}\n\n{skill_prompt}"
        else:
            final_prompt = base_prompt

        return final_prompt, source_name, target_name

    def switch_model(self):
        self.refresh_available_models()
        
        if not self.models_map:
            console.print("\n[bold red]❌ models/ 目录下未发现任何可用的 .gguf 模型文件。[/]\n")
            return

        console.print("\n[bold cyan]📁 models/ 目录已安装的模型列表（自动发现）：[/]")
        for idx, info in self.models_map.items():
            current_flag = " [bold green](当前正在使用)[/]" if idx == self.active_model_idx else ""
            console.print(f"  [bold yellow]{idx}[/]. {info['name']}{current_flag}")
        
        console.print(f"[dim]提示：将任意 .gguf 模型放入 models/ 目录即可在此自动识别加载。[/]")

        try:
            choice = input(f"\n请选择模型编号 [1-{len(self.models_map)}]: ").strip()
            if choice in self.models_map and choice != self.active_model_idx:
                with self.lock:
                    self.active_model_idx = choice
                    self.save_config()
                    self._load_llama(self.models_map[choice]["path"])
                    self.last_active_time = time.time()
                
                console.clear()
                self.print_header()
                console.print(f"\n[bold green]✓ 成功切换模型为:[/] [yellow]{self.get_current_model_name()}[/] [dim](已保存偏好)[/]\n")
            elif choice == self.active_model_idx:
                console.print("[dim]保持当前模型不变。[/]\n")
            else:
                console.print("[bold red]❌ 输入无效[/]\n")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]已取消选择[/]\n")

    def switch_lang(self):
        console.print("\n[bold cyan]请选择翻译目标输出语言：[/]")
        for k, item in LANGUAGES.items():
            current_flag = " [bold green](当前目标)[/]" if k == self.target_lang_key else ""
            console.print(f"  [bold yellow]{k}[/]. {item['flag']} {item['zh']} ({item['en']}){current_flag}")
        
        try:
            choice = input("\n请输入语言编号 [1-9]: ").strip()
            if choice in LANGUAGES:
                self.target_lang_key = choice
                self.save_config()
                console.clear()
                self.print_header()
                console.print(f"\n[bold green]✓ 输出语言已变更为:[/] [yellow]{self.target_lang_display}[/] [dim](已保存偏好)[/]\n")
            else:
                console.print("[bold red]❌ 输入无效，保持原有设置[/]\n")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]已取消选择[/]\n")

    def handle_ocr_and_translate(self, img_path: str):
        img_path = os.path.expanduser(img_path.strip().strip('"').strip("'"))
        if not os.path.exists(img_path):
            console.print(f"[bold red]❌ 图片文件不存在:[/] {img_path}\n")
            return

        with console.status("[bold cyan]📷 正在提取图片文字与排版 (Tesseract OCR)...[/]", spinner="bouncingBar"):
            ocr_text = ocr_extract_text(img_path)

        if not ocr_text:
            console.print("[bold yellow]⚠️ 未能在图片中识别到清晰的文字内容。[/]\n")
            return

        console.print()
        console.rule("[bold yellow]📷 OCR 识别提取原文 (保持原图版面)[/]", style="yellow")
        console.print(ocr_text)
        console.rule("[dim yellow]END[/]", style="yellow")
        console.print()
        
        self.stream_translate(ocr_text)

    def _collect_completion(
        self,
        messages,
        temperature,
        repeat_penalty,
        max_tokens,
    ):
        """Collect a complete model result without exposing unvalidated tokens."""
        stream = self.llm.create_chat_completion(
            messages=messages,
            temperature=temperature,
            repeat_penalty=repeat_penalty,
            max_tokens=max_tokens,
            stream=True,
        )
        text = ""
        finish_reason = None
        for chunk in stream:
            choices = chunk.get("choices", [])
            if not choices:
                continue
            choice = choices[0]
            token = choice.get("delta", {}).get("content", "")
            if token:
                text += token
            if choice.get("finish_reason") is not None:
                finish_reason = choice["finish_reason"]
        return CompletionResult(
            text=text.strip(),
            truncated=finish_reason == "length",
        )

    def stream_translate(self, text: str):
        self.ensure_engine()
        with self.lock:
            self.is_busy = True

        start_time = time.time()

        temperature = float(self.config.get("temperature", 0.1))
        repeat_penalty = float(self.config.get("repeat_penalty", 1.08))
        max_tokens = int(self.config.get("max_tokens", 4096))
        validation_enabled, retry_limit = normalize_quality_settings(
            self.config.get("quality_validation"),
            self.config.get("quality_retry_limit"),
        )

        try:
            normalized_text = normalize_source_structure(text)
            raw_paragraphs = re.split(r'\n\s*\n', normalized_text)
            paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]

            if not paragraphs:
                paragraphs = [normalized_text.strip()]

            console.print()
            console.rule(f"[bold green]Translation ➔ {self.target_lang_display}[/]", style="green")

            for i, p in enumerate(paragraphs):
                if not p:
                    continue

                system_prompt, _, resolved_target_name = self.build_dynamic_prompt(p)
                resolved_target_code = next(
                    (
                        code
                        for code, item in CODE_TO_LANG.items()
                        if item["en"] == resolved_target_name
                    ),
                    self.target_lang_item["code"],
                )
                outcome = run_quality_checked_completion(
                    source=p,
                    target_code=resolved_target_code,
                    system_prompt=system_prompt,
                    complete=lambda messages, attempt_temperature: self._collect_completion(
                        messages,
                        attempt_temperature,
                        repeat_penalty,
                        max_tokens,
                    ),
                    temperature=temperature,
                    retry_limit=retry_limit,
                    validation_enabled=validation_enabled,
                )

                sys.stdout.write(outcome.text)
                if i < len(paragraphs) - 1:
                    sys.stdout.write('\n\n')
                elif not outcome.text.endswith('\n'):
                    sys.stdout.write('\n')
                sys.stdout.flush()

                if outcome.errors:
                    error_list = ", ".join(outcome.errors)
                    console.print(
                        f"[bold yellow]⚠ 质量校验未完全通过: {error_list}[/]"
                    )

            console.rule("[dim green]END[/]", style="green")

            elapsed = time.time() - start_time
            console.print(f"[dim]耗时: {elapsed:.2f}s | (闲置 {self.idle_timeout} 秒后将自动释放内存)[/]\n")

        except Exception as e:
            console.print(f"\n[bold red]❌ 翻译出错: {str(e)}[/]\n")
        finally:
            with self.lock:
                self.is_busy = False
                self.last_active_time = time.time()

    def run(self):
        console.clear()
        self.init_engine()
        console.clear()
        self.print_header()

        prompt_style = Style.from_dict({
            'prompt': '#00afff bold',
        })

        while True:
            try:
                tag = f"auto➔{self.target_lang_item['code']}"
                prompt_text = HTML(f"<prompt>[{tag}] &gt; </prompt>")
                user_input = self.session.prompt(prompt_text, style=prompt_style).strip()

                if not user_input:
                    continue

                if user_input in ["/quit", "/exit", ":q"]:
                    console.print("[dim]👋 Goodbye![/]")
                    break
                elif user_input == "/model":
                    self.switch_model()
                    continue
                elif user_input == "/lang":
                    self.switch_lang()
                    continue
                elif user_input in ["/config", "/settings"]:
                    console.clear()
                    self.print_header()
                    continue
                elif user_input in ["/sleep", "/unload"]:
                    with self.lock:
                        self.unload_engine()
                    console.print("[bold yellow]💤 已手动释放模型内存（当前内存占用已归零）。[/]\n")
                    continue
                elif user_input in ["/ocr", "/clip", "/paste"]:
                    clip_img = grab_clipboard_image()
                    if clip_img:
                        self.handle_ocr_and_translate(clip_img)
                    else:
                        console.print("[bold yellow]⚠️ 当前剪贴板中未检测到截图或图片数据。[/]\n")
                    continue
                elif user_input.startswith("/img ") or user_input.startswith("/ocr "):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) > 1:
                        self.handle_ocr_and_translate(parts[1])
                    continue
                elif user_input in ["/clear", "/cls"]:
                    console.clear()
                    self.print_header()
                    continue
                elif user_input.startswith("/"):
                    console.print(f"[bold red]未知指令:[/] {user_input} (可用指令: /model, /lang, /ocr, /sleep, /config, /clear, /quit)\n")
                    continue

                clean_path = user_input.strip('"').strip("'")
                if os.path.exists(os.path.expanduser(clean_path)) and clean_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
                    self.handle_ocr_and_translate(clean_path)
                    continue

                self.stream_translate(user_input)

            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]👋 退出程序。[/]")
                break

if __name__ == "__main__":
    cli = TranslatorCLI()
    cli.run()
