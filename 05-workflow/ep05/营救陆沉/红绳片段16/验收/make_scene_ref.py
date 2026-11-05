"""P16 场景参考图后期：把新生成的车库图做赛璐璐风格化 + 裁 16:9 去水印，
并另外导出一张 100% 同源的成片截帧备用。不消耗任何生成积分。

用法：python make_scene_ref.py
"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent          # 红绳片段16/验收
SEG = HERE.parent
UP = SEG / "上传包"
P14 = SEG.parent / "红绳片段14"


def load_bgr(p: Path) -> np.ndarray:
    """cv2.imread 不支持中文路径，统一走 PIL。"""
    return cv2.cvtColor(np.array(Image.open(p).convert("RGB")), cv2.COLOR_RGB2BGR)


def save_bgr(bgr: np.ndarray, p: Path, quality: int = 93) -> None:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    Image.fromarray(rgb).save(p, quality=quality, subsampling=0)


def crop169(bgr: np.ndarray) -> np.ndarray:
    """顶部裁成 16:9；右下角「AI生成 / WORKBUDDY」水印随之被切掉。"""
    h, w = bgr.shape[:2]
    nh = int(w * 9 / 16)
    if h >= nh:
        return bgr[:nh, :, :]
    return cv2.copyMakeBorder(bgr, 0, nh - h, 0, 0, cv2.BORDER_REPLICATE)


def celify(bgr: np.ndarray) -> np.ndarray:
    """温和赛璐璐化：双边滤波 + 16 级色阶量化 + 细墨线 + 冷蓝灰微调。

    刻意不用 cv2.stylization + 8 级量化——v1 那样会在大面积混凝土上
    生成青绿／紫色迷彩色块（见 _v1_作废_迷彩色偏.jpg）。
    """
    sm = cv2.bilateralFilter(bgr, 7, 40, 40)
    step = 255 / 15
    q = np.clip(np.round(np.round(sm.astype(np.float32) / step) * step), 0, 255).astype(np.uint8)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    edge = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 30, 90)
    mask = (edge > 0).astype(np.float32)[..., None]
    q = np.clip(q.astype(np.float32) * (1 - 0.22 * mask), 0, 255).astype(np.uint8)
    out = cv2.addWeighted(q, 0.72, bgr, 0.28, 0)
    out[:, :, 0] = np.clip(out[:, :, 0].astype(np.int16) + 4, 0, 255).astype(np.uint8)
    out[:, :, 2] = np.clip(out[:, :, 2].astype(np.int16) - 3, 0, 255).astype(np.uint8)
    return cv2.resize(out, (1664, 928), interpolation=cv2.INTER_LANCZOS4)


def main() -> None:
    # v1 的强风格化出现迷彩色偏，作废并移出上传包，避免误上传
    stale = UP / "image3_garage_anime_v1.jpg"
    if stale.exists():
        import shutil
        shutil.move(str(stale), str(HERE / "_v1_作废_迷彩色偏.jpg"))
        print("v1 作废并移出上传包")

    gen = HERE / "Redraw_as_a_clean_HAND_PAINTED_2026-11-05T14-04-16.png"
    a = celify(crop169(load_bgr(gen)))   # 裁 16:9 时右下角水印一并切掉

    # 抹掉车头格栅上的圆形品牌标志（D 型：参考图不得带 logo）。
    # 坐标来自验收/_车头定位.png：放大 2x 图中 (355,450) → 原图 (458,745)。
    # 不用 inpaint（会填成一块黑圆斑），改为从同一格栅右侧复制横条纹纹理 + 羽化覆盖。
    y0, y1 = 725, 767
    x0, x1 = 438, 480
    px0, px1 = x0 + 70, x1 + 70
    patch = a[y0:y1, px0:px1].copy().astype(np.float32)
    alpha = np.zeros((y1 - y0, x1 - x0), np.float32)
    cv2.circle(alpha, (21, 21), 19, 1.0, -1)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 3)[..., None]
    roi = a[y0:y1, x0:x1].astype(np.float32)
    a[y0:y1, x0:x1] = np.clip(roi * (1 - alpha) + patch * alpha, 0, 255).astype(np.uint8)

    save_bgr(a, UP / "image3_garage_anime_v2.jpg", 93)
    save_bgr(a, HERE / "_garage_cel_v2.png", 100)
    print("A 温和赛璐璐化 ->", UP / "image3_garage_anime_v2.jpg", a.shape)

    # 备用：P06a 成片 0.5s，同源日漫风、无人物、深色轿车 + 湿地面反光
    frame = P14 / "验收_v8" / "P06a_t0.5.png"
    b = cv2.resize(crop169(load_bgr(frame)), (1664, 928), interpolation=cv2.INTER_LANCZOS4)
    save_bgr(b, UP / "image3_P06a_anime_frame.jpg", 95)
    save_bgr(b, HERE / "_garage_P06a_frame.png", 100)
    print("B 成片截帧备用 ->", UP / "image3_P06a_anime_frame.jpg", b.shape)

    font = ImageFont.truetype(r"C:/Windows/Fonts/msyh.ttc", 20)
    items = [
        (HERE / "_garage_cel_v2.png", "A. 新生成车库图（温和赛璐璐化，16:9，水印已裁除）"),
        (HERE / "_garage_P06a_frame.png", "B. P06a 成片截帧（100% 同源日漫风、无人物）"),
    ]
    w = 820
    ims = [Image.open(p).convert("RGB") for p, _ in items]
    ims = [im.resize((w, int(im.height * w / im.width))) for im in ims]
    rows = []
    for (_, label), im in zip(items, ims):
        r = Image.new("RGB", (w, 38 + im.height), (18, 18, 22))
        ImageDraw.Draw(r).text((12, 8), label, font=font, fill=(255, 214, 64))
        r.paste(im, (0, 38))
        rows.append(r)
    out = Image.new("RGB", (w, sum(r.height for r in rows)), (18, 18, 22))
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    out.save(HERE / "_场景图_AB对照.png")
    print("对照图 ->", HERE / "_场景图_AB对照.png", out.size)


if __name__ == "__main__":
    main()
