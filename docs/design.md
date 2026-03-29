# autoresearch — 完整设计规范 v0.1

> 一个基于 gitagent 标准、借鉴 newtype-os 编排模式的多模型深度研究系统。
> Git 是它的数据库，Markdown 是它的接口，任何 AI Coding 工具都是它的宿主。

---

## 目录

1. [项目定位](#1-项目定位)
2. [设计哲学](#2-设计哲学)
3. [完整目录结构](#3-完整目录结构)
4. [Agent 团队设计](#4-agent-团队设计)
5. [核心文件内容规范](#5-核心文件内容规范)
6. [工作流引擎设计](#6-工作流引擎设计)
7. [CLI 接口规范](#7-cli-接口规范)
8. [跨平台适配方案](#8-跨平台适配方案)
9. [内存与状态管理](#9-内存与状态管理)
10. [技术栈选型](#10-技术栈选型)
11. [开发路线图](#11-开发路线图)

---

## 1. 项目定位

autoresearch 是一个**深度研究工具**，不是内容生产工具（那是 newtype-os 的领域）。它的核心用例是：

```text
输入：一个研究课题 / 技术问题 / 竞品分析需求
输出：一份结构化的、有引用来源的、经过事实核查的深度研究报告
```

**与 newtype-os 的区别：**

| 维度 | newtype-os | autoresearch |
|------|------------|--------------|
| 核心场景 | 内容创作（文章、新闻稿） | 深度研究（技术调研、竞品分析、学术综述） |
| 输出形式 | 可发布的文章 | 结构化研究报告 + 原始数据 |
| 上下文长度 | 适中 | 极长（需要 Gemini 级别的上下文窗口） |
| 事实密度 | 中等 | 极高，每个结论都需要来源 |
| 模型策略 | 单一模型配置 | 每个 Agent 独立选型，按特长分配 |

**与 gitagent 的关系：**
autoresearch 是一个**基于 gitagent 标准构建的完整应用**。它遵循 gitagent 的文件规范，
使用 `gitagent export` 导出后可以在 Claude Code / OpenCode / Cursor 中原生运行。

---

## 2. 设计哲学

### 2.1 三条核心原则

**原则一：Git 即数据库**
所有研究中间产物、Agent 记忆、任务状态都存储在 Git 追踪的文件中。
没有额外的数据库，没有 SQLite，没有 Redis。任何人 `git clone` 这个仓库，
就得到了完整的研究历史。

**原则二：模型各司其职**

```text
规划  → Claude Opus（推理能力最强，负责任务拆解和质量把控）
搜索  → Claude Sonnet / GPT-4o（工具调用稳定，成本均衡）
阅读  → Gemini 2.0 Pro（200万 token 上下文，整本书都能读完）
核查  → Claude Sonnet（批判性思维强，擅长发现矛盾）
写作  → Claude Sonnet（写作质量高）
```

**原则三：宿主无关**
autoresearch 的核心逻辑不依赖任何特定的 Coding Agent。
它通过 gitagent 标准文件 + MCP Server 对外暴露能力，
Claude Code / OpenCode / Cursor / Goose 都能调用它。

### 2.2 状态机模型

每个研究任务都有明确的状态机：

```text
CREATED → PLANNING → SEARCHING → READING → SYNTHESIZING → FACT_CHECKING → DONE
                                                               ↓
                                                         REVISION (如果事实核查失败)
```

状态存储在 `.autoresearch/state.json`，Agent 之间通过读写这个文件交接工作。

---

## 3. 完整目录结构

```text
autoresearch/
│
│   # ── 入口与配置 ─────────────────────────────────────────
├── autoresearch.yaml           # 全局配置（模型路由、MCP 服务器、功能开关）
├── AGENTS.md                   # 宿主 AI 的入口说明（Claude Code / Cursor 会读这个）
│
│   # ── Agent 定义（遵循 gitagent 标准）────────────────────
├── agents/
│   ├── planner/                # 规划者 — Claude Opus
│   │   ├── agent.yaml
│   │   ├── SOUL.md
│   │   ├── RULES.md
│   │   └── DUTIES.md
│   ├── searcher/               # 搜索者 — Claude Sonnet
│   │   ├── agent.yaml
│   │   ├── SOUL.md
│   │   └── RULES.md
│   ├── reader/                 # 阅读者 — Gemini 2.0 Pro（长文档）
│   │   ├── agent.yaml
│   │   ├── SOUL.md
│   │   └── RULES.md
│   ├── synthesizer/            # 综合者 — Claude Sonnet
│   │   ├── agent.yaml
│   │   ├── SOUL.md
│   │   └── RULES.md
│   └── fact-checker/           # 核查者 — Claude Sonnet
│       ├── agent.yaml
│       ├── SOUL.md
│       ├── RULES.md
│       └── DUTIES.md           # SOD：核查者不能是综合者
│
│   # ── 共享技能库（所有 Agent 可调用）──────────────────────
├── skills/
│   ├── web-search/
│   │   ├── SKILL.md            # 如何使用 Exa/Tavily 做深度搜索
│   │   └── search.yaml         # MCP tool schema
│   ├── paper-fetch/
│   │   ├── SKILL.md            # 如何从 ArXiv / Semantic Scholar 获取论文
│   │   └── fetch.yaml
│   ├── url-extract/
│   │   ├── SKILL.md            # 如何用 Firecrawl 提取网页完整内容
│   │   └── extract.yaml
│   ├── citation-format/
│   │   ├── SKILL.md            # 如何格式化引用（APA / Chicago / 简化格式）
│   │   └── templates/
│   └── report-structure/
│       ├── SKILL.md            # 如何组织研究报告结构
│       └── templates/
│           ├── technical.md    # 技术调研报告模板
│           ├── competitive.md  # 竞品分析模板
│           └── academic.md     # 学术综述模板
│
│   # ── 工作流定义（gitagent SkillsFlow 格式）────────────────
├── workflows/
│   ├── deep-research.yaml      # 主流程：完整研究流水线
│   ├── quick-scan.yaml         # 快速扫描：只做搜索和摘要，不深度阅读
│   └── fact-check-only.yaml    # 独立事实核查流程
│
│   # ── MCP 工具定义 ────────────────────────────────────────
├── tools/
│   ├── exa-search.yaml         # Exa 语义搜索
│   ├── tavily-search.yaml      # Tavily 实时搜索
│   ├── firecrawl-fetch.yaml    # Firecrawl 网页提取
│   ├── arxiv-fetch.yaml        # ArXiv 论文获取
│   └── git-memory.yaml         # Git 读写（用于 Agent 间通信）
│
│   # ── 适配器 ──────────────────────────────────────────────
├── adapters/
│   ├── claude-code/
│   │   └── CLAUDE.md           # gitagent export --format claude-code 生成
│   ├── opencode/
│   │   └── instructions.md     # gitagent export --format opencode 生成
│   ├── mcp-server/
│   │   ├── index.ts            # MCP Server 入口（stdio transport）
│   │   └── handlers/           # 每个 MCP tool 的处理器
│   └── cli/
│       ├── index.ts            # CLI 入口
│       └── commands/           # 各个子命令
│
│   # ── 知识库（可选，用户放入背景资料）────────────────────
├── knowledge/
│   └── .gitkeep
│
│   # ── 运行时（Git 追踪，但 CI 中 gitignore）───────────────
├── .autoresearch/
│   ├── state.json              # 当前任务状态机
│   ├── tasks/
│   │   └── {task-id}/
│   │       ├── brief.md        # 任务简报（Planner 写，其他人读）
│   │       ├── search-results/ # Searcher 的原始搜索结果
│   │       ├── readings/       # Reader 的精读笔记
│   │       ├── draft.md        # Synthesizer 的草稿
│   │       └── fact-check.md   # Fact-Checker 的核查报告
│   └── memory/
│       ├── MEMORY.md           # 长期记忆摘要（每7天自动归档）
│       └── sessions/           # 每次对话的完整记录
│
│   # ── 输出目录 ────────────────────────────────────────────
├── output/
│   └── {task-id}/
│       ├── report.md           # 最终研究报告
│       ├── sources.json        # 所有来源的结构化数据
│       └── appendix/           # 附录（完整引用、原始数据）
│
├── package.json
├── tsconfig.json
├── .env.example
└── .gitignore
```

---

## 4. Agent 团队设计

### 4.1 编排层级

```text
用户
  │
  ▼
Planner（规划者）── 唯一与用户交互的 Agent，负责整个任务生命周期
  │
  ├──→ Searcher（搜索者）── 执行网络搜索，返回原始结果
  │
  ├──→ Reader（阅读者）── 深度阅读长文档/论文，提取关键信息
  │
  ├──→ Synthesizer（综合者）── 整合所有信息，撰写草稿
  │
  └──→ Fact-Checker（核查者）── 验证草稿中的事实声明，标记问题
```

**关键设计决策：** Planner 是唯一有权修改 `state.json` 中任务状态的 Agent，
其他 Agent 只能向自己的工作目录写入数据，由 Planner 决定何时推进状态。

### 4.2 各 Agent 职责与模型选型

| Agent | 首选模型 | 备选模型 | 选型理由 |
|-------|---------|---------|---------|
| Planner | claude-opus-4 | claude-sonnet-4 | 复杂推理、任务分解、质量判断 |
| Searcher | claude-sonnet-4 | gpt-4o | 工具调用可靠，成本均衡 |
| Reader | gemini-2.0-pro | claude-opus-4 | 200万 token 上下文，整篇文档处理 |
| Synthesizer | claude-sonnet-4 | claude-opus-4 | 写作质量，结构组织 |
| Fact-Checker | claude-sonnet-4 | claude-opus-4 | 批判性分析，矛盾识别 |

### 4.3 职责隔离（SOD 设计）

参考 gitagent 的合规设计，autoresearch 强制执行以下分工原则：

- **Synthesizer ≠ Fact-Checker**：起草者不能核查自己的工作
- **Planner 不执行搜索**：防止规划偏差影响信息收集
- **Reader 不做结论**：只负责信息提取，不做综合判断

违反 SOD 的配置会在 `autoresearch validate` 时报错。

---

## 5. 核心文件内容规范

### 5.1 `autoresearch.yaml` — 全局配置

```yaml
# autoresearch global configuration
spec_version: "0.1.0"
name: autoresearch
version: "0.1.0"
description: Multi-agent deep research system

# Default model assignments (can be overridden per-agent)
models:
  default: claude-sonnet-4-20250514
  providers:
    anthropic:
      api_key_env: ANTHROPIC_API_KEY
    google:
      api_key_env: GOOGLE_API_KEY
    openai:
      api_key_env: OPENAI_API_KEY

# Active agents
agents:
  planner:
    enabled: true
    model: claude-opus-4-20250514
  searcher:
    enabled: true
    model: claude-sonnet-4-20250514
  reader:
    enabled: true
    model: gemini-2.0-pro
  synthesizer:
    enabled: true
    model: claude-sonnet-4-20250514
  fact-checker:
    enabled: true
    model: claude-sonnet-4-20250514

# MCP server configurations
mcp_servers:
  exa:
    type: url
    url: https://mcp.exa.ai/mcp
    api_key_env: EXA_API_KEY
    enabled: true
  tavily:
    type: url
    url: https://mcp.tavily.com/mcp
    api_key_env: TAVILY_API_KEY
    enabled: false  # Enable if you have Tavily API key
  firecrawl:
    type: url
    url: https://mcp.firecrawl.dev/mcp
    api_key_env: FIRECRAWL_API_KEY
    enabled: false

# Memory settings
memory:
  auto_summarize: true
  summarize_after_sessions: 3
  retention_days: 30

# Output settings
output:
  default_format: markdown
  include_sources: true
  citation_style: simplified  # simplified | apa | chicago

# Feature flags
features:
  fact_checking: true
  citation_validation: true
  human_in_the_loop: false  # Set true to require approval before each phase
```

### 5.2 `agents/planner/agent.yaml`

```yaml
spec_version: "0.1.0"
name: autoresearch-planner
version: "0.1.0"
description: >
  The orchestrator of the research pipeline. Decomposes research questions,
  assigns tasks to specialist agents, monitors progress, and ensures quality.

model:
  preferred: claude-opus-4-20250514
  fallback: claude-sonnet-4-20250514
  temperature: 0.3  # Low temperature for consistent planning

tools:
  - name: read_file        # Read task state and agent outputs
  - name: write_file       # Write task brief and state updates
  - name: git_memory       # Commit research milestones to git

skills:
  - path: ../../skills/report-structure
  - path: ../../skills/citation-format

memory:
  auto_load: true
  path: ../../.autoresearch/memory/

compliance:
  segregation_of_duties:
    roles:
      - id: orchestrator
        permissions: [plan, delegate, approve, commit_state]
    assignments:
      autoresearch-planner: [orchestrator]

hooks:
  bootstrap: hooks/bootstrap.md
  on_task_complete: hooks/on_complete.md
```

### 5.3 `agents/planner/SOUL.md`

```markdown
# Planner — Identity & Decision Logic

## Who I Am

I am the research director of autoresearch. I don't do the searching or writing myself —
I design the research strategy, coordinate the specialist agents, and ensure the final
output meets the quality bar.

My job is to think *before* acting. Every research question I receive, I first ask:

- What does the user *actually* need? (Not what they literally asked for)
- What type of research is this? (Technical survey / Competitive analysis / Academic review)
- What's the minimum viable research path? Don't boil the ocean.
- What's the ambiguity that could derail the research?

## Decision Framework

### Phase 1: Question Clarification

Before dispatching any agent, I must have clear answers to:

1. What is the core question? (1 sentence)
2. What are the 3 most important sub-questions?
3. What time period is relevant? (Last 6 months? Last 5 years? All time?)
4. What depth is required? (Quick scan vs. exhaustive review)
5. What's the target audience for the report?

I write these into `.autoresearch/tasks/{id}/brief.md` before any agent starts work.

### Phase 2: Search Strategy

I instruct Searcher with:

- Specific search queries (not vague topics)
- Minimum number of distinct sources (typically 10-20)
- Source type priorities (papers > official docs > news > blogs)
- Keywords to avoid (to prevent irrelevant results)

### Phase 3: Reading Prioritization

After seeing Searcher's results, I triage them:

- MUST READ: Directly answers the core question
- SHOULD READ: Adds important context
- SKIP: Peripheral or duplicative

I give Reader a prioritized reading list, not a raw dump.

### Phase 4: Quality Gate

Before declaring the research done, I check:

- Does the draft answer the core question and all 3 sub-questions?
- Is there a source for every factual claim?
- Has Fact-Checker cleared it?
- Is the structure appropriate for the audience?

If any check fails, I send it back with specific revision instructions.

## Communication Style

- Direct and structured
- Always explain my reasoning when making decisions
- When uncertain, I say so explicitly rather than pretending confidence
- I write task briefs that any agent can execute without asking follow-up questions

## Hard Constraints

- I never skip the fact-checking phase, even for "quick" research
- I never present Searcher's raw results as conclusions
- I always attribute findings to sources in the brief
```

### 5.4 `agents/planner/RULES.md`

```markdown
# Planner — Hard Rules

## Must Always

- Write a `brief.md` before dispatching any specialist agent
- Update `state.json` after each phase transition
- Require at least 5 distinct sources before allowing synthesis
- Require Fact-Checker to run before marking any task DONE
- Include a confidence level (High / Medium / Low) for each major finding

## Must Never

- Perform web searches directly (delegate to Searcher)
- Write the research report directly (delegate to Synthesizer)
- Skip fact-checking due to time pressure
- Fabricate sources or cite sources that haven't been read
- Mark a task complete if Fact-Checker found unresolved issues

## Quality Thresholds

- Research reports < 1000 words are rejected as "too thin"
- Reports with < 5 cited sources are rejected as "insufficiently sourced"
- Reports where any major claim lacks a source are sent back for revision
```

### 5.5 `agents/reader/agent.yaml`

```yaml
spec_version: "0.1.0"
name: autoresearch-reader
version: "0.1.0"
description: >
  Long-context document reader. Processes full papers, documentation, and web pages.
  Extracts key findings, quotes, and data points with precise source attribution.

model:
  preferred: gemini-2.0-pro-exp  # 2M context window
  fallback: claude-opus-4-20250514
  temperature: 0.1  # Near-zero for precise extraction

tools:
  - name: read_file
  - name: write_file
  - name: url_fetch        # Direct URL content retrieval

skills:
  - path: ../../skills/url-extract
  - path: ../../skills/paper-fetch
  - path: ../../skills/citation-format

# Reader-specific config: handle very long documents
context:
  max_input_tokens: 1500000
  chunking_strategy: semantic  # For models with smaller context windows
```

### 5.6 `agents/fact-checker/SOUL.md`

```markdown
# Fact-Checker — Identity & Verification Logic

## Who I Am

I am the skeptic of the research team. My job is to assume the draft is wrong
until proven right. Every claim I see, I ask: "Can I verify this independently?"

I am not here to be nice. I am here to protect the credibility of the research.
A report that goes out with a false claim is worse than no report at all.

## Verification Protocol

For each factual claim in the draft, I:

1. **Locate the cited source** — Does the citation actually exist and say what the draft claims?
2. **Check for misquotation** — Is the claim accurately representing the source?
3. **Check for recency** — Is this still true? (Especially for statistics and market data)
4. **Cross-verify** — Can I find at least one independent source that agrees?
5. **Flag contradictions** — Are there credible sources that say the opposite?

## Output Format

I produce a `fact-check.md` with:

- ✅ VERIFIED: Claims I could independently verify
- ⚠️ UNVERIFIABLE: Claims I couldn't verify (but couldn't disprove either)
- ❌ DISPUTED: Claims where I found contradicting evidence
- 🔄 OUTDATED: Claims that were true but are now stale

Any ❌ DISPUTED finding blocks the task from moving to DONE.
Any ⚠️ UNVERIFIABLE finding must be disclosed in the final report.

## Independence Requirement

I must not have been involved in writing the draft I'm checking.
If I identify that I was the Synthesizer on this task, I flag a SOD violation
and request a different model instance for fact-checking.
```

### 5.7 `workflows/deep-research.yaml`

```yaml
# Main research pipeline workflow (gitagent SkillsFlow format)
name: deep-research
description: Full research pipeline from question to verified report
version: "0.1.0"

triggers:
  - cli_command: "autoresearch run"
  - mcp_tool: "autoresearch_run"

inputs:
  query:
    type: string
    description: The research question or topic
    required: true
  depth:
    type: enum
    values: [quick, standard, deep]
    default: standard
  output_format:
    type: enum
    values: [markdown, json, pdf]
    default: markdown

steps:

  # ── Step 1: Task initialization ────────────────────────────
  init:
    tool: git-memory
    description: Create task directory and initialize state
    inputs:
      action: create_task
      query: ${{ inputs.query }}
    outputs:
      task_id: ${{ result.task_id }}

  # ── Step 2: Research planning ───────────────────────────────
  plan:
    agent: planner
    depends_on: [init]
    prompt: |
      A new research request has arrived.
      Task ID: ${{ steps.init.outputs.task_id }}
      Query: ${{ inputs.query }}
      Depth: ${{ inputs.depth }}

      Write a research brief to .autoresearch/tasks/${{ steps.init.outputs.task_id }}/brief.md
      The brief must include:
      1. Core question (1 sentence)
      2. Three key sub-questions
      3. Search strategy (10-15 specific queries)
      4. Suggested source types to prioritize
      5. Expected report structure

      Update state.json: status → PLANNING → SEARCHING
    inputs:
      task_id: ${{ steps.init.outputs.task_id }}
    outputs:
      brief_path: ${{ result.brief_path }}
      search_queries: ${{ result.search_queries }}

  # ── Step 3: Web search ─────────────────────────────────────
  search:
    agent: searcher
    depends_on: [plan]
    prompt: |
      Execute the search strategy from the research brief.
      Brief: ${{ steps.plan.outputs.brief_path }}
      Queries: ${{ steps.plan.outputs.search_queries }}

      For each query:
      1. Run Exa semantic search
      2. Save results to .autoresearch/tasks/{task_id}/search-results/{query-hash}.json
      3. Flag the top 10 most relevant URLs for deep reading

      Minimum: 15 distinct sources. Target: 20-30 sources.
    inputs:
      brief: ${{ steps.plan.outputs.brief_path }}
    outputs:
      results_dir: ${{ result.results_dir }}
      priority_urls: ${{ result.priority_urls }}

  # ── Step 4: Deep reading (conditional on depth) ────────────
  read:
    agent: reader
    depends_on: [search]
    conditions:
      - ${{ inputs.depth != 'quick' }}
    prompt: |
      Deep-read the priority documents identified by Searcher.
      Priority URLs: ${{ steps.search.outputs.priority_urls }}

      For each document:
      1. Extract the full content (use Firecrawl if needed)
      2. Write a structured reading note to .autoresearch/tasks/{task_id}/readings/{source-id}.md
      3. Format:
         - Source: [title, URL, date]
         - Key Findings: [bulleted list]
         - Relevant Quotes: [exact quotes with page/section references]
         - Data Points: [specific numbers, statistics]
         - Limitations: [what this source doesn't cover]
    inputs:
      priority_urls: ${{ steps.search.outputs.priority_urls }}
      task_id: ${{ steps.init.outputs.task_id }}
    outputs:
      readings_dir: ${{ result.readings_dir }}

  # ── Step 5: Synthesis ──────────────────────────────────────
  synthesize:
    agent: synthesizer
    depends_on: [read, search]
    prompt: |
      Write a research report based on all collected materials.

      Brief: ${{ steps.plan.outputs.brief_path }}
      Search results: ${{ steps.search.outputs.results_dir }}
      Reading notes: ${{ steps.read.outputs.readings_dir || 'N/A (quick mode)' }}
      Report structure template: per brief's suggested structure

      Requirements:
      - Every factual claim must have an inline citation [Source: URL]
      - Minimum 1000 words, no maximum
      - Structure: Executive Summary → Findings → Analysis → Conclusions → Sources
      - Mark confidence level for each major finding (High/Medium/Low)

      Save draft to: .autoresearch/tasks/{task_id}/draft.md
    outputs:
      draft_path: ${{ result.draft_path }}

  # ── Step 6: Fact checking ──────────────────────────────────
  fact_check:
    agent: fact-checker
    depends_on: [synthesize]
    conditions:
      - ${{ autoresearch.config.features.fact_checking == true }}
    prompt: |
      Review the research draft for factual accuracy.
      Draft: ${{ steps.synthesize.outputs.draft_path }}

      Apply the full verification protocol from your SOUL.md.
      Output fact-check report to: .autoresearch/tasks/{task_id}/fact-check.md

      If you find any ❌ DISPUTED claims, the pipeline will pause for revision.
    outputs:
      fact_check_path: ${{ result.fact_check_path }}
      has_disputes: ${{ result.has_disputes }}
      dispute_count: ${{ result.dispute_count }}

  # ── Step 7: Revision (if disputes found) ──────────────────
  revise:
    agent: synthesizer
    depends_on: [fact_check]
    conditions:
      - ${{ steps.fact_check.outputs.has_disputes == true }}
    prompt: |
      The fact-checker found ${{ steps.fact_check.outputs.dispute_count }} disputed claims.
      Fact-check report: ${{ steps.fact_check.outputs.fact_check_path }}
      Current draft: ${{ steps.synthesize.outputs.draft_path }}

      Revise the draft to address all ❌ DISPUTED items.
      Either remove the claims, find better sources, or add appropriate caveats.
      Update draft.md in place.

  # ── Step 8: Final packaging ────────────────────────────────
  package:
    agent: planner
    depends_on: [fact_check, revise]
    prompt: |
      Package the final research report.
      Draft: ${{ steps.synthesize.outputs.draft_path }}
      Fact-check: ${{ steps.fact_check.outputs.fact_check_path }}

      1. Review the final draft for completeness against the brief
      2. Add the fact-check summary section at the end
      3. Format the sources list in the configured citation style
      4. Copy to output/${{ steps.init.outputs.task_id }}/report.md
      5. Generate output/${{ steps.init.outputs.task_id }}/sources.json
      6. Update state.json: status → DONE
      7. Git commit: "research: complete task ${{ steps.init.outputs.task_id }}"

error_handling:
  on_failure: pause
  notify: user
  allow_retry: true
```

---

## 6. 工作流引擎设计

### 6.1 状态机实现

`.autoresearch/state.json` 的结构：

```json
{
  "version": "0.1.0",
  "tasks": {
    "task-2026-001": {
      "id": "task-2026-001",
      "query": "What are the architectural patterns for multi-agent AI systems in 2026?",
      "created_at": "2026-03-28T10:00:00Z",
      "status": "SYNTHESIZING",
      "depth": "deep",
      "current_agent": "synthesizer",
      "phases": {
        "PLANNING": {
          "completed_at": "2026-03-28T10:02:30Z",
          "agent": "planner",
          "output": "tasks/task-2026-001/brief.md"
        },
        "SEARCHING": {
          "completed_at": "2026-03-28T10:08:45Z",
          "agent": "searcher",
          "sources_found": 23,
          "priority_urls_count": 10
        },
        "READING": {
          "completed_at": "2026-03-28T10:25:10Z",
          "agent": "reader",
          "documents_read": 10
        },
        "SYNTHESIZING": {
          "started_at": "2026-03-28T10:25:12Z",
          "agent": "synthesizer"
        }
      },
      "metadata": {
        "model_usage": {
          "planner": "claude-opus-4-20250514",
          "searcher": "claude-sonnet-4-20250514",
          "reader": "gemini-2.0-pro",
          "synthesizer": "claude-sonnet-4-20250514"
        }
      }
    }
  },
  "active_task_id": "task-2026-001"
}
```

### 6.2 Agent 间通信协议

**原则：** Agent 不直接调用彼此，只通过文件系统通信。Planner 是唯一的调度者。

```text
Planner 写入 → brief.md
Searcher 读取 brief.md → 写入 search-results/
Planner 读取 search-results/ → 写入 reading-list.md
Reader 读取 reading-list.md → 写入 readings/
Planner 读取 readings/ → 写入 synthesis-instructions.md
Synthesizer 读取 synthesis-instructions.md → 写入 draft.md
Fact-Checker 读取 draft.md → 写入 fact-check.md
Planner 读取 fact-check.md → 决定 DONE 或 REVISION
```

这个协议的好处：每个文件都可以被人类直接查看和修改，
实现真正的 Human-in-the-Loop。

---

## 7. CLI 接口规范

### 7.1 安装

```bash
npm install -g autoresearch

# 或者在项目中使用
npm install autoresearch
```

### 7.2 核心命令

```bash
# 初始化（在当前项目目录中）
autoresearch init
# → 创建 .autoresearch/ 目录
# → 检测本地 AI 工具（Claude Code, Cursor 等）并注入技能文件
# → 引导配置 API keys

# 执行深度研究
autoresearch run "AI Agent 多模型协作架构的最佳实践"
autoresearch run "what are the best practices for multi-agent AI" --depth deep
autoresearch run "竞品分析：Perplexity vs You.com" --template competitive

# 查看任务状态
autoresearch status
autoresearch status task-2026-001

# 查看研究历史
autoresearch list
autoresearch list --last 10

# 恢复中断的任务
autoresearch resume task-2026-001

# 仅运行某个阶段
autoresearch search "query" --task task-2026-001
autoresearch fact-check --task task-2026-001

# 导出报告
autoresearch export task-2026-001 --format pdf
autoresearch export task-2026-001 --format json

# 验证配置
autoresearch validate

# 管理记忆
autoresearch memory show
autoresearch memory clear --older-than 30d
```

### 7.3 JSON 输出模式（供其他 Agent 调用）

所有命令支持 `--json` 标志，方便其他 AI Agent 以程序化方式调用：

```bash
autoresearch run "query" --json
# 输出：
{
  "task_id": "task-2026-001",
  "status": "DONE",
  "report_path": "output/task-2026-001/report.md",
  "sources_count": 23,
  "fact_check_passed": true,
  "duration_seconds": 180
}
```

---

## 8. 跨平台适配方案

### 8.1 作为 Claude Code 工具

`autoresearch init` 执行后，自动生成 `CLAUDE.md`（通过 `gitagent export --format claude-code`）：

```markdown
# autoresearch — Research Tool Instructions

When the user asks you to research a topic, use the autoresearch CLI:

## Quick Research

    autoresearch run "your research query" --depth quick --json
```

## Deep Research

```bash
autoresearch run "your research query" --depth deep --json
```

## Check Status

```bash
autoresearch status
```

## Key Files

- Research reports: `output/{task-id}/report.md`
- Task state: `.autoresearch/state.json`
- Agent memory: `.autoresearch/memory/MEMORY.md`

```text

### 8.2 作为 MCP Server

在 `~/.claude/claude_desktop_config.json` 或 OpenCode 配置中：

```json
{
  "mcpServers": {
    "autoresearch": {
      "command": "autoresearch-mcp-server",
      "env": {
        "AUTORESEARCH_CONFIG": "/path/to/autoresearch.yaml"
      }
    }
  }
}
```

**MCP Server 暴露的工具：**

```typescript
// Available MCP tools
{
  name: "autoresearch_run",
  description: "Start a deep research task",
  inputSchema: {
    query: string,       // Research question
    depth: "quick" | "standard" | "deep",
    template: "technical" | "competitive" | "academic" | "general"
  }
},
{
  name: "autoresearch_status",
  description: "Get the status of research tasks",
  inputSchema: {
    task_id?: string    // Optional, returns all active tasks if omitted
  }
},
{
  name: "autoresearch_read_report",
  description: "Read the completed research report",
  inputSchema: {
    task_id: string
  }
}
```

### 8.3 作为 OpenCode 插件

```bash
cd ~/.config/opencode
npm install autoresearch-plugin
```

`opencode.json`:

```json
{
  "plugin": ["autoresearch-profile"]
}
```

这与 newtype-os 的插件模式完全相同，用户已有的工作流无需改变。

### 8.4 环境探测

`autoresearch init` 时自动探测宿主环境并注入对应的技能文件：

```typescript
// adapters/cli/detect-host.ts

const HOSTS = [
  { name: 'claude-code',  marker: '.claude/',          skill_file: 'CLAUDE.md' },
  { name: 'opencode',     marker: '.opencode/',         skill_file: 'instructions.md' },
  { name: 'cursor',       marker: '.cursor/',           skill_file: '.cursor/rules/autoresearch.mdc' },
  { name: 'windsurf',     marker: '.windsurf/',         skill_file: '.windsurf/rules/autoresearch.md' },
  { name: 'copilot',      marker: '.github/copilot-instructions.md', skill_file: 'copilot-instructions.md' },
  { name: 'goose',        marker: '.goose/',            skill_file: '.goose/instructions.md' },
];

export function detectHosts(cwd: string): string[] {
  return HOSTS
    .filter(h => fs.existsSync(path.join(cwd, h.marker)))
    .map(h => h.name);
}
```

---

## 9. 内存与状态管理

### 9.1 三级记忆系统

参考 newtype-os 的记忆系统，autoresearch 实现三级记忆：

**Level 1 — 会话记录（短期）**
路径：`.autoresearch/memory/sessions/{date}-{session-id}.md`
内容：本次对话的完整记录
保留：7天

**Level 2 — 任务摘要（中期）**
路径：`.autoresearch/memory/tasks/{task-id}-summary.md`
内容：每个研究任务完成后的自动摘要（由 Planner 生成）
保留：90天

**Level 3 — 长期记忆（持久）**
路径：`.autoresearch/memory/MEMORY.md`
内容：跨任务的持久洞察（用户偏好、常用主题、方法论积累）
保留：永久

### 9.2 Git 作为持久化层

每个研究里程碑都会触发 Git commit：

```text
research: init task-2026-001 "AI Agent 架构调研"
research: planning complete — 3 sub-questions, 15 search queries
research: search complete — 23 sources found
research: reading complete — 10 documents analyzed
research: draft complete — 2847 words
research: fact-check passed — 0 disputes
research: done task-2026-001
```

这让研究过程完全可追溯。`git log --oneline` 就是完整的研究日志。

---

## 10. 技术栈选型

### 10.1 运行时

**首选：TypeScript + Bun（与 newtype-os 保持一致）**

理由：

- Bun 启动速度极快，CLI 工具体验好
- TypeScript 与 gitagent 生态完全对齐
- newtype-os 已验证了这套技术栈的可行性
- npm 发布流程成熟

### 10.2 关键依赖

```json
{
  "dependencies": {
    "@anthropic-ai/sdk": "^0.40.0",          // Anthropic API
    "@google/generative-ai": "^0.21.0",       // Gemini API（Reader）
    "@modelcontextprotocol/sdk": "^1.0.0",    // MCP Server/Client
    "simple-git": "^3.0.0",                   // Git 操作（记忆提交）
    "commander": "^12.0.0",                   // CLI 框架
    "ink": "^5.0.0",                          // 终端 UI（TUI）
    "gray-matter": "^4.0.3",                  // YAML frontmatter 解析
    "zod": "^3.0.0"                           // 配置验证
  },
  "devDependencies": {
    "bun-types": "^1.1.0",
    "typescript": "^5.0.0"
  }
}
```

### 10.3 目录树对应的包结构

```text
src/
├── agents/           # Agent 调用逻辑（封装 LLM API）
│   ├── base.ts       # BaseAgent 抽象类
│   ├── planner.ts
│   ├── searcher.ts
│   ├── reader.ts
│   ├── synthesizer.ts
│   └── fact-checker.ts
├── engine/           # 工作流引擎
│   ├── workflow.ts   # YAML workflow 解析与执行
│   ├── state.ts      # state.json 读写
│   └── memory.ts     # 三级记忆管理
├── adapters/
│   ├── mcp-server.ts
│   └── cli.ts
└── tools/            # MCP tool 实现
    ├── exa.ts
    ├── firecrawl.ts
    └── git-memory.ts
```

---

## 11. 开发路线图

### Phase 0 — 规范与脚手架（第 1-2 周）

**产出物：**

- [ ] 完整的 `autoresearch.yaml` 配置 schema（含 JSON Schema 验证）
- [ ] 所有 5 个 Agent 的 `agent.yaml` + `SOUL.md` + `RULES.md`
- [ ] `deep-research.yaml` 工作流定义
- [ ] `autoresearch validate` CLI 命令（验证配置文件是否合法）
- [ ] `autoresearch init` CLI 命令（初始化目录结构）
- [ ] 通过 `gitagent validate` 的验证

**验收标准：** 运行 `autoresearch init && autoresearch validate` 不报错

---

### Phase 1 — 单 Agent MVP（第 3-4 周）

**产出物：**

- [ ] Planner + Searcher 的完整实现（跳过 Reader 和 Fact-Checker）
- [ ] Exa MCP 搜索工具集成
- [ ] `state.json` 状态机基础实现
- [ ] Git commit 里程碑
- [ ] `autoresearch run --depth quick` 可用（只做搜索，不深度阅读）
- [ ] 基础 CLI TUI（显示进度）

**验收标准：** `autoresearch run "AI 多智能体架构" --depth quick`
在 2 分钟内产出一份有 10+ 来源的研究摘要

---

### Phase 2 — 完整流水线（第 5-7 周）

**产出物：**

- [ ] Reader Agent 实现（Gemini 长上下文集成）
- [ ] Synthesizer Agent 实现
- [ ] Fact-Checker Agent 实现（含 SOD 验证）
- [ ] `deep-research.yaml` 工作流完整执行
- [ ] 修订循环（Disputed claims → Revision → Re-check）
- [ ] 三种报告模板（technical / competitive / academic）
- [ ] `autoresearch run --depth deep` 可用

**验收标准：** 完整的深度研究在 15 分钟内产出一份 2000+ 字、
有 20+ 来源、经过事实核查的报告

---

### Phase 3 — 平台适配（第 8-9 周）

**产出物：**

- [ ] MCP Server 完整实现（stdio + HTTP transport）
- [ ] `autoresearch init` 自动探测并注入 Claude Code / Cursor / OpenCode 技能文件
- [ ] npm 包发布（`@autoresearch/cli` + `@autoresearch/mcp`）
- [ ] 三级记忆系统完整实现
- [ ] `autoresearch memory show/clear` 命令

**验收标准：**
在 Claude Code 中 `autoresearch init` 后，Claude 能自动调用 autoresearch 工具完成研究任务

---

### Phase 4 — 打磨与生态（第 10-12 周）

**产出物：**

- [ ] 完整的文档网站
- [ ] Firecrawl 集成（深度网页提取）
- [ ] ArXiv / Semantic Scholar 论文获取技能
- [ ] PDF 报告导出
- [ ] 人工介入点（`--human-in-the-loop` 模式）
- [ ] gitagent 社区的 Agent 分享（提交 PR 到 gitagent examples）

**验收标准：** 发布 v1.0.0，在 gitagent examples 中有 autoresearch 的完整示例

---

## 附录：`.env.example`

```bash
# Required: at least one search provider
EXA_API_KEY=your_exa_api_key_here

# Required: at least one LLM provider
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: additional LLM providers
GOOGLE_API_KEY=your_google_api_key_here      # For Reader (long context)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: additional search providers
TAVILY_API_KEY=your_tavily_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Optional: override default models
AUTORESEARCH_PLANNER_MODEL=claude-opus-4-20250514
AUTORESEARCH_READER_MODEL=gemini-2.0-pro
AUTORESEARCH_DEFAULT_MODEL=claude-sonnet-4-20250514
```
