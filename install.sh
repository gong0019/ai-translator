#!/usr/bin/env bash
# ==============================================================================
# Qwen Terminal Translator - Automated Installer
# Features: Self-Healing on Interruption, Domestic/Global Auto-Routing, Anti-Sudo Trap, TUI
# Options: ./install.sh [--clean | --reinstall]
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 1. 参数解析 (--clean / --reinstall)
CLEAN_MODE=false
if [ "$1" == "--clean" ] || [ "$1" == "--reinstall" ] || [ "$1" == "-f" ]; then
    CLEAN_MODE=true
fi

# 2. 检测真实用户与家目录 (防止 sudo 权限污染)
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    REAL_USER="$USER"
    REAL_HOME="$HOME"
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BLUE}${BOLD}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          🌐 Qwen Terminal Translator - Automated Setup        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 处理 --clean 强制清理模式
if [ "$CLEAN_MODE" = true ]; then
    echo -e "${YELLOW}🧹 触发 --clean 模式：正在清理历史虚拟环境与临时缓存...${NC}"
    rm -rf .venv
    rm -f /tmp/qwen_clipboard_ocr.png
    echo -e "${GREEN}✓ 历史残留清理完毕，即将开始全新纯净安装。${NC}\n"
fi

# 3. 网络区域智能探测 (国内外镜像自动分流)
detect_network_region() {
    echo -e "${CYAN}[1/6] 正在探测网络环境与测速...${NC}"
    
    if curl -sI --connect-timeout 2 "https://huggingface.co" >/dev/null 2>&1; then
        IS_CN=false
        PIP_INDEX=""
        MODEL_BASE_URL="https://huggingface.co/Qwen"
        echo -e "网络节点: ${GREEN}国际网络 (直连 HuggingFace & PyPI)${NC}\n"
    else
        IS_CN=true
        PIP_INDEX="-i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com"
        MODEL_BASE_URL="https://hf-mirror.com/Qwen"
        echo -e "网络节点: ${YELLOW}国内网络 (自动启用 阿里云 PyPI 镜像 + HF-Mirror 模型高速节点)${NC}\n"
    fi
}

# 4. 检查并安装系统级依赖
install_system_dependencies() {
    echo -e "${CYAN}[2/6] 正在检查与安装系统底层依赖 (OCR、C++ 编译环境、剪贴板)...${NC}"
    
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
            xclip wl-clipboard whiptail curl 2>/dev/null || true
    elif which dnf >/dev/null 2>&1; then
        $SUDO_CMD dnf install -y \
            python3 python3-pip python3-devel gcc-c++ cmake \
            tesseract tesseract-langpack-chi_sim tesseract-langpack-jpn \
            xclip wl-clipboard newt curl || true
    elif which pacman >/dev/null 2>&1; then
        $SUDO_CMD pacman -Sy --noconfirm \
            python python-pip python-virtualenv base-devel cmake \
            tesseract tesseract-data-chi_sim tesseract-data-jpn \
            xclip wl-clipboard libnewt curl || true
    elif [[ "$OSTYPE" == "darwin"* ]] && which brew >/dev/null 2>&1; then
        brew install python cmake tesseract tesseract-lang || true
    fi
    echo -e "${GREEN}✓ 系统依赖检查完成${NC}\n"
}

# 5. 自愈型 Python 虚拟环境配置 (损坏自动修复)
setup_python_environment() {
    echo -e "${CYAN}[3/6] 正在配置项目隔离 Python 虚拟环境 (.venv)...${NC}"
    
    # 健康检查：如果已有 .venv，检查核心包是否完整且可被加载
    if [ -d ".venv" ] && [ -f ".venv/bin/python3" ]; then
        if .venv/bin/python3 -c "import llama_cpp, rich, prompt_toolkit, pyperclip, PIL" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ 检测到已有 Python 虚拟环境且状态健康，跳过重复安装。${NC}\n"
            return
        else
            echo -e "${YELLOW}⚠️ 检测到上次安装中断或环境不完整，正在自动清理并重建 .venv ...${NC}"
            rm -rf .venv
        fi
    fi

    # 创建虚拟环境
    if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        sudo -u "$REAL_USER" python3 -m venv .venv
    else
        python3 -m venv .venv || true
    fi

    PIP_EXEC=".venv/bin/pip"
    if [ ! -f "$PIP_EXEC" ]; then
        PIP_EXEC="pip3"
    fi

    echo -e "${YELLOW}正在安装 Python 依赖库 (llama-cpp-python, rich, prompt_toolkit...)${NC}"
    if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        sudo -u "$REAL_USER" $PIP_EXEC install -q --upgrade pip $PIP_INDEX 2>/dev/null || true
        sudo -u "$REAL_USER" $PIP_EXEC install -r requirements.txt $PIP_INDEX
    else
        $PIP_EXEC install -q --upgrade pip $PIP_INDEX 2>/dev/null || true
        $PIP_EXEC install -r requirements.txt $PIP_INDEX --user --break-system-packages 2>/dev/null || $PIP_EXEC install -r requirements.txt $PIP_INDEX
    fi
    echo -e "${GREEN}✓ Python 环境就绪${NC}\n"
}

# 6. TUI 交互式选择模型 (空格勾选，回车确认，断点续传 + 脏文件清洗)
select_and_download_models() {
    echo -e "${CYAN}[4/6] 配置本地 AI 模型...${NC}"
    mkdir -p "$PROJECT_DIR/models"
    if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        chown -R "$REAL_USER":"$REAL_USER" "$PROJECT_DIR/models"
    fi

    SELECTED_MODELS=""
    if which whiptail >/dev/null 2>&1; then
        SELECTED_MODELS=$(whiptail --title "Qwen Translator - 模型下载选择" \
            --checklist "请按 [空格键] 勾选要下载的模型，按 [Tab] 移动至 OK 回车确认：\n" \
            16 78 3 \
            "3B" "Qwen2.5-3B-Instruct (2.0GB) [推荐·高精度·强逻辑]" ON \
            "1.5B" "Qwen2.5-1.5B-Instruct (1.1GB) [极速·轻量·低内存]" OFF \
            "7B" "Qwen2.5-7B-Instruct (4.7GB) [旗舰·出版级文采]" OFF \
            3>&1 1>&2 2>&3 || true)
    fi

    if [ -z "$SELECTED_MODELS" ]; then
        echo -e "${YELLOW}未通过界面选择，默认下载推荐的 Qwen2.5-3B 高精度模型。${NC}"
        SELECTED_MODELS='"3B"'
    fi

    download_model_file() {
        local name="$1"
        local filename="$2"
        local url="$3"
        local target="$PROJECT_DIR/models/$filename"

        # 清洗小于 1KB 的错误/空文件 (如上次中断保存的 HTML 报错页)
        if [ -f "$target" ]; then
            local fsize
            fsize=$(wc -c <"$target" 2>/dev/null || echo 0)
            if [ "$fsize" -lt 1024 ]; then
                echo -e "${YELLOW}⚠️ 清理异常/空模型残留文件: $filename${NC}"
                rm -f "$target"
            fi
        fi

        echo -e "${CYAN}正在检查/下载 $name -> models/$filename ...${NC}"
        
        # 调用具备断点续传与完整性判断的 Python 下载器
        python3 -c "
import requests, os, time, sys

url = '$url'
target = '$target'

while True:
    existing_size = os.path.getsize(target) if os.path.exists(target) else 0
    headers = {'Range': f'bytes={existing_size}-'} if existing_size > 0 else {}
    try:
        r = requests.get(url, headers=headers, stream=True, timeout=20)
        if r.status_code == 416: # Range not satisfiable: 文件已完整
            print(f'  ✓ 模型文件已完整存在 ({existing_size/(1024*1024):.1f} MB)，跳过下载。')
            break
        r.raise_for_status()
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
            break
    except Exception as e:
        print(f'\n  连接重试中 (2秒后恢复断点续传: {e})...')
        time.sleep(2)
"
    }

    if [[ "$SELECTED_MODELS" =~ "3B" ]]; then
        download_model_file "Qwen2.5-3B" "qwen2.5-3b-instruct-q4_k_m.gguf" "$MODEL_BASE_URL/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
    fi
    if [[ "$SELECTED_MODELS" =~ "1.5B" ]]; then
        download_model_file "Qwen2.5-1.5B" "qwen2.5-1.5b-instruct-q4_k_m.gguf" "$MODEL_BASE_URL/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
    fi
    if [[ "$SELECTED_MODELS" =~ "7B" ]]; then
        download_model_file "Qwen2.5-7B" "qwen2.5-7b-instruct-q4_k_m.gguf" "$MODEL_BASE_URL/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
    fi

    if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        chown -R "$REAL_USER":"$REAL_USER" "$PROJECT_DIR/models"
    fi
    echo -e "${GREEN}✓ 模型配置完成${NC}\n"
}

# 7. 跨平台桌面路径探测
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

# 8. 桌面快捷方式与全局命令配置
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
            cat << 'MAC_EOF' > "$DESKTOP_PATH/Qwen-Translator.command"
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
/bin/bash "$PROJECT_DIR/run.sh"
MAC_EOF
            chmod +x "$DESKTOP_PATH/Qwen-Translator.command"
            chown "$REAL_USER" "$DESKTOP_PATH/Qwen-Translator.command" 2>/dev/null || true
            echo -e "${GREEN}✓ 已在 macOS 桌面创建 Qwen-Translator.command${NC}"
        elif grep -qi microsoft /proc/version 2>/dev/null; then
            cat << WIN_EOF > "$DESKTOP_PATH/Qwen-Translator.bat"
@echo off
wsl.exe -e bash "$PROJECT_DIR/run.sh"
WIN_EOF
            echo -e "${GREEN}✓ 已在 Windows 桌面创建 Qwen-Translator.bat${NC}"
        else
            cat << LINUX_EOF > "$DESKTOP_PATH/Qwen-Translator.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Qwen 终端翻译器
Comment=Local AI Translator powered by Qwen2.5
Exec=gnome-terminal --geometry=95x28 --title="Qwen 终端翻译器" -- bash -c "$PROJECT_DIR/run.sh; exec bash"
Icon=accessories-dictionary
Terminal=false
Categories=Utility;Translation;Development;
LINUX_EOF
            chmod +x "$DESKTOP_PATH/Qwen-Translator.desktop"
            if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
                chown "$REAL_USER":"$REAL_USER" "$DESKTOP_PATH/Qwen-Translator.desktop"
                su - "$REAL_USER" -c "gio set '$DESKTOP_PATH/Qwen-Translator.desktop' metadata::trusted true" 2>/dev/null || true
            else
                gio set "$DESKTOP_PATH/Qwen-Translator.desktop" metadata::trusted true 2>/dev/null || true
            fi
            echo -e "${GREEN}✓ 已在 Linux 桌面创建 Qwen-Translator.desktop 图标${NC}"
        fi
    fi

    echo
    read -p "是否添加全局终端命令 'qwen-trans'？[Y/n]: " ADD_GLOBAL
    ADD_GLOBAL=${ADD_GLOBAL:-Y}

    if [[ "$ADD_GLOBAL" =~ ^[Yy]$ ]]; then
        LOCAL_BIN="$REAL_HOME/.local/bin"
        mkdir -p "$LOCAL_BIN"
        ln -sf "$PROJECT_DIR/run.sh" "$LOCAL_BIN/qwen-trans"
        if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
            chown -h "$REAL_USER":"$REAL_USER" "$LOCAL_BIN/qwen-trans"
            chown "$REAL_USER":"$REAL_USER" "$LOCAL_BIN"
        fi
        echo -e "${GREEN}✓ 全局命令已添加: 输入 'qwen-trans' 即可随时启动${NC}"
        if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
            echo -e "${YELLOW}提示: 请确保 $LOCAL_BIN 已加入你的 PATH 环境变量。${NC}"
        fi
    fi
}

# 9. 安装完成总结
finish_installation() {
    echo -e "\n${CYAN}[6/6] 安装与配置全部完成！${NC}"
    echo -e "${GREEN}${BOLD}================================================================${NC}"
    echo -e "${GREEN}${BOLD}           🎉 Qwen Terminal Translator 安装成功！                ${NC}"
    echo -e "${GREEN}${BOLD}================================================================${NC}"
    echo -e "启动方式："
    echo -e "  1. 双击桌面上的 ${BOLD}「Qwen 终端翻译器」${NC} 图标"
    echo -e "  2. 在任意终端输入：${CYAN}qwen-trans${NC}"
    echo -e "  3. 在项目根目录执行：${CYAN}./run.sh${NC}"
    echo -e "\n快捷指令速查："
    echo -e "  • ${BOLD}Ctrl+V${NC} : 智能粘贴 (截图自动本地 OCR 识别并保留排版翻译)"
    echo -e "  • ${BOLD}/lang${NC}  : 切换目标输出语言"
    echo -e "  • ${BOLD}/model${NC} : 切换 3B (高精度) / 1.5B (极速)"
    echo -e "  • ${BOLD}/sleep${NC} : 立即休眠清空内存 (平时 1分钟闲置自动休眠 0 MB)"
    echo -e "  • ${BOLD}/quit${NC}  : 退出程序"
    echo -e "${GREEN}================================================================${NC}\n"
}

# 执行完整流水线
detect_network_region
install_system_dependencies
setup_python_environment
select_and_download_models
configure_launchers
finish_installation
