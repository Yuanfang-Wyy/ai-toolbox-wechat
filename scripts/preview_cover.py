#!/usr/bin/env python3
import argparse
import base64
import hashlib
import html
import json
import math
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def image_size(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return width, height, "image/png"
    if data.startswith(b"\xff\xd8"):
        offset = 2
        while offset + 4 <= len(data):
            if data[offset] != 0xFF:
                break
            while offset < len(data) and data[offset] == 0xFF:
                offset += 1
            if offset >= len(data):
                break
            marker = data[offset]
            offset += 1
            length = int.from_bytes(data[offset:offset + 2], "big")
            if length < 2 or offset + length > len(data):
                break
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF) and length >= 7:
                height, width = struct.unpack(">HH", data[offset + 3:offset + 7])
                return width, height, "image/jpeg"
            offset += length
    try:
        element = ET.fromstring(data)
        if element.tag != "{http://www.w3.org/2000/svg}svg":
            raise ValueError("不是 SVG 根元素")
        dimensions = [element.get(name, "") for name in ("width", "height")]
        if all(re.fullmatch(r"\d+(?:\.\d+)?(?:px)?", value) for value in dimensions):
            width, height = (float(value.removesuffix("px")) for value in dimensions)
        else:
            _, _, width, height = map(float, element.get("viewBox", "").replace(",", " ").split())
        return width, height, "image/svg+xml"
    except (ET.ParseError, ValueError):
        raise ValueError("无法读取图片尺寸；请提供 PNG、JPEG 或带尺寸/viewBox 的 SVG") from None


def main():
    parser = argparse.ArgumentParser(description="离线封面裁切预览；不修改原图、不做OCR、不上传")
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = args.image.read_bytes()
        width, height, mime = image_size(data)
        if not (math.isfinite(width) and math.isfinite(height)) or width <= 0 or height <= 0:
            raise ValueError("图片尺寸必须为有限正数")
        side = min(width, height)
        left, top = (width - side) / 2, (height - side) / 2
        uri = "data:" + mime + ";base64," + base64.b64encode(data).decode()
        name = html.escape(args.image.name)
        square_style = f"width:{width / side * 100}%;height:{height / side * 100}%;left:50%;top:50%;transform:translate(-50%,-50%);position:absolute;max-width:none"
        overlay_style = f"left:{left / width * 100}%;top:{top / height * 100}%;width:{side / width * 100}%;height:{side / height * 100}%"
        page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'">
<title>封面核查：{name}</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#faf8f2;color:#242424;font:16px/1.8 system-ui}}
main{{max-width:1000px;margin:32px auto;padding:0 24px 40px}}h1{{font-size:28px}}h2{{font-size:20px;color:#df531b}}
section{{background:white;border:1px solid #e5dfd4;border-radius:10px;padding:20px;margin:20px 0}}
.frame{{position:relative;overflow:hidden}}.full{{aspect-ratio:{width}/{height};width:100%}}
.full img{{width:100%;height:100%;display:block}}.zone{{position:absolute;border:3px solid #ff642a;box-shadow:0 0 0 1000px #24242466}}
.square{{aspect-ratio:1;max-width:100%;width:320px}}.thumb{{width:235px;max-width:100%;aspect-ratio:{width}/{height}}}
.thumb img{{width:100%;height:100%;display:block}}.small{{width:96px}}.row{{display:flex;gap:24px;flex-wrap:wrap;align-items:start}}
.note{{color:#666}}li{{margin:8px 0}}</style></head><body><main>
<h1>封面核查 · {name}</h1><p>尺寸 {width:g} × {height:g}；比例 {width / height:.3f}。
中心方形：({left:g}, {top:g}) — ({left + side:g}, {top + side:g})。</p>
<p class="note">这是本地检查用裁切，不代表微信每个入口的实际裁切。未进行文字识别、上传或手机验收。</p>
<section><h2>完整横图</h2><div class="frame full"><img src="{uri}" alt="完整封面"></div></section>
<section><h2>中心安全区</h2><div class="frame full"><img src="{uri}" alt="封面安全区"><div class="zone" style="{overlay_style}"></div></div></section>
<section><h2>方形与缩略图</h2><div class="row">
<div><p>中心 1:1（320px）</p><div class="frame square"><img src="{uri}" alt="中心方形" style="{square_style}"></div></div>
<div><p>横图缩略图（235px）</p><div class="frame thumb"><img src="{uri}" alt="横图缩略图"></div>
<p>方形缩略图（96px）</p><div class="frame square small"><img src="{uri}" alt="方形缩略图" style="{square_style}"></div></div>
</div></section><section><h2>人工核查</h2><ul><li>核心任务词和主体是否完整？</li><li>缩略图的关键字是否能读清？</li>
<li>有无错字、虚假界面或未经验证的效果宣称？</li><li>本地检查完成后，微信手机显示是否另行核查？</li></ul></section>
</main></body></html>"""
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(page)
        ratio_ok = abs(width / height - 2.35) <= 0.02
        print(json.dumps({"ok": True, "width": width, "height": height, "ratio": width / height,
            "recommended_ratio_met": ratio_ok, "square_crop": [left, top, left + side, top + side],
            "preview": str(args.output.resolve()), "source_sha256": hashlib.sha256(data).hexdigest(),
            "text_verified": False, "wechat_verified": False, "uploaded": False,
            "warnings": [] if ratio_ok else ["比例不是约2.35:1；预览已生成，需决定是否调整画幅"]}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as error:
        message = "输出文件已存在，请使用新的预览文件名" if isinstance(error, FileExistsError) else str(error)
        print(json.dumps({"ok": False, "error": message, "uploaded": False}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
