#!/usr/bin/env python
"""
六宫格线稿故事板 - 红绳第一章「递伞戏」
使用 65535.space gpt-image-2 API 并行生图
"""
import asyncio
import aiohttp
import json
import os
import sys
from pathlib import Path

API_URL = "https://img-cn.65535.space/v1/images/generations"
API_KEY = "sk-98e174acc8623acf23364e301d9011e2972dfe5842365a45cc52bd780d0a51fb"
OUTPUT_DIR = Path("D:/HermesWorkspace/ai小说/红绳/05-images/storyboard-demo")
MODEL = "gpt-image-2"

# 六宫格定义
SCENES = [
    {
        "id": 1,
        "file": "@图片1_递伞.png",
        "prompt": "Black-and-white manga line art storyboard, anime style. School entrance in the rain, a boy (Lin Ming) stands under the eaves watching the rain. A girl (Lin Xiao) extends a black umbrella toward him, her right hand holding the umbrella handle where a thin red string is tied. High school uniforms. Rainy atmosphere, dramatic composition, sketch-like lines, no color, clean storyboard aesthetic.",
    },
    {
        "id": 2,
        "file": "@图片2_跑入雨幕.png",
        "prompt": "Black-and-white manga line art storyboard, anime style. A girl with a ponytail (Lin Xiao) runs into the rain holding her backpack over her head. Her red hair tie flashes against the gray rain. School building in background. Dynamic running pose, rain streaks, sketch-like monochrome lines, no color, cinematic storyboard framing.",
    },
    {
        "id": 3,
        "file": "@图片3_伞柄红绳.png",
        "prompt": "Black-and-white manga line art storyboard, extreme close-up. A black umbrella handle with a thin red string tightly wrapped around it, tied in an intricate knot. A small wooden bead beside the knot. High contrast, detailed linework, monochrome except the red string should be rendered as dark crosshatching, sketch-like texture, storyboard aesthetic.",
    },
    {
        "id": 4,
        "file": "@图片4_撑伞独行.png",
        "prompt": "Black-and-white manga line art storyboard, anime style. A boy (Lin Ming) walks alone in the rain under a large black umbrella. The umbrella covers his entire figure. Rainy street scene with blurred figures in the background. Melancholic mood, wide shot, sketch-like monochrome lines, no color, cinematic storyboard composition.",
    },
    {
        "id": 5,
        "file": "@图片5_站台遥望.png",
        "prompt": "Black-and-white manga line art storyboard, anime style. A rainy bus stop shelter, a boy (Lin Ming) stands holding the umbrella, not boarding any bus. Across the street at a convenience store entrance, a girl with a ponytail is sheltering from the rain. Misty rain, longing atmosphere, sketch-like monochrome lines, no color, dramatic storyboard lighting.",
    },
    {
        "id": 6,
        "file": "@图片6_灯下红绳.png",
        "prompt": "Black-and-white manga line art storyboard, anime style. Night scene, desk lamp illuminates a boy's hands examining a red string tied to an umbrella handle. A strawberry candy in pink wrapper sits nearby. Warm lamp light rendered as line shading. Intimate close-up, detailed linework, sketch-like monochrome, storyboard aesthetic, emotional atmosphere.",
    },
]

async def generate_one(session, scene, semaphore):
    async with semaphore:
        prompt = scene["prompt"]
        filename = scene["file"]
        filepath = OUTPUT_DIR / filename

        print(f"[图片{scene['id']}/6] 正在生成: {filename}")

        payload = {
            "model": MODEL,
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json",
        }
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            async with session.post(API_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=180)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"  [图片{scene['id']}] ERROR HTTP {resp.status}: {text[:200]}")
                    return None

                data = await resp.json()

                # 解析返回
                if "data" in data and len(data["data"]) > 0:
                    b64_data = data["data"][0].get("b64_json")
                    if b64_data:
                        import base64
                        img_bytes = base64.b64decode(b64_data)
                        filepath.write_bytes(img_bytes)
                        size_kb = len(img_bytes) / 1024
                        print(f"  [图片{scene['id']}] 已保存: {filename} ({size_kb:.0f} KB)")
                        return filename
                print(f"  [图片{scene['id']}] 返回格式异常: {json.dumps(data, ensure_ascii=False)[:200]}")
                return None
        except asyncio.TimeoutError:
            print(f"  [图片{scene['id']}] 超时")
            return None
        except Exception as e:
            print(f"  [图片{scene['id']}] 异常: {e}")
            return None

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(3)  # 最多3个并发

    async with aiohttp.ClientSession() as session:
        tasks = [generate_one(session, scene, semaphore) for scene in SCENES]
        results = await asyncio.gather(*tasks)

    print("\n===== 生成结果 =====")
    success = [r for r in results if r]
    fail = [r for r in results if r is None]
    print(f"成功: {len(success)}/{len(SCENES)}")
    print(f"失败: {len(fail)}/{len(SCENES)}")

    if success:
        print("\n生成文件:")
        for f in sorted(success):
            size = os.path.getsize(OUTPUT_DIR / f) / 1024
            print(f"  {f} ({size:.0f} KB)")

    return len(fail) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
