# AI Growth Agent — 项目架构分析报告

> 分析日期：2026-08-19
> 分析对象：`ai-growth-agent` 仓库（当前版本 V0.2.1）

---

## 1. 当前技术栈

### 1.1 前端（`frontend/`）

| 技术 | 用途 |
|---|---|
| **React 18 + TypeScript** | 单页应用，表单输入 Growth Brief、展示结构化用户洞察 |
| **Vite** | 构建工具（`vite.config.ts`） |
| **Cloudflare Workers + Vite 插件** | 边缘函数运行时，作为 API 网关与降级层（`frontend/worker/index.ts`） |
| **@openai/sites-vite-plugin** | 静态站点部署 |

前端结构极简：`App.tsx`（单组件）、`api.ts`（fetch 封装）、`types.ts`（与后端 Pydantic schema 对应的 TS 类型）、`styles.css`。**无组件库、无路由、无状态管理**。

### 1.2 后端（`backend/`）

| 技术 | 用途 |
|---|---|
| **Python + FastAPI** | 主 API 服务（`app/main.py`） |
| **Pydantic v2** | 严格数据契约：请求校验、响应 schema、`model_validator` 交叉约束 |
| **Pydantic Settings** | 环境配置（`app/config.py`） |
| **pytest + TestClient** | 接口测试（`tests/test_api.py`） |

模块划分清晰：
- `models.py` — 领域模型，V0.1 / V0.2 双版本 schema
- `services.py` — 业务逻辑（Dify 调用 / mock 回退）
- `quality.py` — 输出质量校验引擎
- `protection.py` — 请求保护 / 限流
- `main.py` — 路由与装配

### 1.3 AI 编排（`dify/`）

- **Dify** 低代码工作流平台（`workflow-v0.2.yml` DSL）
- 两阶段 LLM 节点：`01-context-interpreter` → `02-user-insight`
- JSON Schema 严格约束结构化输出（`schemas/`）
- 提示词工程（`prompts/`）+ 自动构建脚本（`build_workflow_v02.py`）

### 1.4 评估体系（`evals/`）

- **Python 校验脚本** `check_outputs.py` — 离线契约与声明风险检查（复用后端 Pydantic 模型）
- 12 个固定测试场景（`cases.json`）、五维评分量表（`rubric.md`）
- 已提交的 V0.1 基线（`results/baseline-v0.1/`）：原始输出、运行元数据、报告、评分卡

---

## 2. 项目功能

**核心定位**：输入一份"增长简报"（产品 / 市场 / 受众 / 业务目标），由 AI 生成**结构化、带证据标注、可直接用于用户调研的用户洞察报告**。

### 2.1 主要业务流程

```
用户输入 Growth Brief
   └─▶ FastAPI /api/analyze
         └─▶ Cloudflare Worker（生产网关）
               ├─ 校验 Brief（枚举业务目标）
               ├─ 命中缓存？→ 直接返回
               ├─ 限流 / 配额检查
               ├─ 调用 Dify Workflow（90s 超时）
               │    ├─ 节点1：上下文解读 → 结构化 Context
               │    └─ 节点2：生成用户洞察 → 结构化 UserInsight
               ├─ normalizeClaimLanguage（自动改写高风险措辞为假设）
               ├─ evaluateQuality（4 项契约检查）
               └─ 失败 → mock 降级（带 X-AI-Fallback 头）
```

### 2.2 核心功能模块

1. **结构化用户洞察生成** — JTBD（functional/emotional/social 三维度）、痛点、购买动机、采用障碍、典型场景
2. **证据治理** — 每条洞察标注证据基础（brief 显式 / 上下文推断 / 行为假设）+ 置信度 + 验证状态
3. **质量护栏引擎** — 4 项自动契约检查（结构契约、证据契约、研究问题模式、声明措辞），可自动改写高风险声明
4. **接口版本化** — `/api/analyze`、`/api/v1/insights`、`/api/v2/insights` 并存
5. **生产降级策略** — 未配置 Dify / 上游失败 / 超时 / 配额耗尽时回退 mock 响应
6. **评估闭环** — 固定用例 → 运行 → 契约检查 → 盲评 → 回归集

### 2.3 亮点设计（工程价值点）

- **严格的数据契约**：Pydantic 用 `model_validator` 强制交叉约束（如"推断证据必须 `needs_validation`"、"high confidence 只允许 explicit_brief"）
- **双版本演进**：V0.1 → V0.2 通过新增 `quality_review`、`decision_relevance`、`evidence` 字段平滑升级，评估脚本自动区分版本
- **研究问题规范化**：强制"最近一次行为/现状工作流/证据门槛"的行为优先提问模式
- **诚实的数据完整性规则**：评估文档明确"禁止虚构测试结果"、"保留失败用例作为回归输入"

---

## 3. 可优化方向

### 3.1 架构与技术层面

1. **后端双栈冗余**：同时存在 FastAPI 后端 + Cloudflare Worker 网关，职责重叠。FastAPI 目前仅用于测试/开发/评估，生产流量走 Worker。应明确"单一权威实现"，避免业务逻辑在 Python 与 TS 各写一份（`quality.py` 与 `worker/index.ts` 有重复的校验逻辑）。
2. **Worker 内存态限流不可靠**：`visitorUsage`、`resultCache` 存在进程内 `Map`，在无状态边缘运行时每次请求可能命中不同实例，导致限流/缓存失效。建议改用 KV / Durable Objects。
3. **缺少 CI/CD**：无 `.github/workflows`，测试（pytest + worker 测试）未接入 CI。应补充 lint、类型检查、单测、契约验证的自动化流水线。
4. **缺少 e2e / 集成测试**：Dify 上游调用、降级路径、缓存命中未做自动化集成测试。
5. **后端模块未全覆盖测试**：`quality.py`、`services.py`、`protection.py` 的核心逻辑缺少独立单元测试。
6. **前端过于单薄**：无组件拆分、无加载/错误状态管理（报告提到需"可见的进度状态"但未实现）、无可访问性测试。

### 3.2 AI / 产品层面（依据评估报告 V0.1）

1. **声明安全是主要短板**：8/12 用例含需要人工复核的频度/因果措辞，`unsupported-claim safety` 仅 2.67/5。V0.2 的自动改写是缓解，但需评估其有效性。
2. **稀疏简报产生泛化填充**：应动态调整输出体量/置信度。
3. **延迟长尾**：中位 21.5s、最慢 65.1s，需超时消息、重试遥测、流式输出。
4. **二级动机稀释决策**：应按置信度与决策相关性排序而非固定填满 5 个槽位。

---

## 4. 如何提升 GitHub 求职展示价值

### 4.1 当前已具备的加分项（保持并突出）

- **完整的产品化闭环**：提示词 → 工作流 → API → 前端 → 评估，远超一般 demo
- **诚实的评估证据**：提交了 V0.1 真实基线报告（含失败与限制声明），这在求职中极罕见且极具说服力
- **严格的工程纪律**：数据契约、版本兼容、降级策略、完整性规则

### 4.2 建议提升的方向（按优先级）

| 优先级 | 改进 | 求职价值 |
|---|---|---|
| **高** | 补充 README 顶部：架构图（ASCII/mermaid）、运行方式、演示 gif/截图 | 面试官 30 秒内理解项目 |
| **高** | 接入 CI（GitHub Actions）：pytest + lint + typecheck + `check_outputs.py` | 证明工程化成熟度 |
| **高** | 增加 live demo（部署后的公开 URL）或录屏演示 | 可验证性 |
| **中** | 用 Durable Objects/KV 修复限流；或明确单栈（删除 Python/TS 双实现之一） | 展示架构决策能力 |
| **中** | 写一篇深度技术文章（Medium/博客）介绍"如何用契约护栏治理 LLM 输出"，README 关联链接 | 展示思考与表达能力 |
| **中** | 增加单元测试覆盖 `quality.py` 等核心模块并展示覆盖率徽章 | 工程习惯 |
| **低** | 前端补充加载状态、错误边界、移动端适配 | 产品完成度 |

### 4.3 README 建议结构

```
# AI Growth Agent
一句话定位 + 架构图（mermaid）
## ✨ 亮点（3 个 bullet：契约治理 / 评估闭环 / 降级策略）
## 🚀 快速开始（本地 mock 运行 3 条命令）
## 🧭 架构（前后端 + Dify + 评估）
## 📊 评估结果（V0.1 报告关键数据 + 诚实声明）
## 🧪 测试（pytest + CI badge）
## 🗺️ 路线图 / 已知限制
## 📄 授权
```

### 4.4 差异化叙事建议

这个项目最强的差异化是**"用软件工程方法论约束 LLM 输出的不确定性与幻觉风险"**。求职表述建议围绕三个关键词：

1. **可治理** — 不是"AI 生成文本"，而是"带证据标注、声明安全、可审计的结构化输出"
2. **可评估** — 有真实基线数据，诚实报告失败，形成回归闭环
3. **可演进** — 版本化契约、平滑升级、双栈降级策略

---

## 附录：关键指标摘要（V0.1 基线）

| 指标 | 值 |
|---|---|
| 固定用例 | 12 |
| 契约通过率 | 12/12 (100%) |
| 中位延迟 | 21.5s |
| 平均 token/用例 | 2,948 |
| 五维综合得分 | 3.75/5 |
| 声明安全得分 | 2.67/5（主要短板） |
