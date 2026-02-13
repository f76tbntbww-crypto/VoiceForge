# -*- coding: utf-8 -*-
"""
VoiceForge Web UI - 简化版

基于 Gradio 的 Web 界面
提供：语音识别、语音合成、AI对话功能（支持图片上传和多轮记忆）

启动方式：
    python web/ui_simple.py

或使用脚本：
    ..\scripts\start_web.bat
"""

import os
import sys
import uuid
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml
import gradio as gr

# 导入插件
from plugins.asr.sensevoice import SenseVoiceASR
from plugins.tts.cosyvoice import CosyVoiceTTS

# ==================== 配置管理 ====================


class ConfigManager:
    """配置管理器 - 支持热更新"""

    def __init__(self, config_path: Path = None):
        self.config_path = config_path or project_root / "config.yaml"
        self._config = None
        self._load()

    def _load(self):
        """加载配置"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 处理相对路径
        paths = config.get("paths", {})
        if "models" in paths:
            for key, path in paths["models"].items():
                if not os.path.isabs(path):
                    paths["models"][key] = os.path.join(project_root, path)
        if "libs" in paths:
            for key, path in paths["libs"].items():
                if not os.path.isabs(path):
                    paths["libs"][key] = os.path.join(project_root, path)
                if path not in sys.path:
                    sys.path.insert(0, paths["libs"][key])

        self._config = config

    def save(self):
        """保存配置"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, allow_unicode=True, sort_keys=False)

    @property
    def config(self) -> dict:
        """获取当前配置（实时）"""
        return self._config

    def get(self, path: str, default=None):
        """通过路径获取配置值，例如：models.llm.ollama.max_tokens"""
        keys = path.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, path: str, value):
        """通过路径设置配置值"""
        keys = path.split(".")
        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value


# 全局配置管理器
config_manager = ConfigManager()


# ==================== 记忆管理器 ====================


class ChatMemory:
    """
    聊天记忆管理器

    功能：
    - 保存对话历史
    - 支持滑动窗口（限制轮数）
    - 按会话ID隔离不同对话
    - 支持清空记忆
    """

    def __init__(self, max_history: int = 10):
        """
        初始化记忆管理器

        Args:
            max_history: 最大保存的对话轮数（用户+助手算一轮）
        """
        self.max_history = max_history
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    def create_session(self) -> str:
        """创建新会话，返回会话ID"""
        session_id = str(uuid.uuid4())[:8]  # 使用短UUID
        self._sessions[session_id] = []
        return session_id

    def add(self, session_id: str, role: str, content: str, image: str = None):
        """
        添加消息到记忆

        Args:
            session_id: 会话ID
            role: 角色 ("user" 或 "assistant")
            content: 消息内容
            image: 图片路径（可选）
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        message = {"role": role, "content": content}
        if image:
            message["image"] = image

        self._sessions[session_id].append(message)

        # 滑动窗口：保留最近 N 轮对话（用户+助手=一轮）
        # 每轮2条消息，保留 max_history * 2 条
        max_messages = self.max_history * 2
        if len(self._sessions[session_id]) > max_messages:
            # 保留最新的消息
            self._sessions[session_id] = self._sessions[session_id][-max_messages:]

    def get(self, session_id: str, include_system: bool = True) -> List[Dict[str, Any]]:
        """
        获取会话历史

        Args:
            session_id: 会话ID
            include_system: 是否包含 System Message

        Returns:
            消息列表（用于 API 调用）
        """
        messages = []

        # 添加 System Message
        if include_system:
            system_prompt = config_manager.get(
                "models.llm.ollama.system_prompt",
                "你必须在限定字数内完整表达。如果内容较长，请精简回答，确保结尾完整、意思清晰。不要说到一半就停止。优先给出核心结论，细节可省略。",
            )
            messages.append({"role": "system", "content": system_prompt})

        # 添加历史对话
        if session_id in self._sessions:
            for msg in self._sessions[session_id]:
                api_msg = {"role": msg["role"], "content": msg["content"]}
                # 如果有图片，添加图片信息（用于多模态模型）
                if "image" in msg and msg["image"]:
                    # 读取图片并转为base64
                    try:
                        import base64

                        with open(msg["image"], "rb") as f:
                            img_base64 = base64.b64encode(f.read()).decode("utf-8")
                        api_msg["images"] = [img_base64]
                    except:
                        pass
                messages.append(api_msg)

        return messages

    def get_display_history(self, session_id: str) -> List:
        """
        获取用于显示的历史记录（Gradio Chatbot 格式）

        Returns:
            Gradio Chatbot 格式的消息列表
        """
        history = []
        if session_id not in self._sessions:
            return history

        for msg in self._sessions[session_id]:
            if msg["role"] == "user":
                # 如果有图片，使用Gradio Chatbot支持的图片格式
                if "image" in msg and msg["image"] and os.path.exists(msg["image"]):
                    # Gradio Chatbot支持在content中包含图片路径
                    if msg["content"] and msg["content"].strip():
                        # 有文字也有图片
                        history.append(
                            {
                                "role": "user",
                                "content": {
                                    "path": msg["image"],
                                    "text": msg["content"],
                                },
                            }
                        )
                    else:
                        # 只有图片没有文字
                        history.append(
                            {"role": "user", "content": {"path": msg["image"]}}
                        )
                else:
                    # 纯文字
                    history.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                history.append({"role": "assistant", "content": msg["content"]})

        return history

    def clear(self, session_id: str):
        """清空指定会话的记忆"""
        if session_id in self._sessions:
            self._sessions[session_id] = []

    def get_session_count(self) -> int:
        """获取会话数量"""
        return len(self._sessions)

    def get_message_count(self, session_id: str) -> int:
        """获取指定会话的消息数量"""
        return len(self._sessions.get(session_id, []))


# 全局记忆管理器
chat_memory = ChatMemory(max_history=10)


# ==================== 加载配置 ====================

config = config_manager.config
web_config = config.get("web", {}).get("simple", {})
models_config = config.get("models", {})
paths_config = config.get("paths", {})

# ==================== 加载模型 ====================

print("=" * 60)
print("🚀 VoiceForge Web UI (简化版)")
print("=" * 60)

# 加载 ASR
asr_model = None
if models_config.get("asr", {}).get("enabled", True):
    print("\n🔄 加载 ASR 模型...")
    asr_config = models_config["asr"].copy()
    asr_config["model_path"] = paths_config.get("models", {}).get("asr")
    asr_model = SenseVoiceASR(asr_config)
    asr_model.load(asr_config)

# 加载 TTS
tts_model = None
if models_config.get("tts", {}).get("enabled", True):
    print("\n🔄 加载 TTS 模型...")
    tts_config = models_config["tts"].copy()
    tts_config["model_path"] = paths_config.get("models", {}).get("tts")
    tts_config["cosyvoice_lib"] = paths_config.get("libs", {}).get("cosyvoice")
    tts_model = CosyVoiceTTS(tts_config)
    tts_model.load(tts_config)

# 获取音色列表
voices = ["中文女", "中文男", "日语男", "粤语女", "英文女", "英文男", "韩语女"]
if tts_model and tts_model.is_loaded():
    try:
        voice_list = tts_model.get_voices()
        voices = [v["name"] for v in voice_list]
    except:
        pass

print("\n" + "=" * 60)
print("✅ 模型加载完成")
print(f"📝 记忆管理器已启动（最大保留 {chat_memory.max_history} 轮对话）")
print("=" * 60)

# ==================== 功能函数 ====================


def speech_to_text(audio_file, language):
    """语音识别"""
    if not asr_model or not asr_model.is_loaded():
        return "错误：ASR模型未加载", ""

    if audio_file is None:
        return "请先上传音频文件", ""

    try:
        result = asr_model.transcribe(audio_file, language)
        if result.get("success"):
            return result["text"], f"语言: {result['language']}"
        else:
            return f"识别失败: {result.get('error', '')}", ""
    except Exception as e:
        return f"错误: {str(e)}", ""


def text_to_speech(text, voice):
    """语音合成"""
    if not tts_model or not tts_model.is_loaded():
        return None, "错误：TTS模型未加载"

    if not text.strip():
        return None, "请输入文本"

    try:
        audio_path = tts_model.synthesize(text, voice)
        return audio_path, "合成成功"
    except Exception as e:
        return None, f"错误: {str(e)}"


def chat_with_ai(session_id: str, message: str, image: str = None) -> str:
    """
    AI对话（支持图片和多轮记忆）

    Args:
        session_id: 会话ID
        message: 用户消息
        image: 图片路径（可选）

    Returns:
        AI回复内容
    """
    if not models_config.get("llm", {}).get("enabled", True):
        return "错误：LLM已禁用"

    if not message.strip() and image is None:
        return "请输入消息或上传图片"

    import requests

    # 获取实时配置（热更新）
    max_tokens = config_manager.get("models.llm.ollama.max_tokens", 80)
    system_prompt = config_manager.get(
        "models.llm.ollama.system_prompt",
        "你必须在限定字数内完整表达。如果内容较长，请精简回答，确保结尾完整、意思清晰。不要说到一半就停止。优先给出核心结论，细节可省略。",
    )

    try:
        # 添加用户消息到记忆
        chat_memory.add(session_id, "user", message, image)

        # 获取包含历史的完整消息列表
        messages = chat_memory.get(session_id, include_system=True)

        payload = {
            "model": config_manager.get("models.llm.ollama.model", "gemma3:4b"),
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": config_manager.get("models.llm.ollama.temperature", 0.7),
                "num_predict": max_tokens,
            },
        }

        response = requests.post(
            f"{config_manager.get('models.llm.ollama.url', 'http://localhost:11434')}/api/chat",
            json=payload,
            timeout=60,
        )

        if response.status_code == 200:
            data = response.json()
            ai_response = data.get("message", {}).get("content", "无回复")

            # 添加AI回复到记忆
            chat_memory.add(session_id, "assistant", ai_response)

            return ai_response
        else:
            return f"调用失败: HTTP {response.status_code}"
    except Exception as e:
        return f"错误: {str(e)}"


def update_settings(max_tokens_input, system_prompt_input, max_history_input):
    """更新设置并保存到配置文件（热更新）"""
    try:
        # 更新配置
        config_manager.set("models.llm.ollama.max_tokens", int(max_tokens_input))
        config_manager.set("models.llm.ollama.system_prompt", system_prompt_input)

        # 更新记忆管理器的最大历史轮数
        global chat_memory
        chat_memory.max_history = int(max_history_input)

        # 保存到文件
        config_manager.save()

        return (
            f"✅ 设置已更新！\n"
            f"   • Token限制: {max_tokens_input}\n"
            f"   • 最大记忆轮数: {max_history_input}\n"
            f"   • 配置已保存并立即生效"
        )
    except Exception as e:
        return f"❌ 保存失败: {str(e)}"


def get_current_settings():
    """获取当前设置值（实时读取）"""
    max_tokens = config_manager.get("models.llm.ollama.max_tokens", 80)
    system_prompt = config_manager.get(
        "models.llm.ollama.system_prompt",
        "你必须在限定字数内完整表达。如果内容较长，请精简回答，确保结尾完整、意思清晰。不要说到一半就停止。优先给出核心结论，细节可省略。",
    )
    max_history = chat_memory.max_history
    return max_tokens, system_prompt, max_history


def clear_memory(session_id: str):
    """清空记忆"""
    chat_memory.clear(session_id)
    message_count = chat_memory.get_message_count(session_id)
    return f"🗑️ 记忆已清空（当前会话消息数: {message_count}）", []


def get_memory_info(session_id: str):
    """获取记忆信息"""
    count = chat_memory.get_message_count(session_id)
    rounds = count // 2  # 每轮包含用户和助手两条消息
    max_rounds = chat_memory.max_history
    return f"💬 当前对话: {rounds}/{max_rounds} 轮 ({count} 条消息)"


def complete_pipeline(session_id: str, audio_file, text_input, image_file, voice):
    """完整流程：语音/文字+图片 → AI回复 → 语音播放"""
    # 优先使用语音输入，如果没有语音则使用文字输入
    if audio_file is None and not text_input.strip():
        return None, "请先上传音频文件或输入文字", ""

    try:
        # Step 1: 获取输入（ASR或直接使用文字）
        if audio_file is not None:
            # 使用语音识别
            if not asr_model or not asr_model.is_loaded():
                return None, "错误：ASR模型未加载", ""

            asr_result = asr_model.transcribe(audio_file, "auto")
            if not asr_result.get("success"):
                return None, f"识别失败: {asr_result.get('error', '')}", ""
            recognized_text = asr_result["text"]
        else:
            # 直接使用文字输入
            recognized_text = text_input.strip()

        # Step 2: LLM（支持图片）
        if not models_config.get("llm", {}).get("enabled", True):
            return None, "错误：LLM已禁用", recognized_text

        ai_response = chat_with_ai(session_id, recognized_text, image_file)

        if ai_response.startswith("错误：") or ai_response.startswith("调用失败："):
            return None, f"LLM调用失败: {ai_response}", recognized_text

        # Step 3: TTS
        if not tts_model or not tts_model.is_loaded():
            return None, "错误：TTS模型未加载", recognized_text

        audio_path = tts_model.synthesize(ai_response, voice)

        return audio_path, ai_response, recognized_text

    except Exception as e:
        return None, f"错误: {str(e)}", ""


# ==================== 创建界面 ====================

# 获取当前设置
current_max_tokens, current_system_prompt, current_max_history = get_current_settings()

# 初始化会话ID（用于记忆管理）
initial_session_id = chat_memory.create_session()

with gr.Blocks(title="VoiceForge - 本地语音助手") as demo:
    # 隐藏的会话ID存储
    session_id_state = gr.State(value=initial_session_id)

    gr.Markdown("""
    # 🎙️ VoiceForge 本地语音助手
    
    **基于 SenseVoice + CosyVoice + Ollama 的开源语音对话系统**
    
    完全本地运行，无需联网，保护隐私 | 支持多轮对话记忆
    """)

    with gr.Tabs():
        # Tab 1: 语音识别
        with gr.Tab("语音识别"):
            gr.Markdown("### 🎤 上传音频文件进行识别")
            with gr.Row():
                with gr.Column():
                    audio_input = gr.Audio(label="上传音频", type="filepath")
                    language = gr.Dropdown(
                        label="语言",
                        choices=[
                            ("自动检测", "auto"),
                            ("中文", "zh"),
                            ("英语", "en"),
                            ("日语", "ja"),
                            ("韩语", "ko"),
                            ("粤语", "yue"),
                        ],
                        value="auto",
                    )
                    btn_stt = gr.Button("开始识别", variant="primary")

                with gr.Column():
                    text_output = gr.Textbox(label="识别结果", lines=5)
                    lang_output = gr.Textbox(label="语言信息", interactive=False)

            btn_stt.click(
                speech_to_text,
                inputs=[audio_input, language],
                outputs=[text_output, lang_output],
            )

        # Tab 2: 语音合成
        with gr.Tab("语音合成"):
            gr.Markdown("### 🔊 输入文本生成语音")
            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(
                        label="输入文本", lines=3, placeholder="请输入要合成的文本..."
                    )
                    voice_select = gr.Dropdown(
                        label="选择音色",
                        choices=voices,
                        value=voices[0] if voices else "中文女",
                    )
                    btn_tts = gr.Button("生成语音", variant="primary")

                with gr.Column():
                    audio_output = gr.Audio(label="生成的语音", type="filepath")
                    status_output = gr.Textbox(label="状态", interactive=False)

            btn_tts.click(
                text_to_speech,
                inputs=[text_input, voice_select],
                outputs=[audio_output, status_output],
            )

        # Tab 3: AI对话
        with gr.Tab("AI对话"):
            gr.Markdown("### 🤖 与本地大模型对话（支持图片上传和多轮记忆）")

            # 设置区域
            with gr.Accordion("⚙️ 对话设置（点击展开）", open=False):
                gr.Markdown("调整AI回复长度、记忆管理和其他参数")
                with gr.Row():
                    with gr.Column():
                        max_tokens_input = gr.Number(
                            label="Token 限制（回复最大字数）",
                            value=current_max_tokens,
                            minimum=30,
                            maximum=500,
                            step=10,
                            info="数值越小回复越短，建议80-150",
                        )
                        max_history_input = gr.Number(
                            label="最大记忆轮数",
                            value=current_max_history,
                            minimum=1,
                            maximum=20,
                            step=1,
                            info="保留最近N轮对话",
                        )
                    with gr.Column():
                        system_prompt_input = gr.Textbox(
                            label="AI 行为设定（System Prompt）",
                            value=current_system_prompt,
                            lines=3,
                            info="定义AI的回复风格",
                        )
                with gr.Row():
                    save_btn = gr.Button("💾 保存设置", variant="secondary")
                    clear_btn = gr.Button("🗑️ 清空记忆", variant="stop")
                settings_status = gr.Textbox(label="状态", interactive=False)
                memory_info = gr.Textbox(
                    label="记忆状态",
                    value=get_memory_info(initial_session_id),
                    interactive=False,
                )

                # 绑定按钮事件（clear事件在chatbot定义后绑定）
                save_btn.click(
                    update_settings,
                    inputs=[max_tokens_input, system_prompt_input, max_history_input],
                    outputs=settings_status,
                )

            with gr.Row():
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        label="对话记录",
                        height=400,
                        value=chat_memory.get_display_history(initial_session_id),
                    )
                    # 绑定清空按钮事件（在chatbot定义后）
                    clear_btn.click(
                        clear_memory,
                        inputs=[session_id_state],
                        outputs=[settings_status, chatbot],
                    )
                    msg_input = gr.Textbox(
                        label="输入消息", placeholder="输入消息按回车发送..."
                    )
                with gr.Column(scale=1):
                    image_input = gr.Image(
                        label="上传图片（可选）", type="filepath", height=300
                    )
                    gr.Markdown("""
                    **使用说明：**
                    - 💬 仅文字：直接输入消息
                    - 📷 图文对话：上传图片 + 输入问题
                    - 🔄 记忆功能：自动保留上下文
                    - 🗑️ 清空记忆：在设置中点击清空
                    """)

            def respond(message, image, history, session_id):
                if not message.strip() and image is None:
                    return "", history, get_memory_info(session_id)

                # 调用AI（自动保存到记忆）
                response = chat_with_ai(session_id, message, image)

                # 更新显示
                new_history = chat_memory.get_display_history(session_id)

                return "", new_history, get_memory_info(session_id)

            msg_input.submit(
                respond,
                inputs=[msg_input, image_input, chatbot, session_id_state],
                outputs=[msg_input, chatbot, memory_info],
            )

        # Tab 4: 完整流程
        with gr.Tab("完整流程"):
            gr.Markdown("### 🔄 完整语音对话流程（支持图片）")
            gr.Markdown("语音/文字 → AI理解 → 语音回复")

            with gr.Row():
                with gr.Column():
                    complete_audio_input = gr.Audio(
                        label="🎤 上传语音（可选，优先使用）", type="filepath"
                    )
                    complete_text_input = gr.Textbox(
                        label="✏️ 或直接输入文字",
                        placeholder="如果不上传语音，请在这里输入文字...",
                        lines=2,
                    )
                    complete_image_input = gr.Image(
                        label="📷 上传图片（可选）", type="filepath", height=200
                    )
                    complete_voice = gr.Dropdown(
                        label="选择回复音色",
                        choices=voices,
                        value=voices[0] if voices else "中文女",
                    )
                    btn_complete = gr.Button("开始对话", variant="primary")

                with gr.Column():
                    complete_audio_output = gr.Audio(
                        label="AI回复语音", type="filepath"
                    )
                    complete_text_output = gr.Textbox(label="AI回复文本", lines=2)
                    complete_asr_output = gr.Textbox(
                        label="输入内容（语音识别的文字或您输入的文字）", lines=2
                    )

            btn_complete.click(
                complete_pipeline,
                inputs=[
                    session_id_state,
                    complete_audio_input,
                    complete_text_input,
                    complete_image_input,
                    complete_voice,
                ],
                outputs=[
                    complete_audio_output,
                    complete_text_output,
                    complete_asr_output,
                ],
            )

    gr.Markdown(f"""
    ---
    **VoiceForge** v1.0.0-preview | 会话ID: `{initial_session_id}` | 支持多轮记忆
    """)

# ==================== 启动服务 ====================

if __name__ == "__main__":
    port = web_config.get("port", 7860)
    share = web_config.get("share", False)

    print(f"\n🌐 启动 Web 界面...")
    print(f"   地址: http://localhost:{port}")
    print(f"   会话ID: {initial_session_id}")
    print(f"   记忆管理: 已启用（最大{chat_memory.max_history}轮）")
    print("\n按 Ctrl+C 停止服务\n")

    demo.launch(server_name="0.0.0.0", server_port=port, share=share)
