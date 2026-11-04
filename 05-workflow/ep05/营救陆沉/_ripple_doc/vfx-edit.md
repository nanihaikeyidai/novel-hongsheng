# VFX Edit LoRAs

Experimental prompt-directed video editing for MiniMax H3. The source clip is supplied as an
aligned guide, and the goal is to return the same take with only the requested change applied.

**Trigger:** every prompt must begin with `vfx_edit:`. Start with LoRA strength `1.0`.

## Versions

### Standard

[`minimax_h3_vfx_edit_v1.0_r128.safetensors`](../loras/minimax_h3_vfx_edit_v1.0_r128.safetensors)
was trained at the 384 resolution bucket with 73-frame clips. It is the simpler version and does
not require a native image reference.

### FFP

[`minimax_h3_vfx_edit_v1.0_r128_ffp.safetensors`](../loras/minimax_h3_vfx_edit_v1.0_r128_ffp.safetensors)
means **first-frame propagate**. It was continued from the standard LoRA at the higher 512
resolution bucket with 124-frame clips and includes experimental training for sending an edited
first frame through H3's native image-reference channel.

FFP does not always work perfectly. If a native image reference is supplied, the prompt must
explicitly refer to `<Picture 1>` and explain its role. The workflow's auto-prompter can produce
that wording. If no image is supplied, ensure the generated prompt contains neither `<Picture 1>`
nor `<Subject 1>`.

## Workflow

Both versions use:
[`workflows/minimax_h3_vfxedit_wokflow.json`](../workflows/minimax_h3_vfxedit_wokflow.json)

Choose the desired LoRA in the loader. Put the complete source clip into `MiniMaxH3AddGuide`, not
into a video-reference slot. Connect the VAE, use `frame_idx = 0`, and match the source aspect
ratio and supported frame count.

## Prompting

Use one concise English sentence: first state the edit, then define what must remain unchanged.

```text
vfx_edit: Add fire effects to the man's hands while preserving his identity, pose, motion, clothing, framing, lighting and background.
```

Do not ask the model to preserve the same region being replaced. When changing the environment,
preserve only unrelated elements. For progressive effects, describe the sequence literally; for
example, melting skin that reveals machinery is different from turning the skin into metal.

The auto-prompter is useful but can misunderstand the request or invent a reference. Read its
final English prompt before generation.

Known limitations include identity drift, rewritten text and logos, weak tiny details, and poorer
results on long clips. This is not a compositor, face-swap tool or guarantee of exact preservation.

## Examples

<video controls width="100%" src="https://huggingface.co/Alissonerdx/Minimax-H3-ComfyUI/resolve/main/examples/vfx_edit_1.mp4"></video>

<video controls width="100%" src="https://huggingface.co/Alissonerdx/Minimax-H3-ComfyUI/resolve/main/examples/vfx_edit_2.mp4"></video>

<video controls width="100%" src="https://huggingface.co/Alissonerdx/Minimax-H3-ComfyUI/resolve/main/examples/vfx_edit_3.mp4"></video>

<video controls width="100%" src="https://huggingface.co/Alissonerdx/Minimax-H3-ComfyUI/resolve/main/examples/vfx_edit_4.mp4"></video>

<video controls width="100%" src="https://huggingface.co/Alissonerdx/Minimax-H3-ComfyUI/resolve/main/examples/vfx_edit_5.mp4"></video>

<video controls width="100%" src="https://huggingface.co/Alissonerdx/Minimax-H3-ComfyUI/resolve/main/examples/vfx_edit_6.mp4"></video>

<video controls width="100%" src="https://huggingface.co/Alissonerdx/Minimax-H3-ComfyUI/resolve/main/examples/vfx_edit_7.mp4"></video>

[Back to the repository index](../README.md)
