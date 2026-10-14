# 来源与组合说明

此 Skill 根据用户为《AI顺手工具箱》提供的账号定位、多 Agent 协作要求、只存草稿且本人审核发表的边界及本次草稿备份核查独立编写。

参考三份项目的功能设计，未复制它们的代码、主题、提示词或 Skill 正文：

- [iamzifei/wechat-article-publisher-skill](https://github.com/iamzifei/wechat-article-publisher-skill)：参考“写入草稿、用户最终发表”的边界；不使用其第三方授权服务或密钥打印示例。
- [aiworkskills/wechat-article-skills](https://github.com/aiworkskills/wechat-article-skills)：参考选题、写作、审稿、排版、图片、交付的分工；不保留固定九段、金句配额或正式发表模块。
- [geekjourneyx/md2wechat-skill](https://github.com/geekjourneyx/md2wechat-skill)：参考检查、预览和副作用分离的做法；未打包其受限制的主题/布局/提示词，不依赖付费 API。

1.1.0 根据用户要求加入适应性写作、实际成果核验、统筹去重与反馈复盘。写作组织参考已研究的公开样本：[歸藏的工具流程文章](https://mp.weixin.qq.com/s/tmmtyT42RgIlwbDuD541CQ)、[少数派 OCR 同任务比较](https://sspai.com/post/93516)、[新榜微信 2024 复盘](https://xk.newrank.cn/help/z/AF5E585410CB0F0D503939E1FAAB2653)。只参考成果展示、操作组织与证据区分，不复制原文，也不把历史阅读表现归因于某种写作公式。

采用用户现有“AI顺手工具箱”草稿连接。服务源码约束核对日期：2026-10-11；仅接受公开 HTTPS 正文图、最多 15 张、单图 1,000,000 字节以内、实际 PNG/JPEG。没有最低图数或仅官方图限制。运行连接与额度状态须在获授权交付时检查，旧状态不证明当前可用；知识库备份不能替代 live snapshot。

自写脚本只负责交接包预检、可选公开图片读取与固定请求参数，不读取凭证，不生成正文，不提交或发表。

1.3.0 经用户同意，独立吸收 [SpaceZephyr/creator-buddy 的 gzh-Skills](https://github.com/SpaceZephyr/creator-buddy/tree/main/gzh-Skills) 中的材料状态路由、任务主线整合、标题兑现核查、逻辑关系图和封面裁切预览方法；未复制其 Skill 正文、代码、主题或素材。保留本号橙色米白风格与现有四种写法，不加入强制采访/确认、作者“我认为”配额、固定结尾或爆款效果承诺。

未接入其爆款查询与第三方出图 API，不改变云端投递能力。新增自写离线 `preview_cover.py` 与示意 SVG，仅生成本地核查成果；不上传、不识别文字、不更新微信封面。第三方仓库的宣传、语料统计和截图不是本号文章的事实证据。

1.2.0 根据用户提供的四张帖子截图吸收发现感、具体收益、旧麻烦与结果图片的开头组织；仅借鉴写法，不复制帖子，也不采信其中项目数量、免费、性能或资源权属宣称。加入图文策划、无图取舍与预览实际配图检查，保持结构和图片数量自适应。

1.3.1 根据用户2026-10-13提供的AquaType、KiwiDesk、Pippa和RainDesktop截图，调整为单工具标题优先说明名称与具体用途或特色；正文默认比以往同类长稿减少约三分之一。只借鉴标题与表达组织，不复制帖子或采信产品能力、免费、离线等宣称。保留自适应结构、完整可复制成果、必要前提、配图解释与仅存草稿的边界。

1.3.3 根据用户转来的 Muse 实战反馈及本机代码核查，将内容与图片预检独立汇总，补充 GIF 静态关键帧、清单成果声明、逻辑能力映射、缺少快照的分类及额度恢复后的串行处理。不把 approved 视为通用更新锁，不把项目 Markdown 当成微信保存证据；离线模拟验证不代表 Foresight 原稿或微信真实投递已验收。
