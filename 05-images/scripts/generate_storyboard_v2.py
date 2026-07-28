#!/usr/bin/env python3
"""
《红绳》第1集 — 故事板线稿生成脚本
基于Step 4的视频提示词，生成六宫格/九宫格线稿（校对功能）

使用 65535.space gpt-image-2 API
"""

import asyncio
import aiohttp
import json
import os
import sys
import base64
from pathlib import Path

API_URL = "https://img-cn.65535.space/v1/images/generations"
API_KEY = "sk-98e174acc8623acf23364e301d9011e2972dfe5842365a45cc52bd780d0a51fb"
OUTPUT_DIR = Path("D:/HermesWorkspace/ai小说/红绳/05-images/storyboard")
MODEL = "gpt-image-2"

# ── 10个片段的故事板提示词 ──────────────────────────

STORYBOARDS = [
    {
        "id": "片段01",
        "file": "@图片1_进教室初见.png",
        "prompt": (
            "Manga storyboard, 2x3 grid, 16:9 aspect ratio, black and white rough pencil sketch style. "
            "Left to right, top to bottom:\n"
            "1. Wide shot: A teenage boy (Lin Ming) with tanned skin and short black hair enters a classroom through the back door, head down. "
            "All classmates turn to look at him.\n"
            "2. Medium shot: He sits at the last window seat, reaches into the desk and pulls out an old math textbook.\n"
            "3. Close-up: His hands open the textbook cover, revealing the name 'Lin Xiao' written in neat handwriting on the flyleaf.\n"
            "4. Medium over-shoulder: A teacher looks toward a girl with a high ponytail (Lin Xiao), she turns back to look at Lin Ming.\n"
            "5. Close-up: Lin Xiao's calm face as she pushes the textbook toward him on the desk.\n"
            "6. Extreme close-up: Two pairs of fingertips lightly touching on the edge of the textbook. "
            "Only red color allowed for: action arrows showing movement direction between panels 4→5. "
            "Only blue color allowed for: camera angle marks showing over-shoulder composition. "
            "No speech bubbles, no large text blocks, no watermark. Standard storyboard annotation style."
        )
    },
    {
        "id": "片段02",
        "file": "@图片2_答数学题.png",
        "prompt": (
            "Manga storyboard, 2x3 grid, 16:9 aspect ratio, black and white rough pencil sketch style. "
            "Left to right, top to bottom:\n"
            "1. Medium side view: A male teacher (Mr. Chen) speaks rapidly at the front of the classroom, scanning the students.\n"
            "2. Close-up frontal: No students raise their hands. The teacher's gaze lands on Lin Ming.\n"
            "3. Medium frontal: Lin Ming stands up from his seat and walks toward the blackboard.\n"
            "4. Close-up side: Lin Ming picks up chalk and writes math steps quickly on the board. "
            "5. Close-up frontal: The teacher raises an eyebrow and nods approvingly.\n"
            "6. Medium over-shoulder: Lin Ming walks back to his seat as the teacher says something. "
            "Only red color allowed for: gesture arrows showing the teacher's pointing motion. "
            "Only green color allowed for: framing marks. No speech bubbles, no watermark."
        )
    },
    {
        "id": "片段03",
        "file": "@图片3_借笔对话.png",
        "prompt": (
            "Manga storyboard, 2x3 grid, 16:9 aspect ratio, black and white rough pencil sketch style. "
            "Left to right, top to bottom:\n"
            "1. Medium over-shoulder: Lin Ming sits back down, Lin Xiao turns her head sideways to speak to him.\n"
            "2. Close-up reverse shot: Lin Ming looks away, responding briefly.\n"
            "3. Close-up frontal: Lin Xiao's calm gaze, her ponytail slightly swaying.\n"
            "4. Medium side: Lin Ming opens his pencil case looking frustrated, finding only a broken pen.\n"
            "5. Extreme close-up: A slender hand places a black pen and a cartoon-cat eraser on the corner of the desk.\n"
            "6. Close-up: Lin Ming looks up at the pen and eraser on his desk. "
            "Only purple color allowed for: sound marks indicating the small sound of the pen hitting the desk. "
            "No speech bubbles, no watermark. Minimal annotation style."
        )
    },
    {
        "id": "片段04",
        "file": "@图片4_自我介绍.png",
        "prompt": (
            "Manga storyboard, 2x3 grid, 16:9 aspect ratio, black and white rough pencil sketch style. "
            "Left to right, top to bottom:\n"
            "1. Close-up over-shoulder: Lin Ming looks up at the pen and eraser on the desk, speaking.\n"
            "2. Close-up frontal: Lin Xiao turns her face sideways, her ponytail swinging, expression serious.\n"
            "3. Extreme close-up: The cartoon-cat eraser on the desk, edges worn smooth from use.\n"
            "4. Extreme close-up: Lin Ming's fingertip gently touches the eraser.\n"
            "5. Medium: Classroom background softly blurred, the two at their desks.\n"
            "6. Close-up: Lin Ming's thoughtful expression as he looks down at the eraser. "
            "Only red color allowed for: a small arrow showing the direction of Lin Xiao's turn (panel 1→2). "
            "No speech bubbles, no large text, no watermark."
        )
    },
    {
        "id": "片段05",
        "file": "@图片5_下雨公告栏.png",
        "prompt": (
            "Manga storyboard, 2x3 grid, 16:9 aspect ratio, black and white rough pencil sketch style. "
            "Left to right, top to bottom:\n"
            "1. Wide establishing shot: School entrance in heavy rain, students leaving with umbrellas.\n"
            "2. Medium frontal: Lin Ming stands under the eaves of the school building without an umbrella, watching the crowd.\n"
            "3. Close-up low angle: A red notice board with text '108 days until college entrance exam', rain droplets on it.\n"
            "4. Close-up frontal: Lin Ming stares at the notice board, his expression distant.\n"
            "5. Medium side: A black umbrella extends from the right side into the frame, appearing beside Lin Ming.\n"
            "6. Close-up: Raindrops sliding along the edge of the umbrella. "
            "Only blue color allowed for: camera arrows showing the low-angle shot in panel 3. "
            "Only orange color allowed for: light direction marks for the rain. No speech bubbles, no watermark."
        )
    },
    {
        "id": "片段06",
        "file": "@图片6_递伞跑雨.png",
        "prompt": (
            "Manga storyboard, 2x3 grid, 16:9 aspect ratio, black and white rough pencil sketch style. "
            "Left to right, top to bottom:\n"
            "1. Medium frontal: Lin Ming turns, startled. Lin Xiao stands holding the umbrella, calm expression.\n"
            "2. Close-up high angle: Lin Xiao presses the umbrella handle into Lin Ming's hand, raindrops falling.\n"
            "3. Close-up reverse shot: Lin Ming holding the umbrella, looking concerned.\n"
            "4. Medium long shot side: Lin Xiao puts her backpack over her head and turns to run into the rain.\n"
            "5. Medium frontal: Lin Xiao runs into the gray rain curtain, her ponytail bouncing, red hair tie flashing.\n"
            "6. Close-up: Her figure gradually blurs in the rain curtain. "
            "Only red color allowed for: motion arrows showing Lin Xiao's running trajectory (panel 4→5). "
            "Only purple color allowed for: the flash of the red hair tie in panel 5. No speech bubbles, no watermark."
        )
    },
    {
        "id": "片段07",
        "file": "@图片7_伞柄红绳.png",
        "prompt": (
            "Manga storyboard, 2x3 grid, 16:9 aspect ratio, black and white rough pencil sketch style. "
            "Left to right, top to bottom:\n"
            "1. Extreme close-up: Lin Ming's hand grips the umbrella handle, index finger touching a thin string.\n"
            "2. Extreme close-up slow push: A thin red string wrapped tightly around the black umbrella handle, a tiny wooden bead beside the knot.\n"
            "3. Medium side: Lin Ming enters his room holding the umbrella.\n"
            "4. Close-up high angle: Lin Ming sits at his desk under a desk lamp, opens and closes the umbrella.\n"
            "5. Close-up: The umbrella's metal ribs make a soft sound as they open.\n"
            "6. Medium: The warm desk lamp illuminates the desk while rain continues outside the window. "
            "Only blue color allowed for: camera arrow showing the slow push on panel 2. "
            "Only purple color allowed for: sound mark on panel 5. No speech bubbles, no watermark."
        )
    },
    {
        "id": "片段08",
        "file": "@图片8_草莓糖抽屉.png",
        "prompt": (
            "Manga storyboard, 2x3 grid, 16:9 aspect ratio, black and white rough pencil sketch style. "
            "Left to right, top to bottom:\n"
            "1. Extreme close-up slow push: Lin Ming's hand strokes the red string on the umbrella, the knot is tight, the wooden bead is polished shiny.\n"
            "2. Extreme close-up: His fingers pick up a pink strawberry candy, the wrapper slightly translucent under the light.\n"
            "3. Close-up frontal: Lin Ming stares at the candy, his expression thoughtful.\n"
            "4. Extreme close-up: He opens a drawer and reaches in.\n"
            "5. Close-up: His hand places the strawberry candy at the deepest corner of the drawer.\n"
            "6. Close-up: The drawer slides shut with a soft sound. "
            "Only green color allowed for: framing marks on the close-up shots. "
            "Only orange color allowed for: light direction marks showing the desk lamp. No speech bubbles, no watermark."
        )
    },
    {
        "id": "片段09",
        "file": "@图片9_日记绕绳.png",
        "prompt": (
            "Manga storyboard, 3x3 grid, 16:9 aspect ratio, black and white rough pencil sketch style. "
            "Left to right, top to bottom:\n"
            "1. Close-up high angle: Lin Ming opens his diary and picks up a pen.\n"
            "2. Extreme close-up: The pen tip moves on white paper, writing characters about today.\n"
            "3. Extreme close-up: The pen pauses, then adds one more line.\n"
            "4. Close-up frontal: Lin Ming closes the diary.\n"
            "5. Close-up: His finger unconsciously draws circles on the cover.\n"
            "6. Extreme close-up: The circles on the cover increasingly resemble the shape of a knot on an umbrella handle.\n"
            "7. Close-up: His hand reaches for the umbrella on the desk.\n"
            "8. Extreme close-up: His finger winds around the red string on the umbrella handle, one rotation, then releases.\n"
            "9. Close-up: The red string slowly settles back into place. "
            "Only red color allowed for: motion arrows showing the circular drawing motion (panel 5→6). "
            "Only purple color allowed for: sound marks for the pen scratching. No speech bubbles, no watermark."
        )
    },
    {
        "id": "片段10",
        "file": "@图片10_关灯红绳微光.png",
        "prompt": (
            "Manga storyboard, 2x3 grid, 16:9 aspect ratio, black and white rough pencil sketch style. "
            "Left to right, top to bottom:\n"
            "1. Close-up side: Lin Ming's hand reaches for the desk lamp switch.\n"
            "2. Close-up: His finger presses the switch, the light goes out.\n"
            "3. Close-up frontal: The room falls into darkness, Lin Ming's face faintly lit by streetlight from the window.\n"
            "4. Extreme wide: Dark room, only a sliver of light from the window curtain crack.\n"
            "5. Extreme close-up very slow push: In the darkness, the red string and wooden bead on the umbrella handle faintly reflect the streetlight.\n"
            "6. Extreme close-up: The knot on the red string sits still like a heartbeat in the dark. "
            "Only blue color allowed for: camera arrow showing the slow push on panel 5. "
            "Only orange color allowed for: light source direction marks showing the streetlight. No speech bubbles, no watermark."
        )
    },
]


async def generate_one(session, sb, semaphore):
    """Generate one storyboard image"""
    async with semaphore:
        filepath = OUTPUT_DIR / sb["file"]
        print(f"\n[{sb['id']}] → {sb['file']}")

        payload = {
            "model": MODEL,
            "prompt": sb["prompt"],
            "n": 1,
            "size": "1792x1024",
            "response_format": "b64_json",
        }
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            async with session.post(
                API_URL, json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"  [{sb['id']}] ERROR HTTP {resp.status}: {text[:300]}")
                    return None

                data = await resp.json()

                if "data" in data and len(data["data"]) > 0:
                    b64 = data["data"][0].get("b64_json")
                    if b64:
                        img_bytes = base64.b64decode(b64)
                        filepath.write_bytes(img_bytes)
                        size_kb = len(img_bytes) / 1024
                        print(f"  ✅ 已保存: {sb['file']} ({size_kb:.0f} KB)")
                        return sb["file"]

                # Try URL format
                url = data.get("data", [{}])[0].get("url")
                if url:
                    print(f"  [{sb['id']}] Got URL (downloading): {url[:80]}...")
                    async with session.get(url) as img_resp:
                        if img_resp.status == 200:
                            img_bytes = await img_resp.read()
                            filepath.write_bytes(img_bytes)
                            size_kb = len(img_bytes) / 1024
                            print(f"  ✅ 已保存(URL): {sb['file']} ({size_kb:.0f} KB)")
                            return sb["file"]

                print(f"  [{sb['id']}] 返回格式异常: {json.dumps(data, ensure_ascii=False)[:300]}")
                return None

        except asyncio.TimeoutError:
            print(f"  [{sb['id']}] 超时 (>300s)")
            return None
        except Exception as e:
            print(f"  [{sb['id']}] 异常: {e}")
            return None


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 最大3个并发，避免API限流
    semaphore = asyncio.Semaphore(3)

    print("=" * 60)
    print("《红绳》第1集 — 故事板线稿生成")
    print(f"共 {len(STORYBOARDS)} 个片段")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        tasks = [generate_one(session, sb, semaphore) for sb in STORYBOARDS]
        results = await asyncio.gather(*tasks)

    print("\n" + "=" * 60)
    print("【生成结果汇总】")
    success = [r for r in results if r]
    fail_count = len([r for r in results if r is None])
    print(f"✅ 成功: {len(success)}/{len(STORYBOARDS)}")
    print(f"❌ 失败: {fail_count}/{len(STORYBOARDS)}")

    if success:
        print("\n生成文件清单:")
        for f in sorted(success):
            path = OUTPUT_DIR / f
            size = path.stat().st_size / 1024 if path.exists() else 0
            print(f"  📄 {f} ({size:.0f} KB)")

    return fail_count == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
