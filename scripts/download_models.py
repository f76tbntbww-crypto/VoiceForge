#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型下载脚本

自动从 ModelScope 下载 SenseVoice 和 CosyVoice 模型

使用方法：
    python scripts/download_models.py
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def download_sensevoice():
    """下载 SenseVoice 模型"""
    print("=" * 60)
    print("下载 SenseVoice 模型")
    print("=" * 60)

    model_dir = project_root / "models" / "asr" / "SenseVoiceSmall"

    if model_dir.exists():
        print(f"⚠️  模型目录已存在: {model_dir}")
        response = input("是否重新下载？(y/n): ")
        if response.lower() != "y":
            print("跳过下载")
            return

    try:
        from modelscope import snapshot_download

        print("开始下载...")
        print("模型大小: 约 800MB")
        print("这可能需要几分钟时间...")
        print()

        downloaded_path = snapshot_download(
            "iic/SenseVoiceSmall", local_dir=str(model_dir)
        )

        print(f"✅ 下载完成: {downloaded_path}")

    except Exception as e:
        print(f"❌ 下载失败: {e}")
        print()
        print("手动下载方法：")
        print("1. 访问 https://modelscope.cn/models/iic/SenseVoiceSmall")
        print("2. 点击 '下载模型' 按钮")
        print(f"3. 解压到: {model_dir}")


def download_cosyvoice():
    """下载 CosyVoice 模型"""
    print()
    print("=" * 60)
    print("下载 CosyVoice 模型")
    print("=" * 60)

    model_dir = project_root / "models" / "tts" / "CosyVoice-300M-SFT"

    if model_dir.exists():
        print(f"⚠️  模型目录已存在: {model_dir}")
        response = input("是否重新下载？(y/n): ")
        if response.lower() != "y":
            print("跳过下载")
            return

    try:
        from modelscope import snapshot_download

        print("开始下载...")
        print("模型大小: 约 3GB")
        print("这可能需要 10-15 分钟...")
        print()

        downloaded_path = snapshot_download(
            "iic/CosyVoice-300M-SFT", local_dir=str(model_dir)
        )

        print(f"✅ 下载完成: {downloaded_path}")

    except Exception as e:
        print(f"❌ 下载失败: {e}")
        print()
        print("手动下载方法：")
        print("1. 访问 https://modelscope.cn/models/iic/CosyVoice-300M-SFT")
        print("2. 点击 '下载模型' 按钮")
        print(f"3. 解压到: {model_dir}")


def download_cosyvoice_lib():
    """下载 CosyVoice 代码库"""
    print()
    print("=" * 60)
    print("下载 CosyVoice 代码库")
    print("=" * 60)

    lib_dir = project_root / "libs" / "CosyVoice"

    if lib_dir.exists():
        print(f"⚠️  代码库已存在: {lib_dir}")
        response = input("是否重新下载？(y/n): ")
        if response.lower() != "y":
            print("跳过下载")
            return

    print("从 GitHub 克隆 CosyVoice...")
    print()

    import subprocess

    # 创建 libs 目录
    libs_dir = project_root / "libs"
    libs_dir.mkdir(exist_ok=True)

    # 克隆仓库
    result = subprocess.run(
        ["git", "clone", "https://github.com/FunAudioLLM/CosyVoice.git", str(lib_dir)],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"✅ 克隆完成: {lib_dir}")
    else:
        print(f"❌ 克隆失败: {result.stderr}")
        print()
        print("手动下载方法：")
        print("1. 访问 https://github.com/FunAudioLLM/CosyVoice")
        print("2. 下载 ZIP 文件")
        print(f"3. 解压到: {lib_dir}")


def main():
    """主函数"""
    print()
    print("🚀 VoiceForge 模型下载工具")
    print()

    # 检查 modelscope
    try:
        from modelscope import snapshot_download
    except ImportError:
        print("❌ 未安装 modelscope")
        print("请先运行: pip install modelscope")
        return

    print("请选择要下载的模型：")
    print("  1. SenseVoice (ASR) - 约 800MB")
    print("  2. CosyVoice (TTS) - 约 3GB")
    print("  3. CosyVoice 代码库")
    print("  4. 全部下载")
    print("  5. 退出")
    print()

    choice = input("请输入选项 (1-5): ").strip()

    if choice == "1":
        download_sensevoice()
    elif choice == "2":
        download_cosyvoice()
    elif choice == "3":
        download_cosyvoice_lib()
    elif choice == "4":
        download_sensevoice()
        download_cosyvoice()
        download_cosyvoice_lib()
    elif choice == "5":
        print("退出")
        return
    else:
        print("无效的选项")
        return

    print()
    print("=" * 60)
    print("下载完成！")
    print("=" * 60)
    print()
    print("请编辑 config.yaml 确认模型路径配置正确")
    print()


if __name__ == "__main__":
    main()
