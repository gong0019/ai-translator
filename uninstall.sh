#!/usr/bin/env bash
# ==============================================================================
# AI Terminal Translator - Clean & Safe Uninstaller
# Safety: Strict Directory Guardrails (Zero-Risk of Deleting User Files)
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ -z "$PROJECT_DIR" ] || [ "$PROJECT_DIR" == "/" ] || [ "$PROJECT_DIR" == "$HOME" ]; then
    echo -e "\033[0;31m❌ 安全拦截: 项目路径异常 ($PROJECT_DIR)，为保护系统已终止执行。\033[0m"
    exit 1
fi

if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    REAL_USER="$USER"
    REAL_HOME="$HOME"
fi

if [ -z "$REAL_HOME" ] || [ "$REAL_HOME" == "/" ]; then
    REAL_HOME="$HOME"
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${RED}${BOLD}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          🗑️  AI Terminal Translator - 卸载与清理向导          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

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
            linux_desktop=$(su - "$REAL_USER" -c "xdg-user-dir DESKTOP" 2>/dev/null || true)
        else
            linux_desktop=$(xdg-user-dir DESKTOP 2>/dev/null || true)
        fi
        if [ -n "$linux_desktop" ] && [ -d "$linux_desktop" ]; then
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

DESKTOP_PATH=$(get_desktop_dir)

echo -e "${YELLOW}此操作将仅移除本工具生成的桌面图标、全局快捷命令并清理内部虚拟环境。${NC}"
echo -e "${CYAN}受影响范围仅限于本仓库目录与快捷方式，绝不会触碰您的任何系统或个人文件。${NC}\n"

read -p "确定要继续卸载 AI 终端翻译器吗？[y/N]: " CONFIRM
CONFIRM=${CONFIRM:-N}

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "\n${CYAN}已取消卸载。${NC}"
    exit 0
fi

echo -e "\n${CYAN}正在执行安全清理...${NC}"

# 清理桌面启动图标 (兼容旧名与新名)
if [ -n "$DESKTOP_PATH" ] && [ -d "$DESKTOP_PATH" ]; then
    for item in "AI-Translator.desktop" "Qwen-Translator.desktop" "AI-Translator.command" "Qwen-Translator.command" "AI-Translator.bat" "Qwen-Translator.bat"; do
        if [ -f "$DESKTOP_PATH/$item" ]; then
            rm -f "$DESKTOP_PATH/$item"
            echo -e "  ${GREEN}✓ 已移除桌面图标: $DESKTOP_PATH/$item${NC}"
        fi
    done
    if [ -d "$DESKTOP_PATH/AI Translator.app" ]; then
        rm -rf "$DESKTOP_PATH/AI Translator.app"
        echo -e "  ${GREEN}✓ 已移除 macOS 应用图标: $DESKTOP_PATH/AI Translator.app${NC}"
    fi
fi

# 清理全局命令
for cmd in "ai-trans" "qwen-trans"; do
    if [ -L "$REAL_HOME/.local/bin/$cmd" ] || [ -f "$REAL_HOME/.local/bin/$cmd" ]; then
        rm -f "$REAL_HOME/.local/bin/$cmd"
        echo -e "  ${GREEN}✓ 已移除全局终端命令: $REAL_HOME/.local/bin/$cmd${NC}"
    fi
done

# 清理虚拟环境与临时文件
if [ -d "$PROJECT_DIR/.venv" ]; then
    rm -rf "$PROJECT_DIR/.venv"
    echo -e "  ${GREEN}✓ 已清理 Python 虚拟环境 ($PROJECT_DIR/.venv/)${NC}"
fi

rm -rf "$PROJECT_DIR/__pycache__"
rm -f /tmp/ai_translator_clipboard_ocr.png
rm -f /tmp/qwen_clipboard_ocr.png

# 询问删除模型
echo
read -r -p "是否删除 models/ 中已下载的模型文件（默认保留，下次安装可直接复用）？[y/N]: " DEL_MODELS || DEL_MODELS="N"
DEL_MODELS=${DEL_MODELS:-N}

if [[ "$DEL_MODELS" =~ ^[Yy]$ ]]; then
    if [ -d "$PROJECT_DIR/models" ]; then
        rm -f "$PROJECT_DIR/models/"*.gguf
        rm -f "$PROJECT_DIR/models/"*.download-meta.json
        echo -e "  ${GREEN}✓ 已清理本地模型权重文件 ($PROJECT_DIR/models/*.gguf)${NC}"
    fi
else
    echo -e "  ${YELLOW}ℹ️ 保留已下载的模型权重文件，下次重新安装时可秒级复用。${NC}"
fi

echo -e "\n${GREEN}${BOLD}================================================================${NC}"
echo -e "${GREEN}${BOLD}         🎉 AI Terminal Translator 卸载与清理完成！             ${NC}"
echo -e "${GREEN}${BOLD}================================================================${NC}"
echo -e "若需完全彻底移除本工具源码目录，可直接执行："
echo -e "  ${CYAN}rm -rf $PROJECT_DIR${NC}\n"
