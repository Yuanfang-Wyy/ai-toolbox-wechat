# 草稿交付与故障恢复

本文件定义接口与故障处理；文章身份、私有台账、各版本的独立状态及核验证据以 [统一流程](workflow.md) 为准。由 [草稿交付 Skill](../../wechat-draft-delivery/SKILL.md) 按授权执行，总入口仍是唯一统筹。

## 当前连接

优先使用宿主提供的“AI顺手工具箱”现有连接。下表是逻辑能力名：MCP 按实际 schema 映射宿主前缀和参数，REST 按现有 OpenAPI 映射 HTTP 操作；已有 CLI 则按其公开帮助映射相同能力，不猜命令或 endpoint。当前只有草稿能力，服务器禁用正文模型调用与正式发表。

| 逻辑能力 | 参数与边界 | 当前私有 REST 对应操作 |
|---|---|---|
| connection_status | 检查 ready、publishing_enabled=false | GET `/api/drafts/v1/status` |
| list_drafts | query、limit；limit 最大 50，返回项目索引而非完整微信草稿列表 | GET `/api/drafts/v1/drafts` |
| read_draft | article_id；返回项目 markdown、sources；远端可读时返回 remote_title、image_count 和 expected_snapshot | GET `/api/drafts/v1/drafts/{article_id}` |
| create_draft | title、markdown、source_urls、request_id；只存草稿 | POST `/api/drafts/v1/drafts` |
| update_draft | 上述字段 + article_id、expected_snapshot；先读后改，保留旧正文 | PUT `/api/drafts/v1/drafts/{article_id}`，article_id 在路径中 |

映射仅使用当前已有且已授权的入口，不扩展到发表、删除或账户权限，不安装或授权新的投递服务。

## 保存前

1. 确认本次允许写草稿，在同一私有台账核对 article_key、任务、正文版本和原 article_id，由唯一交付者串行操作。文章质量通过，来源与图片真实可用。标题最长 32 字；正文 80—14000 字；source_urls 最多 20 条 HTTPS。
2. 正文不得带知识库 generated 标记、个人思考/计划区、frontmatter、占位内容或主动 HTML。正文图片最多 15 张，按视觉标准检查格式和来源。
3. 已有草稿必须成功 read_draft，保留项目原文与 expected_snapshot。备份正文可用于本地改稿，不能代替最新微信快照。
4. 准备交接包并运行离线 check；提交前运行一次带图片验证的 prepare，固定 request_id、payload 指纹和工具参数：

```bash
python3 scripts/preflight.py check --packet /path/to/packet.json --content-only
python3 scripts/preflight.py prepare --packet /path/to/packet.json --output /path/to/request.json --verify-media
```

脚本路径按本 Skill 所在目录解析。不加 `--verify-media` 时离线；加上时仅 GET 正文公开图片，检查响应 MIME、签名与 1,000,000 字节限制。返回 `media_verified=true` 也不代表图片版权、可读性或微信上传成功。无图无需联网。不要为了参数准备重复下载已经核验的图片。

已有 request.json 与不同 payload 冲突时拒绝覆盖。将 request.json 的 tool 与 arguments 交给宿主调用；脚本不直接提交。参数准备不代表本任务已授权上传，调用前仍核对当前对话。

### 缺少快照或接口限制

缺少 expected_snapshot 时，先核对实际 article_id，再区分没有有效远端绑定、微信读取失败（包括 40007、45009）、使用了不同接口或客户端裁剪结果。截至 2026-10-16 已检查的本项目服务源码中，MCP 与私有 REST 共用读取逻辑：有有效远端绑定且微信读取成功时生成快照，没有按 approved 状态拒绝的分支。这是该实现的条件，不保证任意部署或 Agent 的返回字段都相同；仍应核对当前入口和原始响应。

approved 不能作为通用更新锁。40007 表示本次远端读取未成功，不能单凭它认定稿件已删除、允许重建或需要改本地状态。旧 content-hub 接口的本地记录和状态转换也不等于快照更新能力。

不伪造 snapshot，不改状态或强写数据库绕过校验。无法读取远端正文时，本地新稿不能替代远端基线；保留离线修订。只有确认当前入口的限制后，才将受影响操作交给本人在微信后台处理，不声称所有已批准稿都只能手动修改。

## 保存后

保存回执核对：status 是 created/updated/existing、verified=true、published=false、article_id 存在、标题正确、image_count 与本次正文图片匹配，并与固定 request_id、提交版本和预期 article_id 对账。当前服务通常也返回 expected_snapshot，保留它供后续先读后改；客户端未暴露此字段不自动否定已确认的 verified 回执，但下次 update 仍须重新取得有效快照。

以下两条证据路径均可确认远端正文核验：

1. 与本次请求/版本明确关联的成功保存回执含 verified=true。当前已检查服务是在保存后读微信草稿，核对正文文本、标题、封面和图片数量后才返回该标记；不要求 Agent 再取得微信全文。
2. 现有授权连接直接取得远端正文，与本次提交预期一致，并保存可对账的证据。

把原始回执放入本篇 receipt.json，连同固定 request.json 录入同一私有台账。满足任一路径可报告“已保存，服务端远端正文核验通过，待本人审核”，并记录具体路径。核验不包括 CSS、像素级显示、图片内容或手机排版；手机预览和本人审核分别记录。

保存后读回可能失败：如果已有直接创建成功回执，或独立、明确关联本请求的后端成功任务、media_id 存在与正文指纹匹配，可报告“创建已确认，读回未核验”，保留原 article_id。缺少这些凭据则标为 uncertain。索引 has_wechat_draft=true 仅是线索，不能单独证明成功；也不能把批准字段代替本人审核。

当前 read_draft 的 markdown 来自项目记录。approved、项目正文已改好、remote_title 相同、图片数一致或 snapshot 变化，都不能单独证明微信正文已经更新。单独 succeeded 只支持保存成功口径，不能替代 verified 或真实远端正文一致证据。失败后读到新版项目 Markdown 不补足这项证据，不追溯给历史无证据的稿件补标 verified；已有明确 verified 回执的稿件也不因没有向 Agent 暴露全文而降级。

## 停止条件

- `wechat_api_45009`：记录 quota_blocked，停止本账号后续微信 API 请求；不自动清零额度、不轮询到恢复、不猜重置时间。不要只依赖 HTTP 429：投递内部捕获上游错误后也可能返回 failed 或 uncertain，结合业务错误与原任务阶段判断。可读不调用微信的项目索引/已获授权的独立后端任务凭据判断是否已创建，不能通过它们绕过微信读回。继续本地成稿，按下节恢复。
- `wechat_draft_changed_read_again`：重新读取、比较变更后合并，不沿用旧快照覆盖。
- `remote_draft_changed`：停止该稿写入，核对远端与上次成功版本的正文、图片和封面差异；不能用本地新稿覆盖基线，也不自动重试冲突。
- `busy`：保留同一请求，仅由交付入口做有界重试。不要每个 Agent 同时重试。
- `uncertain` / `submitting` / 超时：查询原任务/已有草稿，未明确结果前不自动重试、不换 request_id、不重复创建。
- 明确在微信创建前失败（例如图片超限）：记录失败阶段及 article_id。只有确认没有创建远端草稿、确需修改 payload 时，才冻结旧请求并准备新修订号；已创建则用原 article_id 更新，不能因读回失败重建。
- `request_id_reused_with_different_content`：冻结原请求，先查结果；已创建稿转 update。
- 旧草稿已发表、被删或无法读回：保留本地修改，不推断允许重建，不调用发表接口。
- 连接或站点安全策略拒绝：报告阻塞，不通过登录 Token、浏览器抓包、SSH 调微信 API 等方式绕过；可读取已获授权的独立知识库备份做离线修订。

### 额度恢复后的串行处理

1. ready 或项目 list_drafts 成功不代表微信额度恢复。下次已获授权的重试只做一次真实草稿读取；仍遇额度错误则停止整批，不继续试其他稿。
2. 确认真实读取恢复后，按标题、原 article_id/request_id 与任务阶段核对待处理稿。成功或已存在的稿先确认结果，uncertain/submitting 或远端冲突稿暂停，不能混入普通重试。
3. 只有明确未提交且允许重试的任务，才用原 request_id、原内容串行继续，并核对最新远端快照；快照冲突或请求指纹变化先停下来比较，不把改变参数当成原请求的重试。
4. 每篇取得 verified 交付结果并核对回执后，再处理下一篇；读回失败、结果不明、远端冲突或再次额度错误时停止受影响的处理。

## 正式发表

所有发表由用户本人执行。本 Skill 不生成可自动执行的发布请求，不提供发表命令、计划任务或审批后自动发文逻辑。审核可以修改、退回或放弃稿件，不能自动流转为发布。
