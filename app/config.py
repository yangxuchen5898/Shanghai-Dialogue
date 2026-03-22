import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # 音频基础配置
    sample_rate: int = int(os.getenv("SAMPLE_RATE", "16000"))
    channels: int = int(os.getenv("CHANNELS", "1"))
    frame_ms: int = int(os.getenv("FRAME_MS", "20"))  # 20ms
    audio_format: str = os.getenv("AUDIO_FORMAT", "paInt16")

    # VAD 配置
    vad_mode: int = int(os.getenv("VAD_MODE", "2"))  # 0-3, 越大越激进
    vad_window_frames: int = int(os.getenv("VAD_WINDOW_FRAMES", "25"))  # 0.5秒 / 20ms = 25
    vad_speech_ratio_threshold: float = float(os.getenv("VAD_SPEECH_RATIO_THRESHOLD", "0.4"))
    end_silence_frames: int = int(os.getenv("END_SILENCE_FRAMES", "35"))  # 约700ms静音判结束

    # 路径
    utterance_dir: str = os.getenv("UTTERANCE_DIR", "runtime/utterances")
    temp_dir: str = os.getenv("TEMP_DIR", "runtime/temp")

    # ASR
    sensevoice_model_dir: str = os.getenv("SENSEVOICE_MODEL_DIR", "models/sensevoice")
    asr_device: str = os.getenv("ASR_DEVICE", "cpu")
    asr_language: str = os.getenv("ASR_LANGUAGE", "zh")

    # LLM（千问，OpenAI兼容接口）
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    qwen_model: str = os.getenv("QWEN_MODEL", "qwen-plus")
    qwen_base_url: str = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "30"))

    # TTS
    tts_sample_rate: int = int(os.getenv("TTS_SAMPLE_RATE", "24000"))
    tts_voice: str = os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural")


settings = Settings()

# 确保目录存在
Path(settings.utterance_dir).mkdir(parents=True, exist_ok=True)
Path(settings.temp_dir).mkdir(parents=True, exist_ok=True)
