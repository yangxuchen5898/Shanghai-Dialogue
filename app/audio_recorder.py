from collections import deque
from typing import Deque, Optional
import pyaudio


class AudioRecorder:
    """
    麦克风输入 + 音频缓存 + 逐帧读取
    """
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        frame_ms: int = 20,
        format_name: str = "paInt16",
        max_buffer_frames: int = 6000,  # 最多缓存约120秒
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_ms = frame_ms
        self.format = getattr(pyaudio, format_name, pyaudio.paInt16)

        self.pa = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None

        self.samples_per_frame = int(self.sample_rate * self.frame_ms / 1000)
        self.bytes_per_sample = 2  # paInt16
        self.sample_width = self.bytes_per_sample
        self.frame_bytes_len = self.samples_per_frame * self.channels * self.bytes_per_sample

        self.audio_buffer: Deque[bytes] = deque(maxlen=max_buffer_frames)
        self.frame_index = -1

    def start(self) -> None:
        try:
            self.stream = self.pa.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.samples_per_frame,
            )
        except Exception as e:
            raise RuntimeError(f"打开麦克风失败: {e}")

    def stop(self) -> None:
        if self.stream is not None:
            try:
                self.stream.stop_stream()
                self.stream.close()
            finally:
                self.stream = None
        self.pa.terminate()

    def read_frame(self) -> bytes:
        if self.stream is None:
            raise RuntimeError("音频流未启动")
        try:
            data = self.stream.read(self.samples_per_frame, exception_on_overflow=False)
            if len(data) != self.frame_bytes_len:
                data = data[: self.frame_bytes_len].ljust(self.frame_bytes_len, b"\x00")
            return data
        except Exception as e:
            raise RuntimeError(f"读取麦克风帧失败: {e}")

    def append_frame(self, frame_data: bytes) -> int:
        self.audio_buffer.append(frame_data)
        self.frame_index += 1
        return self.frame_index
