#!/usr/bin/env bash
# ==============================================================================
# Qwen Terminal Translator - Clean Uninstaller
# Cross-Platform: Linux, macOS, Windows WSL
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 检测真实用户与家目录
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
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${RED}${BOLD}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         🗑️  Qwen Terminal Translator - 卸载与清理向导         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 1. 探测桌面路径
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

DESKTOP_PATH=$(get_desktop_dir)

# 确认卸载
echo -e "${YELLOW}此操作将移除桌面图标、全局快捷命令并清理虚拟环境。${NC}"
read -p "确定要继续卸载 Qwen 终端翻译器吗？[y/N]: " CONFIRM
CONFIRM=${CONFIRM:-N}

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "\n${CYAN}已取消卸载。${NC}"
    exit 0
fi

echo -e "\n${CYAN}正在执行清理任务...${NC}"

# 2. 移除桌面启动图标
if [ -f "$DESKTOP_PATH/Qwen-Translator.desktop" ]; then
    rm -f "$DESKTOP_PATH/Qwen-Translator.desktop"
    echo -e "  ${GREEN}✓ 已移除 Linux 桌面图标: $DESKTOP_PATH/Qwen-Translator.desktop${NC}"
fi

if [ -f "$DESKTOP_PATH/Qwen-Translator.command" ]; then
    rm -f "$DESKTOP_PATH/Qwen-Translator.command"
    echo -e "  ${GREEN}✓ 已移除 macOS 桌面启动器: $DESKTOP_PATH/Qwen-Translator.command${NC}"
fi

if [ -f "$DESKTOP_PATH/Qwen-Translator.bat" ]; then
    rm -f "$DESKTOP_PATH/Qwen-Translator.bat"
    echo -e "  ${GREEN}✓ 已移除 Windows WSL 桌面启动器: $DESKTOP_PATH/Qwen-Translator.bat${NC}"
fi

# 3. 移除全局终端软链接
if [ -L "$REAL_HOME/.local/bin/qwen-trans" ] || [ -f "$REAL_HOME/.local/bin/qwen-trans" ]; then
    rm -f "$REAL_HOME/.local/bin/qwen-trans"
    echo -e "  ${GREEN}✓ 已移除全局终端命令: $REAL_HOME/.local/bin/qwen-trans${NC}"
fi

# 4. 清理虚拟环境与临时缓存
if [ -d "$PROJECT_DIR/.venv" ]; then
    rm -rf "$PROJECT_DIR/.venv"
    echo -e "  ${GREEN}✓ 已清理 Python 虚拟环境 (.venv/)${NC}"
fi

rm -rf "$PROJECT_DIR/__pycache__"
rm -f /tmp/qwen_clipboard_ocr.png

# 5. 询问是否删除已下载的模型文件 (大文件)
echo
read -p "是否同时删除 models/ 目录下已下载的模型权重文件 (~几GB)？[y/N]: " DEL_MODELS
DEL_MODELS=${DEL_MODELS:-N}

if [[ "$DEL_MODELS" =~ ^[Yy]$ ]]; then
    rm -f "$PROJECT_DIR/models/"*.gguf
    echo -e "  ${GREEN}✓ 已清理所有本地模型权重文件 (models/*.gguf)${NC}"
else
    echo -e "  ${YELLOW}ℹ️ 保留已下载的模型权重文件，下次重新安装时可秒级复用。${NC}"
fi

echo -e "\n${GREEN}${BOLD}================================================================${NC}"
echo -e "${GREEN}${BOLD}        🎉 Qwen Terminal Translator 卸载与清理完成！            ${NC}"
echo -e "${GREEN}${BOLD}================================================================${NC}"
echo -e "若需完全彻底移除本目录，可直接执行："
echo -e "  ${CYAN}rm -rf $PROJECT_DIR${NC}\n"
