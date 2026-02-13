# -*- coding: utf-8 -*-
"""
Plugin Base - 插件基类模块

定义所有插件必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

# ==================== ASR 插件基类 ====================


class BaseASRPlugin(ABC):
    """
    ASR (语音识别) 插件基类

    所有 ASR 插件必须继承此类并实现抽象方法

    Example:
        class MyASR(BaseASRPlugin):
            @property
            def name(self) -> str:
                return "my_asr"

            def load(self, config: dict) -> bool:
                # 加载模型
                return True

            def transcribe(self, audio_path: str, language: str = "auto") -> dict:
                # 识别语音
                return {"text": "识别结果", "language": "zh"}
    """

    def __init__(self, config: dict = None):
        """
        初始化插件

        Args:
            config: 插件配置字典
        """
        self.config = config or {}
        self.model = None
        self._loaded = False

    @property
    @abstractmethod
    def name(self) -> str:
        """
        插件名称

        Returns:
            str: 唯一标识名称
        """
        pass

    @property
    def version(self) -> str:
        """
        插件版本（可选重写）

        Returns:
            str: 版本号，默认 "1.0.0"
        """
        return "1.0.0"

    @abstractmethod
    def load(self, config: dict = None) -> bool:
        """
        加载模型

        Args:
            config: 加载配置

        Returns:
            bool: 是否加载成功
        """
        pass

    @abstractmethod
    def transcribe(self, audio_path: str, language: str = "auto") -> Dict[str, Any]:
        """
        语音识别

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (auto/zh/en/ja/ko/yue/...)

        Returns:
            dict: 识别结果
            {
                "success": bool,
                "text": str,           # 识别文本
                "language": str,       # 检测到的语言
                "confidence": float,   # 置信度 (可选)
                "duration": float      # 音频时长 (可选)
            }
        """
        pass

    def is_loaded(self) -> bool:
        """
        检查模型是否已加载

        Returns:
            bool: 是否已加载
        """
        return self._loaded and self.model is not None

    def get_supported_languages(self) -> List[str]:
        """
        获取支持的语言列表（可选重写）

        Returns:
            list: 语言代码列表
        """
        return ["auto", "zh", "en"]

    def cleanup(self):
        """
        清理资源（可选重写）

        在插件卸载时调用
        """
        self.model = None
        self._loaded = False


# ==================== TTS 插件基类 ====================


class BaseTTSPlugin(ABC):
    """
    TTS (语音合成) 插件基类

    所有 TTS 插件必须继承此类并实现抽象方法

    Example:
        class MyTTS(BaseTTSPlugin):
            @property
            def name(self) -> str:
                return "my_tts"

            def load(self, config: dict) -> bool:
                # 加载模型
                return True

            def synthesize(self, text: str, voice: str) -> str:
                # 合成语音
                return "/path/to/audio.wav"
    """

    def __init__(self, config: dict = None):
        """
        初始化插件

        Args:
            config: 插件配置字典
        """
        self.config = config or {}
        self.model = None
        self._loaded = False

    @property
    @abstractmethod
    def name(self) -> str:
        """
        插件名称

        Returns:
            str: 唯一标识名称
        """
        pass

    @property
    def version(self) -> str:
        """
        插件版本（可选重写）

        Returns:
            str: 版本号，默认 "1.0.0"
        """
        return "1.0.0"

    @abstractmethod
    def load(self, config: dict = None) -> bool:
        """
        加载模型

        Args:
            config: 加载配置

        Returns:
            bool: 是否加载成功
        """
        pass

    @abstractmethod
    def synthesize(self, text: str, voice: str = None, **kwargs) -> str:
        """
        语音合成

        Args:
            text: 要合成的文本
            voice: 音色名称 (可选)
            **kwargs: 额外参数
                - speed: 语速 (0.5-2.0)
                - pitch: 音调
                - emotion: 情感

        Returns:
            str: 生成的音频文件路径
        """
        pass

    @abstractmethod
    def get_voices(self) -> List[Dict[str, str]]:
        """
        获取可用音色列表

        Returns:
            list: 音色信息列表
            [
                {
                    "id": "voice_id",
                    "name": "显示名称",
                    "language": "zh",
                    "gender": "female"
                },
                ...
            ]
        """
        pass

    def is_loaded(self) -> bool:
        """
        检查模型是否已加载

        Returns:
            bool: 是否已加载
        """
        return self._loaded and self.model is not None

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的音频格式（可选重写）

        Returns:
            list: 格式列表
        """
        return ["wav"]

    def cleanup(self):
        """
        清理资源（可选重写）

        在插件卸载时调用
        """
        self.model = None
        self._loaded = False


# ==================== LLM 插件基类（预留） ====================


class BaseLLMPlugin(ABC):
    """
    LLM (大语言模型) 插件基类（预留）

    方案A中 LLM 通过 Ollama 调用，不需要插件
    方案B/C 可以实现自定义 LLM 后端
    """

    def __init__(self, config: dict = None):
        self.config = config or {}

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def load(self, config: dict = None) -> bool:
        pass

    @abstractmethod
    def chat(self, message: str, history: list = None, **kwargs) -> str:
        """
        对话生成

        Args:
            message: 用户消息
            history: 历史对话
            **kwargs: 生成参数
                - max_tokens: 最大token数
                - temperature: 温度
                - top_p: top-p采样

        Returns:
            str: AI回复
        """
        pass

    @abstractmethod
    def stream_chat(self, message: str, history: list = None, **kwargs):
        """
        流式对话（方案C实现）

        Yields:
            str: 生成的文本片段
        """
        pass
