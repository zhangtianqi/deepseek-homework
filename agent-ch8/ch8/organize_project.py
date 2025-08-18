#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目文件整理脚本
将文件按功能分类到不同目录
"""

import os
import shutil
from pathlib import Path


def organize_project():
    """整理项目文件结构"""
    print("🗂️ 开始整理项目文件结构")
    print("=" * 50)
    
    # 创建目录结构
    directories = {
        'core': '核心模块',
        'scrapers': '网页抓取',
        'tests': '测试演示',
        'config': '配置文件',
        'data': '数据文件',
        'results': '测试结果',
        'docs': '文档说明'
    }
    
    # 创建目录
    for dir_name, desc in directories.items():
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"📁 创建目录: {dir_name}/ ({desc})")
    
    # 文件分类映射
    file_mapping = {
        'core': [
            'tencent_embeddings.py',
            'document_splitter.py', 
            'vector_store_manager.py',
            'real_vector_store.py',
            'rag_complete_demo.py'
        ],
        'scrapers': [
            'rag_homework.py',
            'url_to_markdown_simple.py'
        ],
        'tests': [
            'test_embedding_api.py',
            'demo_vector_store.py',
            'recall_test.py',
            'example_usage.py'
        ],
        'config': [
            'vector_store_config.json',
            'requirements.txt'
        ],
        'data': [
            '腾讯云IM群组系统完整文档.md',
            '腾讯云IM群组系统文档.md',
            '腾讯云IM文档块.json',
            '腾讯云IM文档块_处理后.json',
            'rag_ready_chunks.json',
            'example_output.json'
        ],
        'results': [
            'recall_test_results.json',
            'real_vector_search_results.json',
            'vector_store_demo_results.json'
        ],
        'docs': [
            'README.md',
            'VECTOR_STORE_README.md',
            '召回测试报告.md',
            '项目文档结构.md'
        ]
    }
    
    # 移动文件
    moved_files = 0
    for target_dir, files in file_mapping.items():
        for file_name in files:
            if os.path.exists(file_name):
                target_path = os.path.join(target_dir, file_name)
                shutil.move(file_name, target_path)
                print(f"📄 移动: {file_name} → {target_dir}/")
                moved_files += 1
    
    print(f"\n✅ 文件整理完成，移动了 {moved_files} 个文件")
    
    # 创建新的主README
    create_main_readme()
    
    # 显示最终结构
    print_project_structure()


def create_main_readme():
    """创建主README文件"""
    readme_content = """# 腾讯云IM文档RAG系统

## 🎯 项目简介

这是一个基于腾讯云LKE嵌入模型和Chroma向量数据库的完整RAG（检索增强生成）系统，专门用于腾讯云IM群组系统文档的智能问答。

## 📁 项目结构

```
ch8/
├── core/           # 核心模块
├── scrapers/       # 网页抓取
├── tests/          # 测试演示  
├── config/         # 配置文件
├── data/           # 数据文件
├── results/        # 测试结果
├── docs/           # 文档说明
├── tencent.im.db/  # 向量数据库
└── venv/           # 虚拟环境
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r config/requirements.txt
```

### 2. 配置API密钥
编辑 `config/vector_store_config.json`:
```json
{
  "tencent_cloud": {
    "secret_id": "your_secret_id",
    "secret_key": "your_secret_key"
  }
}
```

### 3. 运行演示
```bash
# 完整RAG演示
python3 core/rag_complete_demo.py

# 召回测试
python3 tests/recall_test.py

# API测试
python3 tests/test_embedding_api.py
```

## 📊 性能指标

- **召回准确率**: 93.8%
- **平均响应时间**: 0.366秒
- **测试成功率**: 100%
- **向量维度**: 1024维

## 🔧 技术栈

- **嵌入模型**: 腾讯云LKE
- **向量数据库**: Chroma
- **文档处理**: Langchain + BeautifulSoup
- **API框架**: 腾讯云SDK

## 📚 使用文档

详细文档请查看 `docs/` 目录中的相关文件。

## 🎯 主要功能

1. **文档抓取**: 从URL抓取网页内容并转换为Markdown
2. **文档分割**: 按标题级别智能分割文档
3. **向量化**: 使用腾讯云LKE生成文档向量
4. **向量存储**: 基于Chroma的持久化向量数据库
5. **语义搜索**: 高精度的文档检索
6. **答案生成**: 基于检索内容的智能问答

## 🔗 相关链接

- [腾讯云LKE文档](https://cloud.tencent.com/document/product/269)
- [Chroma官方文档](https://docs.trychroma.com/)
- [项目详细文档](docs/项目文档结构.md)
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("📄 创建主README.md文件")


def print_project_structure():
    """打印项目结构"""
    print(f"\n📊 最终项目结构:")
    print("=" * 50)
    
    for root, dirs, files in os.walk('.'):
        # 跳过某些目录
        if any(skip in root for skip in ['__pycache__', '.git', 'venv']):
            continue
            
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        
        sub_indent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # 只显示前5个文件
            print(f"{sub_indent}{file}")
        
        if len(files) > 5:
            print(f"{sub_indent}... 还有 {len(files) - 5} 个文件")


if __name__ == "__main__":
    # 询问用户是否要整理文件
    response = input("是否要整理项目文件结构? (y/N): ")
    if response.lower() in ['y', 'yes']:
        organize_project()
    else:
        print("取消文件整理")
        print_project_structure()