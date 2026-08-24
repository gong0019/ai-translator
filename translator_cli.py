#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Terminal Translator (Claude Code CLI Aesthetic)
Powered by Universal GGUF Engine (Qwen2.5, DeepSeek, Llama, Mistral, etc.) via llama.cpp
Architecture: Python Language Sniffer + Modular File-based Skill Routing (skills/*.md)
Features: Persistent Config (config.json), Fixed Bottom Status Toolbar & Live Header Sync, Dynamic Model Discovery
"""

import os
import re
import sys
import time
import json
import gc
import glob
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

console = Console()

BASE_DIR = os.path.dirname(__file__)
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
MODELS_DIR = os.path.join(BASE_DIR, "models")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

LANGUAGES = {
    "1": ("中文", "Simplified Chinese", "zh", "🇨🇳"),
    "2": ("英语", "English", "en", "🇬🇧"),
    "3": ("日语", "Japanese", "ja", "🇯🇵"),
    "4": ("韩语", "Korean", "ko", "🇰🇷"),
    "5": ("德语", "German", "de", "🇩🇪"),
    "6": ("法语", "French", "fr", "🇫🇷"),
    "7": ("西班牙语", "Spanish", "es", "🇪🇸"),
    "8": ("俄语", "Russian", "ru", "🇷🇺"),
    "9": ("意大利语", "Italian", "it", "🇮🇹"),
}

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
    """通过字符集特征高效嗅探源语言 (Python 路由层)"""
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text):
        return "ja", "Japanese"
    if re.search(r'[\uAC00-\uD7AF\u1100-\u11FF]', text):
        return "ko", "Korean"
    if re.search(r'[\u0400-\u04FF]', text):
        return "ru", "Russian"
    
    chinese_chars = len(re.findall(r'[\u4E00-\u9FFF]', text))
    total_alpha = len(re.findall(r'[a-zA-Z]', text))
    if chinese_chars > 0 and chinese_chars >= total_alpha * 0.3:
        return "zh", "Simplified Chinese"
    
    return "en", "English"

def grab_clipboard_image():
    """检测并提取剪贴板中的图片保存为临时文件"""
    tmp_path = "/tmp/ai_translator_clipboard_ocr.png"
    if os.path.exists(tmp_path):
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    try:
        im = ImageGrab.grabclipboard()
        if isinstance(im, Image.Image):
            im.save(tmp_path)
            return tmp_path
    except Exception:
        pass

    try:
        p = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        if p.returncode == 0 and len(p.stdout) > 0:
            with open(tmp_path, "wb") as f:
                f.write(p.stdout)
            return tmp_path
    except Exception:
        pass

    try:
        p = subprocess.run(
            ["wl-paste", "--type", "image/png"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        if p.returncode == 0 and len(p.stdout) > 0:
            with open(tmp_path, "wb") as f:
                f.write(p.stdout)
            return tmp_path
    except Exception:
        pass

    return None

def ocr_extract_text(img_path):
    """调用本地 tesseract 提取文本并保留空间排版"""
    try:
        cmd = ["tesseract", img_path, "stdout", "-l", "chi_sim+eng+jpn", "--psm", "3"]
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
        # 默认配置
        self.target_lang_key = "1"
        self.auto_copy = True
        self.saved_model_filename = ""
        self.idle_timeout = 60
        self.last_active_time = time.time()
        self.is_busy = False
        self.llm = None
        self.lock = threading.Lock()

        # 读取持久化配置 (config.json)
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

        # 底部常驻状态栏 (Fixed Bottom Toolbar)
        def get_bottom_toolbar():
            engine_status = "[Active]" if self.llm is not None else "[0 MB Sleep]"
            copy_status = "ON" if self.auto_copy else "OFF"
            model_disp = self.get_current_model_name()
            lang_disp = self.target_lang_display
            return HTML(
                f" <style bg='#1a1a24' fg='#00d7af'><b>Target:</b></style> {lang_disp} | "
                f"<style bg='#1a1a24' fg='#00afff'><b>Model:</b></style> {model_disp} {engine_status} | "
                f"<style bg='#1a1a24' fg='#ffd700'><b>Copy:</b></style> {copy_status} | "
                f"<style fg='#777777'>/model /lang /copy /sleep /clear /quit</style> "
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

    def load_config(self):
        """从 config.json 读取持久化用户偏好"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.target_lang_key = str(data.get("target_lang_key", "1"))
                    self.auto_copy = bool(data.get("auto_copy", True))
                    self.saved_model_filename = data.get("selected_model_filename", "")
                    self.idle_timeout = int(data.get("idle_timeout", 60))
            except Exception:
                pass

    def save_config(self):
        """将用户偏好即时保存到 config.json"""
        current_fn = ""
        if self.active_model_idx in self.models_map:
            current_fn = self.models_map[self.active_model_idx]["filename"]
            
        data = {
            "selected_model_filename": current_fn,
            "target_lang_key": self.target_lang_key,
            "auto_copy": self.auto_copy,
            "idle_timeout": self.idle_timeout
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def refresh_available_models(self):
        """自动扫描 models/ 目录下所有的 *.gguf 模型文件并动态编号"""
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

        # 1. 优先定位 config.json 中保存的模型文件名
        found_saved = False
        if self.saved_model_filename:
            for k, info in self.models_map.items():
                if info["filename"] == self.saved_model_filename:
                    self.active_model_idx = k
                    found_saved = True
                    break

        # 2. 若无保存记录，则按优先级默认：3B -> 1.5B -> 7B
        if not found_saved:
            found_pref = False
            for pref in ["3b", "1.5b", "7b"]:
                for k, info in self.models_map.items():
                    if pref in info["filename"].lower():
                        self.active_model_idx = k
                        found_pref = True
                        break
                if found_pref:
                    break
            if not found_pref and self.models_map:
                self.active_model_idx = "1"

    def _idle_watchdog(self):
        """闲置 60 秒自动清空模型常驻内存"""
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
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=8192,
            n_threads=os.cpu_count() or 4,
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
        return f"{item[3]} {item[0]} ({item[1]})"

    def print_header(self):
        model_name = self.get_current_model_name()
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="right")
        grid.add_row(
            f"[bold cyan]Input:[/] [yellow]🔍 智能语种嗅探[/] ➔ [bold cyan]Target:[/] [green]{self.target_lang_display}[/]",
            f"[bold cyan]Model:[/] [green]{model_name}[/] | [dim]AutoSleep: 1m[/] | [dim]AutoCopy: {'[green]ON[/]' if self.auto_copy else '[red]OFF[/]'}[/]"
        )
        console.print(Panel(
            grid,
            title="[bold blue]🌐 AI Terminal Translator (Universal GGUF Engine)[/]",
            subtitle="[dim]Shortcuts: Ctrl+V (智能粘图/文本) | /lang (语言) | /model (换模型) | /sleep | /quit[/]",
            border_style="bright_blue"
        ))

    def build_dynamic_prompt(self, text: str):
        source_code, source_name = detect_language(text)
        target_code = self.target_lang_item[2]
        target_name = self.target_lang_item[1]
        
        if source_code == target_code:
            if target_code == "zh":
                target_code = "en"
                target_name = "English"
            else:
                target_code = "zh"
                target_name = "Simplified Chinese"
        
        base_template = load_skill("base")
        if not base_template:
            base_template = "You are a professional translator.\nDIRECTION: {source_name} → {target_name}\nTranslate the input into {target_name}."
        
        base_prompt = base_template.replace("{source_name}", source_name).replace("{target_name}", target_name)
        
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
                    self.saved_model_filename = self.models_map[choice]["filename"]
                    self.save_config()  # 立即保存新模型偏好
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
        for k, (zh, en, _, flag) in LANGUAGES.items():
            current_flag = " [bold green](当前目标)[/]" if k == self.target_lang_key else ""
            console.print(f"  [bold yellow]{k}[/]. {flag} {zh} ({en}){current_flag}")
        
        try:
            choice = input("\n请输入语言编号 [1-9]: ").strip()
            if choice in LANGUAGES:
                self.target_lang_key = choice
                self.save_config()  # 立即保存新语言偏好
                console.clear()
                self.print_header()
                console.print(f"\n[bold green]✓ 输出语言已变更为:[/] [yellow]{self.target_lang_display}[/] [dim](已保存偏好)[/]\n")
            else:
                console.print("[bold red]❌ 输入无效，保持原有设置[/]\n")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]已取消选择[/]\n")

    def toggle_copy(self):
        self.auto_copy = not self.auto_copy
        self.save_config()  # 立即保存剪贴板偏好
        console.clear()
        self.print_header()
        status = "[green]开启 (ON)[/]" if self.auto_copy else "[red]关闭 (OFF)[/]"
        console.print(f"\n[bold green]✓ 译文自动同步剪贴板:[/] {status} [dim](已保存偏好)[/]\n")

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

    def stream_translate(self, text: str):
        self.ensure_engine()
        with self.lock:
            self.is_busy = True

        full_translation = ""
        start_time = time.time()

        try:
            system_prompt, source_name, target_name = self.build_dynamic_prompt(text)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]

            stream = self.llm.create_chat_completion(
                messages=messages,
                temperature=0.1,
                repeat_penalty=1.08,
                max_tokens=4096,
                stream=True
            )

            console.print()
            console.rule(f"[bold green]Translation ➔ {target_name} ({source_name} ➔ {target_name})[/]", style="green")

            for chunk in stream:
                delta = chunk['choices'][0].get('delta', {})
                token = delta.get('content', '')
                if token:
                    full_translation += token
                    sys.stdout.write(token)
                    sys.stdout.flush()

            if not full_translation.endswith('\n'):
                sys.stdout.write('\n')
            sys.stdout.flush()

            console.rule("[dim green]END[/]", style="green")

            elapsed = time.time() - start_time
            full_translation = full_translation.strip()

            clipboard_info = ""
            if self.auto_copy and full_translation:
                try:
                    pyperclip.copy(full_translation)
                    clipboard_info = " | [cyan]已复制到剪贴板 📋[/]"
                except Exception:
                    pass

            console.print(f"[dim]耗时: {elapsed:.2f}s{clipboard_info} | (闲置 1 分钟后将自动释放内存)[/]\n")

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
                tag = f"auto➔{self.target_lang_item[2]}"
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
                elif user_input == "/copy":
                    self.toggle_copy()
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
                    console.print(f"[bold red]未知指令:[/] {user_input} (可用指令: /model, /lang, /ocr, /sleep, /copy, /config, /clear, /quit)\n")
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
