import threading
import time
from pathlib import Path
from typing import Optional
import uuid

import simpleaudio as sa


class InterruptibleTTSEngine:
    """
    TTS 引擎：
    1) synthesize_tts(text) 与 play_tts(audio) 分离
    2) 异步播放线程
    3) stop_tts() 可立即打断
    4) 状态管理 is_playing_tts
    """
    def __init__(self, sample_rate: int = 24000, voice: str = "zh-CN-XiaoxiaoNeural", temp_dir: str = "runtime/temp") -> None:
        self.sample_rate = sample_rate
        self.voice = voice
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self._play_thread: Optional[threading.Thread] = None
        self._play_obj: Optional[sa.PlayObject] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._is_playing_tts = False
        self._current_audio_file: Optional[str] = None

    @property
    def is_playing_tts(self) -> bool:
        with self._lock:
            return self._is_playing_tts

    def _set_playing(self, val: bool) -> None:
        with self._lock:
            self._is_playing_tts = val

    def synthesize_tts(self, text: str) -> str:
        if not text.strip():
            raise ValueError("TTS 输入文本为空")

        out_file = self.temp_dir / f"tts_{uuid.uuid4().hex}.wav"
        try:
            import pyttsx3
            # 初始化 pyttsx3 引擎
            engine = pyttsx3.init()
            # 设置一些参数，比如语速（默认200太快，调成150）
            engine.setProperty('rate', 150)
            engine.save_to_file(text, str(out_file))
            engine.runAndWait()
            
            return str(out_file)
        except Exception as e:
            raise RuntimeError(f"TTS 合成失败: {e}")

    def play_tts(self, audio_path: str) -> None:
        self.stop_tts()

        self._stop_event.clear()
        self._current_audio_file = audio_path

        def _worker() -> None:
            self._set_playing(True)
            try:
                wave_obj = sa.WaveObject.from_wave_file(audio_path)
                self._play_obj = wave_obj.play()

                while self._play_obj.is_playing():
                    if self._stop_event.is_set():
                        self._play_obj.stop()
                        break
                    time.sleep(0.01)

            except Exception as e:
                print(f"[TTS] 播放失败: {e}")
            finally:
                self._set_playing(False)
                self._play_obj = None

                try:
                    if self._current_audio_file and Path(self._current_audio_file).exists():
                        Path(self._current_audio_file).unlink(missing_ok=True)
                except Exception as e:
                    print(f"[TTS] 临时文件清理失败: {e}")

                self._current_audio_file = None

        self._play_thread = threading.Thread(target=_worker, daemon=True)
        self._play_thread.start()

    def stop_tts(self) -> None:
        self._stop_event.set()
        if self._play_obj is not None:
            try:
                self._play_obj.stop()
            except Exception:
                pass

        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=0.2)

        self._set_playing(False)

        try:
            if self._current_audio_file and Path(self._current_audio_file).exists():
                Path(self._current_audio_file).unlink(missing_ok=True)
        except Exception:
            pass
        self._current_audio_file = None

    def shutdown(self) -> None:
        self.stop_tts()
