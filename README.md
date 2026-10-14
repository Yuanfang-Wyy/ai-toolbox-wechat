# AI顺手工具箱编辑 Skill

版本：**1.3.3**。

帮助内容创作者围绕一个具体读者任务完成选题、资料整合、写作、审稿、配图策划与草稿交付。文章保留完整可复制的步骤、示例和必要条件；正文结构、标题和配图随任务调整，不套固定长文模板。

## 给 Muse 或其他网页 Agent 阅读

打开 [MUSE_GUIDE.md](MUSE_GUIDE.md)。它完整汇集主规则与七份参考规则，是本仓库的聚合阅读入口。

可以把下面的提示词和该文件的公开地址一起交给 Agent：

```text
先完整阅读这份公众号编辑规则及其中的资料，再按本次任务执行。
围绕读者要完成的具体任务整合官方资料，写清入口、示例、优缺点和费用。
文末默认保留2—3个关键官方入口，每项名称后单独显示完整HTTPS网址。
查不到或未实测的内容明确说明，不虚构体验和截图。
如果当前环境没有公众号草稿工具，就交付本地或会话中的成稿，明确尚未写入微信。
只按当前授权准备和更新草稿；正式发表由我本人在微信后台操作。
```

**读取规则不等于具备工具权限。** 本仓库没有微信凭证、连接密码、用户草稿或服务器。上传仓库不会自动配置 Muse、同步 Dot、启动本机程序或获得微信草稿接口。网页 Agent 能否读取链接、加载 Skills、执行脚本和调用已有连接，由实际运行环境决定。

## 给支持 Agent Skills 的运行时使用

加载本目录的 [SKILL.md](SKILL.md)，并保持 `references`、`assets` 和 `scripts` 的相对目录关系。例如：

> 使用 $ai-toolbox-wechat，整合这些资料，围绕具体任务写清步骤、示例、优缺点及费用，安排必要配图。按本次授权保存草稿，正式发表由我本人审核操作。

已有同名 Skill 时先比较与备份，再按运行时支持的安装方式处理。公开源码不会自动覆盖已有配置，也不自动安装依赖。

## 离线检查脚本

两份脚本只用 Python 标准库，需要 **Python 3.9 或更新版本**。在 Skill 根目录运行：

```bash
python3 scripts/preview_cover.py --image assets/cover-layout.svg --output cover-review.html
python3 scripts/preflight.py check --packet packet.json --content-only
```

- `preview_cover.py`：生成自包含的本地封面裁切预览，不改原图、不做 OCR、不上传。输出文件已有时不会覆盖。
- `preflight.py`：检查文章交接包，或准备固定请求参数；默认离线。只有显式使用 `--verify-media` 时才读取正文中的公开 HTTPS 图片，核验 MIME、签名及大小。
- 脚本不生成正文，不读取凭证，不提交或发表草稿。结构检查不等于事实校验、真实流程跑通或微信手机验收。

`assets/article-packet.json` 是交接包模板，使用前需要填写，并准备它引用的正文文件。示例 SVG 是说明图模板，不是软件实测截图。

## 完整文件

除本说明和 Muse 阅读文档外，Skill 包含 14 个源码/规则文件：

| 目录 | 文件 | 用途 |
|---|---|---|
| 根目录 | `SKILL.md` | 主规则与按任务加载指引 |
| `agents` | `openai.yaml` | 支持该元数据的运行时显示说明 |
| `references` | `editorial.md` | 选题、写作、事实、篇幅与可见网址规则 |
| `references` | `collaboration.md` | 多 Agent 分工、交接和去重 |
| `references` | `visual.md` | 正文排版、图文策划和封面标准 |
| `references` | `visual-production.md` | 逻辑图与封面制作、裁切核查 |
| `references` | `delivery.md` | 只存草稿、先读后改和错误恢复 |
| `references` | `feedback.md` | 基于真实反馈改进文章 |
| `references` | `provenance.md` | 参考来源与独立组合说明 |
| `assets` | `article-packet.json` | 文章交接模板 |
| `assets` | `cover-layout.svg` | 封面示例版式 |
| `assets` | `workflow-example.svg` | 流程示意示例 |
| `scripts` | `preflight.py` | 离线交接预检与参数准备 |
| `scripts` | `preview_cover.py` | 离线封面预览 |

## 草稿与发表边界

只使用当前运行环境已有且获授权的草稿连接，先发现实际工具 schema。当前规则适配 `connection_status`、`list_drafts`、`read_draft`、`create_draft`、`update_draft`；不能因为读到这些名称就声称工具可调用。

正式发表、群发和定时发表由用户本人在微信后台审核后操作。当前连接没有自定义封面、HTML 或主题参数；本地封面和预览不能视为微信已经更新。资料来源、图片来源与传输条件分别核查，默认不新增模型 API、付费服务、自动同步或发表权限。

参考来源见 [references/provenance.md](references/provenance.md)。本仓库未新增或推定任何第三方材料、模型或声音的授权；使用时仍须核查相应条件。
