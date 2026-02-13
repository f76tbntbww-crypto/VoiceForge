# -*- coding: utf-8 -*-
"""
VoiceForge REST API Server

提供 RESTful API 接口：
- /          - 服务状态
- /asr       - 语音识别
- /tts       - 语音合成
- /chat      - AI对话
- /complete  - 完整流程 (ASR+LLM+TTS)
- /voices    - 获取音色列表

启动方式：
    python api/rest_api.py

或使用脚本：
    ..\scripts\start_api.bat
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify, send_file
import yaml

# 导入插件
from plugins.asr.sensevoice import SenseVoiceASR
from plugins.tts.cosyvoice import CosyVoiceTTS

# ==================== 加载配置 ====================


def load_config():
    """加载配置文件"""
    config_path = project_root / "config.yaml"
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 处理相对路径
    config = resolve_paths(config, project_root)
    return config


def resolve_paths(config, root_path):
    """将相对路径转换为绝对路径"""
    paths = config.get("paths", {})

    # 处理 models 路径
    if "models" in paths:
        for key, path in paths["models"].items():
            if not os.path.isabs(path):
                paths["models"][key] = os.path.join(root_path, path)

    # 处理 libs 路径
    if "libs" in paths:
        for key, path in paths["libs"].items():
            if not os.path.isabs(path):
                paths["libs"][key] = os.path.join(root_path, path)
            # 添加到 Python 路径
            if path not in sys.path:
                sys.path.insert(0, paths["libs"][key])

    return config


# 加载配置
config = load_config()
system_config = config.get("system", {})
models_config = config.get("models", {})
paths_config = config.get("paths", {})

# ==================== 初始化 Flask ====================

app = Flask(__name__)

# ==================== 加载模型 ====================

print("=" * 60)
print(f"🚀 VoiceForge API Server")
print(f"   版本: {system_config.get('version', '1.0.0-preview')}")
print("=" * 60)

# 加载 ASR
asr_model = None
if models_config.get("asr", {}).get("enabled", True):
    print("\n🔄 加载 ASR 模型...")
    asr_config = models_config["asr"].copy()
    asr_config["model_path"] = paths_config.get("models", {}).get("asr")
    asr_model = SenseVoiceASR(asr_config)
    asr_model.load(asr_config)
else:
    print("\n⚠️ ASR 已禁用")

# 加载 TTS
tts_model = None
if models_config.get("tts", {}).get("enabled", True):
    print("\n🔄 加载 TTS 模型...")
    tts_config = models_config["tts"].copy()
    tts_config["model_path"] = paths_config.get("models", {}).get("tts")
    tts_config["cosyvoice_lib"] = paths_config.get("libs", {}).get("cosyvoice")
    tts_model = CosyVoiceTTS(tts_config)
    tts_model.load(tts_config)
else:
    print("\n⚠️ TTS 已禁用")

# LLM 配置
llm_config = models_config.get("llm", {})
ollama_config = llm_config.get("ollama", {})

print("\n" + "=" * 60)
print("✅ 模型加载完成")
print("=" * 60)

# ==================== API 路由 ====================


@app.route("/")
def index():
    """服务状态"""
    return jsonify(
        {
            "success": True,
            "status": "running",
            "version": system_config.get("version", "1.0.0-preview"),
            "services": {
                "asr": {
                    "enabled": models_config.get("asr", {}).get("enabled", False),
                    "loaded": asr_model.is_loaded() if asr_model else False,
                    "type": models_config.get("asr", {}).get("type", "none"),
                },
                "tts": {
                    "enabled": models_config.get("tts", {}).get("enabled", False),
                    "loaded": tts_model.is_loaded() if tts_model else False,
                    "type": models_config.get("tts", {}).get("type", "none"),
                },
                "llm": {
                    "enabled": llm_config.get("enabled", False),
                    "type": llm_config.get("type", "none"),
                    "model": ollama_config.get("model", "none"),
                },
            },
            "endpoints": {
                "GET /": "服务状态",
                "GET /voices": "获取音色列表",
                "POST /asr": "语音识别 (form-data: audio)",
                "POST /tts": "语音合成 (json: {text, voice})",
                "POST /chat": "AI对话 (json: {message})",
                "POST /complete": "完整流程 (form-data: audio)",
            },
        }
    )


@app.route("/voices", methods=["GET"])
def get_voices():
    """获取音色列表"""
    if not tts_model or not tts_model.is_loaded():
        return jsonify({"success": False, "error": "TTS模型未加载", "voices": []}), 503

    try:
        voices = tts_model.get_voices()
        return jsonify({"success": True, "voices": voices, "count": len(voices)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "voices": []}), 500


@app.route("/asr", methods=["POST"])
def asr():
    """
    语音识别

    Request (multipart/form-data):
        - audio: 音频文件
        - language: 语言代码 (optional, default: auto)

    Response (json):
        {
            "success": bool,
            "text": str,
            "language": str
        }
    """
    # 检查模型
    if not asr_model or not asr_model.is_loaded():
        return jsonify({"success": False, "error": "ASR模型未加载"}), 503

    # 检查文件
    if "audio" not in request.files:
        return jsonify(
            {"success": False, "error": "未提供音频文件 (field: audio)"}
        ), 400

    audio_file = request.files["audio"]
    language = request.form.get("language", "auto")

    # 保存临时文件
    temp_path = os.path.join(tempfile.gettempdir(), audio_file.filename)
    audio_file.save(temp_path)

    try:
        # 执行识别
        result = asr_model.transcribe(temp_path, language)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": f"识别失败: {str(e)}"}), 500
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.route("/tts", methods=["POST"])
def tts():
    """
    语音合成

    Request (application/json):
        {
            "text": "要合成的文本",
            "voice": "音色名称" (optional)
        }

    Response:
        - audio/wav 文件
    """
    # 检查模型
    if not tts_model or not tts_model.is_loaded():
        return jsonify({"success": False, "error": "TTS模型未加载"}), 503

    # 获取参数
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "请求体必须是 JSON 格式"}), 400

    text = data.get("text", "").strip()
    voice = data.get("voice")

    if not text:
        return jsonify({"success": False, "error": "文本不能为空"}), 400

    try:
        # 执行合成
        audio_path = tts_model.synthesize(text, voice)

        # 返回音频文件
        return send_file(
            audio_path,
            mimetype="audio/wav",
            as_attachment=True,
            download_name="tts_output.wav",
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"合成失败: {str(e)}"}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """
    AI对话

    Request (application/json):
        {
            "message": "用户消息",
            "history": [] (optional)
        }

    Response (json):
        {
            "success": bool,
            "response": str
        }
    """
    if not llm_config.get("enabled", True):
        return jsonify({"success": False, "error": "LLM 已禁用"}), 503

    # 获取参数
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "请求体必须是 JSON 格式"}), 400

    message = data.get("message", "").strip()
    if not message:
        return jsonify({"success": False, "error": "消息不能为空"}), 400

    # 获取配置
    max_tokens = ollama_config.get("max_tokens", 80)
    system_prompt = ollama_config.get(
        "system_prompt", "请用简洁的语言回答，确保意思完整。回答要简短精炼，不要冗长。"
    )

    try:
        # 使用 Chat API 和 System Message
        import requests

        payload = {
            "model": ollama_config.get("model", "gemma3:4b"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "stream": False,
            "options": {
                "temperature": ollama_config.get("temperature", 0.7),
                "top_p": ollama_config.get("top_p", 0.9),
                "num_predict": max_tokens,
            },
        }

        response = requests.post(
            f"{ollama_config.get('url', 'http://localhost:11434')}/api/chat",
            json=payload,
            timeout=ollama_config.get("timeout", 60),
        )

        if response.status_code == 200:
            response_data = response.json()
            ai_response = response_data.get("message", {}).get("content", "")
            return jsonify(
                {
                    "success": True,
                    "response": ai_response,
                    "model": ollama_config.get("model"),
                    "max_tokens": max_tokens,
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "error": f"Ollama 调用失败: HTTP {response.status_code}",
                }
            ), 500

    except Exception as e:
        return jsonify({"success": False, "error": f"Ollama 调用失败: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/complete", methods=["POST"])
def complete():
    """
    完整流程：ASR -> LLM -> TTS

    Request (multipart/form-data):
        - audio: 音频文件
        - voice: 音色名称 (optional)

    Response:
        - audio/wav 文件
    """
    temp_files = []

    try:
        # Step 1: ASR
        print("\n[1/3] 语音识别...")
        if "audio" not in request.files:
            return jsonify({"success": False, "error": "未提供音频文件"}), 400

        # 保存音频
        audio_file = request.files["audio"]
        temp_audio = os.path.join(tempfile.gettempdir(), audio_file.filename)
        audio_file.save(temp_audio)
        temp_files.append(temp_audio)

        # 识别
        if not asr_model or not asr_model.is_loaded():
            return jsonify({"success": False, "error": "ASR模型未加载"}), 503

        asr_result = asr_model.transcribe(temp_audio, "auto")
        if not asr_result.get("success"):
            return jsonify(
                {
                    "success": False,
                    "stage": "ASR",
                    "error": asr_result.get("error", "识别失败"),
                }
            ), 500

        recognized_text = asr_result.get("text", "")
        print(f"   识别结果: {recognized_text[:50]}...")

        # Step 2: LLM
        print("[2/3] AI对话...")
        if not llm_config.get("enabled", True):
            return jsonify(
                {"success": False, "stage": "LLM", "error": "LLM 已禁用"}
            ), 503

        # 获取配置
        max_tokens = ollama_config.get("max_tokens", 80)
        system_prompt = ollama_config.get(
            "system_prompt",
            "请用简洁的语言回答，确保意思完整。回答要简短精炼，不要冗长。",
        )

        # 使用 Chat API
        try:
            import requests

            payload = {
                "model": ollama_config.get("model", "gemma3:4b"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": recognized_text},
                ],
                "stream": False,
                "options": {
                    "temperature": ollama_config.get("temperature", 0.7),
                    "num_predict": max_tokens,
                },
            }

            response = requests.post(
                f"{ollama_config.get('url', 'http://localhost:11434')}/api/chat",
                json=payload,
                timeout=ollama_config.get("timeout", 60),
            )

            if response.status_code != 200:
                return jsonify(
                    {
                        "success": False,
                        "stage": "LLM",
                        "error": f"LLM 调用失败: HTTP {response.status_code}",
                    }
                ), 500

            llm_data = response.json()
            ai_response = llm_data.get("message", {}).get("content", "")
            print(f"   AI回复: {ai_response[:50]}...")

        except Exception as e:
            return jsonify(
                {"success": False, "stage": "LLM", "error": f"LLM 调用失败: {str(e)}"}
            ), 500

        # Step 3: TTS
        print("[3/3] 语音合成...")
        if not tts_model or not tts_model.is_loaded():
            return jsonify(
                {"success": False, "stage": "TTS", "error": "TTS模型未加载"}
            ), 503

        voice = request.form.get("voice")
        audio_path = tts_model.synthesize(ai_response, voice)

        print("✅ 流程完成")

        # 返回音频
        return send_file(
            audio_path,
            mimetype="audio/wav",
            as_attachment=True,
            download_name="response.wav",
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        # 清理临时文件
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)


# ==================== 启动服务 ====================

if __name__ == "__main__":
    port = system_config.get("port", 7861)
    debug = system_config.get("debug", False)

    print(f"\n🌐 启动 API 服务...")
    print(f"   地址: http://0.0.0.0:{port}")
    print(f"   调试模式: {debug}")
    print("\n按 Ctrl+C 停止服务\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
