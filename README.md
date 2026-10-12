# BOSS 问数 · 数据查询 Agent

> 自然语言驱动的数据查询系统 —— Text-to-SQL × 多数据源 × 流式响应

## 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [工作流程](#工作流程)
- [快速启动](#快速启动)
- [配置说明](#配置说明)
- [API 文档](#api-文档)
- [项目结构](#项目结构)
- [功能扩展建议](#功能扩展建议)
- [License](#license)

## 项目简介

基于 LangChain + LangGraph 构建的数据查询 Agent，支持用户通过自然语言提问，自动转换为 SQL 查询并返回结构化结果。

系统通过 **关键词提取 → 多路召回（列/指标/值） → 信息过滤 → SQL 生成 → 校验修正 → 执行** 的流水线，将自然语言精准转化为数据仓库可执行的 SQL 语句。

## 核心功能

| 模块 | 能力 |
|------|------|
| **自然语言查询** | 用户输入自然语言，Agent 自动理解意图 |
| **Text-to-SQL** | 大模型将自然语言转换为可执行 SQL |
| **多路召回** | 并行从 Qdrant 向量库、ES 全文检索召回列、指标、值信息 |
| **SQL 校验与自修正** | 生成 SQL 自动校验语法，失败时触发修正节点重试 |
| **流式响应** | SSE 实时推送查询进度与结果 |
| **结果可视化** | 表格展示查询结果，支持导出 |

## 技术栈

```
后端：Python 3.11 · FastAPI · LangChain · LangGraph · SQLAlchemy
大模型：DeepSeek (via 腾讯云) · BAAI/bge-large-zh-v1.5 向量化
向量库：Qdrant（列信息 & 指标信息）
全文检索：Elasticsearch 8.x（值信息）
数据库：MySQL 8.0（元数据库 + 数据仓库）
前端：Vue 3 · Vite · 紫色商务风 UI
部署：Docker Compose
```

## 工作流程

Agent 核心流程基于 LangGraph StateGraph 编排，节点间通过 State 对象传递数据：

```
                        ┌─────────────────┐
                        │  extract_keywords│  提取查询关键词
                        └────────┬────────┘
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
            ┌────────────┐ ┌──────────┐ ┌───────────┐
            │recall_column│ │recall_   │ │recall_    │  并行多路召回
            │ (Qdrant)   │ │metric    │ │value (ES) │
            └─────┬──────┘ │(Qdrant)  │ └─────┬─────┘
                  │        └────┬─────┘       │
                  └─────────┐   │   ┌─────────┘
                            ▼   ▼   ▼
                    ┌───────────────────┐
                    │merge_retrieved_info│  合并召回结果
                    └────────┬──────────┘
                    ┌────────┴──────────┐
                    ▼                   ▼
            ┌──────────────┐   ┌─────────────┐
            │ filter_metric │   │ filter_table │  过滤指标 & 表
            └───────┬──────┘   └──────┬───────┘
                    └────────┬────────┘
                             ▼
                    ┌──────────────────┐
                    │add_extra_context │  补充时间/数据库环境
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │  generate_sql    │  LLM 生成 SQL
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │  validate_sql    │  语法校验
                    └────────┬─────────┘
                       ┌─────┴─────┐
                  有错误 │           │ 无错误
                       ▼           │
                ┌────────────┐     │
                │ correct_sql │     │  自修正
                └─────┬──────┘     │
                      └─────┬─────┘
                            ▼
                    ┌──────────────────┐
                    │   execute_sql    │  执行并返回结果
                    └──────────────────┘
```

## 快速启动

### 前置条件

- Python >= 3.11、[uv](https://docs.astral.sh/uv/) 包管理器
- Node.js >= 18
- Docker & Docker Compose（用于基础设施）

### 1. 启动基础设施

```bash
cd docker
docker-compose up -d
```

将启动 MySQL 8.0、Elasticsearch 8.x、Qdrant、Kibana、Embedding 服务。

### 2. 启动后端

```bash
uv sync
uvicorn main:app --reload
```

后端默认运行在 `http://127.0.0.1:8000`。

### 3. 启动前端

```bash
cd date-agent-frontend
npm install
npm run dev
```

访问 http://localhost:5173 打开问数界面。

## 配置说明

项目配置集中在 `conf/` 目录下，使用 YAML 格式：

| 配置文件 | 用途 |
|---------|------|
| `conf/app_config.yaml` | 数据库连接、向量库、Embedding、LLM 等核心配置 |
| `conf/meta_config.yaml` | 元数据定义（表、列、指标的元信息描述） |
| `conf/text_config.yaml` | 文本处理相关配置 |

> **注意**：首次使用前请根据实际环境修改 `conf/app_config.yaml` 中的数据库地址、端口、密码等连接信息。请勿将包含 API Key 的配置文件提交到公共仓库。

## API 文档

### 查询接口

```
POST /api/query
Content-Type: application/json
```

**请求体：**

```json
{
  "query": "统计华北地区销售总额"
}
```

**响应：** SSE 流式响应（`text/event-stream`），实时推送查询各阶段进度与最终结果。

启动后端后访问 http://127.0.0.1:8000/docs 查看完整 Swagger 文档。

## 项目结构

```
data-agent/
├── main.py                     # FastAPI 入口
├── pyproject.toml              # Python 依赖管理 (uv)
├── conf/                       # YAML 配置文件
│   ├── app_config.yaml         #   核心配置
│   ├── meta_config.yaml        #   元数据定义
│   └── text_config.yaml        #   文本处理配置
├── app/
│   ├── agent/                  # LangGraph Agent 编排
│   │   ├── graph.py            #   工作流图定义
│   │   ├── state.py            #   State 数据结构
│   │   ├── context.py          #   Context 运行时上下文
│   │   ├── llm.py              #   LLM 客户端
│   │   └── nodes/              #   各工作流节点
│   │       ├── extract_keywords.py
│   │       ├── recall_column.py / recall_metric.py / recall_value.py
│   │       ├── merge_retrieved_info.py
│   │       ├── filter_metric.py / filter_table.py
│   │       ├── add_extra_context.py
│   │       ├── generate_sql.py / validate_sql.py / correct_sql.py
│   │       └── execute_sql.py
│   ├── api/                    # FastAPI 路由 & Schema
│   ├── clients/                # 外部客户端管理（MySQL/ES/Qdrant/Embedding）
│   ├── core/                   # 生命周期、日志、上下文
│   ├── conf/                   # 配置加载模块
│   ├── models/                 # 数据模型
│   ├── prompt/                 # Prompt 模板
│   ├── repositories/           # 数据访问层
│   ├── scripts/                # 工具脚本（如构建元数据知识库）
│   └── services/               # 业务服务层
├── date-agent-frontend/        # Vue 3 前端
│   ├── src/
│   │   ├── App.vue             #   主组件（对话界面）
│   │   └── style.css
│   └── package.json
├── docker/                     # Docker Compose 编排
│   └── docker-compose.yaml     #   MySQL/ES/Qdrant/Kibana/Embedding
└── README.md
```

## 功能扩展建议

1. **图表可视化** — 查询结果自动生成 ECharts 图表
2. **权限控制** — 数据源级别的访问权限管理
3. **查询历史** — 保存用户查询记录，支持收藏与复用
4. **多轮对话** — 支持上下文关联的追问式查询
5. **结果导出** — 支持 CSV / Excel 格式下载

## License

MIT
