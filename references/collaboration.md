# 多 Agent 协作与文章交接

本规则支持用户已有的多个 Agent，不默认创建新聊天、自动化或长期后台进程。用户明确要求并行时可使用宿主已授权的协作能力。

## 分工

- 选题 Agent：按任务和读者筛选，核对与已有草稿是否重复。
- 研究/写作 Agent：独立工作目录内收集来源并成稿；不直接调用微信写入工具。
- 审稿 Agent：核对事实、可照做程度、费用风险、图文和成稿质量。
- 编辑统筹：把关用途、证据、标题承诺和实际成果；比较同批及可访问的近期文章，消除选题和表达重复。统筹不是收齐文件即通过。
- 交付 Agent：合并通过检查的任务，作为当前账号唯一写入入口，串行创建/更新并记录回执。
- 用户本人：在微信后台审核、决定是否发表并亲自完成发表。

分工可由同一个 Agent 顺序完成，不要求为每篇都开新 Agent。审稿 Agent 判断质量，不冒充用户审核。

## 去重与工作目录

统筹方给每篇分配 `article_key`，建议“工具官方标识 + 具体任务”，例如 `joplin-project-note-retrieval`。仅标题不同但任务相同，不视为新的选题。

每篇独立目录，其他 Agent 不改正在交付的正文；多个 Agent 不同时修改同一微信草稿。不同机器的 Agent 也必须经过同一个交付入口与台账，不能靠各自的本地锁保证全局去重。

台账至少记录 article_key、负责人、article_id、正文指纹、request_id、当前状态和错误。先查台账和项目索引，再决定 create/update。索引不是完整微信草稿箱，读回失败不能宣布草稿不存在。

新文已创建后，任何修订都通过原 article_id 更新，不更换请求号把修订当另一篇新文。已准备但尚未确认的请求冻结正文和参数。

每篇保留写作模式、标题推荐理由、开头切入方式与成果位置，便于统筹比较。统筹按编辑标准检查标题能否一眼说明用途、正文是否精简；有原稿时在内部记录前后篇幅与必要保留项，不新增必填交接字段。不把模式做成固定栏目配额；局部修订只审查受影响内容。

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

不把 API 密钥、Token、微信登录 URL 或用户私密资料加入包。

## 状态

`assigned → researched → written → reviewed → prepared → draft_created → draft_verified → awaiting_owner_review`

异常分支：`blocked_content / blocked_media / quota_blocked / conflict / uncertain`。

只有直接创建成功回执，或明确关联本请求的后端成功凭据，才能进入 draft_created；只有成功读回才能进入 draft_verified。若已创建但读回受限，保留 article_id 和两项状态，不重复创建。后台 approved、review_hash、approved_hash 等字段属于内部流程，不证明本人已审阅。任何状态均不触发发表。
