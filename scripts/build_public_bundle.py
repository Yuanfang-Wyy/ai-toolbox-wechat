#!/usr/bin/env python3
"""Build a public four-skill bundle and generated legacy/Muse entry points."""
import argparse
import hashlib
import json
import re
from pathlib import Path


VERSION = "1.4.0"
NAMES = ("ai-toolbox-wechat", "wechat-topic-research", "wechat-visual", "wechat-draft-delivery")
REFS = ("editorial", "collaboration", "visual", "visual-production", "delivery", "feedback", "provenance", "workflow")
MAIN_FILES = ("SKILL.md", "agents/openai.yaml", "assets/article-packet.json", "assets/cover-layout.svg", "assets/workflow-example.svg") + tuple("references/" + name + ".md" for name in REFS) + tuple("scripts/" + name for name in ("preflight.py", "preview_cover.py", "workflow_ledger.py", "build_public_bundle.py"))


def reader_links(text):
    def convert(match):
        label, target = match.groups()
        for name in NAMES:
            if target.endswith(name + "/SKILL.md"):
                return "[" + label + "](#skill-" + name + ")"
        for name in REFS:
            if target.split("#")[0].endswith(name + ".md"):
                return "[" + label + "](#ref-" + name + ")"
        if "assets/" in target and not target.startswith("https://"):
            target = "https://github.com/Yuanfang-Wyy/ai-toolbox-wechat/blob/main/skills/ai-toolbox-wechat/assets/" + target.split("assets/", 1)[1]
        return "[" + label + "](" + target + ")"
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", convert, text)


def build(source, output, manifest):
    if output.exists() and any(output.iterdir()):
        raise ValueError("输出目录非空；先备份并选择新目录，不覆盖原包")
    contents = {}
    for name in NAMES:
        paths = MAIN_FILES if name == NAMES[0] else ("SKILL.md", "agents/openai.yaml")
        for relative in paths:
            text = (source / name / relative).read_text(encoding="utf-8")
            if relative == "SKILL.md" and 'version: "' + VERSION + '"' not in text:
                raise ValueError("Skill 版本不一致：" + name)
            if relative == "references/visual-production.md":
                text = re.sub(r"cd /Users/[^\n]+/ai-toolbox-wechat\n", "# 在总入口 Skill 根目录运行\n", text)
            contents["skills/" + name + "/" + relative] = text
    for relative in MAIN_FILES:
        text = contents["skills/ai-toolbox-wechat/" + relative]
        if relative == "SKILL.md":
            for name in NAMES[1:]:
                text = text.replace("../" + name + "/", "skills/" + name + "/")
        elif relative.startswith("references/"):
            for name in NAMES[1:]:
                text = text.replace("../../" + name + "/", "../skills/" + name + "/")
        contents[relative] = text
    contents["README.md"] = """# AI顺手工具箱 Skill 套件

版本：**1.4.0**。保留 `$ai-toolbox-wechat` 总入口，按需使用三个专项：

| Skill | 用途 |
|---|---|
| [总入口](skills/ai-toolbox-wechat/SKILL.md) | 写作、审稿、反馈与流程统筹 |
| [选题研究](skills/wechat-topic-research/SKILL.md) | 按读者任务查重、整合官方证据与使用门槛 |
| [视觉制作](skills/wechat-visual/SKILL.md) | 图位、真实素材、示意图、封面与预览检查 |
| [草稿交付](skills/wechat-draft-delivery/SKILL.md) | 固定请求、串行保存、快照与回执核验 |

## Muse 与网页 Agent

公开阅读入口：[MUSE_GUIDE.md](MUSE_GUIDE.md)。按本次任务读取总入口、对应专项和共享规范；本文件由同一源码生成，不单独维护第二套规则。

可复制提示词：

> 阅读本仓库 v1.4.0 的 MUSE_GUIDE.md，使用 AI顺手工具箱总入口处理我的任务，按需调用选题研究、视觉制作和草稿交付规则。先查重，沿用原 article_key；使用总控指定的同一私有台账。没有台账或公众号工具时交付 packet 和本地成果，不自建第二套权威记录，不声称已写微信。只按当前授权存草稿，正式发表由我本人操作。

公开读取不等于实际安装、可执行 Python 或已有连接。Muse 没有同一私有台账时，把交接包交回总控对账；不要求公开台账、正文、回执或凭证。当前服务器仍只提供已有五项草稿能力，不提供新增台账 API，也不因本套件更新而自动部署。

## 安装到支持 Agent Skills 的运行时

从仓库 `skills/` 下复制四个完整目录到运行时 Skill 目录，保持它们为同级目录；专项通过相对路径引用总入口的共享规则和脚本。已有同名版本先比较和备份，使用目标运行时支持的安装流程；不默认覆盖。根目录 `SKILL.md`、references、assets、scripts 是自动生成的旧路径兼容版，旧链接继续有效；新安装优先使用 `skills/` 里的四个目录，避免重复安装总入口。

## 台账与核验

共享口径见 [workflow.md](skills/ai-toolbox-wechat/references/workflow.md)。继续使用现有 packet.json、文章标识和图片台账。私有总台账通过 `workflow_ledger.py` 对账并分别记录内容、媒体、交付、正文核验、手机预览及本人审核。项目索引只作线索，不能推定微信已保存、远端已核验或用户已批准。

本次提交的 `verified=true` 成功回执可以作为服务端远端正文核验证据，不要求 Agent 再取得微信全文；手机视觉和本人审核另记。缺少快照不否定明确的历史核验回执，但下一次更新必须先取得有效新快照。所有发表由本人在微信后台操作。

## 离线工具与维护

脚本只用 Python 3.9+ 标准库；在总入口 Skill 根目录运行。`preflight.py` 默认离线，只有 `--verify-media` 会读取正文公开 HTTPS 图片；`preview_cover.py` 只做本地裁切预览；`workflow_ledger.py` 不联网、不提交；本地台账是指定交付者的私有工作记录，不提供跨主机锁或自动同步。

维护者从四个同级本机 Skill 生成公开包：

```bash
python3 scripts/build_public_bundle.py --skill-root /path/to/skill-directory --output /path/to/new-public-bundle --manifest /path/to/private-audit.json
```

输出目录必须为空。构建仅包含明确允许的规则、脚本和示例资源，不打包私有台账、稿件、回执、实测图片、缓存或服务器配置。公开包不新增模型 API、图床、付费服务或发表权限。模板 SVG 是示意，不是产品实测截图。版权与来源说明见 [provenance.md](skills/ai-toolbox-wechat/references/provenance.md)。
"""
    sections = ["# AI顺手工具箱：Muse 完整阅读版\n\n版本：**1.4.0**。本页由四个 Skill 与共享参考生成。按任务读相关章节；读取规则不等于拥有执行、台账或微信工具权限。首次核对本页版本，后续交接沿用同一正文版本和文章标识。实际私有台账不在此公开仓库。\n\n## 导航\n"]
    sections.extend("- [" + name + "](#skill-" + name + ")\n" for name in NAMES)
    sections.extend("- [" + name + "](#ref-" + name + ")\n" for name in REFS)
    for name in NAMES:
        text = contents["skills/" + name + "/SKILL.md"]
        text = re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.S)
        sections.append('\n<a id="skill-' + name + '"></a>\n\n' + reader_links(text))
    for name in REFS:
        sections.append('\n<a id="ref-' + name + '"></a>\n\n' + reader_links(contents["skills/ai-toolbox-wechat/references/" + name + ".md"]))
    contents["MUSE_GUIDE.md"] = "\n".join(sections)
    for relative, text in contents.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    report = {"version": VERSION, "file_count": len(contents), "files": [{"path": path, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()} for path, text in sorted(contents.items())], "generated_legacy_root": True, "generated_muse_reader": True, "private_runtime_data_included": False}
    manifest.parent.mkdir(parents=True, exist_ok=True)
    if manifest.exists():
        raise ValueError("manifest 已存在，选择新的审计文件")
    manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description="从同级四 Skill 生成公开包；不发布、不联网")
    parser.add_argument("--skill-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.skill_root, args.output, args.manifest)
    print(json.dumps({"ok": True, "version": VERSION, "files": report["file_count"]}))


if __name__ == "__main__":
    main()
