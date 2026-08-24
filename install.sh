#!/usr/bin/env bash
# ==============================================================================
# AI Terminal Translator - Universal GGUF Installer
# Features: Zero Hardcoding, Cross-Platform Support, Domestic/Global Auto-Routing, TUI
# Options: ./install.sh [--clean | --reinstall]
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

CLEAN_MODE=false
if [ "$1" == "--clean" ] || [ "$1" == "--reinstall" ] || [ "$1" == "-f" ]; then
    CLEAN_MODE=true
fi

if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    REAL_USER="$USER"
    REAL_HOME="$HOME"
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BLUE}${BOLD}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           🌐 AI Terminal Translator - Automated Setup          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

if [ "$CLEAN_MODE" = true ]; then
    echo -e "${YELLOW}🧹 触发 --clean 模式：正在清理历史虚拟环境与临时缓存...${NC}"
    rm -rf .venv
    rm -f /tmp/ai_translator_clipboard_ocr.png
    echo -e "${GREEN}✓ 历史残留清理完毕，即将开始全新纯净安装。${NC}\n"
fi

# 1. 下载源选择与网络探测
detect_network_region() {
    local source="${AI_TRANSLATOR_NETWORK_SOURCE:-}"

    # 不使用调用终端遗留的本地代理设置；仅影响当前安装进程。
    unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy

    if [ -z "$source" ] && [ -t 0 ]; then
        echo -e "${CYAN}[1/6] 请选择模型与 Python 依赖下载源：${NC}"
        echo "  1) 国际直连（Hugging Face + 官方 PyPI）"
        echo "  2) 国内镜像（HF-Mirror + 阿里云 PyPI）"
        echo "  3) 自动检测（默认）"
        read -r -p "输入编号 [3]: " source || source="auto"
    fi
    source=${source:-auto}

    case "$source" in
        1|international)
            IS_CN=false
            PIP_INDEX=""
            MODEL_HOST="https://huggingface.co"
            echo -e "网络节点: ${GREEN}国际直连 (Hugging Face & PyPI)${NC}\n"
            return
            ;;
        2|domestic)
            IS_CN=true
            PIP_INDEX="-i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com"
            MODEL_HOST="https://hf-mirror.com"
            echo -e "网络节点: ${YELLOW}国内镜像 (HF-Mirror + 阿里云 PyPI)${NC}\n"
            return
            ;;
        3|auto)
            echo -e "${CYAN}[1/6] 正在自动探测网络环境...${NC}"
            ;;
        *)
            echo -e "${YELLOW}未知下载源选项 '$source'，将自动检测。${NC}"
            ;;
    esac

    if curl -sI --connect-timeout 2 "https://huggingface.co" >/dev/null 2>&1; then
        IS_CN=false
        PIP_INDEX=""
        MODEL_HOST="https://huggingface.co"
        echo -e "网络节点: ${GREEN}国际网络 (直连 HuggingFace & PyPI)${NC}\n"
    else
        IS_CN=true
        PIP_INDEX="-i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com"
        MODEL_HOST="https://hf-mirror.com"
        echo -e "网络节点: ${YELLOW}国内网络 (自动启用 阿里云 PyPI 镜像 + HF-Mirror 模型高速节点)${NC}\n"
    fi
}

# 2. 系统底层依赖安装 (包含全 9 语种 OCR 支持包)
install_system_dependencies() {
    echo -e "${CYAN}[2/6] 正在检查与安装系统底层依赖 (全语种 OCR、C++ 编译环境、剪贴板)...${NC}"
    
    if [ "$EUID" -ne 0 ]; then
        SUDO_CMD="sudo"
        echo -e "${YELLOW}提示: 系统底层依赖安装需要管理员权限。${NC}"
    else
        SUDO_CMD=""
    fi

    if which apt-get >/dev/null 2>&1; then
        $SUDO_CMD apt-get update -qq || true
        $SUDO_CMD apt-get install -y -qq \
            python3 python3-pip python3-venv \
            build-essential cmake \
            tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng tesseract-ocr-jpn \
            tesseract-ocr-kor tesseract-ocr-rus tesseract-ocr-deu tesseract-ocr-fra \
            tesseract-ocr-spa tesseract-ocr-ita \
            xclip wl-clipboard curl 2>/dev/null || true
    elif which dnf >/dev/null 2>&1; then
        $SUDO_CMD dnf install -y \
            python3 python3-pip python3-devel gcc-c++ cmake \
            tesseract tesseract-langpack-chi_sim tesseract-langpack-jpn tesseract-langpack-kor \
            tesseract-langpack-rus tesseract-langpack-deu tesseract-langpack-fra tesseract-langpack-spa tesseract-langpack-ita \
            xclip wl-clipboard curl || true
    elif which pacman >/dev/null 2>&1; then
        $SUDO_CMD pacman -Sy --noconfirm \
            python python-pip python-virtualenv base-devel cmake \
            tesseract tesseract-data-chi_sim tesseract-data-jpn tesseract-data-kor \
            tesseract-data-rus tesseract-data-deu tesseract-data-fra tesseract-data-spa tesseract-data-ita \
            xclip wl-clipboard curl || true
    elif [[ "$OSTYPE" == "darwin"* ]] && which brew >/dev/null 2>&1; then
        # Homebrew 在 install 前会拉取软件索引；先做本地检测，避免每次安装器运行都下载索引。
        MISSING_BREW_PACKAGES=()
        command -v python3 >/dev/null 2>&1 || MISSING_BREW_PACKAGES+=(python)
        command -v cmake >/dev/null 2>&1 || MISSING_BREW_PACKAGES+=(cmake)
        command -v tesseract >/dev/null 2>&1 || MISSING_BREW_PACKAGES+=(tesseract)
        brew list --versions tesseract-lang >/dev/null 2>&1 || MISSING_BREW_PACKAGES+=(tesseract-lang)

        if [ "${#MISSING_BREW_PACKAGES[@]}" -gt 0 ]; then
            echo -e "${YELLOW}缺少 macOS 依赖，正在通过 Homebrew 安装: ${MISSING_BREW_PACKAGES[*]}${NC}"
            brew install "${MISSING_BREW_PACKAGES[@]}" || true
        else
            echo -e "${GREEN}✓ macOS 系统依赖已存在，跳过 Homebrew 下载。${NC}"
        fi
    fi
    echo -e "${GREEN}✓ 系统依赖检查完成${NC}\n"
}

# 3. Python 虚拟环境
setup_python_environment() {
    echo -e "${CYAN}[3/6] 正在配置项目隔离 Python 虚拟环境 (.venv)...${NC}"
    
    if [ -d ".venv" ] && [ -f ".venv/bin/python3" ]; then
        if .venv/bin/python3 -c "import llama_cpp, rich, prompt_toolkit, pyperclip, PIL" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ 检测到已有 Python 虚拟环境且状态健康，跳过重复安装。${NC}\n"
            return
        else
            echo -e "${YELLOW}⚠️ 检测到上次安装中断或环境不完整，正在自动清理并重建 .venv ...${NC}"
            rm -rf .venv
        fi
    fi

    if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        sudo -u "$REAL_USER" python3 -m venv .venv
    else
        python3 -m venv .venv || true
    fi

    PIP_EXEC=".venv/bin/pip"
    if [ ! -f "$PIP_EXEC" ]; then
        PIP_EXEC="pip3"
    fi

    echo -e "${YELLOW}正在安装 Python 依赖库 (llama-cpp-python, rich, prompt_toolkit, Pillow...)${NC}"
    if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        sudo -u "$REAL_USER" $PIP_EXEC install -q --upgrade pip $PIP_INDEX 2>/dev/null || true
        sudo -u "$REAL_USER" $PIP_EXEC install -r requirements.txt $PIP_INDEX
    else
        $PIP_EXEC install -q --upgrade pip $PIP_INDEX 2>/dev/null || true
        $PIP_EXEC install -r requirements.txt $PIP_INDEX --user --break-system-packages 2>/dev/null || $PIP_EXEC install -r requirements.txt $PIP_INDEX
    fi
    echo -e "${GREEN}✓ Python 环境就绪${NC}\n"
}

# 4. 模型交互选择
select_and_download_models() {
    echo -e "${CYAN}[4/6] 配置本地 AI 模型...${NC}"
    mkdir -p "$PROJECT_DIR/models"
    if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        chown -R "$REAL_USER":"$REAL_USER" "$PROJECT_DIR/models"
    fi

    SELECTED_MODELS=""
    prompt_for_models() {
        local choice selections item selected="" invalid=false

        echo "请选择要下载的模型（可用逗号多选，例如 1,4；直接回车默认 1）："
        echo "  1) Qwen2.5-3B-Instruct   (约 2.0GB，推荐·高精度)"
        echo "  2) Qwen2.5-1.5B-Instruct (约 1.1GB，极速·轻量)"
        echo "  3) Qwen2.5-7B-Instruct   (约 4.7GB，旗舰·高质量)"
        echo "  4) Tencent Hy-MT2-1.8B   (翻译专用，Q4_K_M)"
        read -r -p "输入编号 [1]: " choice
        choice=${choice:-1}
        choice=${choice//，/,}
        choice=${choice//[[:space:]]/}
        IFS=',' read -r -a selections <<< "$choice"

        for item in "${selections[@]}"; do
            case "$item" in
                1) selected+='"3B" ' ;;
                2) selected+='"1.5B" ' ;;
                3) selected+='"7B" ' ;;
                4) selected+='"HYMT" ' ;;
                *) invalid=true ;;
            esac
        done

        if [ "$invalid" = true ] || [ -z "$selected" ]; then
            return 1
        fi
        SELECTED_MODELS="$selected"
    }

    if [ -t 0 ]; then
        until prompt_for_models; do
            echo -e "${YELLOW}输入无效，请输入菜单中的编号，例如 1 或 1,4。${NC}"
        done
    else
        echo -e "${YELLOW}未检测到可交互终端，默认下载推荐的 Qwen2.5-3B 高精度模型。${NC}"
        SELECTED_MODELS='"3B"'
    fi

    DOWNLOAD_MODE="${AI_TRANSLATOR_DOWNLOAD_MODE:-}"
    if [ -z "$DOWNLOAD_MODE" ] && [ -t 0 ]; then
        echo "请选择下载方式："
        echo "  1) 由安装器下载（默认，支持断点续传）"
        echo "  2) 仅显示下载链接（使用浏览器或下载器自行下载）"
        read -r -p "输入编号 [1]: " DOWNLOAD_MODE || DOWNLOAD_MODE="auto"
    fi
    case "${DOWNLOAD_MODE:-auto}" in
        1|auto|download) DOWNLOAD_MODE="auto" ;;
        2|manual|links) DOWNLOAD_MODE="manual" ;;
        *)
            echo -e "${YELLOW}未知下载方式，默认由安装器下载。${NC}"
            DOWNLOAD_MODE="auto"
            ;;
    esac

    download_model_file() {
        local name="$1"
        local filename="$2"
        local url="$3"
        local target="$PROJECT_DIR/models/$filename"

        if [ -f "$target" ]; then
            local fsize
            fsize=$(wc -c <"$target" 2>/dev/null || echo 0)
            if [ "$fsize" -lt 1024 ]; then
                echo -e "${YELLOW}⚠️ 清理异常/空模型残留文件: $filename${NC}"
                rm -f "$target"
            fi
        fi

        echo -e "${CYAN}正在检查/下载 $name -> models/$filename ...${NC}"
        echo "  下载链接：$url"
        echo "  手动续传：env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy curl -L -C - -o \"$target\" \"$url\""
        
        .venv/bin/python3 -c "
import requests, json, os, time, sys

url = '$url'
target = '$target'
model_host = '$MODEL_HOST'
metadata_path = target + '.download-meta.json'

def read_metadata():
    try:
        with open(metadata_path, encoding='utf-8') as metadata_file:
            return json.load(metadata_file)
    except (OSError, ValueError):
        return None

def write_metadata(etag):
    temporary_path = metadata_path + '.tmp'
    with open(temporary_path, 'w', encoding='utf-8') as metadata_file:
        json.dump({'model_host': model_host, 'etag': etag}, metadata_file)
    os.replace(temporary_path, metadata_path)

def discard_partial(reason):
    print(f'  ⚠️ {reason}，将按当前下载节点重新开始。')
    for path in (target, metadata_path):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

while True:
    existing_size = os.path.getsize(target) if os.path.exists(target) else 0
    headers = {'Range': f'bytes={existing_size}-'} if existing_size > 0 else {}
    try:
        r = requests.get(url, headers=headers, stream=True, timeout=20)
        if r.status_code == 416:
            print(f'  ✓ 模型文件已完整存在 ({existing_size/(1024*1024):.1f} MB)，跳过下载。')
            try:
                os.remove(metadata_path)
            except FileNotFoundError:
                pass
            break
        r.raise_for_status()
        metadata = read_metadata() if existing_size > 0 else None
        remote_etag = r.headers.get('etag')

        if existing_size > 0:
            if (not metadata or not metadata.get('etag') or not remote_etag
                    or metadata.get('etag') != remote_etag or r.status_code != 206):
                r.close()
                discard_partial('远端模型已变化或来源无法验证')
                continue
            if metadata.get('model_host') != model_host:
                print('  ⚡ 已确认远端模型未变化，跨下载节点断点续传...')

        write_metadata(remote_etag)
        content_range = r.headers.get('content-range', '')
        total_size = int(content_range.split('/')[-1]) if content_range else int(r.headers.get('content-length', 0)) + existing_size
        
        if existing_size > 0 and existing_size == total_size:
            print(f'  ✓ 模型文件已完整 ({total_size/(1024*1024):.1f} MB)。')
            break
        elif existing_size > 0:
            print(f'  ⚡ 发现上次下载残留 ({existing_size/(1024*1024):.1f} MB)，正在断点续传...')

        with open(target, 'ab' if existing_size > 0 else 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    existing_size += len(chunk)
                    pct = (existing_size / total_size) * 100 if total_size else 0
                    print(f'\r  Progress: {pct:.1f}% ({existing_size/(1024*1024):.1f}/{total_size/(1024*1024):.1f} MB)', end='', flush=True)
        if total_size and existing_size >= total_size:
            print('\n  Done!')
            try:
                os.remove(metadata_path)
            except FileNotFoundError:
                pass
            break
    except Exception as e:
        print(f'\n  连接重试中 (2秒后恢复断点续传: {e})...')
        time.sleep(2)
"
    }

    show_manual_download() {
        local name="$1"
        local filename="$2"
        local url="$3"
        local target="$PROJECT_DIR/models/$filename"

        echo -e "${CYAN}$name${NC}"
        echo "  下载链接：$url"
        echo "  保存位置：$target"
        echo "  断点续传命令：env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy curl -L -C - -o \"$target\" \"$url\""
    }

    if [ "$DOWNLOAD_MODE" = "manual" ]; then
        echo -e "${YELLOW}仅显示下载链接，未开始自动下载。下载完成后将 .gguf 文件放入 models/ 即可。${NC}"
        if [[ "$SELECTED_MODELS" =~ "3B" ]]; then
            show_manual_download "Qwen2.5-3B" "qwen2.5-3b-instruct-q4_k_m.gguf" "$MODEL_HOST/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
        fi
        if [[ "$SELECTED_MODELS" =~ "1.5B" ]]; then
            show_manual_download "Qwen2.5-1.5B" "qwen2.5-1.5b-instruct-q4_k_m.gguf" "$MODEL_HOST/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
        fi
        if [[ "$SELECTED_MODELS" =~ "7B" ]]; then
            show_manual_download "Qwen2.5-7B" "qwen2.5-7b-instruct-q4_k_m.gguf" "$MODEL_HOST/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
        fi
        if [[ "$SELECTED_MODELS" =~ "HYMT" ]]; then
            show_manual_download "Tencent Hy-MT2-1.8B" "Hy-MT2-1.8B-Q4_K_M.gguf" "$MODEL_HOST/tencent/Hy-MT2-1.8B-GGUF/resolve/main/Hy-MT2-1.8B-Q4_K_M.gguf"
        fi
        return
    fi

    if [[ "$SELECTED_MODELS" =~ "3B" ]]; then
        download_model_file "Qwen2.5-3B" "qwen2.5-3b-instruct-q4_k_m.gguf" "$MODEL_HOST/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
    fi
    if [[ "$SELECTED_MODELS" =~ "1.5B" ]]; then
        download_model_file "Qwen2.5-1.5B" "qwen2.5-1.5b-instruct-q4_k_m.gguf" "$MODEL_HOST/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
    fi
    if [[ "$SELECTED_MODELS" =~ "7B" ]]; then
        download_model_file "Qwen2.5-7B" "qwen2.5-7b-instruct-q4_k_m.gguf" "$MODEL_HOST/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
    fi
    if [[ "$SELECTED_MODELS" =~ "HYMT" ]]; then
        download_model_file "Tencent Hy-MT2-1.8B" "Hy-MT2-1.8B-Q4_K_M.gguf" "$MODEL_HOST/tencent/Hy-MT2-1.8B-GGUF/resolve/main/Hy-MT2-1.8B-Q4_K_M.gguf"
    fi

    if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        chown -R "$REAL_USER":"$REAL_USER" "$PROJECT_DIR/models"
    fi
    echo -e "${GREEN}✓ 模型配置完成${NC}\n"
}

# 5. 桌面路径
get_desktop_dir() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "$REAL_HOME/Desktop"
        return
    fi

    if grep -qi microsoft /proc/version 2>/dev/null; then
        local win_desktop
        win_desktop=$(powershell.exe -NoProfile -Command "[Environment]::GetFolderPath('Desktop')" 2>/dev/null | tr -d '\r')
        if [ -n "$win_desktop" ] && which wslpath >/dev/null 2>&1; then
            wslpath "$win_desktop"
            return
        fi
    fi

    if which xdg-user-dir >/dev/null 2>&1; then
        local linux_desktop
        if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
            linux_desktop=$(su - "$REAL_USER" -c "xdg-user-dir DESKTOP")
        else
            linux_desktop=$(xdg-user-dir DESKTOP)
        fi
        if [ -d "$linux_desktop" ]; then
            echo "$linux_desktop"
            return
        fi
    fi

    if [ -d "$REAL_HOME/Desktop" ]; then
        echo "$REAL_HOME/Desktop"
    elif [ -d "$REAL_HOME/桌面" ]; then
        echo "$REAL_HOME/桌面"
    else
        echo "$REAL_HOME"
    fi
}

# 6. 桌面快捷方式与全局命令
configure_launchers() {
    echo -e "${CYAN}[5/6] 桌面快捷方式与全局命令配置...${NC}"
    
    DESKTOP_PATH=$(get_desktop_dir)
    echo -e "检测到桌面路径: ${YELLOW}$DESKTOP_PATH${NC}"

    chmod +x "$PROJECT_DIR/run.sh"
    if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        chown "$REAL_USER":"$REAL_USER" "$PROJECT_DIR/run.sh"
    fi

    read -p "是否在桌面创建双击启动图标？[Y/n]: " CREATE_DESKTOP
    CREATE_DESKTOP=${CREATE_DESKTOP:-Y}

    if [[ "$CREATE_DESKTOP" =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            APP_PATH="$DESKTOP_PATH/AI Translator.app"
            APP_CONTENTS="$APP_PATH/Contents"
            APP_MACOS="$APP_CONTENTS/MacOS"
            APP_RESOURCES="$APP_PATH/Contents/Resources"
            ICON_PATH="$PROJECT_DIR/assets/icons/AI-Translator.icns"
            mkdir -p "$APP_MACOS" "$APP_RESOURCES"
            cat <<'MAC_PLIST_EOF' > "$APP_CONTENTS/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>AI Translator</string>
    <key>CFBundleIconFile</key>
    <string>AI-Translator.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.local.ai-translator</string>
    <key>CFBundleName</key>
    <string>AI Translator</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
</dict>
</plist>
MAC_PLIST_EOF
            cat << MAC_EOF > "$APP_MACOS/AI Translator"
#!/bin/bash
# 此项目是终端交互程序；Finder 启动 .app 时不会自动创建终端窗口。
exec /usr/bin/open -a Terminal "$PROJECT_DIR/run.sh"
MAC_EOF
            chmod +x "$APP_MACOS/AI Translator"
            if [ -f "$ICON_PATH" ]; then
                cp "$ICON_PATH" "$APP_RESOURCES/AI-Translator.icns"
            else
                echo -e "${YELLOW}⚠ 未找到应用图标: $ICON_PATH${NC}"
            fi
            chown -R "$REAL_USER":"$REAL_USER" "$APP_PATH" 2>/dev/null || true
            touch "$APP_PATH"
            echo -e "${GREEN}✓ 已在 macOS 桌面创建 AI Translator.app（原 AI-Translator.command 保留为备用）${NC}"
        elif grep -qi microsoft /proc/version 2>/dev/null; then
            cat << WIN_EOF > "$DESKTOP_PATH/AI-Translator.bat"
@echo off
wsl.exe -e bash "$PROJECT_DIR/run.sh"
WIN_EOF
            echo -e "${GREEN}✓ 已在 Windows 桌面创建 AI-Translator.bat${NC}"
        else
            cat << LINUX_EOF > "$DESKTOP_PATH/AI-Translator.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=AI 终端翻译器
Comment=Universal Local AI Translator powered by GGUF
Exec="$PROJECT_DIR/run.sh"
Icon=$PROJECT_DIR/assets/icons/AI-Translator.png
Terminal=true
Categories=Utility;Translation;Development;
LINUX_EOF
            chmod +x "$DESKTOP_PATH/AI-Translator.desktop"
            if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
                chown "$REAL_USER":"$REAL_USER" "$DESKTOP_PATH/AI-Translator.desktop"
                su - "$REAL_USER" -c "gio set '$DESKTOP_PATH/AI-Translator.desktop' metadata::trusted true" 2>/dev/null || true
            else
                gio set "$DESKTOP_PATH/AI-Translator.desktop" metadata::trusted true 2>/dev/null || true
            fi
            echo -e "${GREEN}✓ 已在 Linux 桌面创建 AI-Translator.desktop 图标${NC}"
        fi
    fi

    echo
    read -p "是否添加全局终端命令 'ai-trans'？[Y/n]: " ADD_GLOBAL
    ADD_GLOBAL=${ADD_GLOBAL:-Y}

    if [[ "$ADD_GLOBAL" =~ ^[Yy]$ ]]; then
        LOCAL_BIN="$REAL_HOME/.local/bin"
        mkdir -p "$LOCAL_BIN"
        ln -sf "$PROJECT_DIR/run.sh" "$LOCAL_BIN/ai-trans"
        ln -sf "$PROJECT_DIR/run.sh" "$LOCAL_BIN/qwen-trans"
        if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
            chown -h "$REAL_USER":"$REAL_USER" "$LOCAL_BIN/ai-trans" "$LOCAL_BIN/qwen-trans"
            chown "$REAL_USER":"$REAL_USER" "$LOCAL_BIN"
        fi
        echo -e "${GREEN}✓ 全局命令已添加: 输入 'ai-trans' 或 'qwen-trans' 即可随时启动${NC}"
        if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
            echo -e "${YELLOW}提示: 请确保 $LOCAL_BIN 已加入你的 PATH 环境变量。${NC}"
        fi
    fi
}

finish_installation() {
    echo -e "\n${CYAN}[6/6] 安装与配置全部完成！${NC}"
    echo -e "${GREEN}${BOLD}================================================================${NC}"
    echo -e "${GREEN}${BOLD}           🎉 AI Terminal Translator 安装成功！                  ${NC}"
    echo -e "${GREEN}${BOLD}================================================================${NC}"
    echo -e "启动方式："
    echo -e "  1. 双击桌面上的 ${BOLD}「AI 终端翻译器」${NC} 图标"
    echo -e "  2. 在任意终端输入：${CYAN}ai-trans${NC} (或 ${CYAN}qwen-trans${NC})"
    echo -e "  3. 在项目根目录执行：${CYAN}./run.sh${NC}"
    echo -e "${GREEN}================================================================${NC}\n"
}

detect_network_region
install_system_dependencies
setup_python_environment
select_and_download_models
configure_launchers
finish_installation
