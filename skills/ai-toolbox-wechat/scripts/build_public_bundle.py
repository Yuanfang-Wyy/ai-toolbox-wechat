#!/usr/bin/env python3
"""Build a public four-skill bundle and generated legacy/Muse entry points."""
import argparse
import hashlib
import json
import re
from pathlib import Path


VERSION = "2.2.0"
NAMES = ("ai-toolbox-wechat", "wechat-topic-research", "wechat-visual", "wechat-draft-delivery")
REFS = ("editorial", "collaboration", "visual", "visual-production", "delivery", "feedback", "provenance", "workflow", "content-craft")
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

版本：**2.2.0**。保留 `$ai-toolbox-wechat` 总入口，按需使用三个专项：

| Skill | 用途 |
|---|---|
| [总入口](skills/ai-toolbox-wechat/SKILL.md) | 写作、审稿、反馈与流程统筹 |
| [选题研究](skills/wechat-topic-research/SKILL.md) | 按读者任务查重、整合官方证据与使用门槛 |
| [视觉制作](skills/wechat-visual/SKILL.md) | 图位、真实素材、示意图、封面与预览检查 |
| [草稿交付](skills/wechat-draft-delivery/SKILL.md) | 固定请求、串行保存、快照与回执核验 |

## v2.2.0 标题亮点与封面同文

单工具稿统一“工具名 - 后半句”，比较或方法稿用“主题名 - 后半句”；半角短横线两侧各一空格，完整标题最多32字符。后半句从具体麻烦与本任务最有辨识度的做法或结果切入，亮点须与官方资料或实测证据相称，不写无依据的最强排名、效率倍数或自动化承诺。封面主标题与文章标题同文，只按视觉宽度换行；横图与方形裁切分别核查，不能把本地更新报成微信封面已同步。

保留约1500字、短编号功能概览、一个典型场景、完整操作与结果核对，沿用用户已确认的明亮蓝绿排版。不改变交付权限、既有任务启停状态或微信额度停止条件。

## 场景上手与明亮蓝绿排版

开头用真实编号简述主要功能，随后完整讲一个典型场景；步骤说明入口、输入/设置、动作、可见结果与核对。使用用户确认的明亮蓝绿浅色卡、真实步骤号和浅绿完成提示；正文16px，卡片至少15px，不强制四项四步。默认约1500字，保留2—3个有用入口和完整可见网址。内容核验、远端HTML机器检查、手机预览和本人审核分别记录。

## Muse 与网页 Agent

公开阅读入口：[MUSE_GUIDE.md](MUSE_GUIDE.md)。按本次任务读取总入口、对应专项和共享规范；本文件由同一源码生成，不单独维护第二套规则。

可复制提示词：

> 每次任务开始在线重读本仓库当前 MUSE_GUIDE.md，记录版本和commit（本版v2.2.0），使用 AI顺手工具箱总入口处理我的任务，按需调用选题研究、视觉制作和草稿交付规则。单工具稿默认约1500字，保留示例、步骤和结果核对，不硬凑字数。标题用“工具名/主题名 - 后半句”，突出具体麻烦与可证实亮点，封面主标题同文，不捏造效果或同类排名。先检查现有连接 api_version=1.1.0、workflow_enabled=true、workflow_storage=cloud、publishing_enabled=false。经同一授权 REST/MCP 分页查云台账去重，沿用原 article_key；每次先读 revision，再只合并本次准备字段。由唯一交付入口用稳定 request_id 保存，核对 verified 与 ledger_sync 及云记录。台账同步 pending 时先查原ID，不换号重建。没有连接时交付 packet 和本地成果，不自建第二主库，不声称已写微信。只按当前授权存草稿，正式发表由我本人操作。

公开读取不等于已有连接。Muse 使用现有安全凭据存储配置的 REST 或已有 OAuth MCP，直接调用云台账与草稿能力，不需新增本地依赖或让 Mac 开机。REST 基址为 `https://www.yuanfangwyy.xyz/api/drafts/v1`，当前注册版本1.1.0；运行前读取 OpenAPI 与 connection_status，确认实际部署，不因读取 Skill 就假定工具已增加。密钥不进入提示词、公开文档或仓库，台账数据也不公开。字段与请求示例见统一流程。

## 安装到支持 Agent Skills 的运行时

从仓库 `skills/` 下复制四个完整目录到运行时 Skill 目录，保持它们为同级目录；专项通过相对路径引用总入口的共享规则和脚本。已有同名版本先比较和备份，使用目标运行时支持的安装流程；不默认覆盖。根目录 `SKILL.md`、references、assets、scripts 是自动生成的旧路径兼容版，旧链接继续有效；新安装优先使用 `skills/` 里的四个目录，避免重复安装总入口。

## 内容辅助能力

中文终审按需使用 `humanizer-zh`，正文插画与原创封面由视觉专项按需使用 `baoyu-article-illustrator`、`baoyu-cover-image`。它们是补充能力，不是新总入口；本机可安装固定版本，Muse 可直接读取 [账号适配规则](skills/ai-toolbox-wechat/references/content-craft.md) 和其中的固定上游来源，无需 Mac 在线或安装第三方运行依赖。公开包不打包上游整包、不启用额外付费模型、登录、托管或发表。真实软件图、准确关系图和插画分别处理；不机械增加图片或第一人称体验。

## 台账与核验

共享口径见 [workflow.md](skills/ai-toolbox-wechat/references/workflow.md)。继续使用现有 packet.json、文章标识和图片台账。私有总台账通过同一已授权 REST/MCP 云服务按 revision 合并，分别记录内容、媒体、交付、正文核验、手机预览及本人审核；客户端只能提交准备/实际审稿证据，真实保存回执由服务内部写回。项目索引只作线索，不能推定微信已保存、远端已核验或用户已批准。

本次提交的 `verified=true` 成功回执可以作为服务端远端正文核验证据，不要求 Agent 再取得微信全文；手机视觉和本人审核另记。缺少快照不否定明确的历史核验回执，但下一次更新必须先取得有效新快照。所有发表由本人在微信后台操作。

## 离线工具与维护

脚本只用 Python 3.9+ 标准库；在总入口 Skill 根目录运行。`preflight.py` 默认离线，只有 `--verify-media` 会读取正文公开 HTTPS 图片；`preview_cover.py` 只做本地裁切预览；`workflow_ledger.py` 不联网、不提交；cloud 模式拒绝本地写入，本地 JSON 仅为非权威只读备份，不与云端双向合并。Muse 无需执行这些脚本，可用已授权连接完成同等检查并如实记录证据，不能声称运行过本地脚本。

维护者从四个同级本机 Skill 生成公开包：

```bash
python3 scripts/build_public_bundle.py --skill-root /path/to/skill-directory --output /path/to/new-public-bundle --manifest /path/to/private-audit.json
```

输出目录必须为空。构建仅包含明确允许的规则、脚本和示例资源，不打包私有台账、稿件、回执、实测图片、缓存或服务器配置。公开包不新增模型 API、图床、付费服务或发表权限。模板 SVG 是示意，不是产品实测截图。版权与来源说明见 [provenance.md](skills/ai-toolbox-wechat/references/provenance.md)。
"""
    sections = ["# AI顺手工具箱：Muse 完整阅读版\n\n版本：**2.2.0**。默认篇幅约1500字；标题突出具体麻烦与可证实亮点，封面主标题同文，详见编辑标准。本页由四个 Skill 与共享参考生成。按任务读相关章节；读取规则不等于拥有执行、台账或微信工具权限。每次任务先在线重读本页并核对版本与commit，不能仅凭旧缓存；后续交接沿用同一正文版本和文章标识。实际私有台账不在此公开仓库。云台账由现有授权服务持久保存，Mac 关机后仍可访问；先核对 api_version=1.1.0 与 workflow_enabled=true，不从本地备份写生产。Muse 无需新增本地依赖，接口与可复制 JSON 见统一流程章节。\n\n## 导航\n"]
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
