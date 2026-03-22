import wave
from datetime import datetime
from pathlib import Path
from typing import Deque


class SegmentManager:
    """
    根据 start_frame / end_frame 从 audio_buffer 中截取并保存 utterance
    """
    def __init__(self, sample_rate: int, channels: int, sample_width: int, output_dir: str) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_utterance(self, frames: Deque[bytes], start_frame: int, end_frame: int) -> str:
        if start_frame < 0:
            start_frame = 0
        if end_frame < start_frame:
            raise ValueError(f"非法切片区间: start={start_frame}, end={end_frame}")

        frame_list = list(frames)
        if not frame_list:
            raise RuntimeError("音频缓存为空，无法保存 utterance")

        end_frame = min(end_frame, len(frame_list) - 1)
        start_frame = min(start_frame, end_frame)

        utter_frames = frame_list[start_frame:end_frame + 1]
        if len(utter_frames) == 0:
            raise RuntimeError("切片后 utterance 为空")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        wav_path = self.output_dir / f"utt_{ts}.wav"

        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.sample_width)
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(utter_frames))

        return str(wav_path)
