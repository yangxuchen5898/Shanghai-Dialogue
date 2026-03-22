# Shanghai-Dialogue

本项目实现本地实时语音对话链路：

麦克风输入 -> VAD -> 单轮切分保存 -> ASR(SenseVoice) -> LLM(千问) -> TTS(可打断播放)

## 功能特点

- 20ms 逐帧 VAD（webrtcvad）
- 0.5秒窗口级语音占比判断（25帧，阈值40%）
- 明确拆分开始判定 / 结束判定 / 音频切片保存
- 推理链路函数化：`asr_inference` / `llm_inference` / `synthesize_tts` / `play_tts`
- TTS 异步播放 + `stop_tts()` 实时打断
- 主线程在播放期间持续监听麦克风，可“说话即打断”

## 快速开始

1. 安装依赖
2. 复制配置模板并填写密钥、模型路径
3. 运行主程序

详见下文“启动方式”。

## 启动方式（Windows PowerShell）

```powershell
cd d:\github_projects\Shanghai-Dialogue
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```