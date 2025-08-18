# 腾讯云IM文档处理与RAG准备工具

## 📁 项目概述

这个项目包含了一套完整的工具，用于将腾讯云IM群组系统文档从URL保存为Markdown格式，并进行文档分割，为RAG（检索增强生成）系统做准备。

## 🚀 主要功能

### 1. URL转Markdown工具
- **通用版本** (`rag_homework.py`) - 可处理任意网页URL
- **专用版本** (`url_to_markdown_simple.py`) - 专门针对腾讯云文档优化

### 2. 文档分割工具 (`document_splitter.py`)
- 📝 按Markdown标题级别分割文档
- 🔍 关键词搜索和内容过滤
- 📊 文档块统计分析
- 💾 JSON格式输出，便于后续处理

### 3. 完整使用示例 (`example_usage.py`)
- 🎯 展示所有功能的使用方法
- 📈 内容分析和统计
- 🤖 RAG系统数据准备

## 📦 生成的文件

| 文件名 | 描述 | 大小 |
|--------|------|------|
| `腾讯云IM群组系统完整文档.md` | 完整的腾讯云IM文档（Markdown格式） | 20KB |
| `rag_ready_chunks.json` | RAG准备就绪的文档块数据 | 28KB |
| `example_output.json` | 示例输出的分割数据 | 15KB |

## 🔧 安装与使用

### 环境准备

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install requests beautifulsoup4 html2text lxml
```

### 基本使用

```python
from document_splitter import read_and_split_document

# 1. 分割文档
chunks = read_and_split_document("腾讯云IM群组系统完整文档.md", "###")

# 2. 查看结果
print(f"共分割出 {len(chunks)} 个文档块")

# 3. 搜索特定内容
from document_splitter import search_chunks_by_keyword
permission_chunks = search_chunks_by_keyword(chunks, "权限")
```

### 运行示例

```bash
# 运行文档分割工具
python3 document_splitter.py

# 运行完整使用示例
python3 example_usage.py

# 从URL获取新文档
python3 url_to_markdown_simple.py
```

## 📊 文档分割统计

根据三级标题(`###`)分割的结果：

- **总块数**: 12个
- **平均块大小**: 986字符
- **大小范围**: 373-3,418字符
- **内容类型**:
  - 表格密集型: 10个块
  - 文本密集型: 2个块

### 文档块列表

| 序号 | 标题 | 字符数 | 类型 |
|------|------|--------|------|
| 0 | 群组基础能力操作差异 | 982 | 表格 |
| 1 | 加群方式差异 | 375 | 表格 |
| 2 | 成员管理能力差异 | 495 | 表格 |
| 3 | 群组限制差异 | 373 | 表格 |
| 4 | 消息能力差异 | 416 | 表格 |
| 5 | 批量导入与自动回收差异 | 563 | 表格 |
| 6 | 群基础资料 | 1,133 | 表格 |
| 7 | 群成员资料 | 775 | 表格 |
| 8 | 权限组资料 | 460 | 表格 |
| 9 | 权限组中的权限含义介绍 | 3,418 | 文本+表格 |
| 10 | 特性介绍 | 1,661 | 文本 |
| 11 | 配置方法 | 1,190 | 文本 |

## 🤖 RAG系统集成

### 数据格式

每个文档块包含以下字段：

```json
{
  "chunk_id": "tencent_im_doc_001",
  "title": "群组基础能力操作差异", 
  "content": "完整的块内容...",
  "level": 3,
  "start_line": 97,
  "end_line": 108,
  "word_count": 470,
  "char_count": 982,
  "vector_ready": true,
  "embedding_text": "标题 + 内容的组合文本"
}
```

### 建议的RAG工作流

1. **文档预处理**: 使用 `document_splitter.py` 分割文档
2. **向量化**: 对每个块的 `embedding_text` 生成向量
3. **索引构建**: 使用向量数据库（如Milvus、Pinecone等）
4. **检索**: 根据用户查询检索相关文档块
5. **生成**: 使用检索到的上下文生成回答

## 🔍 搜索和过滤功能

### 关键词搜索
```python
# 搜索包含特定关键词的块
chunks = search_chunks_by_keyword(chunks, "直播群")
```

### 按大小过滤
```python
# 获取大于1000字符的块
large_chunks = filter_chunks_by_size(chunks, min_chars=1000)
```

### 按标题查找
```python
# 查找特定标题的块
chunk = get_chunk_by_title(chunks, "消息能力差异")
```

## 📈 内容分析结果

### 群组类型提及频率
- **Community**: 11次
- **AVChatRoom**: 8次
- **Work**: 7次
- **Public**: 7次  
- **Meeting**: 7次

### 表格密度分析
- 消息能力差异: 101.0/1000字符（最密集）
- 群组限制差异: 93.8/1000字符
- 加群方式差异: 93.3/1000字符

## 🛠️ 扩展功能

### 自定义分割级别
```python
# 按二级标题分割
chunks = read_and_split_document(file_path, "##")

# 按四级标题分割  
chunks = read_and_split_document(file_path, "####")
```

### 自定义元数据
```python
metadata = {
    'source': '腾讯云官方文档',
    'version': '2025-05-12',
    'domain': 'instant_messaging'
}
save_chunks_to_json(chunks, 'output.json', metadata)
```

## 📝 使用案例

### 场景1: 客服机器人
使用文档块构建IM群组系统的智能客服，可以准确回答关于群组类型、权限配置等问题。

### 场景2: 开发文档助手  
为开发者提供快速查询IM SDK功能和API的助手工具。

### 场景3: 产品知识库
构建内部产品知识库，帮助销售和技术支持快速获取准确信息。

## 🔧 依赖项

```txt
requests>=2.25.0
beautifulsoup4>=4.9.0
html2text>=2020.1.16
lxml>=4.6.0
```

## 📄 许可证

本项目仅用于学习和研究目的。腾讯云IM文档内容版权归腾讯云所有。

---

**🎯 总结**: 这套工具提供了从URL获取、文档处理到RAG准备的完整工作流，特别针对腾讯云IM群组系统文档进行了优化，生成的结构化数据可以直接用于RAG系统的构建。