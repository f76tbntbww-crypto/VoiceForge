# -*- coding: utf-8 -*-
"""
Plugin Manager - 插件管理模块

功能（方案B实现）：
- 插件注册：动态加载插件
- 插件发现：自动识别可用插件
- 版本管理：插件依赖检查
- 热加载：运行时更新

方案A状态：预留框架，基础功能
"""

import os
import sys
import importlib
import importlib.util
from typing import Dict, Type, Any


class PluginManager:
    """
    插件管理器

    当前方案A：基础功能，手动注册
    未来方案B：
    - 自动发现插件
    - 动态加载
    - 依赖管理
    """

    def __init__(self, config=None):
        """
        初始化插件管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.plugins = {
            "asr": {},  # name -> class
            "tts": {},
            "llm": {},
        }
        self.instances = {}  # name -> instance

    def register(self, plugin_type: str, name: str, plugin_class: Type):
        """
        注册插件

        Args:
            plugin_type: 插件类型 (asr/tts/llm)
            name: 插件名称
            plugin_class: 插件类
        """
        if plugin_type not in self.plugins:
            raise ValueError(f"未知插件类型: {plugin_type}")

        self.plugins[plugin_type][name] = plugin_class
        print(f"✅ 插件注册成功: [{plugin_type}] {name}")

    def load(self, plugin_type: str, name: str, config: dict = None):
        """
        加载插件实例

        Args:
            plugin_type: 插件类型
            name: 插件名称
            config: 插件配置

        Returns:
            插件实例
        """
        instance_key = f"{plugin_type}:{name}"

        # 如果已加载，直接返回
        if instance_key in self.instances:
            return self.instances[instance_key]

        # 获取插件类
        if name not in self.plugins[plugin_type]:
            raise ValueError(f"插件未注册: [{plugin_type}] {name}")

        plugin_class = self.plugins[plugin_type][name]

        # 创建实例
        try:
            instance = plugin_class(config or {})
            self.instances[instance_key] = instance
            print(f"✅ 插件加载成功: [{plugin_type}] {name}")
            return instance
        except Exception as e:
            print(f"❌ 插件加载失败: [{plugin_type}] {name} - {e}")
            raise

    def get(self, plugin_type: str, name: str):
        """
        获取已加载的插件实例

        Args:
            plugin_type: 插件类型
            name: 插件名称

        Returns:
            插件实例或None
        """
        instance_key = f"{plugin_type}:{name}"
        return self.instances.get(instance_key)

    def list_plugins(self, plugin_type: str = None):
        """
        列出可用插件

        Args:
            plugin_type: 插件类型（可选）

        Returns:
            dict: 插件列表
        """
        if plugin_type:
            return {plugin_type: list(self.plugins.get(plugin_type, {}).keys())}
        return {t: list(plugins.keys()) for t, plugins in self.plugins.items()}

    def unload(self, plugin_type: str, name: str):
        """
        卸载插件

        Args:
            plugin_type: 插件类型
            name: 插件名称
        """
        instance_key = f"{plugin_type}:{name}"
        if instance_key in self.instances:
            # 调用清理方法（如果有）
            instance = self.instances[instance_key]
            if hasattr(instance, "cleanup"):
                instance.cleanup()
            del self.instances[instance_key]
            print(f"✅ 插件卸载成功: [{plugin_type}] {name}")

    def unload_all(self):
        """卸载所有插件"""
        for key in list(self.instances.keys()):
            plugin_type, name = key.split(":")
            self.unload(plugin_type, name)

    def auto_discover(self, plugin_dir: str):
        """
        自动发现插件（方案B实现）

        Args:
            plugin_dir: 插件目录
        """
        # 方案B：自动扫描目录加载插件
        # 方案A：手动注册
        pass


# 全局插件管理器实例
_plugin_manager = None


def get_plugin_manager(config=None):
    """
    获取全局插件管理器实例

    Args:
        config: 配置字典

    Returns:
        PluginManager: 插件管理器实例
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager(config)
    return _plugin_manager
