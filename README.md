# AI顺手工具箱 Skill 套件

版本：**2.3.0**。保留 `$ai-toolbox-wechat` 总入口，按需使用三个专项：

| Skill | 用途 |
|---|---|
| [总入口](skills/ai-toolbox-wechat/SKILL.md) | 写作、审稿、反馈与流程统筹 |
| [选题研究](skills/wechat-topic-research/SKILL.md) | 按读者任务查重、整合官方证据与使用门槛 |
| [视觉制作](skills/wechat-visual/SKILL.md) | 图位、真实素材、示意图、封面与预览检查 |
| [草稿交付](skills/wechat-draft-delivery/SKILL.md) | 固定请求、串行保存、快照与回执核验 |

## v2.3.0 场景封面与云端内容认领

封面采用已确认的蓝绿/米白场景插画、深色大标题与完整原题，每篇画面对应具体任务，检查横图、中心方图和手机缩略图；原生生图，禁止代码覆盖文字。参考两张示例图和通用提示词，不复制占位框圆点。

同一私有云workflow是唯一内容目录。新题先全分页查当前及history、官方标识和别名，缺网址/not_submitted不代表没写过；同工具已出现默认避开，真正不同任务要比对原key并审阅留痕。零记录工具按规范官方ID的SHA256生成固定key，expected_revision=0认领owner，成功后才开写，409不换key。提交前再查；历史身份不改名，不能另建同题。完整协议与Muse可复制请求见[内容目录](skills/ai-toolbox-wechat/references/content-registry.md)。

## 标题亮点与封面同文

单工具稿统一“工具名 - 后半句”，比较或方法稿用“主题名 - 后半句”；半角短横线两侧各一空格，完整标题最多32字符。后半句从具体麻烦与本任务最有辨识度的做法或结果切入，亮点须与官方资料或实测证据相称，不写无依据的最强排名、效率倍数或自动化承诺。封面主标题与文章标题同文，只按视觉宽度换行；横图与方形裁切分别核查，不能把本地更新报成微信封面已同步。

保留约1500字、短编号功能概览、一个典型场景、完整操作与结果核对，沿用用户已确认的明亮蓝绿排版。不改变交付权限、既有任务启停状态或微信额度停止条件。

## 场景上手与明亮蓝绿排版

开头用真实编号简述主要功能，随后完整讲一个典型场景；步骤说明入口、输入/设置、动作、可见结果与核对。使用用户确认的明亮蓝绿浅色卡、真实步骤号和浅绿完成提示；正文16px，卡片至少15px，不强制四项四步。默认约1500字，保留2—3个有用入口和完整可见网址。内容核验、远端HTML机器检查、手机预览和本人审核分别记录。

## Muse 与网页 Agent

公开阅读入口：[MUSE_GUIDE.md](MUSE_GUIDE.md)。按本次任务读取总入口、对应专项和共享规范；本文件由同一源码生成，不单独维护第二套规则。

可复制提示词：

> 每次任务开始在线重读本仓库当前 MUSE_GUIDE.md，记录版本和commit（本版v2.3.0），使用 AI顺手工具箱总入口处理我的任务，按需调用选题研究、视觉制作和草稿交付规则。单工具稿默认约1500字，保留示例、步骤和结果核对，不硬凑字数。标题用“工具名/主题名 - 后半句”，突出具体麻烦与可证实亮点，场景插画封面主标题同文，不捏造效果或同类排名。全分页检查云目录当前及history、来源和别名，已有工具默认避开，先认领owner再写，409不换key；缺网址和待核对任务不代表没写过。先检查现有连接 api_version=1.1.0、workflow_enabled=true、workflow_storage=cloud、publishing_enabled=false。经同一授权 REST/MCP 分页查云台账去重，沿用原 article_key；每次先读 revision，再只合并本次准备字段。由唯一交付入口用稳定 request_id 保存，核对 verified 与 ledger_sync 及云记录。台账同步 pending 时先查原ID，不换号重建。没有连接时交付 packet 和本地成果，不自建第二主库，不声称已写微信。只按当前授权存草稿，正式发表由我本人操作。

公开读取不等于已有连接。Muse 使用现有安全凭据存储配置的 REST 或已有 OAuth MCP，直接调用云台账与草稿能力，不需新增本地依赖或让 Mac 开机。REST 基址为 `https://www.wangyuyangwyy.com/api/drafts/v1`，当前注册版本1.1.0；运行前读取 OpenAPI 与 connection_status，确认实际部署，不因读取 Skill 就假定工具已增加。密钥不进入提示词、公开文档或仓库，台账数据也不公开。字段与请求示例见统一流程。

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

输出目录必须为空。构建仅包含明确允许的规则、脚本和示例资源，不打包私有台账、稿件、回执、实测图片、缓存或服务器配置。公开包不新增模型 API、图床、付费服务或发表权限。模板 SVG 仅作裁切示意，不是新版成品封面；两张已确认编辑封面仅作风格示例，不是产品实测截图。实际逐稿提示词保留私有目录，公开只放通用框架。版权与来源说明见 [provenance.md](skills/ai-toolbox-wechat/references/provenance.md)。
