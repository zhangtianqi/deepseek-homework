#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量数据库演示脚本
使用模拟的embedding来演示向量存储和搜索功能
"""

import json
import os
import numpy as np
from typing import List, Dict
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain.embeddings.base import Embeddings
from document_splitter import read_and_split_document


class MockEmbeddings(Embeddings):
    """模拟的嵌入模型，用于演示目的"""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
    
    def _get_embedding(self, text: str) -> List[float]:
        """根据文本内容生成模拟向量"""
        # 使用文本的hash值作为种子，确保相同文本生成相同向量
        np.random.seed(hash(text) % (2**32))
        vector = np.random.normal(0, 1, self.dimension)
        # 归一化向量
        vector = vector / np.linalg.norm(vector)
        return vector.tolist()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量生成文档向量"""
        return [self._get_embedding(text) for text in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """生成查询向量"""
        return self._get_embedding(text)


def create_mock_vectorstore_demo():
    """
    使用模拟embedding创建向量数据库演示
    """
    print("🎯 腾讯云IM文档向量数据库演示 (模拟版本)")
    print("=" * 60)
    
    # 配置
    db_name = "tencent.im.db"
    persist_directory = f"./{db_name}"
    markdown_file = "/Users/zhangtianqi/git_root/agent_homework/ch8/腾讯云IM群组系统完整文档.md"
    
    try:
        # 1. 读取和分割文档
        print("📖 读取和分割Markdown文档...")
        chunks = read_and_split_document(markdown_file, "###")
        
        if not chunks:
            print("❌ 无法读取或分割文档")
            return
        
        print(f"📄 成功分割出 {len(chunks)} 个文档块")
        
        # 2. 转换为Document格式
        print("📝 转换为Langchain Document格式...")
        documents = []
        
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk['content'],
                metadata={
                    'chunk_id': f"tencent_im_{i:03d}",
                    'title': chunk['title'],
                    'level': chunk['level'],
                    'start_line': chunk['start_line'],
                    'end_line': chunk['end_line'],
                    'char_count': chunk['char_count'],
                    'word_count': chunk['word_count'],
                    'source': 'tencent_im_docs',
                    'chunk_index': i
                }
            )
            documents.append(doc)
        
        print(f"✅ 转换了 {len(documents)} 个文档")
        
        # 3. 初始化模拟嵌入模型
        print("🔧 初始化模拟嵌入模型...")
        embeddings = MockEmbeddings(dimension=384)
        
        # 4. 创建向量数据库
        print("💾 创建Chroma向量数据库...")
        
        # 删除已存在的数据库
        if os.path.exists(persist_directory):
            import shutil
            shutil.rmtree(persist_directory)
            print(f"🗑️ 删除已存在的数据库: {db_name}")
        
        # 创建新的向量数据库
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=persist_directory
        )
        
        print(f"✅ 向量数据库 {db_name} 创建成功！")
        
        # 5. 获取数据库信息
        print("\n📊 数据库信息:")
        all_docs = vectorstore.get()
        print(f"   📦 数据库名称: {db_name}")
        print(f"   📁 存储路径: {persist_directory}")
        print(f"   📄 文档总数: {len(all_docs['ids']) if all_docs['ids'] else 0}")
        print(f"   🤖 嵌入模型: MockEmbeddings (384维)")
        print(f"   💾 数据库大小: {get_folder_size(persist_directory):.2f} MB")
        
        # 6. 演示搜索功能
        print("\n🔍 搜索功能演示:")
        test_queries = [
            "直播群有什么特点",
            "如何设置群组权限", 
            "群成员管理功能",
            "社群Community的优势",
            "消息存储和漫游"
        ]
        
        for query in test_queries:
            print(f"\n🔎 查询: '{query}'")
            
            # 执行相似性搜索
            results = vectorstore.similarity_search_with_score(query, k=3)
            
            for i, (doc, score) in enumerate(results):
                title = doc.metadata.get('title', 'Unknown')
                char_count = doc.metadata.get('char_count', 0)
                content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                
                print(f"   {i+1}. 📄 {title}")
                print(f"      📏 {char_count} 字符 | 🎯 相似度: {1-score:.4f}")
                print(f"      📝 内容: {content_preview}")
        
        # 7. 保存搜索结果示例
        print(f"\n💾 保存演示结果...")
        demo_results = {
            'database_info': {
                'name': db_name,
                'total_documents': len(documents),
                'embedding_dimension': 384,
                'persist_directory': persist_directory
            },
            'search_examples': []
        }
        
        for query in test_queries[:2]:  # 只保存前两个查询的结果
            results = vectorstore.similarity_search_with_score(query, k=2)
            query_results = {
                'query': query,
                'results': []
            }
            
            for doc, score in results:
                query_results['results'].append({
                    'title': doc.metadata.get('title'),
                    'similarity_score': float(1-score),
                    'char_count': doc.metadata.get('char_count'),
                    'content_preview': doc.page_content[:200]
                })
            
            demo_results['search_examples'].append(query_results)
        
        with open('vector_store_demo_results.json', 'w', encoding='utf-8') as f:
            json.dump(demo_results, f, ensure_ascii=False, indent=2)
        
        print(f"📊 演示结果已保存到: vector_store_demo_results.json")
        
        return vectorstore
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        return None


def get_folder_size(folder_path: str) -> float:
    """获取文件夹大小（MB）"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                total_size += os.path.getsize(file_path)
        return total_size / (1024 * 1024)  # 转换为MB
    except Exception:
        return 0.0


def test_vector_operations(vectorstore):
    """
    测试向量数据库的各种操作
    """
    if not vectorstore:
        print("❌ 向量数据库未创建，跳过测试")
        return
    
    print("\n🧪 向量数据库操作测试:")
    print("=" * 40)
    
    # 1. 测试不同类型的查询
    query_tests = [
        ("功能查询", "直播群支持哪些功能"),
        ("对比查询", "Work群和Public群的区别"),
        ("配置查询", "如何配置群组权限"),
        ("限制查询", "群组有哪些限制")
    ]
    
    for test_type, query in query_tests:
        print(f"\n📋 {test_type}: '{query}'")
        results = vectorstore.similarity_search(query, k=2)
        
        for i, doc in enumerate(results):
            title = doc.metadata.get('title', 'Unknown')
            print(f"   {i+1}. {title}")
    
    # 2. 测试元数据过滤
    print(f"\n🔍 元数据过滤测试:")
    
    # 查找包含"权限"的文档
    all_docs = vectorstore.get()
    permission_docs = []
    
    for i, doc_content in enumerate(all_docs['documents']):
        if '权限' in doc_content:
            metadata = all_docs['metadatas'][i]
            permission_docs.append(metadata.get('title', 'Unknown'))
    
    print(f"   包含'权限'的文档块: {len(permission_docs)} 个")
    for title in permission_docs[:3]:  # 只显示前3个
        print(f"   - {title}")


def main():
    """
    主函数
    """
    print("🚀 腾讯云IM文档向量数据库完整演示")
    print("=" * 80)
    
    # 创建向量数据库演示
    vectorstore = create_mock_vectorstore_demo()
    
    # 测试向量操作
    test_vector_operations(vectorstore)
    
    print(f"\n🎉 演示完成!")
    print(f"📁 生成的文件:")
    print(f"   • tencent.im.db/ - 向量数据库目录")
    print(f"   • vector_store_demo_results.json - 演示结果")
    
    print(f"\n💡 下一步:")
    print(f"   1. 替换MockEmbeddings为TencentLKEEmbeddings")
    print(f"   2. 配置真实的腾讯云API密钥")
    print(f"   3. 集成到RAG系统中")


if __name__ == "__main__":
    main()