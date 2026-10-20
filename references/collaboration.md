# 多 Agent 协作与文章交接

本规则支持用户已有的多个 Agent，按任务需要使用宿主已授权的协作能力，不默认创建新聊天、自动化或长期后台进程。

文章标识、台账、版本与核验状态以 [统一流程](workflow.md) 为唯一口径。本文件只规定分工和现有 packet 交接，不另设协调 Skill 或另一套完成标准。

## 分工

- 选题 Agent：按任务和读者筛选，核对与已有草稿是否重复。
- 研究/写作 Agent：独立工作目录内收集来源并成稿；不直接调用微信写入工具。
- 审稿 Agent：核对事实、可照做程度、费用风险、图文和成稿质量。
- 编辑统筹：把关用途、证据、标题承诺和实际成果；比较同批及可访问的近期文章，消除选题和表达重复。统筹不是收齐文件即通过。
- 交付 Agent：合并通过检查的任务，作为当前账号唯一写入入口，串行创建/更新并记录回执。
- 用户本人：在微信后台审核、决定是否发表并亲自完成发表。

分工可由同一个 Agent 顺序完成，不要求为每篇都开新 Agent。审稿 Agent 判断质量，不冒充用户审核。

## 去重与工作目录

统筹方沿用同一 `article_key` 和云台账，按统一流程核对工具、任务与场景；标题不同不能自动成为新题。

每篇独立目录，其他 Agent 不改正在交付的正文；多个 Agent 不同时修改同一微信草稿。不同机器的 Agent 也必须经过同一个交付入口与云台账，不能靠各自的本地锁保证全局去重。Mac 关机后仍经已有 REST/MCP 连接工作，不依赖本机 JSON。准备记录用先读 revision 再合并的乐观并发控制；409 时重新比较，不把不同编辑者的记录覆盖掉。

先通过 list_workflow_entries 分页查同一云台账与可访问项目索引，再决定 create/update。研究、视觉、写作 Agent 不向各自新建的记录分配远端身份；拿不到同一私有台账或工具时只交包，交付者对账后再操作。公开包、Muse 聚合阅读版和 GitHub 不包含生产台账、稿件或回执。

选题、写作和视觉 Agent 只能合并获授权的准备字段、版本和实际审核证据，不可写 receipt/history/远端成功或本人批准。微信服务保存后自动记回执；交付者核对 ledger_sync，pending 时先查原ID补记，不能换号重建。

新文已创建后，任何修订都通过原 article_id 更新；同一次交付重试保持原请求号，确认上次结果后才为内容修订分配新的 delivery_key/request_id。已准备但尚未确认的请求冻结正文和参数。

每篇保留写作模式、标题推荐理由、开头切入方式与成果位置，便于统筹比较。统筹按编辑标准检查标题场景与正文是否兑现、首屏是否愿读、逐段是否有信息增量及正文是否精简；有原稿时在内部记录前后篇幅与必要保留项，不新增必填交接字段。不把模式做成固定栏目配额；局部修订只审查受影响内容。

## packet.json

交接包用 UTF-8 JSON；markdown_path 相对交接包所在目录。完整模板见 [article-packet.json](../assets/article-packet.json)。

基础字段：article_key、agent_id、title、markdown_path、source_urls、article_type、reader_result、delivery_key、action、destination、requires_owner_review、publish。`lead` 可选，是开头原文记录，不要求统一句式。

新稿使用 `packet_version=2`，另有 `writing_mode`、`topic_brief`、`deliverables`。旧包仍可检查和交付，不为升级重新写已有成稿；改写成新稿时再补齐成果记录。

- `destination` 只能是 `wechat_draft`；`publish` 必须 false；`requires_owner_review` 必须 true。
- `action` 为 create 或 update。update 还需要原 article_id 与本次 `read_draft` 返回的 expected_snapshot。
- `delivery_key` 由统筹方分配，例如 `article_key:update:r2`。同一次交付的重试保持不变；修改内容须先查明上次交付结果。
- `writing_mode` 选 tested-tutorial/documented-workflow/task-comparison/template-delivery；组合写法记录主模式即可，不限制正文结构。
- `topic_brief` 记录 audience、task、current_way、improvement、setup_cost、evidence。无统一评分；选题结论及理由用 `editorial_note` 保存。
- `deliverables` 每项有 kind（prompt/workflow/template/file）、acceptance；正文成果用 `text` 指向真实完整内容，附件用 `path` 指向包目录下真实文件。脚本只检查匹配和文件存在；可执行性、可编辑性仍需验证并记录 `validation_note`。
- `title_candidates`、`title_reason`、`opening_approach` 是内部编辑记录，按任务填写，不输出到公众号正文。
- `visual_plan` 按必要图位记录 role、purpose、asset、caption；`visual_reason` 说明无图或缺图的取舍。正文中出现的本地图片文件也应核验；已有图位并不代表图片真的进了成稿。`opening_approach` 记录本篇发现感/收益/场景切口，方便统筹检查是否又套同一种开头。
- `image_ledger` 逐图记录 url、origin（official/user-capture/self-created/licensed）、source_url、caption、rights_note。真实自制图和有许可的图可用，不能把模仿生成图写成实测截图；上传条件见视觉标准。
- `evidence_level` 写 official-docs/source-inspected/tested；tested 须附 `test_evidence` 文件路径列表（相对包目录），且文件确实存在。文件存在不能代替内容核验。

### 从正文记录实际成果

新版包的 `deliverables` 必须从正文已有的实际成果填写，不能留空，也不能只填成果名称或章节标题。有入口、输入、动作和验收的行动清单用 `kind=workflow`；供读者填写或反复使用的字段表、检查清单用 `kind=template`。不新增 `checklist` 类型，不强制“今晚做三件事”等栏目或新必填字段；正文已有完整成果时补齐交接记录，不另写重复清单。

`text` 复制正文中完整的成果原文，`acceptance` 写读者怎样核查结果，`validation_note` 如实记录已验证和未实测的范围。下面是会议待办清单的说明用示例，仅展示现有字段组织；实际使用时应与本篇正文逐字匹配，不能把示例当作处理过真实材料的证据：

```json
{
  "deliverables": [
    {
      "kind": "workflow",
      "text": "1. 从会议原文摘出待办。\n2. 为每项填写任务、责任人、截止日期和原文出处；缺信息标记待确认。\n3. 逐项对照原文核查，不补写未出现的承诺。",
      "acceptance": "每项待办都有原文出处；责任人和日期有依据，缺项明确标为待确认。",
      "validation_note": "说明用示例，未处理真实会议材料；实际交付前仍需核对正文与原始记录。"
    }
  ]
}
```

不把 API 密钥、Token、微信登录 URL 或用户私密资料加入包。

## 核验与交接

按 [统一流程](workflow.md) 分别记录内容、媒体、远端交付、正文核验、手机预览和本人审核，不用一条线性“完成”状态掩盖缺项。正文改版后旧证据留在旧版；局部改稿只补核查受影响内容，但须明确当前版复用了哪些证据。

与本次请求/版本关联的 created/updated/existing 且 verified=true 的保存回执，可以记为服务端远端正文核验，不要求写作 Agent 再取全文。服务端核验不等于手机预览或本人审核；只有 succeeded 或项目 Markdown 的稿件，分别保留保存与核验状态。具体证据与异常处理见 [交付说明](delivery.md)。


## v2.0.0 版本交接与明日任务

每次开始从公开指南重读当前版本，并在既有editorial_note记录version/commit及本篇实际遵循规则，不把聊天中的旧版本当新版本。升级只更新已有任务提示，不自动新增平行定时任务。研究/写作/视觉交给同一交付入口前，必须分别说明愿读、可用和渲染检查范围；服务端HTML机器检查、手机预览与本人审核不混写。短稿比较前后阅读字符数，含代码与图注；不要把长功能表转图片伪造精简。


## v2.1.0 批量改稿

整批由一个交付者串行写入。逐篇保留原article_id、原稿与冻结请求；已完成或结果不明的旧请求先核对，不把新版正文塞入旧request_id。按本篇工具核对主要功能概览和真实步骤，缺图/缺操作细节单列补证据，不仅批量加相同前后缀。技术、对比与模板稿保留自己的写法和有效材料。通知Muse/Dot在线重读公开commit并回报实际版本；其他Agent未确认前不声称已升级。
