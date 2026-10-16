# 统一流程、台账与核验口径

这是总入口与三个专项 Skill 共用的流程契约。编辑细则、视觉细则和接口操作仍在各自参考文件；不要复制并维护第二套状态规则。

## 同一文章与同一台账

- 统筹方按“读者要完成的任务 + 工具官方标识”分配稳定 `article_key`。题目改名不换标识；同一工具的不同任务可分别成题，不同工具解决同一任务要先比较角度是否重复。
- 查重覆盖已发表、已有草稿、待研究和已否决；同时看工具、任务和场景，不只做标题精确匹配。已否决记录保留理由，出现新版本或新证据可以重新评估。
- 本机总入口若有私有 `runtime.json`，先读取其中 ledger_path；该配置不进入公开包，也不代表其他机器已共享。没有此配置时由当前任务交接提供同一台账位置。
- 总控先确定当前任务使用的私有台账路径，所有 Agent 的交接均引用该路径或同一授权服务记录。优先复用已有台账；需要初始化时由总控指定，不能每个专项静默各建一份。目录不公开、凭证不入包。
- 台账关联 `article_key`、负责人、标题与任务、`article_id`、正文版本/指纹、`delivery_key`、`request_id`、各环节状态及证据/错误。版本指纹为 UTF-8 `title + "\n" + markdown` 的 SHA-256；请求 payload 指纹另行保存。保留历史回执，不用新索引覆盖已确认事实。
- 云端项目索引用于对账和定位已有 `article_id`，不是微信完整草稿列表。没有条目、远端读取失败或 `has_wechat_draft=false` 都不能单独证明微信没有稿件，也不授权重新创建。

索引覆盖范围写明来源、采集时间与是否局部；例如最近 50 条只能标为 partial，不能称全历史。`index_observation` 保留项目状态与 `has_wechat_draft` 观察值，不自动映射为内容已审、正文已核验或本人审核。

现有 `packet.json` 继续作为交接包，不为拆分要求另造一组必填字段。正文版本指纹由台账脚本计算，请求参数与 payload 指纹由现有预检生成；台账脚本只组织记录和证据，不获得外部写入权限，也不证明网页、图片或草稿已经验证。

## 分开记录结果

| 维度 | 通过的依据 | 不足以通过的依据 |
|---|---|---|
| 内容审核 | 审稿者核对当前版事实、标题承诺、可照做的成果及必要条件 | 文件存在、已生成、仅预检通过 |
| 媒体检查 | 当前稿所引用图片的格式/签名/大小检查，加图源、图注与可读性人工检查；无图说明取舍 | 有图位、旧版图检、上传数量相同 |
| 远端交付 | 与本次请求/版本关联的 created/updated/existing 回执，或独立且明确关联的后端成功凭据 | prepared、项目索引、仅本地文件或 Markdown 更新 |
| 远端正文核验 | 与本次请求/版本关联的保存回执含 verified=true，或授权读取取得远端正文与预期一致的证据 | 单独 succeeded、approved、remote_title、图片数或 snapshot 变化 |
| 手机预览 | 确实打开本次草稿手机预览，检查正文、图片、字号、留白和裁切并记录结果 | 服务端 verified=true、HTML 预览或结构检查 |
| 本人审核 | 用户本人明确审核该版本 | Agent 审稿、项目 approved、自动流转 |

台账分开保存：`editorial`（pending/reviewed/blocked）、`media`（pending/verified/blocked/not_required）、`delivery`（not_submitted/prepared/created/updated/existing/uncertain/quota_blocked/conflict）、`remote_verification`（pending/verified/failed）、`mobile_preview`（pending/passed/needs_fix）及 `owner_review`（pending/approved/rejected）。后两项只能按真实预览或本人决定更新，不由本地预检或 Agent 审稿推定。

服务端 `verified=true` 路径足以确认远端正文核验，无须把微信全文再暴露给写作 Agent。当前已检查服务会比较正文文本、标题、封面与图片数量；不验证 CSS、像素级显示、图片内容或手机排版。回执字段与当前接口能力仍应实际核对，不能因为历史服务曾验证就给无标记的成功结果补写 verified。

`draft_created` 表示已确认保存；`draft_verified` 表示保存且远端正文核验有证据；`awaiting_owner_review` 表示仍待本人审核。这些交付汇总标签不代替上表各维度。草稿已保存而正文未核验时保留两项状态和原 `article_id`，不重复创建。任何状态都不触发发表。

## 版本与依赖

正文或标题修改后登记新版本，内容审核、媒体、远端正文核验回到 pending。旧版内容审核不能标为新版通过；旧版媒体和回执留在旧版本下，新版需逐项确认适用范围。正文图片及用途均未变时可以明确引用原媒体检查证据，但不能无说明地继承旧通过状态；远端回执必须对应本次实际提交的版本。手机预览和本人审核也注明版本。保留已有远端身份与历史交付状态，修订进入 update，不重新 create。

内容阻塞只暂停受影响的内容交付，媒体阻塞只暂停需要这些图的提交。微信连接、额度或快照问题不阻止继续已授权的离线研究、写稿和图像准备；不能把这些本地成果报成已保存微信。

## 唯一交付入口与工具

研究、写作、视觉和审稿 Agent 交 packet 与证据给总控；只有当前账号指定交付者创建/更新微信草稿，串行操作。跨机器或 Muse 拿不到同一私有台账、回执或工具时，交 packet 等总控对账，不自建第二份权威台账、不直接重复 create。离线演练只写隔离的试跑台账，明确标为模拟，不并入生产记录。

总入口的标准库脚本 `scripts/workflow_ledger.py` 供总控离线操作，使用前查看实际 `--help`：

```bash
python3 scripts/workflow_ledger.py import-index --ledger /private/path/ledger.json --input /private/path/project-index.json
python3 scripts/workflow_ledger.py record-topic --ledger /private/path/ledger.json --packet /path/to/packet.json --decision research
python3 scripts/workflow_ledger.py reconcile --ledger /private/path/ledger.json --packet /path/to/packet.json
python3 scripts/workflow_ledger.py record-review --ledger /private/path/ledger.json --packet /path/to/packet.json --review /path/to/review.json
python3 scripts/workflow_ledger.py record-receipt --ledger /private/path/ledger.json --packet /path/to/packet.json --request /path/to/request.json --receipt /path/to/receipt.json
python3 scripts/workflow_ledger.py list --ledger /private/path/ledger.json
```

`import-index` 只导入项目线索；`record-topic` 在尚无正文时记录写作、待研究、暂缓或否决判断（write/research/defer/reject），复用 packet 的 article_key、title、topic_brief 和来源；`reconcile` 登记、比对任务/身份/版本，不投递；`record-review` 记录已完成的 Agent 审核，review 须绑定 content_sha256，仅更新编辑和媒体状态；`record-receipt` 核对固定请求及已取得的回执。脚本不会联网、创建微信草稿或替 Agent/本人审稿，不标记本人审批。不能把示例私有路径作为默认多机共享目录。记录回执时，原始调用若未在响应内回显 request_id，由交付者依据同一工具调用记录补充关联；不猜测请求号，不改原始响应，并在内部证据说明关联方式。record-review 的 evidence 填实际检查记录位置。台账脚本按单写者使用，本地覆盖前检测变化并保留修订备份，不提供跨主机锁或共享服务。详细参数以随包脚本为准。
