---
name: wechat-draft-delivery
description: 通过《AI顺手工具箱》已有授权连接串行创建、更新或核查公众号草稿，执行预检、固定请求、快照比较与回执核验；只处理草稿，不发表或绕过接口限制。
metadata:
  owner: wangyuyang
  version: "2.3.0"
---

# 公众号草稿交付

作为当前账号唯一微信写入入口，接收已经过内容与图片检查的明确版本。其他研究、写作、视觉或审稿 Agent 通过交接包提交，不分别向微信写入。

## 伴随依赖与共享规范

本 Skill 必须与 [ai-toolbox-wechat](../ai-toolbox-wechat/SKILL.md) 安装为同级目录。先读 [统一台账与核验口径](../ai-toolbox-wechat/references/workflow.md) 与 [草稿交付](../ai-toolbox-wechat/references/delivery.md)；交接字段和图片限制分别见 [协作约定](../ai-toolbox-wechat/references/collaboration.md)、[视觉标准](../ai-toolbox-wechat/references/visual.md)。脚本和 schema 仍以总入口为准，不在此复制。

缺少依赖、台账访问或已授权连接时，指出受影响环节并保留本地交付包，不假装可以独立投递。规则可读不代表工具可调用；不新增微信服务、读取凭证、安装依赖或调用正文模型 API。

## 授权与准备

- 先确认当前任务已授权创建或更新草稿。查看、盘点、审稿和连接检查只读；不能因加载 Skill 自动上传。正式发表、群发和定时发表均交用户本人在后台操作。
- 按现有 schema 发现八项逻辑能力：状态、草稿列表/读取/创建/更新，以及云台账列表/读取/合并准备字段，确认 `publishing_enabled=false`。能力或发表边界不明时暂停写入，继续本地检查。
- 提交前按 [内容目录](../ai-toolbox-wechat/references/content-registry.md) 再查当前及history，核对认领owner、revision和同工具/同任务是否有新增；已保存或在写的稿件不能因改标题另建。
- 查同一云台账与原任务，确认 `article_key`、正文指纹、审过的版本和原 `article_id`；项目索引不是完整微信草稿箱。更新必须先读取有效远端绑定及最新 `expected_snapshot`，不根据 `approved` 字段猜测可否更新。
- 沿用 `packet.json` 运行总入口 `scripts/preflight.py` 的 `check` 和必要的 `prepare --verify-media`。固定 `request_id`、请求参数与指纹，冻结交付版本，并以当前云台账 revision 保存 request_id、payload_sha256、content_sha256 与 prepared；prepared 不是微信成功回执。同一请求不得替换内容，也不覆盖已存在的不同参数文件。

## 串行写入与核验

按照共享交付规则串行处理当前账号，每篇先核对结果再开始下一篇。只把已获授权且预检通过的参数交给现有连接；草稿创建之后的修订沿用原 `article_id` 更新，不能因读回受限重建一篇。

核验口径由共享流程维护，记录证据与文章版本的关联：

- 明确对应本次请求的创建/更新成功证据可确认保存；单纯本地成稿、参数已准备、索引或 `approved` 不能确认微信保存。
- 本次成功回执的 `verified=true` 若明确表示服务端保存后已读取微信并校验正文，即可作为 `draft_verified` 的服务端证据，不强制 Agent 再取微信全文。通过授权连接取得正文与本次提交一致的直接证据也是有效路径。
- 项目 `read_draft.markdown`、相同远端标题、图片数或快照变化本身不足以证明正文核验。缺少有效证据时分别报告“保存已确认”和“微信正文未核验”，不一律撤销历史成功回执。
- 手机预览与本人审核各自记录；服务端核验通过不能替代排版检查或本人发表决定。

## 停止与恢复

`45009` 停止本账号后续微信 API；`uncertain`、`submitting`、超时、快照冲突及 `remote_draft_changed` 均按共享规则保留原请求、查明结果，不换请求号盲重发，不伪造快照或强写数据库。只读项目记录不能证明微信额度恢复。

恢复使用 [交付规则](../ai-toolbox-wechat/references/delivery.md) 的串行流程：先核对原任务，只对确认允许重试的请求沿用原号和冻结参数；再次额度错误或结果不明时停止受影响处理。实际接口限制未查清前，不把所有 `approved` 草稿说成只能后台修改。

真实保存回执由云端服务自动录入台账；客户端保留原始回执，核对 `ledger_sync.status=recorded` 后再读同一条目。`ledger_sync=pending` 时先查原 article_id/request_id 和云记录，不能 PUT receipt 或改成功状态，更不能换 ID 重建；按共享交付规则补记。公开仓库只放规则和匿名示例。分别报告内容审稿、图片准备、保存、服务端核验、手机预览和待本人审核，不把某一项通过概括成全部完成。
