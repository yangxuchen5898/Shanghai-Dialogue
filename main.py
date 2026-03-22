import time
import traceback
from pathlib import Path

from app.config import settings
from app.audio_recorder import AudioRecorder
from app.vad_manager import VADManager
from app.segment_manager import SegmentManager
from app.asr_engine import SenseVoiceASR
from app.llm_engine import QwenLLM
from app.tts_engine import InterruptibleTTSEngine


def inference(audio_path: str, asr: SenseVoiceASR, llm: QwenLLM, tts: InterruptibleTTSEngine) -> None:
    """
    单轮推理链路:
    asr_inference(audio_path) -> llm_inference(text) -> synthesize_tts(text) -> play_tts(audio)
    """
    try:
        user_text = asr.asr_inference(audio_path)
        if not user_text.strip():
            print("[Inference] ASR 结果为空，跳过本轮。")
            return
        print(f"[ASR] {user_text}")

        reply = llm.llm_inference(user_text)
        print(f"[LLM] {reply}")

        tts_audio = tts.synthesize_tts(reply)
        tts.play_tts(tts_audio)

    except Exception as e:
        print(f"[Inference] 本轮处理失败: {e}")
        traceback.print_exc()


def main() -> None:
    print("=== Shanghai-Dialogue 启动 ===")
    print("按 Ctrl+C 退出。")

    temp_dir = Path(settings.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    recorder = AudioRecorder(
        sample_rate=settings.sample_rate,
        channels=settings.channels,
        frame_ms=settings.frame_ms,
        format_name=settings.audio_format,
    )
    vad = VADManager(
        sample_rate=settings.sample_rate,
        frame_ms=settings.frame_ms,
        mode=settings.vad_mode,
        window_frames=settings.vad_window_frames,
        speech_ratio_threshold=settings.vad_speech_ratio_threshold,
        end_silence_frames=settings.end_silence_frames,
    )
    segment_manager = SegmentManager(
        sample_rate=settings.sample_rate,
        channels=settings.channels,
        sample_width=recorder.sample_width,
        output_dir=settings.utterance_dir,
    )
    asr = SenseVoiceASR(
        model_dir=settings.sensevoice_model_dir,
        device=settings.asr_device,
        language=settings.asr_language,
    )

    try:
        llm = QwenLLM(
            api_key=settings.qwen_api_key,
            model=settings.qwen_model,
            base_url=settings.qwen_base_url,
            timeout=settings.llm_timeout,
        )
    except Exception as e:
        print(f"[Startup] LLM 初始化失败: {e}")
        return

    tts = InterruptibleTTSEngine(
        sample_rate=settings.tts_sample_rate,
        voice=settings.tts_voice,
        temp_dir=settings.temp_dir,
    )

    try:
        asr.load_model()
    except Exception as e:
        print(f"[Startup] ASR 模型加载失败: {e}")
        print("将继续运行，但 ASR 调用会失败，请检查配置。")

    try:
        recorder.start()
    except Exception as e:
        print(f"[Startup] 麦克风打开失败: {e}")
        return

    try:
        while True:
            frame_bytes = recorder.read_frame()
            frame_idx = recorder.append_frame(frame_bytes)

            # 逐帧 VAD
            is_speech_frame = vad.is_speech_frame(frame_bytes)
            # 0.5s 窗口级别状态
            window_state = vad.update_window_and_get_state(is_speech_frame)

            # 新语音开始判定
            just_started = vad.update_start_detection(frame_idx, window_state)

            # 若播放中遇到新语音活动：实时打断
            if just_started and tts.is_playing_tts:
                print("[Main] 检测到用户新语音，立即打断当前 TTS。")
                tts.stop_tts()

            # 语音结束判定（连续静音）
            end_triggered, start_frame, end_frame = vad.update_end_detection(frame_idx, is_speech_frame)
            if end_triggered and start_frame is not None and end_frame is not None:
                try:
                    audio_path = segment_manager.save_utterance(
                        frames=recorder.audio_buffer,
                        start_frame=start_frame,
                        end_frame=end_frame,
                    )
                    print(f"[Segment] 已保存单轮语音: {audio_path}")
                    inference(audio_path, asr=asr, llm=llm, tts=tts)
                except Exception as e:
                    print(f"[Main] 语音切分/推理失败: {e}")

            # 降低 CPU 占用
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n[Main] 收到退出信号，正在关闭...")
    except Exception as e:
        print(f"[Main] 主循环异常: {e}")
        traceback.print_exc()
    finally:
        try:
            recorder.stop()
        except Exception:
            pass
        try:
            tts.shutdown()
        except Exception:
            pass
        print("[Main] 已安全退出。")


if __name__ == "__main__":
    main()
