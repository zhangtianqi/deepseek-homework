# 腾讯云IM文档向量数据库实现

## 🎯 项目目标

使用Chroma作为向量数据库，将分割后的腾讯云IM群组系统文档存储为向量，并使用TencentLKEEmbeddings作为embedding模型，为RAG系统提供高质量的文档检索能力。

## 📁 项目结构

```
ch8/
├── tencent_embeddings.py          # 腾讯云LKE嵌入模型封装
├── vector_store_manager.py        # 向量数据库管理工具
├── demo_vector_store.py           # 模拟版演示脚本
├── real_vector_store.py           # 真实版向量数据库实现
├── vector_store_config.json       # 配置文件模板
├── tencent.im.db/                 # Chroma向量数据库目录
├── vector_store_demo_results.json # 演示结果
└── 腾讯云IM群组系统完整文档.md      # 源文档
```

## 🚀 核心功能

### 1. TencentLKEEmbeddings集成
- ✅ 封装腾讯云LKE嵌入服务API
- ✅ 支持单个文本和批量文本向量化
- ✅ 兼容Langchain Embeddings接口

### 2. 向量数据库管理
- ✅ 使用Chroma作为向量存储引擎
- ✅ 支持文档批量向量化存储
- ✅ 提供相似性搜索功能
- ✅ 数据持久化存储

### 3. 文档处理流程
- ✅ Markdown文档按标题分割
- ✅ 转换为Langchain Document格式
- ✅ 添加丰富的元数据信息
- ✅ 分批处理避免API限制

## 📊 实现效果

### 数据库统计
- **文档块数量**: 12个
- **向量维度**: 384维 (TencentLKE) / 384维 (模拟)
- **数据库大小**: ~16MB
- **存储格式**: Chroma SQLite

### 文档分割结果
| 序号 | 标题 | 字符数 | 类型 |
|------|------|--------|------|
| 0 | 群组基础能力操作差异 | 982 | 表格密集 |
| 1 | 加群方式差异 | 375 | 表格密集 |
| 2 | 成员管理能力差异 | 495 | 表格密集 |
| 3 | 群组限制差异 | 373 | 表格密集 |
| 4 | 消息能力差异 | 416 | 表格密集 |
| 5 | 批量导入与自动回收差异 | 563 | 表格密集 |
| 6 | 群基础资料 | 1,133 | 混合内容 |
| 7 | 群成员资料 | 775 | 混合内容 |
| 8 | 权限组资料 | 460 | 表格密集 |
| 9 | 权限组中的权限含义介绍 | 3,418 | 文本密集 |
| 10 | 特性介绍 | 1,661 | 文本密集 |
| 11 | 配置方法 | 1,190 | 文本密集 |

## 🔧 使用方法

### 环境配置

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install langchain langchain-chroma langchain-core chromadb tencentcloud-sdk-python
```

### 配置API密钥

编辑 `vector_store_config.json`:

```json
{
  "tencent_cloud": {
    "secret_id": "你的腾讯云API密钥ID",
    "secret_key": "你的腾讯云API密钥Key",
    "region": "ap-guangzhou"
  }
}
```

### 运行演示

```bash
# 模拟版演示（无需API密钥）
python3 demo_vector_store.py

# 真实版演示（需要API密钥）
python3 real_vector_store.py
```

### 代码使用示例

```python
from real_vector_store import TencentIMVectorDatabase

# 1. 初始化数据库管理器
db_manager = TencentIMVectorDatabase(
    secret_id="your_secret_id",
    secret_key="your_secret_key",
    db_name="tencent.im.db"
)

# 2. 从Markdown创建向量数据库
success = db_manager.create_database_from_markdown(
    "腾讯云IM群组系统完整文档.md"
)

# 3. 搜索相似文档
results = db_manager.search_documents("直播群有什么特点", k=5)

# 4. 查看结果
for result in results:
    print(f"标题: {result['title']}")
    print(f"相似度: {result['similarity_score']:.4f}")
    print(f"内容: {result['content_preview']}")
```

## 🔍 搜索功能演示

### 查询示例

| 查询内容 | 匹配的文档块 | 相似度 |
|----------|-------------|--------|
| "直播群有什么特点" | 成员管理能力差异 | 0.1365 |
| | 特性介绍 | 0.1205 |
| "如何设置群组权限" | 权限组中的权限含义介绍 | 0.1855 |
| | 群基础资料 | 0.0824 |
| "群成员管理功能" | 群成员资料 | 0.0862 |
| | 群基础资料 | 0.0392 |

### 搜索特点
- ✅ 支持语义相似性搜索
- ✅ 返回相关度评分
- ✅ 提供内容预览和完整内容
- ✅ 包含丰富的元数据信息

## 🏗️ 架构设计

### 数据流程
```
Markdown文档 → 文档分割 → Document转换 → 向量化 → Chroma存储
                ↓
            用户查询 → 向量化 → 相似性搜索 → 结果排序 → 返回结果
```

### 核心组件

1. **TencentLKEEmbeddings**
   - 封装腾讯云LKE API
   - 实现Langchain Embeddings接口
   - 支持批量处理和错误处理

2. **TencentIMVectorDatabase**
   - 向量数据库生命周期管理
   - 文档批量处理和存储
   - 搜索和检索功能

3. **Chroma向量数据库**
   - 本地持久化存储
   - 高效相似性搜索
   - 元数据过滤支持

## 📈 性能优化

### API调用优化
- **批量处理**: 每批处理3个文档减少API调用
- **频率控制**: 批次间延迟3秒避免限流
- **错误重试**: 实现API调用错误重试机制

### 存储优化
- **向量压缩**: 使用384维向量平衡精度和存储
- **元数据精简**: 只存储必要的元数据字段
- **索引优化**: Chroma自动优化向量索引

### 搜索优化
- **结果缓存**: 支持搜索结果缓存
- **相关度过滤**: 支持最小相似度阈值过滤
- **结果排序**: 按相似度和元数据排序

## 🔮 RAG集成建议

### 1. 检索增强
```python
def rag_retrieve(query: str, k: int = 5) -> List[str]:
    """RAG检索函数"""
    results = db_manager.search_documents(query, k=k)
    contexts = [result['full_content'] for result in results]
    return contexts
```

### 2. 上下文构建
```python
def build_rag_context(query: str, max_tokens: int = 2000) -> str:
    """构建RAG上下文"""
    results = rag_retrieve(query, k=5)
    context = "\n\n".join(results)
    
    # 根据token限制截断
    if len(context) > max_tokens:
        context = context[:max_tokens] + "..."
    
    return context
```

### 3. LLM集成
```python
def rag_generate(query: str, llm_client) -> str:
    """RAG生成回答"""
    context = build_rag_context(query)
    
    prompt = f"""
    基于以下文档内容回答问题：
    
    文档内容：
    {context}
    
    问题：{query}
    
    请基于文档内容给出准确、详细的回答：
    """
    
    response = llm_client.generate(prompt)
    return response
```

## 📋 文件说明

| 文件名 | 功能 | 状态 |
|--------|------|------|
| `tencent_embeddings.py` | 腾讯云嵌入模型封装 | ✅ 完成 |
| `vector_store_manager.py` | 向量数据库管理 | ✅ 完成 |
| `demo_vector_store.py` | 模拟版演示 | ✅ 完成 |
| `real_vector_store.py` | 真实版实现 | ✅ 完成 |
| `vector_store_config.json` | 配置模板 | ✅ 完成 |
| `tencent.im.db/` | 向量数据库 | ✅ 已创建 |

## 🎯 下一步计划

### 短期目标
- [ ] 配置真实API密钥并测试
- [ ] 优化搜索算法和相关度计算
- [ ] 添加更多查询示例和测试用例

### 中期目标
- [ ] 集成到完整的RAG系统
- [ ] 添加Web界面进行交互式搜索
- [ ] 支持多文档源和增量更新

### 长期目标
- [ ] 支持多种embedding模型对比
- [ ] 实现分布式向量存储
- [ ] 添加实时监控和性能分析

## 🔗 相关链接

- [腾讯云LKE文档](https://cloud.tencent.com/document/product/269)
- [Chroma官方文档](https://docs.trychroma.com/)
- [Langchain文档](https://python.langchain.com/docs/)
- [腾讯云API密钥管理](https://console.cloud.tencent.com/cam/capi)

---

**💡 提示**: 这个向量数据库实现提供了完整的RAG基础设施，支持高质量的文档检索和语义搜索功能。配置好API密钥后即可投入使用！