# -*- coding: utf-8 -*-
"""
VoiceForge - 核心框架模块

包含：
- session_manager: 会话管理
- pipeline: 处理管道
- router: 智能路由
- plugin_manager: 插件系统

注意：方案A（技术预览版）中这些模块为预留框架，
      功能在方案B/C中逐步实现。
"""

__version__ = "1.0.0-preview"
__all__ = [
    "session_manager",
    "pipeline",
    "router",
    "plugin_manager",
]
