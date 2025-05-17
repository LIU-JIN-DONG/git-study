# 实时AI语音聊天 🎤💬🧠🔊

**与AI进行自然的语音对话！**  

这个项目让你只用语音就能与大型语言模型(LLM)交谈，并几乎实时地收到语音回应。把它想象成你自己的数字对话伙伴。

https://github.com/user-attachments/assets/16cc29a7-bec2-4dd0-a056-d213db798d8f

*（早期预览版 - 第一个相对稳定的版本）*

## 核心原理

这是一个为低延迟交互而构建的复杂客户端-服务器系统：

1. 🎙️ **捕获：** 你的声音通过浏览器被捕获。
2. ➡️ **传输：** 音频数据块通过WebSockets传送到Python后端。
3. ✍️ **转录：** `RealtimeSTT`快速将你的语音转换为文本。
4. 🤔 **思考：** 文本被发送到LLM（如Ollama或OpenAI）进行处理。
5. 🗣️ **合成：** AI的文本回应通过`RealtimeTTS`转换回语音。
6. ⬅️ **返回：** 生成的音频被传回浏览器进行播放。
7. 🔄 **打断：** 随时可以插话！系统能优雅地处理打断。

## 主要特点 ✨

* **流畅对话：** 说话和聆听，就像真实的聊天。
* **实时反馈：** 实时查看部分转录和AI响应。
* **低延迟设计：** 使用音频数据块流传输的优化架构。
* **智能轮换：** 动态静音检测（`turndetect.py`）适应对话节奏。
* **灵活AI引擎：** 可插拔的LLM后端（默认为Ollama，通过`llm_module.py`支持OpenAI）。
* **可定制语音：** 从不同的文本转语音引擎中选择（通过`audio_module.py`支持Kokoro、Coqui、Orpheus）。
* **网页界面：** 使用原生JS和Web Audio API的简洁界面。
* **Docker部署：** 推荐使用Docker Compose进行设置，更易于管理依赖关系。

## 技术栈 🛠️

* **后端：** Python 3.x, FastAPI
* **前端：** HTML, CSS, JavaScript（原生JS、Web Audio API、AudioWorklets）
* **通信：** WebSockets
* **容器化：** Docker, Docker Compose
* **核心AI/ML库：**
  * `RealtimeSTT`（语音转文本）
  * `RealtimeTTS`（文本转语音）
  * `transformers`（轮换检测、分词）
  * `torch` / `torchaudio`（机器学习框架）
  * `ollama` / `openai`（LLM客户端）
* **音频处理：** `numpy`, `scipy`

## 开始前：前提条件 🏊‍♀️

本项目利用强大的AI模型，有一些要求：

* **操作系统：**
  * **Docker：** 推荐Linux以获得最佳的GPU与Docker集成。
  * **手动：** 提供的脚本（`install.bat`）适用于Windows。Linux/macOS上的手动步骤可能需要更多的故障排除（尤其是对于DeepSpeed）。
* **🐍 Python：** 3.9或更高版本（如果手动设置）。
* **🚀 GPU：** **强烈推荐使用支持CUDA的NVIDIA GPU**，尤其是为了更快的STT（Whisper）和TTS（Coqui）。仅CPU或较弱GPU的性能将明显变慢。
  * 设置假定使用**CUDA 12.1**。如果你有不同的CUDA版本，请调整PyTorch安装。
  * **Docker（Linux）：** 需要[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。
* **🐳 Docker（可选但推荐）：** Docker Engine和Docker Compose v2+用于容器化设置。
* **🧠 Ollama（可选）：** 如果在没有Docker的情况下使用Ollama后端，请单独安装并拉取你想要的模型。Docker设置包括一个Ollama服务。
* **🔑 OpenAI API密钥（可选）：** 如果使用OpenAI后端，请设置`OPENAI_API_KEY`环境变量（例如，在`.env`文件中或传递给Docker）。

---

## 入门：安装与设置 ⚙️

**首先克隆仓库：**

```bash
git clone https://github.com/KoljaB/RealtimeVoiceChat.git
cd RealtimeVoiceChat
```

现在，选择你的安装方式：

<details>
<summary><strong>🚀 选项A：Docker安装（推荐用于Linux/GPU）</strong></summary>

这是最直接的方法，将应用程序、依赖项甚至Ollama打包到可管理的容器中。

1. **构建Docker镜像：**
   *（这需要时间！它会下载基础镜像，安装Python/ML依赖项，并预下载默认的STT模型。）*
   ```bash
   docker compose build
   ```
   *（如果你想自定义`code/*.py`中的模型/设置，请在**此步骤之前**进行！）*

2. **启动服务（App和Ollama）：**
   *（在后台运行容器。GPU访问在`docker-compose.yml`中配置。）*
   ```bash
   docker compose up -d
   ```
   给它们一分钟初始化时间。

3. **（关键！）拉取你想要的Ollama模型：**
   *（这在启动后完成，以保持主应用镜像较小，并允许在不重建的情况下更改模型。执行此命令将默认模型拉取到运行中的Ollama容器。）*
   ```bash
   # 拉取默认模型（如果在server.py中配置了不同的模型，请调整）
   docker compose exec ollama ollama pull hf.co/bartowski/huihui-ai_Mistral-Small-24B-Instruct-2501-abliterated-GGUF:Q4_K_M

   # （可选）验证模型可用
   docker compose exec ollama ollama list
   ```

4. **停止服务：**
   ```bash
   docker compose down
   ```

5. **重启：**
   ```bash
   docker compose up -d
   ```

6. **查看日志/调试：**
   * 跟踪应用日志：`docker compose logs -f app`
   * 跟踪Ollama日志：`docker compose logs -f ollama`
   * 将日志保存到文件：`docker compose logs app > app_logs.txt`

</details>

<details>
<summary><strong>🛠️ 选项B：手动安装（Windows脚本/虚拟环境）</strong></summary>

此方法需要自己管理Python环境。它提供更直接的控制，但可能更棘手，尤其是关于ML依赖项。

**B1）使用Windows安装脚本：**

1. 确保你满足前提条件（Python，可能还需要CUDA驱动程序）。
2. 运行脚本。它尝试创建虚拟环境，为CUDA 12.1安装PyTorch，兼容的DeepSpeed wheel，以及其他要求。
   ```batch
   install.bat
   ```
   *（这会在激活的虚拟环境中打开一个新的命令提示符。）*
   继续到**"运行应用程序"**部分。

**B2）手动步骤（Linux/macOS/Windows）：**

1. **创建并激活虚拟环境：**
   ```bash
   python -m venv venv
   # Linux/macOS:
   source venv/bin/activate
   # Windows:
   .\venv\Scripts\activate
   ```

2. **升级Pip：**
   ```bash
   python -m pip install --upgrade pip
   ```

3. **导航到代码目录：**
   ```bash
   cd code
   ```

4. **安装PyTorch（关键步骤 - 匹配你的硬件！）：**
   * **使用NVIDIA GPU（CUDA 12.1示例）：**
     ```bash
     # 验证你的CUDA版本！如果需要，调整'cu121'和URL。
     pip install torch==2.5.1+cu121 torchaudio==2.5.1+cu121 torchvision --index-url https://download.pytorch.org/whl/cu121
     ```
   * **仅CPU（预期性能较慢）：**
     ```bash
     # pip install torch torchaudio torchvision
     ```
   * *查找其他PyTorch版本：* [https://pytorch.org/get-started/previous-versions/](https://pytorch.org/get-started/previous-versions/)

5. **安装其他要求：**
   ```bash
   pip install -r requirements.txt
   ```
   * **关于DeepSpeed的说明：** `requirements.txt`可能包含DeepSpeed。安装可能很复杂，尤其是在Windows上。`install.bat`尝试使用预编译的wheel。如果手动安装失败，你可能需要从源代码构建或查阅资源，如[deepspeedpatcher](https://github.com/erew123/deepspeedpatcher)（使用风险自负）。Coqui TTS性能最受DeepSpeed的益处。

</details>

---

## 运行应用程序 ▶️

**如果使用Docker：**
你的应用程序已经通过`docker compose up -d`运行！使用`docker compose logs -f app`检查日志。

**如果使用手动/脚本安装：**

1. **激活你的虚拟环境**（如果尚未激活）：
   ```bash
   # Linux/macOS: source ../venv/bin/activate
   # Windows: ..\venv\Scripts\activate
   ```
2. **导航到`code`目录**（如果尚未到达）：
   ```bash
   cd code
   ```
3. **启动FastAPI服务器：**
   ```bash
   python server.py
   ```

**访问客户端（两种方法）：**

1. 在浏览器中打开`http://localhost:8000`（如果远程运行/在另一台机器的Docker上，则使用你服务器的IP）。
2. 在提示时**授予麦克风权限**。
3. 点击**"开始"**开始聊天！使用"停止"结束，使用"重置"清除对话。

---

## 深入配置 🔧

想要调整AI的声音、大脑或它的聆听方式？修改`code/`目录中的Python文件。

**⚠️ 重要Docker注意事项：** 如果使用Docker，请在运行`docker compose build`之前进行任何配置更改，以确保它们包含在镜像中。

* **TTS引擎和声音（`server.py`，`audio_module.py`）：**
  * 将`server.py`中的`START_ENGINE`更改为`"coqui"`、`"kokoro"`或`"orpheus"`。
  * 在`audio_module.py`的`AudioProcessor.__init__`中调整引擎特定设置（例如，Coqui的语音模型路径，Orpheus的扬声器ID，速度）。
* **LLM后端与模型（`server.py`，`llm_module.py`）：**
  * 在`server.py`中设置`LLM_START_PROVIDER`（`"ollama"`或`"openai"`）和`LLM_START_MODEL`（例如，Ollama的`"hf.co/..."`，OpenAI的模型名称）。如果使用Docker，请记得拉取Ollama模型（参见安装步骤A3）。
  * 通过编辑`system_prompt.txt`自定义AI的个性。
* **STT设置（`transcribe.py`）：**
  * 修改`DEFAULT_RECORDER_CONFIG`以更改Whisper模型（`model`）、语言（`language`）、静音阈值（`silence_limit_seconds`）等。默认的`base.en`模型在Docker构建期间预下载。
* **轮换检测灵敏度（`turndetect.py`）：**
  * 在`TurnDetector.update_settings`方法中调整暂停持续时间常量。
* **SSL/HTTPS（`server.py`）：**
  * 设置`USE_SSL = True`并提供证书（`SSL_CERT_PATH`）和密钥（`SSL_KEY_PATH`）文件的路径。
  * **Docker用户：** 你需要调整`docker-compose.yml`以映射SSL端口（例如，443）并可能将你的证书文件作为卷挂载。
  <details>
  <summary><strong>生成本地SSL证书（Windows示例，使用mkcert）</strong></summary>

  1. 如果尚未安装，请安装Chocolatey包管理器。
  2. 安装mkcert：`choco install mkcert`
  3. 以管理员身份运行命令提示符。
  4. 安装本地证书颁发机构：`mkcert -install`
  5. 生成证书（替换`your.local.ip`）：`mkcert localhost 127.0.0.1 ::1 your.local.ip`
     * 这会在当前目录中创建`.pem`文件（例如，`localhost+3.pem`和`localhost+3-key.pem`）。相应地更新`server.py`中的`SSL_CERT_PATH`和`SSL_KEY_PATH`。记得可能需要将这些挂载到你的Docker容器中。
  </details>

---

## 贡献 🤝

有想法或发现了错误？欢迎贡献！随时提出问题或提交拉取请求。

## 许可证 📜

本项目的核心代码库在**MIT许可证**下发布（详见[LICENSE](./LICENSE)文件）。

本项目依赖于具有**自己许可条款**的外部特定TTS引擎（如`Coqui XTTSv2`）和LLM提供商。请确保你遵守所有使用组件的许可证。 