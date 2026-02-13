# -*- coding: utf-8 -*-
"""
CosyVoice TTS 插件

基于阿里 FunAudioLLM/CosyVoice 的语音合成插件
支持多语言、音色克隆、情感控制

GitHub: https://github.com/FunAudioLLM/CosyVoice
"""

import os
import sys
import tempfile
from typing import Dict, List, Any

# 导入基类
from ..base import BaseTTSPlugin


class CosyVoiceTTS(BaseTTSPlugin):
    """
    CosyVoice 语音合成插件

    特点：
    - 8种预设音色
    - 支持跨语言克隆
    - 情感控制（通过指令）
    - 高质量语音合成
    """

    # 预设音色列表
    DEFAULT_VOICES = [
        "中文女",
        "中文男",
        "日语男",
        "粤语女",
        "英文女",
        "英文男",
        "韩语女",
        "清新女声",  # CosyVoice2新增
    ]

    @property
    def name(self) -> str:
        return "cosyvoice"

    @property
    def version(self) -> str:
        return "1.0.0"

    def load(self, config: dict = None) -> bool:
        """
        加载 CosyVoice 模型

        Args:
            config: 配置字典
                - model_path: 模型路径
                - device: 设备 (cuda/cpu)

        Returns:
            bool: 是否加载成功
        """
        config = config or self.config

        if not config.get("enabled", True):
            print("⚠️ CosyVoice 已禁用")
            return False

        try:
            # 添加 CosyVoice 库路径
            cosyvoice_lib = config.get("cosyvoice_lib") or config.get("paths", {}).get(
                "cosyvoice"
            )
            if cosyvoice_lib and cosyvoice_lib not in sys.path:
                sys.path.insert(0, cosyvoice_lib)

            # 添加 Matcha-TTS 路径 (required by CosyVoice)
            import os as _os

            matcha_path = _os.path.join(cosyvoice_lib, "third_party", "Matcha-TTS")
            if _os.path.exists(matcha_path) and matcha_path not in sys.path:
                sys.path.insert(0, matcha_path)
                print(f"   已添加 Matcha-TTS 路径: {matcha_path}")

            from cosyvoice.cli.cosyvoice import CosyVoice

            model_path = config.get("model_path") or config.get("paths", {}).get(
                "cosyvoice"
            )

            print(f"🔄 正在加载 CosyVoice...")
            print(f"   模型路径: {model_path}")

            # 检查路径是否存在
            if not os.path.exists(model_path):
                print(f"❌ 模型路径不存在: {model_path}")
                return False

            self.model = CosyVoice(model_path)
            self._loaded = True

            # 获取可用音色
            voices = self.get_voices()
            print(f"✅ CosyVoice 加载成功")
            print(f"   可用音色: {len(voices)}个")

            return True

        except ImportError as e:
            print(f"❌ 导入失败: {e}")
            print(f"   请确保 CosyVoice 代码库路径正确")
            return False
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def synthesize(self, text: str, voice: str = None, **kwargs) -> str:
        """
        语音合成

        Args:
            text: 要合成的文本
            voice: 音色名称（默认使用配置中的默认值）
            **kwargs: 额外参数
                - speed: 语速 (未使用，CosyVoice暂不支持)
                - instruction: 指令（如"用开心的语气说"）

        Returns:
            str: 生成的音频文件路径
        """
        if not self.is_loaded():
            raise RuntimeError("CosyVoice 模型未加载")

        # 使用默认音色
        voice = voice or self.config.get("default_voice", "中文女")

        # 检查音色是否有效
        available_voices = self._get_voice_ids()
        if voice not in available_voices:
            print(f"⚠️ 未知音色 '{voice}'，使用默认音色")
            voice = "中文女"

        # 生成临时文件路径
        output_path = os.path.join(
            tempfile.gettempdir(), f"cosyvoice_{os.getpid()}_{hash(text) % 10000}.wav"
        )

        try:
            import torchaudio

            # 获取指令（如果有）
            instruction = kwargs.get("instruction", "")

            # 合成语音
            if instruction:
                # 使用指令模式
                result = self.model.inference_instruct(text, voice, instruction)
            else:
                # 使用预设音色模式
                result = self.model.inference_sft(text, voice, stream=False)

            # 保存音频
            for item in result:
                torchaudio.save(output_path, item["tts_speech"], 22050)
                break  # 只取第一个结果

            return output_path

        except Exception as e:
            raise RuntimeError(f"语音合成失败: {e}")

    def get_voices(self) -> List[Dict[str, str]]:
        """
        获取可用音色列表

        Returns:
            list: 音色信息列表
        """
        if not self.is_loaded():
            # 返回默认列表
            return [
                {
                    "id": v,
                    "name": v,
                    "language": self._get_voice_language(v),
                    "gender": self._get_voice_gender(v),
                }
                for v in self.DEFAULT_VOICES
            ]

        try:
            # 尝试从模型获取
            voices = self.model.list_available_spks()
            if voices:
                return [
                    {
                        "id": v,
                        "name": v,
                        "language": self._get_voice_language(v),
                        "gender": self._get_voice_gender(v),
                    }
                    for v in voices
                ]
        except:
            pass

        # 返回默认列表
        return [
            {
                "id": v,
                "name": v,
                "language": self._get_voice_language(v),
                "gender": self._get_voice_gender(v),
            }
            for v in self.DEFAULT_VOICES
        ]

    def _get_voice_ids(self) -> List[str]:
        """获取音色ID列表"""
        voices = self.get_voices()
        return [v["id"] for v in voices]

    def _get_voice_language(self, voice: str) -> str:
        """根据音色名称推断语言"""
        if "中文" in voice or "粤语" in voice:
            return "zh"
        elif "英文" in voice:
            return "en"
        elif "日语" in voice:
            return "ja"
        elif "韩语" in voice:
            return "ko"
        return "zh"

    def _get_voice_gender(self, voice: str) -> str:
        """根据音色名称推断性别"""
        if "男" in voice:
            return "male"
        elif "女" in voice:
            return "female"
        return "female"

    def clone_voice(self, reference_audio: str, text: str) -> str:
        """
        音色克隆（方案B实现）

        Args:
            reference_audio: 参考音频路径
            text: 要合成的文本

        Returns:
            str: 生成的音频文件路径
        """
        if not self.is_loaded():
            raise RuntimeError("CosyVoice 模型未加载")

        # TODO: 方案B实现跨语言音色克隆
        raise NotImplementedError("音色克隆功能在方案B中实现")
