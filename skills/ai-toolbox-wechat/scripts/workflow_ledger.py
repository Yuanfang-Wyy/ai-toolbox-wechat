#!/usr/bin/env python3
"""Private workflow ledger; local records never submit or publish a draft."""
import argparse
import copy
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


VERSION = "1.4.0"
STATES = {"editorial": "pending", "media": "pending", "delivery": "not_submitted", "remote_verification": "pending", "mobile_preview": "pending", "owner_review": "pending"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def packet_content(path):
    packet = read_json(path)
    markdown = (path.parent / packet["markdown_path"]).read_text(encoding="utf-8")
    if packet.get("destination") != "wechat_draft" or packet.get("publish") is not False or packet.get("requires_owner_review") is not True:
        raise ValueError("packet 只允许草稿及本人审核")
    if not packet.get("article_key") or not packet.get("title"):
        raise ValueError("packet 缺少 article_key/title")
    return packet, markdown, digest(packet["title"] + "\n" + markdown)


def find_entry(ledger, packet):
    matches = [row for row in ledger["articles"] if row["article_key"] == packet["article_key"] or packet["article_key"] in row.get("aliases", []) or packet.get("article_id") and row.get("article_id") == packet["article_id"]]
    if len(matches) > 1:
        raise ValueError("article_key 与 article_id 指向不同条目；先人工对账")
    return matches[0] if matches else None


def reconcile(ledger, packet, content_hash, receipt_record=False):
    entry = find_entry(ledger, packet)
    if entry and entry.get("article_id") and packet.get("action") == "create" and not receipt_record:
        raise ValueError("已有关联 article_id；保留旧稿并核对 update，禁止重复 create")
    if entry and packet.get("article_id") and entry.get("article_id") not in (None, packet["article_id"]):
        raise ValueError("article_id 与台账冲突")
    if entry is None:
        entry = {"article_key": packet["article_key"], "aliases": [], "states": dict(STATES), "history": []}
        ledger["articles"].append(entry)
    elif entry["article_key"] != packet["article_key"]:
        if not entry["article_key"].startswith("legacy:"):
            raise ValueError("不能把已有文章身份改成另一 article_key")
        entry.setdefault("aliases", []).append(entry["article_key"])
        entry["article_key"] = packet["article_key"]
    if entry.get("content_sha256") and entry["content_sha256"] != content_hash:
        entry.setdefault("history", []).append(copy.deepcopy({k: v for k, v in entry.items() if k != "history"}))
        entry["states"] = dict(STATES)
        for field in ("request_id", "payload_sha256", "receipt", "review"):
            entry.pop(field, None)
    entry.update(title=packet["title"], content_sha256=content_hash, task=packet.get("topic_brief", {}).get("task", packet.get("reader_result", "")), source_urls=packet.get("source_urls", []), owner=packet.get("agent_id"), delivery_key=packet.get("delivery_key"))
    if packet.get("article_id"):
        entry["article_id"] = packet["article_id"]
    return entry


def record_review(entry, review):
    if review.get("content_sha256") != entry["content_sha256"]:
        raise ValueError("审稿证据不属于当前正文版本")
    if not review.get("evidence"):
        raise ValueError("审稿报告缺少实际检查证据")
    entry["review"] = {k: review[k] for k in ("content_sha256", "evidence", "editorial_review_passed", "media_status") if k in review}
    if "editorial_review_passed" in review:
        if not isinstance(review["editorial_review_passed"], bool):
            raise ValueError("editorial_review_passed 必须为布尔值")
        entry["states"]["editorial"] = "reviewed" if review["editorial_review_passed"] else "blocked"
    if "media_status" in review:
        if review["media_status"] not in ("pending", "verified", "blocked", "not_required"):
            raise ValueError("未知媒体状态")
        entry["states"]["media"] = review["media_status"]


def record_receipt(entry, packet, markdown, request, receipt):
    args = request.get("arguments", {})
    if request.get("article_key") != packet["article_key"] or request.get("tool") != packet["action"] + "_draft":
        raise ValueError("请求与 article_key/action 不匹配")
    if any(args.get(k) != value for k, value in (("title", packet["title"]), ("markdown", markdown), ("source_urls", packet.get("source_urls", [])))):
        raise ValueError("请求正文与当前 packet 不一致")
    request_id = args.get("request_id")
    uuid.UUID(request_id)
    prior_ids = {row["request_id"] for row in entry.get("history", []) + [entry] if row.get("request_id")}
    if packet["action"] == "create" and entry.get("article_id") and prior_ids and request_id not in prior_ids:
        raise ValueError("已有创建回执，不接受另一 create 请求；后续修订应核对 update")
    payload_hash = digest(json.dumps(args, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if request.get("payload_sha256") != payload_hash:
        raise ValueError("请求指纹不匹配")
    for prior in entry.get("history", []) + [entry]:
        if prior.get("request_id") == request_id and prior.get("payload_sha256") != payload_hash:
            raise ValueError("跨版本复用了不同内容的 request_id")
    if packet["action"] == "update" and (args.get("article_id") != packet.get("article_id") or not args.get("expected_snapshot") or args["expected_snapshot"] != packet.get("expected_snapshot")):
        raise ValueError("更新请求缺少对应 article_id/expected_snapshot")
    if receipt.get("request_id") != request_id:
        raise ValueError("回执必须由调用记录绑定到同一个 request_id")
    if receipt.get("published") is not False:
        raise ValueError("不是明确未发表的草稿回执")
    if receipt.get("title", packet["title"]) != packet["title"]:
        raise ValueError("回执标题与提交版本不匹配")
    article_id = receipt.get("article_id")
    if not article_id or entry.get("article_id") not in (None, article_id):
        raise ValueError("回执 article_id 缺失或冲突")
    if entry.get("request_id") == request_id and entry.get("payload_sha256") != payload_hash:
        raise ValueError("相同请求号不得对应不同内容")
    entry.update(article_id=article_id, request_id=request_id, payload_sha256=payload_hash)
    status = receipt.get("status")
    success = status in ("created", "updated", "existing")
    if success and receipt.get("error"):
        raise ValueError("成功状态与错误字段矛盾，先核查原始回执")
    entry["receipt"] = {k: receipt[k] for k in ("status", "article_id", "request_id", "published", "verified", "title", "image_count", "expected_snapshot", "error") if k in receipt}
    error = str(receipt.get("error", ""))
    if success:
        entry["states"]["delivery"] = status
        image_count = len(re.findall(r'!\[[^\]]*\]\((https://[^\s)]+)', markdown))
        count = receipt.get("image_count")
        if count is not None and (type(count) is not int or count < image_count):
            raise ValueError("回执图片数量与提交内容矛盾")
        if receipt.get("verified") is True:
            entry["states"]["remote_verification"] = "verified"
        else:
            entry["states"]["remote_verification"] = "pending"
    else:
        entry["states"]["delivery"] = "quota_blocked" if "45009" in error else "conflict" if "changed" in error else "uncertain"
        entry["states"]["remote_verification"] = "pending"
    return {"request_id": request_id, "states": entry["states"], "evidence_scope": "服务端回执；不代表手机预览或本人审批"}


def main():
    parser = argparse.ArgumentParser(description="私有单写者台账，不联网、不调用模型或微信；所有命令显式指定同一台账")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("import-index", "record-topic", "reconcile", "record-review", "record-receipt", "list"):
        command = commands.add_parser(name)
        command.add_argument("--ledger", type=Path, required=True)
        if name == "import-index":
            command.add_argument("--input", type=Path, required=True)
        elif name != "list":
            command.add_argument("--packet", type=Path, required=True)
        if name == "record-review":
            command.add_argument("--review", type=Path, required=True)
        if name == "record-topic":
            command.add_argument("--decision", choices=("write", "research", "defer", "reject"), required=True)
        if name == "record-receipt":
            command.add_argument("--request", type=Path, required=True)
            command.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        previous = args.ledger.read_bytes() if args.ledger.exists() else None
        if previous is None and args.command != "import-index":
            raise ValueError("先指定总控创建并导入索引的同一私有台账，不自行创建孤立台账")
        ledger = json.loads(previous) if previous is not None else {"ledger_version": 1, "bundle_version": VERSION, "articles": []}
        if ledger.get("ledger_version") != 1 or not isinstance(ledger.get("articles"), list):
            raise ValueError("未知台账格式")
        if args.command == "list":
            print(json.dumps({"ok": True, "ledger": ledger}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "import-index":
            index = read_json(args.input)
            for item in index["drafts"]:
                existing = next((row for row in ledger["articles"] if row.get("article_id") == item["article_id"]), None)
                if existing is None:
                    existing = {"article_key": "legacy:" + item["article_id"], "article_id": item["article_id"], "title": item["title"], "task": "待核对原文任务", "aliases": [], "states": dict(STATES), "history": []}
                    ledger["articles"].append(existing)
                existing["index_observation"] = {k: item[k] for k in ("status", "has_wechat_draft", "updated") if k in item}
            ledger["index_coverage"] = {"count": len(index["drafts"]), "scope": "partial_project_index", "note": index.get("note", "项目索引不等于微信完整列表")}
            result = {"imported": len(index["drafts"]), "total": len(ledger["articles"]), "coverage": "partial_project_index"}
        elif args.command == "record-topic":
            packet = read_json(args.packet)
            if not packet.get("article_key") or not packet.get("title") or not packet.get("topic_brief", {}).get("task"):
                raise ValueError("选题记录须有 article_key、title 和 topic_brief.task")
            entry = find_entry(ledger, packet)
            if entry is None:
                entry = {"article_key": packet["article_key"], "aliases": [], "states": dict(STATES), "history": [], "title": packet["title"], "task": packet["topic_brief"]["task"]}
                ledger["articles"].append(entry)
            entry["topic_record"] = {"decision": args.decision, "title": packet["title"], "brief": packet["topic_brief"], "source_urls": packet.get("source_urls", []), "editorial_note": packet.get("editorial_note", ""), "owner": packet.get("agent_id")}
            result = {"article_key": entry["article_key"], "decision": args.decision, "states": entry["states"]}
        else:
            packet, markdown, content_hash = packet_content(args.packet)
            entry = reconcile(ledger, packet, content_hash, receipt_record=args.command == "record-receipt")
            result = {"article_key": entry["article_key"], "article_id": entry.get("article_id"), "content_sha256": content_hash, "states": entry["states"]}
            if args.command == "record-review":
                record_review(entry, read_json(args.review))
            elif args.command == "record-receipt":
                result.update(record_receipt(entry, packet, markdown, read_json(args.request), read_json(args.receipt)))
                result["article_id"] = entry["article_id"]
        ledger["bundle_version"] = VERSION
        ledger["updated_at"] = datetime.now(timezone.utc).isoformat()
        args.ledger.parent.mkdir(parents=True, exist_ok=True)
        if previous is not None:
            if args.ledger.read_bytes() != previous:
                raise ValueError("台账已被其他写者修改；重新读取，不覆盖")
            backup = args.ledger.parent / "revisions" / (args.ledger.stem + "-" + uuid.uuid4().hex + ".json")
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(previous)
        temp = args.ledger.with_name(args.ledger.name + "." + uuid.uuid4().hex + ".pending")
        with temp.open("x", encoding="utf-8") as stream:
            json.dump(ledger, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp, args.ledger)
        print(json.dumps({"ok": True, "ledger_path": str(args.ledger), **result}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
