from __future__ import annotations

import argparse
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel


class GpuMemoryMonitor:
    def __init__(self) -> None:
        self.peak_used_mib: int | None = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="gpu-memory-monitor")

    def __enter__(self) -> GpuMemoryMonitor:
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop.wait(0.1):
            try:
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=memory.used",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=2,
                )
                used = int(result.stdout.strip().splitlines()[0])
                self.peak_used_mib = max(self.peak_used_mib or 0, used)
            except (FileNotFoundError, subprocess.SubprocessError, ValueError):
                return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded Faster-Whisper benchmark")
    parser.add_argument("audio", type=Path)
    parser.add_argument("--model", default="small")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--compute-type", default="float16")
    parser.add_argument("--model-cache", type=Path, required=True)
    args = parser.parse_args()

    with GpuMemoryMonitor() as gpu:
        started = time.perf_counter()
        model = WhisperModel(
            args.model,
            device=args.device,
            compute_type=args.compute_type,
            download_root=str(args.model_cache),
        )
        loaded = time.perf_counter()
        segments, info = model.transcribe(
            str(args.audio),
            language="en",
            beam_size=1,
            best_of=1,
            temperature=0,
            vad_filter=False,
            condition_on_previous_text=False,
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        completed = time.perf_counter()
    result: dict[str, Any] = {
        "model": args.model,
        "device": args.device,
        "compute_type": args.compute_type,
        "load_seconds": round(loaded - started, 3),
        "transcribe_seconds": round(completed - loaded, 3),
        "audio_seconds": round(info.duration, 3),
        "real_time_factor": round((completed - loaded) / info.duration, 3),
        "language_probability": round(info.language_probability, 4),
        "peak_total_gpu_memory_used_mib": gpu.peak_used_mib,
        "transcript": text,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
