"""生成角色音色参考：用现有人物音色的克隆 + 情绪，向 H3 输出参考音频。

用法：
    USE_TF=0 <整合包python> scripts/gen_voice_ref.py \
        --ref <参考音色.wav> --text-file <文本.txt> --out <输出.wav> \
        [--emo-text "<情绪描述>"] [--emo-vector happy,angry,...]

脚本调用 IndexTTS2.5 的 infer() 并自行落盘（官方 CLI 的 output_path 分支
在某些环境下不写文件，此处直接接管返回值）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import wave

import numpy as np


def save_wav(path: Path, wav_int16: np.ndarray, sample_rate: int) -> None:
    """落盘 PCM16 WAV。

    不用 torchaudio.save：整合包内torchcodec 缺 FFmpeg DLL 会直接抛错，
    改用标准库 wave 最稳。
    """
    wav_int16 = np.asarray(wav_int16, dtype=np.int16).reshape(-1)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate))
        wf.writeframes(wav_int16.tobytes())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, type=Path)
    ap.add_argument("--text-file", type=Path)
    ap.add_argument("--text")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--model-dir", required=True, type=Path)
    ap.add_argument("--emo-text")
    ap.add_argument(
        "--emo-vector",
        help="happy,angry,sad,fear,disgust,melancholy,surprise,calm (0~1, 和<=1)",
    )
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if args.text_file:
        text = args.text_file.read_text(encoding="utf-8").strip()
    else:
        text = (args.text or "").strip()
    if not text:
        print("文本为空", file=sys.stderr)
        return 1

    import torch

    # indextts 包位于 comfyui-indextts25-T8 节点目录，运行时按 cwd 找不到，这里显式补路径
    node_dir = Path(
        r"F:\Work-Fisher纯净包2026.8.7\ComfyUI\custom_nodes\comfyui-indextts25-T8"
    )
    if str(node_dir) not in sys.path:
        sys.path.insert(0, str(node_dir))

    from indextts.infer_v2_5 import IndexTTS2

    tts = IndexTTS2(
        cfg_path=str(args.model_dir / "config.yaml"),
        model_dir=str(args.model_dir),
        use_bf16=True,
        use_fp16=False,
        device="cuda:0",
        use_qwen_emo=bool(args.emo_text),
    )

    emo_vector = None
    if args.emo_vector:
        emo_vector = [float(v) for v in args.emo_vector.split(",")]

    # output_path 传空串，让 infer 直接返回 (sample_rate, wav_int16.numpy())
    result = tts.infer(
        spk_audio_prompt=str(args.ref),
        text=text,
        output_path="",
        lang="ZH",
        emo_vector=emo_vector,
        use_emo_text=bool(args.emo_text),
        emo_text=args.emo_text,
        seed=args.seed,
    )
    if result is None:
        print("生成失败：infer 返回 None", file=sys.stderr)
        return 2

    sample_rate, wav = result
    wav = np.asarray(wav).squeeze()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    save_wav(args.out, wav, sample_rate)
    dur = len(wav) / sample_rate
    print(f">> saved {args.out}  {dur:.2f}s  {sample_rate}Hz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())