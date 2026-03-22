from pathlib import Path


class SenseVoiceASR:
    """
    SenseVoice ASR 封装：
    - load_model()
    - asr_inference(audio_path)
    """
    def __init__(self, model_dir: str, device: str = "cpu", language: str = "zh") -> None:
        self.model_dir = model_dir
        self.device = device
        self.language = language
        self.model = None

    def load_model(self) -> None:
        try:
            from funasr import AutoModel
        except Exception as e:
            raise RuntimeError(f"导入 FunASR 失败，请先安装依赖: {e}")

        model_path = self.model_dir
        if not Path(model_path).exists():
            raise FileNotFoundError(f"SenseVoice 模型路径不存在: {model_path}")

        self.model = AutoModel(
            model=model_path,
            device=self.device,
            disable_update=True,
        )

    def asr_inference(self, audio_path: str) -> str:
        if self.model is None:
            raise RuntimeError("ASR 模型未加载，请先调用 load_model()")

        try:
            result = self.model.generate(
                input=audio_path,
                language=self.language,
                use_itn=True,
            )
            if isinstance(result, list) and result:
                text = result[0].get("text", "")
            elif isinstance(result, dict):
                text = result.get("text", "")
            else:
                text = str(result)
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"ASR 推理失败: {e}")
