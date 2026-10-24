"""金鱼工作流本地化最后一步：用本地等价的 H3 采样链替换 RH 的 SelfLiftH3Sampler。

背景：
  金鱼工作流的采样器是 RunningHub 侧的 SelfLiftH3Sampler，它把
  「低分辨率采样 + 潜空间超分采样」揉在一个节点里，本地没有这个节点。
  但它的下游用法是确定的：
      SelfLift.out0 -> VAEDecode.samples        (video VAE 解码)
      SelfLift.out0 -> VAEDecodeAudio.samples  (audio VAE 解码)
  即输出的是**一个 AV latent**，两边各用对应 VAE 解。
  这正是本地 MiniMaxH3AVDecodeT8 的职责（outputs: images / audio）。

  所以降级方案是照搬本地已验证过的 Ref2VA 采样链：
      MiniMaxH3MultiRateSamplerEXPT8  (model, av_latent) -> model / sampler / sigmas
      BasicGuider(model, conditioning)
      RandomNoise(seed)
      SamplerCustomAdvanced(noise, guider, sampler, sigmas, latent_image)
      MiniMaxH3AVDecodeT8(av_latent, video_vae, audio_vae) -> images, audio

  与金鱼原图的差异（都是刻意的）：
      - 砍掉超分采样（lowres_scale 0.6 / upscaler），
        本地 16GB 显存下先保证能出片；需要细节时再单独接 upscale pass。
      - shift / steps 沿用本地验证过的 turbo 4 步组合：
        video_steps=4, audio_steps=10, shift_video=12.0, shift_audio=3.0
        金鱼原图这两个值来自 MiniMaxH3SigmaShift#333，改由 MultiRateSampler 内部承担。

顺带清理：
  - Note / MarkdownNote：纯备注节点，直接删。
  - Reroute#220/#221：纯连线节点，被采样链取代后一并删。
  - 「忽略多组孤海」：无输入无输出的孤立标注节点，删。
  - KSamplerSelect#255 / BasicScheduler#261：采样参数已由 MultiRateSampler 承担，删。
  - ConditioningZeroOut#328：SelfLift 内部用，接入新的 BasicGuider 后不需要，删。
"""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path("F:/h3tmp/jinyu_resolved.json")
OUT = Path("F:/h3tmp/jinyu_local_final.json")

# 本地采样链的新节点 id（避开原图已用 id）
NEW_IDS = {
    "mrs": 9001,   # MiniMaxH3MultiRateSamplerEXPT8
    "guider": 9002,
    "noise": 9003,
    "sampler": 9004,
    "avdecode": 9005,
}

VIDEO_STEPS = 4
AUDIO_STEPS = 10
SHIFT_VIDEO = 12.0
SHIFT_AUDIO = 3.0
SEED = 29732110694208


def main() -> None:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    nodes = d["nodes"]
    links = d["links"]
    by_id = {n["id"]: n for n in nodes}
    by_link = {l[0]: l for l in links}

    # ---------- 定位关键节点 ----------
    h3 = next(n for n in nodes if n["type"] == "MiniMaxH3ReferenceToVideo")
    selflift = next(n for n in nodes if n["type"] == "SelfLiftH3Sampler")
    model_prev = next(n for n in nodes if n["type"] == "ModelPreviewOverrideKJ")
    vvae = next(n for n in nodes if n["id"] == 36)   # video VAE
    avae = next(n for n in nodes if n["id"] == 37)   # audio VAE
    combine = next(n for n in nodes if n["type"] == "VHS_VideoCombine")

    print(f"H3#{h3['id']}  SelfLift#{selflift['id']}  "
          f"ModelPreviewOverrideKJ#{model_prev['id']}  "
          f"VVAE#{vvae['id']} AVAE#{avae['id']}  Combine#{combine['id']}")

    # ---------- 建新采样链节点（前端格式） ----------
    def mk(nid, ntype, title, inputs, outputs, widgets=None):
        n = {
            "id": nid, "type": ntype, "pos": [4400, 1700], "size": [300, 120],
            "flags": {}, "order": 900, "mode": 0,
            "inputs": inputs, "outputs": outputs,
            "properties": {"Node name for S&R": ntype},
            "title": title,
        }
        if widgets is not None:
            n["widgets_values"] = widgets
        return n

    new_nodes = [
        mk(NEW_IDS["mrs"], "MiniMaxH3MultiRateSamplerEXPT8",
           "本地采样(替代SelfLift)",
           [{"name": "model", "type": "MODEL", "link": 7001},
            {"name": "av_latent", "type": "LATENT", "link": 7010}],
           [{"name": "MODEL", "type": "MODEL", "links": [7001, 7012]},
            {"name": "sampler", "type": "SAMPLER", "links": [7002]},
            {"name": "sigmas", "type": "SIGMAS", "links": [7003]}],
           [VIDEO_STEPS, AUDIO_STEPS, SHIFT_VIDEO, SHIFT_AUDIO]),

        mk(NEW_IDS["guider"], "BasicGuider", "Guider",
           [{"name": "model", "type": "MODEL", "link": 7012},
            {"name": "conditioning", "type": "CONDITIONING", "link": 7004}],
           [{"name": "GUIDER", "type": "GUIDER", "links": [7011]}]),

        mk(NEW_IDS["noise"], "RandomNoise", "噪声",
           [], [{"name": "NOISE", "type": "NOISE", "links": [7005]}],
           [SEED]),

        mk(NEW_IDS["sampler"], "SamplerCustomAdvanced", "采样执行",
           [{"name": "noise", "type": "NOISE", "link": 7005},
            {"name": "guider", "type": "GUIDER", "link": 7011},
            {"name": "sampler", "type": "SAMPLER", "link": 7002},
            {"name": "sigmas", "type": "SIGMAS", "link": 7003},
            {"name": "latent_image", "type": "LATENT", "link": 7007}],
           [{"name": "output", "type": "LATENT", "links": [7006]}]),

        mk(NEW_IDS["avdecode"], "MiniMaxH3AVDecodeT8", "AV 解码",
           [{"name": "av_latent", "type": "LATENT", "link": 7006},
            {"name": "video_vae", "type": "VAE", "link": 7008},
            {"name": "audio_vae", "type": "VAE", "link": 7009}],
           [{"name": "images", "type": "IMAGE", "links": []},
            {"name": "audio", "type": "AUDIO", "links": []}]),
    ]

    # ---------- 重建连线 ----------
    def link(lid, oid, oslot, tid, tslot, ltype):
        return [lid, oid, oslot, tid, tslot, ltype]

    # H3.out1(LATENT) -> MultiRateSampler.av_latent
    h3_latent_link = h3["outputs"][1]["links"][0]
    new_links = [
        link(h3_latent_link, h3["id"], 1, NEW_IDS["mrs"], 1, "LATENT"),
        # ModelPreviewOverrideKJ.out0 -> MultiRateSampler.model
        link(7001, model_prev["id"], 0, NEW_IDS["mrs"], 0, "MODEL"),
        # H3.out0(CONDITIONING) -> Guider.conditioning
        link(7004, h3["id"], 0, NEW_IDS["guider"], 1, "CONDITIONING"),
        # Guider -> SamplerCustomAdvanced.guider
        link(7011, NEW_IDS["guider"], 0, NEW_IDS["sampler"], 1, "GUIDER"),
        # BasicGuider.model 也来自 ModelPreviewOverrideKJ（独立 link id，
        # 因为 wf_to_api 是按 link 逐条写 inputs，同一 link id 只能写一次）
        link(7012, model_prev["id"], 0, NEW_IDS["guider"], 0, "MODEL"),
        # Sampler.latent_image <- H3 的 latent（与 av_latent 同源）
        link(7007, h3["id"], 1, NEW_IDS["sampler"], 4, "LATENT"),
        # VAE
        link(7008, vvae["id"], 0, NEW_IDS["avdecode"], 1, "VAE"),
        link(7009, avae["id"], 0, NEW_IDS["avdecode"], 2, "VAE"),
    ]
    # MultiRateSampler 同时吃 H3 的 latent 作 av_latent（7010 与 h3_latent_link 同源）
    new_links.append(link(7010, h3["id"], 1, NEW_IDS["mrs"], 1, "LATENT"))
    # 内部 7002/7003/7005/7006 已在节点 outputs/inputs 里互相登记
    for lid, oid, oslot, tid, tslot, lt in (
        (7002, NEW_IDS["mrs"], 1, NEW_IDS["sampler"], 2, "SAMPLER"),
        (7003, NEW_IDS["mrs"], 2, NEW_IDS["sampler"], 3, "SIGMAS"),
        (7005, NEW_IDS["noise"], 0, NEW_IDS["sampler"], 0, "NOISE"),
        (7006, NEW_IDS["sampler"], 0, NEW_IDS["avdecode"], 0, "LATENT"),
    ):
        new_links.append(link(lid, oid, oslot, tid, tslot, lt))

    drop_ids: set[int] = set()

    # ---------- 旁路 BlockSparseAttention ----------
    # 金鱼用它做稀疏注意力省显存，但本地版的 selection 是必填且无默认值
    # （RH 版节点签名不同），直接报 missing 1 required positional argument。
    # 它是纯优化、不是功能必需，直接把 model 从上游直连到下游。
    bsa = next((n for n in nodes if n["type"] == "BlockSparseAttention"), None)
    if bsa:
        up = [l for l in links if l[3] == bsa["id"]]
        down = [l for l in links if l[1] == bsa["id"]]
        if up and down:
            u, dn = up[0], down[0]
            print(f"旁路 BlockSparseAttention#{bsa['id']}："
                  f"上游#{u[1]} -> 下游#{dn[3]}")
            links = [l for l in links
                     if l[0] not in (u[0], dn[0])]
            links.append([u[0], u[1], u[2], dn[3], dn[4], dn[5]])
            drop_ids.add(bsa["id"])

    # ---------- 删旧节点 + 其所有连线 ----------
    drop_ids.add(selflift["id"])
    for iid in (220, 221, 255, 261, 328):
        if iid in by_id:
            drop_ids.add(iid)
    # 纯备注 / 孤立标注
    for n in nodes:
        if n["type"] in ("Note", "MarkdownNote", "Reroute"):
            drop_ids.add(n["id"])
        elif n["type"] == "忽略多组孤海":
            drop_ids.add(n["id"])

    keep_links = [l for l in links if l[1] not in drop_ids and l[3] not in drop_ids]
    dropped_link_ids = {l[0] for l in links} - {l[0] for l in keep_links}

    # ---------- 把 Combine 的 images / audio 指到 AVDecode ----------
    combine = next(n for n in nodes if n["type"] == "VHS_VideoCombine")
    for l in keep_links:
        if l[3] == combine["id"]:
            if l[4] == 0:      # images
                l[1], l[2] = NEW_IDS["avdecode"], 0
                l[5] = "IMAGE"
            elif l[4] == 1:    # audio
                l[1], l[2] = NEW_IDS["avdecode"], 1
                l[5] = "AUDIO"

    # H3 原来 out1 指向的旧 link 已被 drop；把 h3.outputs 的 links 登记改成新链
    h3["outputs"][1]["links"] = [h3_latent_link, 7010, 7007]
    h3["outputs"][0]["links"] = [7004]

    nodes = [n for n in nodes if n["id"] not in drop_ids] + new_nodes
    all_links = keep_links + new_links

    # 清理所有节点里指向已删 link 的输入端口
    alive = {l[0] for l in all_links}
    fixed = 0
    for n in nodes:
        for sp in n.get("inputs") or []:
            if sp.get("link") is not None and sp["link"] not in alive:
                sp["link"] = None
                fixed += 1
        for op in n.get("outputs") or []:
            if op.get("links"):
                op["links"] = [x for x in op["links"] if x in alive]
    print(f"删除节点 {sorted(drop_ids)}（共 {len(drop_ids)}）")
    print(f"清理悬空端口 {fixed} 个")

    d["nodes"] = nodes
    d["links"] = all_links
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已输出 {OUT}：{len(nodes)} 节点 / {len(all_links)} 连线")
    miss = sorted({n["type"] for n in nodes} - set(json.loads(
        (__import__("urllib.request", fromlist=["x"]).urlopen(
            "http://127.0.0.1:8188/object_info", timeout=60)).read())))
    print("本地缺失节点类型：", miss)


if __name__ == "__main__":
    main()
