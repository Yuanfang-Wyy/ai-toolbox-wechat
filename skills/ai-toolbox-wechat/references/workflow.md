# 统一流程、台账与核验口径

这是总入口与三个专项 Skill 共用的流程契约。编辑细则、视觉细则和接口操作仍在各自参考文件；不要复制并维护第二套状态规则。

## 同一文章与同一台账

- 统筹方按“读者要完成的任务 + 工具官方标识”分配稳定 `article_key`。题目改名不换标识；同一工具的不同任务可分别成题，不同工具解决同一任务要先比较角度是否重复。
- 查重覆盖已发表、已有草稿、待研究和已否决；同时看工具、任务和场景，不只做标题精确匹配。已否决记录保留理由，出现新版本或新证据可以重新评估。
- v1.5.0 以既有授权服务的私有云台账为唯一权威记录，REST 基址为 `https://www.yuanfangwyy.xyz/api/drafts/v1`，或使用同服务的 MCP 台账工具。台账在云端持久保存，Muse 与 Codex 共用，不要求 Mac 开机或共享本地文件。正式使用先检查 `api_version=1.1.0`、`workflow_enabled=true`、`workflow_storage=cloud` 与 `publishing_enabled=false`。
- 本机私有 `runtime.json` 标记 `ledger_mode=cloud`；其中原 ledger_path 仅指只读备份。配置、旧台账、稿件和回执均不进入公开包。没有配置的 Muse 也可用已授权连接按下节访问云台账，无需新装依赖、读取服务器文件或粘贴密钥。云连接不可用时只保留待同步 packet，不回退成另一份生产主库。
- 台账关联 `article_key`、负责人、标题与任务、`article_id`、正文版本/指纹、`delivery_key`、`request_id`、各环节状态及证据/错误。版本指纹为 UTF-8 `title + "\n" + markdown` 的 SHA-256；请求 payload 指纹另行保存。保留历史回执，不用新索引覆盖已确认事实。
- 云端项目索引用于对账和定位已有 `article_id`，不是微信完整草稿列表。没有条目、远端读取失败或 `has_wechat_draft=false` 都不能单独证明微信没有稿件，也不授权重新创建。

索引覆盖范围写明来源、采集时间与是否局部；例如最近 50 条只能标为 partial，不能称全历史。`index_observation` 保留项目状态与 `has_wechat_draft` 观察值，不自动映射为内容已审、正文已核验或本人审核。

现有 `packet.json` 继续作为交接包，不为拆分要求另造一组必填字段。正文指纹是 UTF-8 `title + "\n" + markdown` 的 SHA-256。payload 指纹是实际 MCP arguments 的 JSON（ensure_ascii=false、键排序、分隔符为逗号/冒号）的 SHA-256，更新时包括 article_id 和 expected_snapshot；REST 的 article_id 虽在路径，计算时仍并入同一 arguments。请求号沿用现有 preflight 或冻结请求，不为方便同步换号。prepared 只证明准备元数据已登记，不能证明微信保存。

## 分开记录结果

| 维度 | 通过的依据 | 不足以通过的依据 |
|---|---|---|
| 内容审核 | 审稿者核对当前版事实、标题承诺、可照做的成果及必要条件 | 文件存在、已生成、仅预检通过 |
| 媒体检查 | 当前稿所引用图片的格式/签名/大小检查，加图源、图注与可读性人工检查；无图说明取舍 | 有图位、旧版图检、上传数量相同 |
| 远端交付 | 与本次请求/版本关联的 created/updated/existing 回执，或独立且明确关联的后端成功凭据 | prepared、项目索引、仅本地文件或 Markdown 更新 |
| 远端正文核验 | 与本次请求/版本关联的保存回执含 verified=true，或授权读取取得远端正文与预期一致的证据 | 单独 succeeded、approved、remote_title、图片数或 snapshot 变化 |
| 手机预览 | 确实打开本次草稿手机预览，检查正文、图片、字号、留白和裁切并记录结果 | 服务端 verified=true、HTML 预览或结构检查 |
| 本人审核 | 用户本人明确审核该版本 | Agent 审稿、项目 approved、自动流转 |

台账分开保存：`editorial`（pending/reviewed/blocked）、`media`（pending/verified/blocked/not_required）、`delivery`（not_submitted/prepared/created/updated/existing/uncertain/quota_blocked/conflict）、`remote_verification`（pending/verified/failed）、`mobile_preview`（pending/passed/needs_fix）及 `owner_review`（pending/approved/rejected）。后两项只能依据真实预览或本人决定确认，不由本地预检或 Agent 审稿推定。当前云台账外部写接口不开放提升这两项状态；私有检查记录可保留实际证据，不能因接口限制伪造通过。

服务端 `verified=true` 路径足以确认远端正文核验，无须把微信全文再暴露给写作 Agent。当前已检查服务会比较正文文本、标题、封面与图片数量；不验证 CSS、像素级显示、图片内容或手机排版。回执字段与当前接口能力仍应实际核对，不能因为历史服务曾验证就给无标记的成功结果补写 verified。

`draft_created` 表示已确认保存；`draft_verified` 表示保存且远端正文核验有证据；`awaiting_owner_review` 表示仍待本人审核。这些交付汇总标签不代替上表各维度。草稿已保存而正文未核验时保留两项状态和原 `article_id`，不重复创建。任何状态都不触发发表。

## 版本与依赖

正文或标题修改后登记新版本，内容审核、媒体、远端正文核验回到 pending。旧版内容审核不能标为新版通过；旧版媒体和回执留在旧版本下，新版需逐项确认适用范围。正文图片及用途均未变时可以明确引用原媒体检查证据，但不能无说明地继承旧通过状态；远端回执必须对应本次实际提交的版本。手机预览和本人审核也注明版本。保留已有远端身份与历史交付状态，修订进入 update，不重新 create。

内容阻塞只暂停受影响的内容交付，媒体阻塞只暂停需要这些图的提交。微信连接、额度或快照问题不阻止继续已授权的离线研究、写稿和图像准备；不能把这些本地成果报成已保存微信。

## 唯一交付入口与工具

研究、写作、视觉和审稿 Agent 交 packet 与证据给总控；只有当前账号指定交付者创建/更新微信草稿，串行操作。跨机器或 Muse 拿不到同一私有台账、回执或工具时，交 packet 等总控对账，不自建第二份权威台账、不直接重复 create。离线演练只写隔离的试跑台账，明确标为模拟，不并入生产记录。

## 云台账接口与交接

台账接口与原五项草稿能力使用同一已有授权：REST 的安全凭据存储注入 `X-API-Key`，MCP 沿用现有 OAuth 和 drafts:read/drafts:write scopes。只发现并调用现有连接，不把密钥写入提示词、正文、公包或日志。下面基址均指现有服务，不能拿公众号 AppSecret 替代连接密钥。

| MCP 逻辑能力 | REST 路径（相对基址） | 参数与结果 |
|---|---|---|
| list_workflow_entries | GET `/workflow?query=&limit=50&offset=0` | query 最长100，limit 1–50，offset 非负；返回 articles、total、limit、offset、ledger_version，可能带 index_coverage |
| read_workflow_entry | GET `/workflow/{article_key}` | 返回当前完整记录和 revision；404 workflow_not_found 表示台账未录入，不能据此推断微信没有草稿 |
| save_workflow_entry | PUT `/workflow/{article_key}` | 请求仅 `{record, expected_revision}`；record 是本次字段变更，返回合并后的记录和新 revision；新条目用 expected_revision=0 |

article_key 为 1–160 个 ASCII 字符，首位字母或数字，后续可用字母、数字、冒号、点、下划线及连字符。已有 `legacy:UUID`、`request:UUID` 都是有效身份：先定位并沿用，不能为好看的命名另建具有同一 article_id 的条目。HTTP 路径按 URL 编码传递，不能拼接任意文件路径。

**每次写入先读，使用返回的 revision。** `workflow_revision_conflict`、`workflow_identity_conflict`、`workflow_request_conflict` 或 `workflow_review_version_conflict` 返回409：保留本次 patch，重新读差异并合并，不强制覆盖、不盲改 expected_revision。校验或受保护状态返回422，修正文档/字段后再登记；不绕过规则。除用户授权本次保存外，不因加载 Skill 自动登记研究结果。

### 正确的记录字段

record 允许：`article_key`、`article_id`、`title`、`task`、`source_urls`、`owner`、`delivery_key`、`content_sha256`、`request_id`、`payload_sha256`、`topic_record`、`editorial_note`、`review`、`states`。一般不重复传路径 article_key；article_id 与 request_id 是规范小写 UUID，指纹为64位小写十六进制。来源为公开 HTTPS，无登录凭据或令牌查询参数。

- `topic_record`：decision 为 write/research/defer/reject；可含 title、brief、source_urls、editorial_note、owner。brief 只含 audience、task、current_way、improvement、setup_cost、evidence。
- `review`：必含 content_sha256 与非空 evidence，可含 editorial_review_passed（布尔）和 media_status（pending/verified/blocked/not_required）。证据须对应本次正文，不能用旧审核盖新版本。
- 客户端 states 只能登记 editorial、media 的准备/审核结果，以及 delivery=not_submitted/prepared；reviewed 和媒体 verified/not_required 须有上述 review。prepared 须与 request_id、payload_sha256、content_sha256 一起登记。
- remote_verification、mobile_preview、owner_review 外部仅允许 pending；客户端不能写 receipt、history、revision、updated_at 或成功交付状态，也不要把 GET 返回的整条记录原样 PUT。微信真实回执由服务端内部录入，客户端不制造通过证据。

新选题登记的可复制请求体示例（先查重；新条目才用 revision 0）：

```json
{
  "record": {
    "title": "配音总要重录？先把旁白单独做好",
    "task": "给软件教程制作可修改的中文旁白",
    "source_urls": ["https://github.com/debpalash/VoiceStudio"],
    "owner": "editor",
    "topic_record": {
      "decision": "research",
      "brief": {
        "audience": "需要做软件教程的内容创作者",
        "task": "制作并修改中文旁白",
        "current_way": "口播有错后整段重录",
        "improvement": "先比较逐段生成与导出能力",
        "setup_cost": "核查硬件、模型下载与授权条件",
        "evidence": "先核对官方文档，不能称已实测"
      }
    }
  },
  "expected_revision": 0
}
```

正文定稿后，先 PATCH 式 PUT `content_sha256` 与绑定该指纹的 review，待真实检查完成才设 editorial_review_passed=true 和适用 media_status。再把实际冻结 request.json 的 request_id、payload_sha256、delivery_key 与 `states:{"delivery":"prepared"}` 登记到同一条目；每次沿用最新 revision。不能为了演示直接填写假指纹或假审核。

保存后核对原始回执的 article_id、request_id、published=false、verified 和 ledger_sync。`ledger_sync.status=recorded` 后 GET 同一 article_key，确认版本与回执一致。`ledger_sync.status=pending` 不抹掉已取得的微信成功回执，也不意味着应重建草稿：先查询原 article_id/request_id 与云台账，按 [交付恢复](delivery.md) 由服务补记，客户端不能 PUT receipt。

### 本机脚本与离线备份

`scripts/workflow_ledger.py` 是旧本地台账工具，不能替代云接口。运行前读取总入口私有 runtime.json：cloud 模式下所有本地写命令（import-index、record-topic、reconcile、record-review、record-receipt）拒绝执行；`list` 只能查看明确标成非权威的旧备份。迁移、恢复与模拟需明确隔离并由总控处理，不把本地 JSON 双向同步成第二个主库。

Muse 只需已有 REST/MCP 连接：读公开规则→查云台账→按当前 revision 记录研究/审核/准备→按既有草稿接口保存→核对服务回执与云记录。若没有脚本运行能力，按相同 preflight 标准人工检查并保留证据，不声称运行过本地脚本；图检、请求冻结和交付边界不因此省略。
