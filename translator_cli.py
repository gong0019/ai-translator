#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen Terminal Translator (Claude Code CLI Aesthetic)
Powered by Qwen2.5 (3B / 1.5B) via llama.cpp (Local Standalone Engine)
Architecture: Python Language Sniffer + Modular File-based Skill Routing (skills/*.md)
Features: 1-Minute Auto-Idle Memory Release with Active-Translation Protection
"""

import os
import re
import sys
import time
import gc
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

MODELS = {
    "1": ("Qwen2.5-3B (高精度·推荐)", "qwen2.5-3b-instruct-q4_k_m.gguf", 3),
    "2": ("Qwen2.5-1.5B (极速·轻量)", "qwen2.5-1.5b-instruct-q4_k_m.gguf", 1.5),
}

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
    tmp_path = "/tmp/qwen_clipboard_ocr.png"
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
        cmd = ["tesseract", img_path, "stdout", "-l", "chi_sim+eng", "--psm", "3"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception as e:
        console.print(f"[bold red]❌ OCR 执行异常: {str(e)}[/]")
        return ""

class TranslatorCLI:
    def __init__(self):
        self.model_key = "1"
        self.target_lang_key = "1"
        self.auto_copy = True
        
        # 1 分钟自动休眠释放内存 (秒)
        self.idle_timeout = 60
        self.last_active_time = time.time()
        self.is_busy = False  # 正在翻译中锁，彻底杜绝翻译长文时被误释放
        self.llm = None
        self.lock = threading.Lock()

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

        self.session = PromptSession(
            multiline=True,
            key_bindings=self.kb,
            enable_history_search=True
        )

        # 启动后台闲置看门狗线程
        self.watchdog = threading.Thread(target=self._idle_watchdog, daemon=True)
        self.watchdog.start()

    def _idle_watchdog(self):
        """后台检测闲置时间：仅在完全没有翻译任务进行中且闲置 > 60秒时释放"""
        while True:
            time.sleep(3)
            with self.lock:
                # 若正在翻译中（is_busy = True），绝不释放
                if self.is_busy:
                    continue
                
                if self.llm is not None and (time.time() - self.last_active_time > self.idle_timeout):
                    self.unload_engine()

    def get_model_path(self):
        filename = MODELS[self.model_key][1]
        return os.path.join(BASE_DIR, "models", filename)

    def init_engine(self, silent=False):
        model_path = self.get_model_path()
        model_name = MODELS[self.model_key][0]
        
        if not os.path.exists(model_path):
            console.print(f"[bold red]❌ 未找到模型文件:[/] {model_path}")
            sys.exit(1)
        
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
        """从内存中彻底释放模型"""
        if self.llm is not None:
            del self.llm
            self.llm = None
            gc.collect()

    def ensure_engine(self):
        """需要推理时确保模型在内存中"""
        with self.lock:
            if self.llm is None:
                model_name = MODELS[self.model_key][0]
                with console.status(f"[dim cyan]⚡ 唤醒 {model_name} (0.3秒从 SSD 加载)...[/]", spinner="dots"):
                    self._load_llama(self.get_model_path())
            self.last_active_time = time.time()

    @property
    def target_lang_item(self):
        return LANGUAGES[self.target_lang_key]

    @property
    def target_lang_display(self):
        item = self.target_lang_item
        return f"{item[3]} {item[0]} ({item[1]})"

    def print_header(self):
        model_name = MODELS[self.model_key][0]
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="right")
        grid.add_row(
            f"[bold cyan]Input:[/] [yellow]🔍 智能语种嗅探[/] ➔ [bold cyan]Target:[/] [green]{self.target_lang_display}[/]",
            f"[bold cyan]Model:[/] [green]{model_name}[/] | [dim]AutoSleep: 1m[/] | [dim]AutoCopy: {'[green]ON[/]' if self.auto_copy else '[red]OFF[/]'}[/]"
        )
        console.print(Panel(
            grid,
            title="[bold blue]🌐 Qwen Terminal Translator (1-Min Auto Sleep)[/]",
            subtitle="[dim]Shortcuts: Ctrl+V (智能粘图/文本) | /lang (目标语言) | /model (切换模型) | /copy | /quit[/]",
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
        console.print("\n[bold cyan]可选本地模型清单：[/]")
        for k, (name, filename, _) in MODELS.items():
            current_flag = " [bold green](当前使用)[/]" if k == self.model_key else ""
            exists = "✓" if os.path.exists(os.path.join(BASE_DIR, "models", filename)) else "✗ 未就绪"
            console.print(f"  [bold yellow]{k}[/]. {name} [{exists}]{current_flag}")
        
        try:
            choice = input("\n请选择模型编号 [1-2]: ").strip()
            if choice in MODELS and choice != self.model_key:
                with self.lock:
                    self.model_key = choice
                    self.init_engine()
                console.print(f"\n[bold green]✓ 模型已成功切换为:[/] [yellow]{MODELS[self.model_key][0]}[/]\n")
            elif choice == self.model_key:
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
                console.print(f"\n[bold green]✓ 输出语言已变更为:[/] [yellow]{self.target_lang_display}[/]\n")
            else:
                console.print("[bold red]❌ 输入无效，保持原有设置[/]\n")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]已取消选择[/]\n")

    def toggle_copy(self):
        self.auto_copy = not self.auto_copy
        status = "[green]开启 (ON)[/]" if self.auto_copy else "[red]关闭 (OFF)[/]"
        console.print(f"\n[bold green]✓ 译文自动同步剪贴板:[/] {status}\n")

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
        
        # 标记为繁忙状态（防止长文翻译途中被看门狗释放）
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
            # 翻译结束，重置计时器并解除繁忙锁，从此时起重新倒计时 60 秒
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

                # 处理斜杠指令
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
