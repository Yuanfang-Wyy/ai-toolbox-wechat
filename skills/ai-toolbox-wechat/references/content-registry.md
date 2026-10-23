# 云端内容目录与开写认领

## 一个地方保存全部内容记录

唯一权威目录是已有私有云台账 `https://www.yuanfangwyy.xyz/api/drafts/v1/workflow`，与草稿服务使用原有授权。Muse、Dot、Codex 都检查这里；Mac 关机后仍可读写。公开 GitHub 只保存规则和匿名示例，不放真实目录、稿件、回执、认领信息或凭证；本机导出是带采集时间的只读证据，不是第二主库。

目录包含已知选题、已写稿件、交付记录和历史版本。微信后台发表、删除或改名，不会使旧题变成新题；不能因 `delivery=not_submitted`、缺网址、任务写“待核对原文任务”或远端不可读，就认定没有写过。项目迁移覆盖范围仍按 `index_coverage` 报告，不把本目录称为微信全历史实况。

## 两次查重，先认领再开写

1. **选题前**：用现有 `GET /workflow?limit=50&offset=0` 分页至覆盖 total，比较当前记录和全部 `history`。同时查官方工具标识、来源网址、中文/英文名及曾用名；不能只搜索最终标题。来源相同或工具命中时默认避开批量新写，先判断是否应修原稿。未查完、目录变化导致覆盖不确定或连接中断，只交离线候选，不认领、不投递。
2. 判断“读者拿什么输入、完成什么动作、带走什么结果”是否相同。同工具改标题、换译名、换模型、重新讲相同安装步骤不算新题；不同工具重复同一成果也要比较。只有明确不同任务或有实质新证据，才说明区别与已有 article_key，交统筹/Muse审阅。模型或脚本的字符串匹配不能代替语义判断。
3. **零记录的新工具**才生成工具级确定性 key。首选官方 GitHub 仓库，规范工具 ID 如 `github:owner/repo`（小写、去.git/tree/blob等后缀）；无官方仓库时用官方产品入口 `web:host/必要产品路径`。官网、仓库、曾用名的对应关系必须核实。key 为 `topic:` 加工具 ID 的完整 SHA-256；不用标题、中文任务描述或日期的哈希。工具若已以 legacy:/request:/其他格式存在，保留原 key，不为新规范创建第二身份。
4. 开写前 GET 确认新 key 不存在，随后用 `PUT /workflow/{key}`、`expected_revision=0` 写真实 title、task、owner、source_urls、topic_record。成功后读回，核对 owner、revision 与认领信息，再开始成稿。**409 停下来读回，不能换 key、换日期或抢占 owner。**这是防同一规范 key 同时认领的事务护栏；不承诺自动消除所有语义重复。
5. **交付前**再分页查一次，比较认领后是否出现同工具/同任务条目，并 GET 本条检查 owner、revision、正文版本。出现另一写作者、未知变动或待确认请求，暂停该稿并协商；同一稿有 article_id 就用原身份更新，不重新 create。规则升级不授权重放旧 STOP 或旧失败批次。

历史记录工具可辨但任务不明时，按“已出现、待人工核对”处理；不要先重写再补查。已写且保存、研究中、写作中、曾否决都纳入检查。相似不等于一定重复，输出命中依据和区别，不自动删除、合并历史稿或改其成功状态。

## 只使用现有可写字段

`aliases`、`receipt`、`history`、`revision`、`published` 不是客户端可写字段。工具标识与别名放在 `topic_record.editorial_note` 的 JSON 字符串中；官方入口同时写进 `source_urls`。沿用已有 topic_record 白名单，不向 schema 编造新顶层字段。

元数据示例（说明用，不是真实认领）：

```json
{
  "registry_version": 1,
  "tool_id": "github:example-org/example-tool",
  "aliases": ["Example Tool", "示例工具"],
  "related_article_keys": [],
  "claim_started_at": "2026-10-23T08:00:00+00:00",
  "claim_token": "example-job-correlation-id"
}
```

这里的 claim_token 只是任务关联号，不是权限或登录凭据。`owner` 用可追踪的 Agent/任务名，不共用含糊的“editor”来冒充同一写作者。外部只登记准备和实际审稿证据，不 PUT 保存回执或成功状态。

### 同工具合法分题

先列出所比较的原 article_key，说明输入、动作、成果或新证据的实质差异，得到本轮统筹/审稿确认后再认领。分题 key 统一为 `topic:<工具ID的SHA256>:case:<经协作确认的ASCII任务短名>`；任务短名一经确认不随标题改写。`topic_record.editorial_note` 同时保存 related_article_keys、case_id、split_reason 与审阅依据。不能因工具级 key 冲突自行走分题路径；普通自动选题默认跳过已覆盖工具，优先找未写过的新工具。

### 中断认领的接管

没有自动过期或“超时即抢占”。先核对原 owner 的任务确已结束/主动交接或本人明确授权接管，保留原 owner、认领时间与交接依据到现有编辑备注；GET 最新 revision 后只合并本次 owner/备注。原 article_key、article_id、请求与证据保留。owner 不明或任务状态无法核实时等待统筹裁定，不另建同题。

## 标准库检查与认领脚本

`scripts/content_registry.py` 只调用现有状态和云台账，不调用微信、不生成正文、不写本地生产目录。`check` 只读，`claim` 在本次已授权写作时显式认领。使用现有安全存储中的 REST 凭据文件，或已配置的 `WECHAT_DRAFTS_REST_KEY`，不把值写到命令行/提示词/公开包。没有既有授权不去找新密钥。

```bash
python3 scripts/content_registry.py check --source-url https://github.com/example-org/example-tool --tool-name 'Example Tool' --alias '示例工具' --task '将三条反馈整理成待追问清单' --credential-file /path/to/existing-private-rest-key

python3 scripts/content_registry.py claim --source-url https://github.com/example-org/example-tool --tool-name 'Example Tool' --alias '示例工具' --task '将三条反馈整理成待追问清单' --title 'Example Tool - 整理三条反馈再讨论排期' --owner 'codex:existing-job' --credential-file /path/to/existing-private-rest-key
```

输出 `existing_tool_review_required` 时列出当前/历史命中与原身份，不得自动成稿；输出 `candidate_only` 只表示在本次可读目录未匹配，不代表已通过语义审稿。认领成功才返回 `claimed`；重复运行已认领任务应核对现有记录，不用另一个认领号。脚本不提供分题绕过参数，也不自动接管。

Muse 没有 Python 执行能力时，按同一协议使用现有 REST/CLI：全分页读→查当前及history→核对工具标识与读者任务→GET原key→PUT准备字段及revision→读回。不得声称运行过本地脚本。给新题的认领请求只传以下允许字段；editorial_note 中的内层JSON必须作为字符串传递：

```json
{
  "expected_revision": 0,
  "record": {
    "title": "Example Tool - 整理三条反馈再讨论排期",
    "task": "将三条反馈整理成待追问清单",
    "owner": "muse:existing-job",
    "source_urls": ["https://github.com/example-org/example-tool"],
    "topic_record": {
      "decision": "write",
      "editorial_note": "{\"registry_version\":1,\"tool_id\":\"github:example-org/example-tool\",\"aliases\":[\"Example Tool\",\"示例工具\"]}"
    }
  }
}
```

这只是请求格式，示例并未被保存，也不允许在生产台账里放测试文章。并发测试使用隔离台账或受控假客户端；真实验证优先用已有稿件证明换标题仍会命中，不为验收制造新微信草稿。
