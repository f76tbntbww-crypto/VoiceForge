# VoiceForge 更新日志

## 2024-02-13 重大更新（记忆系统版）

### 🎉 新功能

#### 1. 多轮对话记忆系统
- **自研 ChatMemory 记忆管理器**：轻量级 Python 实现
- **自动保存对话历史**：支持最近 10 轮对话（可配置）
- **滑动窗口机制**：超出限制自动删除旧对话
- **Web 界面管理**：实时显示记忆状态，支持一键清空
- **按会话隔离**：不同对话互不干扰

#### 2. 热更新配置系统
- **Token 限制实时调整**：无需重启立即生效
- **AI 行为设定可调**：修改 System Prompt 立即生效
- **最大记忆轮数可调**：随时调整记忆深度
- **配置持久化**：自动保存到 config.yaml

#### 3. 简化安装流程
- **移除复杂的子模块初始化**：Matcha-TTS 已完整包含在项目中
- **集成模型下载**：install.bat 中新增模型下载选项
- **一键安装**：用户只需运行 install.bat 即可完成所有配置

#### 4. 图片上传功能
- **AI对话支持图片上传**：在 "AI对话" 标签页可上传图片
- **多模态对话**：支持图文混合对话，LLM 可以看懂图片内容
- **完整流程支持图片**：语音+图片混合输入

### 🔧 优化改进

#### 1. 项目结构优化
- **清理缓存文件**：删除所有 `__pycache__` 和 `.DS_Store`
- **更新 .gitignore**：确保缓存文件不会上传到 GitHub
- **删除冗余文件**：移除 `check_install.bat`

#### 2. 安装脚本改进
- **5步安装**：简化安装流程，从6步优化为5步
- **模型下载选项**：提供自动/手动/跳过三种选择
- **用户友好**：每个步骤都有清晰提示

#### 3. 代码优化
- **移除 curl 依赖**：改用 Python requests 调用 Ollama
- **修复 Gradio 格式**：更新 Chatbot 组件到新格式
- **增强错误处理**：更好的错误提示和恢复建议

### 📦 文件变更

#### 修改的文件
- `scripts/install.bat` - 简化并集成模型下载
- `web/ui_simple.py` - 增加图片上传功能
- `README.md` - 更新文档和说明
- `.gitignore` - 完善忽略规则

#### 删除的文件
- `scripts/check_install.bat` - 冗余文件
- 所有 `__pycache__` 目录 - Python 缓存
- 所有 `.DS_Store` 文件 - macOS 系统文件

### 🚀 快速开始（更新后）

```powershell
# 1. 下载项目并解压到 C:\VoiceForge

# 2. 进入项目目录
cd C:\VoiceForge

# 3. 运行安装脚本（包含模型下载选项）
.\scripts\install.bat

# 4. 启动服务
.\scripts\start_api.bat
.\scripts\start_web.bat

# 5. 访问 http://localhost:7860
```

### 📝 注意事项

1. **模型文件较大**：SenseVoice (~800MB) + CosyVoice (~3GB)
2. **安装时需要网络**：用于下载 PyTorch 和依赖包
3. **Ollama 需要单独安装**：从 https://ollama.com/download 下载
4. **支持多模态模型**：上传图片功能需要 Ollama 多模态模型支持

### 🐛 已知问题

- 模型下载可能需要中国大陆网络环境
- 首次启动时需要加载模型，可能需要 1-2 分钟
- GPU 模式需要 NVIDIA 显卡和 CUDA 驱动

---

### 📚 技术参考

#### Flask + LangChain 开源项目调研

经过调研，以下是一些优秀的 Flask + LangChain 开源项目供参考：

**1. ashhass/Chatbot** (30⭐)
- 简单的 LangChain + RAG + Flask 聊天机器人
- 功能：基础对话、RAG检索
- 特点：代码简洁，适合入门学习

**2. BlueBash/langchain-chatbot** (21⭐)
- 完整的 LangChain 聊天机器人
- 功能：对话管理、多轮记忆
- 特点：MIT许可证，代码规范

**3. justynigam/AI_Debales** (1⭐)
- LangChain + HuggingFace + FAISS 向量存储
- 功能：文档检索、RAG问答
- 特点：RESTful API设计

**4. Anshuman-git-code/Langchain_Flask_Bot** (1⭐)
- Flask + LangChain + Hugging Face
- 功能：向量嵌入、智能检索
- 特点：支持ngrok公网访问

**5. superjose129/LangChain-as-a-service** 
- LangChain 即服务架构
- 功能：微服务化、API化
- 特点：适合生产环境部署

#### 为什么我们自研而非直接使用

**自研的优势**：
- ✅ 零额外依赖（仅使用 Python 标准库 + 已有依赖）
- ✅ 完全掌控代码逻辑，易于定制
- ✅ 轻量级实现（ChatMemory 仅 150 行代码）
- ✅ 不引入 LangChain 的复杂性
- ✅ 针对本地部署优化（无需向量数据库）

**参考设计模式**：
```
ChatMemory（记忆管理）← 参考 Spring AI 的 ChatMemory 接口
ConfigManager（配置管理）← 支持热更新
Session ID（会话隔离）← 参考 LangChain 的 ConversationBufferMemory
```

---

**VoiceForge v1.0.0-preview** | 2026-02-13
