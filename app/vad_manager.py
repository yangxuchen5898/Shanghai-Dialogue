from collections import deque
from typing import Deque, Optional, Tuple
import webrtcvad


class VADManager:
    """
    1) 20ms 逐帧VAD
    2) 0.5秒窗口聚合判断
    3) 语音开始/结束判定（开始和结束逻辑拆分）
    """
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_ms: int = 20,
        mode: int = 2,
        window_frames: int = 25,
        speech_ratio_threshold: float = 0.4,
        end_silence_frames: int = 35,
    ) -> None:
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.vad = webrtcvad.Vad(mode)

        self.window_frames = window_frames
        self.speech_ratio_threshold = speech_ratio_threshold
        self.window_buffer: Deque[bool] = deque(maxlen=window_frames)

        self.in_speech = False
        self.start_frame: Optional[int] = None
        self.end_silence_frames = end_silence_frames
        self.current_silence_count = 0

    def is_speech_frame(self, frame_bytes: bytes) -> bool:
        try:
            return self.vad.is_speech(frame_bytes, self.sample_rate)
        except Exception:
            return False

    def update_window_and_get_state(self, is_speech_frame: bool) -> bool:
        self.window_buffer.append(is_speech_frame)
        if len(self.window_buffer) < self.window_frames:
            return False
        speech_count = sum(1 for x in self.window_buffer if x)
        ratio = speech_count / self.window_frames
        return ratio > self.speech_ratio_threshold

    def update_start_detection(self, frame_idx: int, window_has_speech: bool) -> bool:
        if (not self.in_speech) and window_has_speech:
            self.in_speech = True
            self.start_frame = max(0, frame_idx - self.window_frames + 1)
            self.current_silence_count = 0
            return True
        return False

    def update_end_detection(self, frame_idx: int, is_speech_frame: bool) -> Tuple[bool, Optional[int], Optional[int]]:
        if not self.in_speech:
            return False, None, None

        if is_speech_frame:
            self.current_silence_count = 0
            return False, None, None

        self.current_silence_count += 1
        if self.current_silence_count >= self.end_silence_frames:
            end_frame = frame_idx - self.current_silence_count
            start = self.start_frame

            self.in_speech = False
            self.start_frame = None
            self.current_silence_count = 0
            self.window_buffer.clear()

            return True, start, end_frame

        return False, None, None
