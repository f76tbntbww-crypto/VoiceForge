# -*- coding: utf-8 -*-
"""
SenseVoice ASR 插件

基于阿里 FunAudioLLM/SenseVoice 的语音识别插件
支持多语言、情感识别、高效推理

GitHub: https://github.com/FunAudioLLM/SenseVoice
"""

import os
import sys
import re
from typing import Dict, Any, List

# 导入基类
from ..base import BaseASRPlugin


class SenseVoiceASR(BaseASRPlugin):
    """
    SenseVoice 语音识别插件

    特点：
    - 支持 50+ 语言
    - 推理速度极快 (70ms for 10s audio)
    - 支持情感识别
    - 支持声音事件检测
    """

    @property
    def name(self) -> str:
        return "sensevoice"

    @property
    def version(self) -> str:
        return "1.0.0"

    def load(self, config: dict = None) -> bool:
        """
        加载 SenseVoice 模型

        Args:
            config: 配置字典
                - model_path: 模型路径
                - device: 设备 (cuda/cpu)

        Returns:
            bool: 是否加载成功
        """
        config = config or self.config

        if not config.get("enabled", True):
            print("⚠️ SenseVoice 已禁用")
            return False

        try:
            from funasr import AutoModel

            model_path = config.get("model_path") or config.get("paths", {}).get(
                "sensevoice"
            )
            device = config.get("device", "cuda")

            print(f"🔄 正在加载 SenseVoice...")
            print(f"   模型路径: {model_path}")
            print(f"   设备: {device}")

            # 检查路径是否存在
            if not os.path.exists(model_path):
                print(f"❌ 模型路径不存在: {model_path}")
                return False

            self.model = AutoModel(
                model=model_path,
                device=device,
                disable_update=True,
                trust_remote_code=True,
            )

            self._loaded = True
            print(f"✅ SenseVoice 加载成功")
            return True

        except ImportError as e:
            print(f"❌ 导入失败: {e}")
            print(f"   请确保已安装 funasr: pip install funasr")
            return False
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return False

    def transcribe(self, audio_path: str, language: str = "auto") -> Dict[str, Any]:
        """
        语音识别

        Args:
            audio_path: 音频文件路径
            language: 语言代码
                - auto: 自动检测
                - zh: 中文
                - en: 英语
                - ja: 日语
                - ko: 韩语
                - yue: 粤语

        Returns:
            dict: 识别结果
            {
                "success": bool,
                "text": str,
                "language": str,
                "raw_result": dict  # 原始结果（包含情感等）
            }
        """
        if not self.is_loaded():
            return {"success": False, "error": "模型未加载", "text": "", "language": ""}

        try:
            # 执行识别
            result = self.model.generate(
                input=audio_path, language=language, use_itn=True
            )

            # 解析结果
            if result and len(result) > 0:
                raw_text = result[0].get("text", "")

                # 移除标签（如 <|zh|><|NEUTRAL|><|Speech|>）
                text = re.sub(r"<\|[^|]+\|>", "", raw_text).strip()

                # 提取语言标签
                lang_match = re.search(r"<\|(\w{2})\|>", raw_text)
                detected_lang = lang_match.group(1) if lang_match else language

                return {
                    "success": True,
                    "text": text,
                    "language": detected_lang,
                    "raw_result": result[0],
                }
            else:
                return {
                    "success": False,
                    "error": "未能识别",
                    "text": "",
                    "language": "",
                }

        except Exception as e:
            return {"success": False, "error": str(e), "text": "", "language": ""}

    def get_supported_languages(self) -> List[str]:
        """
        获取支持的语言列表

        Returns:
            list: 语言代码列表
        """
        return [
            "auto",  # 自动检测
            "zh",  # 中文（普通话）
            "en",  # 英语
            "ja",  # 日语
            "ko",  # 韩语
            "yue",  # 粤语
            "ms",  # 马来语
            "id",  # 印尼语
            "vi",  # 越南语
            "th",  # 泰语
            "ar",  # 阿拉伯语
            "ru",  # 俄语
            "es",  # 西班牙语
            "pt",  # 葡萄牙语
            "de",  # 德语
            "fr",  # 法语
            "it",  # 意大利语
            "hi",  # 印地语
        ]

    def get_emotions(self) -> List[str]:
        """
        获取支持的情感标签

        Returns:
            list: 情感标签列表
        """
        return [
            "NEUTRAL",  # 中性
            "HAPPY",  # 开心
            "SAD",  # 悲伤
            "ANGRY",  # 生气
            "FEAR",  # 恐惧
        ]
