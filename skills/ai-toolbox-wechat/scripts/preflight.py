#!/usr/bin/env python3
import argparse
import hashlib
import ipaddress
import json
import re
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import URLError
from urllib.request import Request, urlopen


MAX_IMAGE_BYTES = 1_000_000
WRITING_MODES = ("tested-tutorial", "documented-workflow", "task-comparison", "template-delivery")


def valid_image_url(url):
    try:
        parsed = urlparse(url)
        if parsed.netloc.startswith("["):
            ipaddress.IPv6Address(parsed.hostname)
        return parsed.scheme == "https" and bool(parsed.hostname) and parsed.username is None and parsed.password is None and (parsed.port is None or parsed.port > 0)
    except (TypeError, ValueError):
        return False


def verify_image(url):
    if not valid_image_url(url):
        return {"url": "<invalid URL>", "verified": False, "error": "图片必须为不含登录凭据的有效公开 HTTPS 地址"}
    result = {"url": url, "verified": False}
    try:
        request = Request(url, headers={"User-Agent": "AI-toolbox-media-check/1.1"})
        with urlopen(request, timeout=20) as response:
            if urlparse(response.geturl()).scheme != "https":
                raise ValueError("图片重定向到非 HTTPS 地址")
            mime = response.headers.get_content_type()
            if mime not in ("image/png", "image/jpeg"):
                raise ValueError("图片响应 MIME 不是 PNG/JPEG")
            data = response.read(MAX_IMAGE_BYTES + 1)
        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError("图片超过 1,000,000 字节")
        signature_matches = data.startswith(b"\x89PNG\r\n\x1a\n") if mime == "image/png" else data.startswith(b"\xff\xd8\xff")
        if not signature_matches:
            raise ValueError("图片文件签名与 MIME 不匹配")
        result.update(verified=True, mime=mime, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    except (URLError, OSError, ValueError) as exc:
        result["error"] = str(exc)
    return result


def check(packet_path, content_only=False, verify_media=False):
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    errors, warnings = [], []
    for key in ("article_key", "agent_id", "title", "markdown_path", "reader_result", "delivery_key"):
        if not isinstance(packet.get(key), str) or not packet[key].strip():
            errors.append(f"缺少 {key}")
    if packet.get("destination") != "wechat_draft" or packet.get("publish") is not False or packet.get("requires_owner_review") is not True:
        errors.append("只允许微信草稿，publish=false，requires_owner_review=true")
    if packet.get("article_type") not in ("办公省事", "内容创作", "选工具避坑"):
        errors.append("article_type 不在账号栏目范围")
    if packet.get("evidence_level") not in ("official-docs", "source-inspected", "tested"):
        errors.append("缺少有效 evidence_level")
    if packet.get("evidence_level") == "tested":
        evidence = packet.get("test_evidence", [])
        if isinstance(evidence, str):
            evidence = [evidence]
        if not isinstance(evidence, list) or not evidence:
            errors.append("tested 必须提供实测证据文件路径")
        else:
            for path in evidence:
                if not isinstance(path, str) or not path.strip():
                    errors.append("实测证据必须是文件路径")
                    continue
                evidence_path = packet_path.parent / path
                if not evidence_path.is_file() or evidence_path.stat().st_size == 0:
                    errors.append("实测证据文件不存在或为空：" + path)
    title = packet.get("title", "")
    if not 1 <= len(title) <= 32 or "\n" in title:
        errors.append("标题必须为 1—32 字且不换行")
    sources = packet.get("source_urls", [])
    if not isinstance(sources, list) or not sources or len(sources) > 20 or any(not isinstance(s, str) or not s.startswith("https://") or not urlparse(s).hostname or urlparse(s).username or len(s) > 2000 for s in sources):
        errors.append("source_urls 必须含 1—20 条 HTTPS 来源")
    markdown_path = packet_path.parent / packet.get("markdown_path", "")
    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.is_file() else ""
    if not 80 <= len(markdown) <= 14000:
        errors.append("正文文件须存在，长度 80—14000 字")
    if any(s in markdown for s in ("<!-- radar:generated:", "# 我的思考", "# 我的使用计划")) or markdown.startswith("---\n"):
        errors.append("正文含知识库内部标记或 frontmatter")
    if re.search(r"placeholder|待补图|\{embed:|<\s*(?:script|iframe|form|input)\b", markdown, re.I):
        errors.append("正文含占位内容或主动 HTML")
    if packet.get("packet_version", 1) == 2:
        if packet.get("writing_mode") not in WRITING_MODES:
            errors.append("新稿缺少有效 writing_mode")
        if packet.get("writing_mode") == "tested-tutorial" and packet.get("evidence_level") != "tested":
            errors.append("实测教程必须有 tested 证据，资料流程不能冒充实测")
        brief = packet.get("topic_brief", {})
        for key in ("audience", "task", "current_way", "improvement", "setup_cost", "evidence"):
            if not isinstance(brief, dict) or not isinstance(brief.get(key), str) or not brief[key].strip():
                errors.append("选题记录缺少 " + key)
        deliverables = packet.get("deliverables", [])
        if not isinstance(deliverables, list) or not deliverables:
            errors.append("新稿必须指向实际流程、提示词、模板或附件")
        else:
            for item in deliverables:
                if not isinstance(item, dict) or item.get("kind") not in ("prompt", "workflow", "template", "file"):
                    errors.append("成果 kind 只允许 prompt/workflow/template/file")
                    continue
                if not isinstance(item.get("acceptance"), str) or not item["acceptance"].strip():
                    errors.append("成果缺少读者验收方法")
                if item["kind"] == "file":
                    path = item.get("path")
                    if not isinstance(path, str) or not path.strip():
                        errors.append("文件成果缺少 path")
                    else:
                        artifact = packet_path.parent / path
                        if not artifact.is_file() or artifact.stat().st_size == 0:
                            errors.append("承诺的附件不存在或为空：" + path)
                else:
                    text = item.get("text")
                    if not isinstance(text, str) or not text.strip() or text.strip() not in markdown:
                        errors.append("承诺的完整成果文字未在正文中找到")
        warnings.append("成果匹配和证据文件存在不代表流程跑通或附件可用，仍需按验收方法检查")
    else:
        warnings.append("旧版交接包兼容检查；新写文章使用 packet_version=2 并记录实际成果")
    if not re.search(r"^## .*官方资料", markdown, re.M):
        errors.append("缺少文末官方资料区")
    # Exclude fenced prompts/code: URLs inside copyable examples are not source clutter.
    prose = re.sub(r"(?ms)^```[^\n]*\n.*?^```[^\n]*$", "", markdown)
    parts = re.split(r"^## .*官方资料[^\n]*\n", prose, flags=re.M, maxsplit=1)
    before_sources = parts[0]
    images = re.findall(r'!\[[^\]]*\]\((https://[^\s)]+)(?:\s+"[^"\n]*")?\)', markdown)
    raw_images = re.findall(r'!\[[^\]]*\]\(([^)\n]+)\)', markdown)
    if len(raw_images) != len(images):
        (warnings if content_only else errors).append("存在本地、非HTTPS或无法解析的图片，不能直接提交当前连接")
    local_images = [source for source in raw_images if not urlparse(source).scheme]
    if content_only:
        for source in local_images:
            image_path = packet_path.parent / source
            if not image_path.is_file() or image_path.stat().st_size == 0:
                errors.append("正文引用的本地图片不存在或为空：" + source)
                continue
            with image_path.open("rb") as stream:
                signature = stream.read(8)
            if not signature.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")):
                errors.append("正文引用的本地图片签名不是 PNG/JPEG：" + source)
            if image_path.stat().st_size > MAX_IMAGE_BYTES:
                warnings.append("本地图片超过连接单图上限，公开上传前需准备符合限制的副本：" + source)
    if not raw_images:
        warnings.append("正文零配图：检查成果、入口与验收是否需要图；短清单可无图，在 visual_reason 说明取舍，不按数量凑图")
    prose_without_images = re.sub(r'!\[[^\]]*\]\([^\n]*?\)', "", before_sources)
    if re.search(r"https?://", prose_without_images):
        warnings.append("正文资料网址建议集中到文末，保留短编号出处")
    if len(raw_images) > 15:
        errors.append("正文图片超过 15 张")
    ledger = packet.get("image_ledger", [])
    if not isinstance(ledger, list):
        errors.append("image_ledger 必须为列表")
        ledger = []
    by_url = {row.get("url"): row for row in ledger if isinstance(row, dict)}
    media_results = []
    for url in images:
        row = by_url.get(url)
        if not valid_image_url(url):
            errors.append("图片必须为不含登录凭据的有效公开 HTTPS 地址")
            continue
        if not row or not row.get("source_url") or not row.get("caption") or not row.get("rights_note"):
            errors.append("图片缺少来源、说明或授权备注：" + url)
        elif row.get("origin") not in ("official", "user-capture", "self-created", "licensed"):
            errors.append("图片 origin 须说明真实来源：" + url)
        if row and row.get("mime") and row["mime"] not in ("image/png", "image/jpeg"):
            (warnings if content_only else errors).append("已知图片格式不是 PNG/JPEG：" + url)
        if row and isinstance(row.get("bytes"), int) and row["bytes"] > MAX_IMAGE_BYTES:
            (warnings if content_only else errors).append("已知图片超过 1,000,000 字节：" + url)
    if verify_media:
        for url in dict.fromkeys(images):
            result = verify_image(url)
            media_results.append(result)
            if not result["verified"]:
                errors.append("图片验证失败：" + result["url"] + "；" + result["error"])
    elif images and not verify_media:
        warnings.append("图片尚未读取实际响应；写入前用 --verify-media 核验 MIME、签名与大小")
    headings = re.findall(r"^## .+", markdown, re.M)
    if not re.search(r"费用|收费|免费", markdown) or not re.search(r"限制|门槛|不适合|数据|上传|适用边界", markdown):
        warnings.append("补查费用、门槛、限制和数据去向")
    action = packet.get("action")
    if action not in ("create", "update"):
        errors.append("action 只允许 create/update")
    if action == "update" and not content_only and (not packet.get("article_id") or not packet.get("expected_snapshot")):
        errors.append("更新缺少 article_id 或最新 expected_snapshot")
    if content_only:
        warnings.append("仅内容检查，不代表具备微信更新条件")
    media_verified = len(raw_images) == len(images) and (not images or bool(media_results) and all(row["verified"] for row in media_results))
    return packet, markdown, {"ok": not errors, "errors": errors, "warnings": warnings, "image_count": len(raw_images), "uploadable_image_count": len(images), "local_image_count": len(local_images), "heading_count": len(headings), "media_verified": media_verified, "media_results": media_results, "live_verified": False}


def prepare(packet_path, output, verify_media=False):
    packet, markdown, report = check(packet_path, verify_media=verify_media)
    if not report["ok"]:
        return report
    arguments = {k: packet[k] for k in ("title", "source_urls")}
    arguments["markdown"] = markdown
    if packet["action"] == "update":
        arguments.update({k: packet[k] for k in ("article_id", "expected_snapshot")})
    # A delivery identity remains stable even if another Agent accidentally edits the packet.
    arguments["request_id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, "ai-toolbox-wechat:" + packet["delivery_key"]))
    payload_hash = hashlib.sha256(json.dumps(arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    request = {"tool": packet["action"] + "_draft", "arguments": arguments, "article_key": packet["article_key"], "payload_sha256": payload_hash, "destination": "wechat_draft", "requires_owner_review": True}
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("x", encoding="utf-8") as stream:
            json.dump(request, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except FileExistsError:
        prior = json.loads(output.read_text(encoding="utf-8"))
        if prior != request:
            return {"ok": False, "errors": ["已有请求与本次参数不同；先查询原交付结果，不覆盖或换请求号重建"], "warnings": report["warnings"]}
    return {"ok": True, "request_path": str(output), "request_id": arguments["request_id"], "payload_sha256": payload_hash, "warnings": report["warnings"], "media_verified": report["media_verified"], "media_results": report["media_results"], "submitted": False}


def main():
    parser = argparse.ArgumentParser(description="AI顺手工具箱草稿预检；默认离线，--verify-media 只读取公开图片，不提交或发表")
    sub = parser.add_subparsers(dest="command", required=True)
    checker = sub.add_parser("check")
    checker.add_argument("--packet", type=Path, required=True)
    checker.add_argument("--content-only", action="store_true")
    checker.add_argument("--verify-media", action="store_true")
    preparer = sub.add_parser("prepare")
    preparer.add_argument("--packet", type=Path, required=True)
    preparer.add_argument("--output", type=Path, required=True)
    preparer.add_argument("--verify-media", action="store_true")
    args = parser.parse_args()
    if args.command == "check":
        report = check(args.packet, args.content_only, args.verify_media)[2]
    else:
        report = prepare(args.packet, args.output, args.verify_media)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
