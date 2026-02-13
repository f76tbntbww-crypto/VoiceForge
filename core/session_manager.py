# -*- coding: utf-8 -*-
"""
Session Manager - 会话管理模块

功能（方案B/C实现）：
- 多轮对话上下文管理
- 会话持久化
- 用户隔离
- 过期清理

方案A状态：预留框架，暂未实现
"""


class SessionManager:
    """
    会话管理器

    未来功能：
    - 保存对话历史
    - 支持多用户会话
    - 会话恢复
    - 自动过期清理
    """

    def __init__(self, config=None):
        """
        初始化会话管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.sessions = {}  # session_id -> history

    def create_session(self, session_id=None):
        """
        创建新会话

        Args:
            session_id: 会话ID（可选，自动生成）

        Returns:
            str: 会话ID
        """
        # 方案A：简单返回空会话
        return session_id or "default"

    def get_history(self, session_id):
        """
        获取会话历史

        Args:
            session_id: 会话ID

        Returns:
            list: 对话历史
        """
        # 方案A：返回空列表
        return []

    def add_message(self, session_id, role, content):
        """
        添加消息到会话

        Args:
            session_id: 会话ID
            role: 角色 (user/assistant)
            content: 内容
        """
        # 方案B/C 实现
        pass

    def clear_session(self, session_id):
        """
        清除会话

        Args:
            session_id: 会话ID
        """
        if session_id in self.sessions:
            del self.sessions[session_id]

    def cleanup_expired(self):
        """清理过期会话"""
        # 方案B/C 实现
        pass


# 全局会话管理器实例（单例模式）
_session_manager = None


def get_session_manager(config=None):
    """
    获取全局会话管理器实例

    Args:
        config: 配置字典

    Returns:
        SessionManager: 会话管理器实例
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(config)
    return _session_manager
