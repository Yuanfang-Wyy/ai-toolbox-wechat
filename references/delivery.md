# 草稿交付与故障恢复

## 当前连接

优先使用宿主提供的“AI顺手工具箱”MCP 工具。先发现实际 schema，不猜调用名、参数或 endpoint。当前只有草稿能力，服务器禁用正文模型调用与正式发表。

| 工具 | 参数与边界 |
|---|---|
| connection_status | 检查 ready、publishing_enabled=false |
| list_drafts | query、limit；limit 最大 50，返回项目索引而非完整微信草稿列表 |
| read_draft | article_id；返回 markdown、sources、remote_title、image_count 和 expected_snapshot |
| create_draft | title、markdown、source_urls、request_id；只存草稿 |
| update_draft | 上述字段 + article_id、expected_snapshot；先读后改，保留旧正文 |

宿主可能给这些名字加前缀；按已发现的实际名称调用。不安装或授权新的投递服务。

## 保存前

1. 确认本次允许写草稿，文章质量通过，来源与图片真实可用。标题最长 32 字；正文 80—14000 字；source_urls 最多 20 条 HTTPS。
2. 正文不得带知识库 generated 标记、个人思考/计划区、frontmatter、占位内容或主动 HTML。正文图片最多 15 张，按视觉标准检查格式和来源。
3. 已有草稿必须成功 read_draft，保存原文与 expected_snapshot。备份正文可用于本地改稿，不能代替最新微信快照。
4. 准备交接包并运行离线 check；提交前运行一次带图片验证的 prepare，固定 request_id、payload 指纹和工具参数：

```bash
python3 scripts/preflight.py check --packet /path/to/packet.json --content-only
python3 scripts/preflight.py prepare --packet /path/to/packet.json --output /path/to/request.json --verify-media
```

脚本路径按本 Skill 所在目录解析。不加 `--verify-media` 时离线；加上时仅 GET 正文公开图片，检查响应 MIME、签名与 1,000,000 字节限制。返回 `media_verified=true` 也不代表图片版权、可读性或微信上传成功。无图无需联网。不要为了参数准备重复下载已经核验的图片。

已有 request.json 与不同 payload 冲突时拒绝覆盖。将 request.json 的 tool 与 arguments 交给宿主调用；脚本不直接提交。参数准备不代表本任务已授权上传，调用前仍核对当前对话。

## 保存后

回执需同时满足：status 是 created/updated/existing、verified=true、published=false、article_id 存在、expected_snapshot 存在、标题正确、image_count 与正文图片匹配。当前服务保存后会读回核对正文与封面。

把回执放入本篇 receipt.json，分别记录 created、readback_verified、published=false、owner_review_pending=true；完整读回后才注明“已保存并核验草稿，待本人审核”。图片数量/结构检查不能证明手机预览通过；后者单独记录。

保存后读回可能失败：如果已有直接创建成功回执，或独立、明确关联本请求的后端成功任务、media_id 存在与正文指纹匹配，可报告“创建已确认，读回未核验”，保留原 article_id。缺少这些凭据则标为 uncertain。索引 has_wechat_draft=true 仅是线索，不能单独证明成功；也不能把批准字段代替本人审核。

## 停止条件

- `wechat_api_45009`：记录 quota_blocked，停止本账号后续微信 API 请求；不自动清零额度、不轮询到恢复、不猜重置时间。可读不调用微信的项目索引/已获授权的独立后端任务凭据判断是否已创建，不能通过它们绕过微信读回。继续本地成稿，恢复后再读取。
- `wechat_draft_changed_read_again`：重新读取、比较变更后合并，不沿用旧快照覆盖。
- `busy`：保留同一请求，仅由交付入口做有界重试。不要每个 Agent 同时重试。
- `uncertain` / 超时：查询原任务/已有草稿，未明确结果前不换 request_id、不重复创建。
- 明确在微信创建前失败（例如图片超限）：记录失败阶段及 article_id。只有确认没有创建远端草稿、确需修改 payload 时，才冻结旧请求并准备新修订号；已创建则用原 article_id 更新，不能因读回失败重建。
- `request_id_reused_with_different_content`：冻结原请求，先查结果；已创建稿转 update。
- 旧草稿已发表、被删或无法读回：保留本地修改，不推断允许重建，不调用发表接口。
- 连接或站点安全策略拒绝：报告阻塞，不通过登录 Token、浏览器抓包、SSH 调微信 API 等方式绕过；可读取已获授权的独立知识库备份做离线修订。

## 正式发表

所有发表由用户本人执行。本 Skill 不生成可自动执行的发布请求，不提供发表命令、计划任务或审批后自动发文逻辑。审核可以修改、退回或放弃稿件，不能自动流转为发布。
