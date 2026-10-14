# 音寻 · Sound Explorer

探索音乐风格的地图游戏原型。当前优先验证 **选子图 → 精确落点 → 距离反馈**，无需音频、API 凭证、GPU 或数据库。灵感来自 [Every Noise at Once](https://everynoise.com/engenremap.html)。

## 立即运行

需要 Python 3.10+，地图演示仅使用 Python 标准库与浏览器原生 JavaScript。

```sh
git clone https://github.com/Master070806/yinxun.git
cd yinxun
python serve.py --port 8780
```

打开 **http://127.0.0.1:8780/map.html**。如端口被占用，修改 `--port`。不要直接双击 HTML，页面需要 HTTP 加载 JSON。此服务仅供本地开发，不是生产部署方案。

## 当前进度 · 2026-10-15

| 模块 | 状态 |
| --- | --- |
| 5,453 个风格的坐标地图 | 已实现，支持搜索、缩放和平移 |
| 四选一子图与精确落点 | 已实现，以文字目标代替音频 |
| XY 点距离、区域最近距离、子图 Hausdorff 对照 | 已实现；Hausdorff 暂不判分 |
| 24 首音乐与整曲 CLAP 分析 | 保留为早期对照实验 |
| 网站原始邻居抓取数据 | 已收到并本地统计，尚未接入界面 |
| 100 首在线题库 | 尚未采集；暂不阻塞无音频玩法 |
| 用户系统、排行榜、线上服务 | 未实现 |

当前子图由 **XY 最近 20 个邻居**生成，不是网站原有邻居。RGB 只用于配色，距离使用原始 XY 坐标；缩放保持等比例。现成地图的距离不等于客观音乐差异。

原始抓取关系与 XY 最近邻并不等价：同一份 6,291 节点快照的本地比较，平均每个节点的两组邻居只重合约 2.08 个。完整背景和限制见 [进度与下一步](docs/STATUS.md)。

## 协作入口

- [贡献指南与分支规则](CONTRIBUTING.md)
- [进度、数据结论与待办](docs/STATUS.md)
- [第三方数据与许可](DATA_SOURCES.md)
- [早期听音实验](docs/audio-experiment.md)

开发前在 Issue 中认领一个明确任务，避免两个人同时修改同一模块。功能分支通过 PR 合入 main；不要提交音频、模型、原始网页包、密钥或个人环境信息。

## 项目结构

```text
web/map.html、map.js、map.css  地图演示
web/map-data.json             5,453 个风格坐标（CC BY-SA 4.0）
web/index.html、app.js        早期听音原型
web/catalog.json             24 首音乐的预计算分数
serve.py                     本地开发服务
build_catalog.py             下载与整曲 CLAP 分析
experiment.py                最初三个样例实验
scripts/check_project.py     无网络基础检查
```

## 验证

```sh
python scripts/check_project.py
node --check web/map.js
node --check web/app.js
```

Node 仅用于开发时语法检查，不是试玩所需依赖。GitHub Actions 在 push / PR 时运行上述检查。涉及界面、距离算法或数据变更时，仍需按贡献指南完成对应人工验收，不能仅以 CI 通过代替试玩。

## 许可

项目代码采用 [MIT](LICENSE)。第三方地图数据、歌曲、模型权重分别遵循自己的许可，**不随代码变成 MIT**。详见 [DATA_SOURCES.md](DATA_SOURCES.md)。
