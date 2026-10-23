#!/usr/bin/env python3
"""Check and claim topics through the existing private cloud ledger."""
import argparse
import hashlib
import json
import os
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

BASE = "https://www.yuanfangwyy.xyz/api/drafts/v1"


def tool_id(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("registry_invalid_source_url")
    if parsed.query or parsed.fragment:
        raise ValueError("registry_use_canonical_source_url")
    host = parsed.hostname.lower().removeprefix("www.")
    parts = [part for part in parsed.path.split("/") if part]
    if host == "github.com":
        if len(parts) < 2:
            raise ValueError("registry_repository_required")
        return "github:" + parts[0].lower() + "/" + parts[1].lower().removesuffix(".git")
    path = "/" + "/".join(parts) if parts else ""
    return "web:" + host + path


def topic_key(identity):
    return "topic:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()


def views(entry):
    yield entry
    for old in entry.get("history", []):
        if isinstance(old, dict):
            yield from views(old)


def registry_meta(entry):
    note = entry.get("topic_record", {}).get("editorial_note", "")
    try:
        parsed = json.loads(note)
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def name_match(name, value):
    name = unicodedata.normalize("NFKC", name).casefold().strip()
    value = unicodedata.normalize("NFKC", value).casefold()
    if not name:
        return False
    if re.fullmatch(r"[a-z0-9 ._+-]+", name):
        return re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", value) is not None
    return name in value


def find_matches(entries, identity, names):
    matches = []
    for entry in entries:
        reasons = []
        historical = []
        for index, view in enumerate(views(entry)):
            metadata = registry_meta(view)
            found = []
            if metadata.get("tool_id") == identity:
                found.append("canonical_tool_id")
            for url in view.get("source_urls", []) + view.get("topic_record", {}).get("source_urls", []):
                try:
                    parsed = urllib.parse.urlsplit(url)
                    canonical = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
                    if tool_id(canonical) == identity:
                        found.append("official_source")
                except (ValueError, TypeError):
                    continue
            values = [view.get("title", ""), view.get("task", ""), *metadata.get("aliases", [])]
            if any(name_match(name, value) for name in names for value in values if isinstance(value, str)):
                found.append("name_or_alias")
            if found:
                reasons.extend(found)
                if index:
                    historical.append(view.get("title", ""))
        if reasons:
            matches.append({"article_key": entry["article_key"], "article_id": entry.get("article_id"),
                            "title": entry.get("title"), "task": entry.get("task"), "owner": entry.get("owner"),
                            "revision": entry["revision"], "states": entry.get("states", {}),
                            "match_reasons": sorted(set(reasons)), "historical_titles": list(dict.fromkeys(historical))})
    return matches


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        raise ValueError("registry_redirect_refused")


class Cloud:
    def __init__(self, key):
        self.key = key
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, method, path, body=None):
        headers = {"X-API-Key": self.key, "Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 409:
                raise ValueError("registry_conflict_read_existing_do_not_rekey") from None
            raise ValueError("registry_http_" + str(error.code)) from None
        except (urllib.error.URLError, TimeoutError):
            raise ValueError("registry_connection_unavailable") from None

    def entries(self):
        status = self.request("GET", "/status")
        if (status.get("status") != "ready" or status.get("publishing_enabled") is not False
                or status.get("workflow_storage") != "cloud" or status.get("workflow_enabled") is not True):
            raise ValueError("registry_cloud_not_ready")
        entries, offset, expected_total = [], 0, None
        while True:
            page = self.request("GET", "/workflow?limit=50&offset=" + str(offset))
            if expected_total is None:
                expected_total = page["total"]
            if page["total"] != expected_total:
                raise ValueError("registry_changed_during_pagination")
            entries.extend(page["articles"])
            offset += len(page["articles"])
            if offset >= expected_total:
                break
            if not page["articles"]:
                raise ValueError("registry_incomplete_pagination")
        if len(entries) != expected_total or len({e["article_key"] for e in entries}) != expected_total:
            raise ValueError("registry_incomplete_pagination")
        return entries


def check(cloud, source, names):
    identity = tool_id(source)
    entries = cloud.entries()
    matches = find_matches(entries, identity, names)
    return {"status": "existing_tool_review_required" if matches else "candidate_only",
            "checked_at": datetime.now(timezone.utc).isoformat(), "coverage": "current_cloud_ledger_and_history",
            "total_checked": len(entries), "tool_id": identity, "new_tool_key": topic_key(identity),
            "semantic_review_required": True, "matches": matches, "wechat_called": False}


def claim(cloud, source, names, title, task, owner):
    result = check(cloud, source, names)
    if result["matches"]:
        return result
    key = result["new_tool_key"]
    try:
        cloud.request("GET", "/workflow/" + key)
    except ValueError as error:
        if str(error) != "registry_http_404":
            raise
    else:
        raise ValueError("registry_existing_key_read_before_writing")
    metadata = {"registry_version": 1, "tool_id": result["tool_id"], "aliases": names,
                "related_article_keys": [], "claim_started_at": result["checked_at"], "claim_token": str(uuid4())}
    record = {"title": title, "task": task, "owner": owner, "source_urls": [source],
              "topic_record": {"decision": "write", "editorial_note": json.dumps(metadata, ensure_ascii=False)}}
    saved = cloud.request("PUT", "/workflow/" + key, {"record": record, "expected_revision": 0})
    readback = cloud.request("GET", "/workflow/" + key)
    if (readback.get("owner") != owner or readback.get("revision") != saved.get("revision")
            or registry_meta(readback).get("claim_token") != metadata["claim_token"]):
        raise ValueError("registry_claim_readback_mismatch")
    return {**result, "status": "claimed", "article_key": key, "owner": owner,
            "revision": readback["revision"], "claim_token": metadata["claim_token"], "wechat_called": False}


def main():
    parser = argparse.ArgumentParser(description="Existing cloud ledger only: read check or explicit topic claim; no WeChat calls")
    parser.add_argument("command", choices=["check", "claim"])
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--tool-name", required=True)
    parser.add_argument("--alias", action="append", default=[])
    parser.add_argument("--task", required=True)
    parser.add_argument("--title")
    parser.add_argument("--owner")
    parser.add_argument("--credential-file", type=Path)
    args = parser.parse_args()
    if args.command == "claim" and (not args.owner or not args.title):
        parser.error("claim requires --owner and --title")
    try:
        key = args.credential_file.read_text().strip() if args.credential_file else os.environ.get("WECHAT_DRAFTS_REST_KEY", "")
        if not key:
            raise ValueError("registry_existing_credentials_unavailable")
        cloud = Cloud(key)
        names = list(dict.fromkeys([args.tool_name, *args.alias]))
        result = claim(cloud, args.source_url, names, args.title, args.task, args.owner) if args.command == "claim" else check(cloud, args.source_url, names)
        result["candidate_task"] = args.task
    except (OSError, ValueError, KeyError, TypeError) as error:
        code = str(error)
        result = {"status": "blocked", "error": code if re.fullmatch(r"[a-z_0-9]+", code) else "registry_check_failed", "wechat_called": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"candidate_only", "claimed"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
