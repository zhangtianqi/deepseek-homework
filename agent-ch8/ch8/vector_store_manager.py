#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量数据库管理工具
使用Chroma存储分割后的腾讯云IM文档，并使用TencentLKEEmbeddings进行向量化
"""

import json
import os
from typing import List, Dict, Optional
from langchain_core.documents import Document
from langchain_chroma import Chroma
from tencent_embeddings import TencentLKEEmbeddings
from document_splitter import read_and_split_document


class TencentIMVectorStore:
    """腾讯云IM文档向量存储管理器"""
    
    def __init__(self, secret_id: str, secret_key: str, db_name: str = "tencent.im.db"):
        """
        初始化向量存储管理器
        
        Args:
            secret_id (str): 腾讯云API密钥ID
            secret_key (str): 腾讯云API密钥Key
            db_name (str): 向量数据库名称
        """
        self.db_name = db_name
        self.persist_directory = f"./{db_name}"
        
        # 初始化腾讯云嵌入模型
        self.embeddings = TencentLKEEmbeddings(
            secret_id=secret_id,
            secret_key=secret_key,
            region="ap-guangzhou"
        )
        
        # 初始化或加载向量数据库
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """初始化向量数据库"""
        try:
            if os.path.exists(self.persist_directory):
                print(f"📂 加载已存在的向量数据库: {self.db_name}")
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
            else:
                print(f"🆕 创建新的向量数据库: {self.db_name}")
                # 先创建一个空的向量数据库
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
        except Exception as e:
            print(f"❌ 初始化向量数据库失败: {e}")
            raise
    
    def chunks_to_documents(self, chunks: List[Dict]) -> List[Document]:
        """
        将文档块转换为Langchain Document格式
        
        Args:
            chunks (List[Dict]): 文档块列表
            
        Returns:
            List[Document]: Langchain Document列表
        """
        documents = []
        
        for i, chunk in enumerate(chunks):
            # 创建Document对象
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
        
        return documents
    
    def add_documents_to_vectorstore(self, documents: List[Document], batch_size: int = 5) -> bool:
        """
        批量添加文档到向量数据库
        
        Args:
            documents (List[Document]): 文档列表
            batch_size (int): 批处理大小（避免API调用过于频繁）
            
        Returns:
            bool: 是否成功
        """
        try:
            print(f"📝 开始向量化并存储 {len(documents)} 个文档块...")
            
            # 分批处理以避免API限制
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                print(f"🔄 处理批次 {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1} ({len(batch)} 个文档)")
                
                # 添加到向量数据库
                self.vectorstore.add_documents(batch)
                
                # 添加延迟以避免API频率限制
                if i + batch_size < len(documents):
                    print("⏱️ 等待2秒以避免API频率限制...")
                    import time
                    time.sleep(2)
            
            print(f"✅ 成功存储所有文档到向量数据库 {self.db_name}")
            return True
            
        except Exception as e:
            print(f"❌ 存储文档到向量数据库失败: {e}")
            return False
    
    def search_similar_documents(self, query: str, k: int = 5) -> List[Dict]:
        """
        搜索相似文档
        
        Args:
            query (str): 查询文本
            k (int): 返回的文档数量
            
        Returns:
            List[Dict]: 相似文档列表
        """
        try:
            print(f"🔍 搜索查询: '{query}'")
            
            # 执行相似性搜索
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            search_results = []
            for doc, score in results:
                result = {
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    'full_content': doc.page_content,
                    'metadata': doc.metadata,
                    'similarity_score': float(score),
                    'title': doc.metadata.get('title', 'Unknown')
                }
                search_results.append(result)
            
            return search_results
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []
    
    def get_database_info(self) -> Dict:
        """
        获取数据库信息
        
        Returns:
            Dict: 数据库统计信息
        """
        try:
            # 获取所有文档
            all_docs = self.vectorstore.get()
            
            info = {
                'database_name': self.db_name,
                'persist_directory': self.persist_directory,
                'total_documents': len(all_docs['ids']) if all_docs['ids'] else 0,
                'embedding_model': 'TencentLKEEmbeddings',
                'database_exists': os.path.exists(self.persist_directory)
            }
            
            return info
            
        except Exception as e:
            print(f"❌ 获取数据库信息失败: {e}")
            return {}
    
    def delete_database(self) -> bool:
        """
        删除数据库
        
        Returns:
            bool: 是否成功删除
        """
        try:
            import shutil
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                print(f"🗑️ 已删除数据库: {self.db_name}")
                return True
            else:
                print(f"⚠️ 数据库不存在: {self.db_name}")
                return False
        except Exception as e:
            print(f"❌ 删除数据库失败: {e}")
            return False


def create_vectorstore_from_markdown(
    markdown_file: str,
    secret_id: str,
    secret_key: str,
    db_name: str = "tencent.im.db"
) -> TencentIMVectorStore:
    """
    从Markdown文件创建向量数据库
    
    Args:
        markdown_file (str): Markdown文件路径
        secret_id (str): 腾讯云API密钥ID
        secret_key (str): 腾讯云API密钥Key
        db_name (str): 数据库名称
        
    Returns:
        TencentIMVectorStore: 向量存储管理器
    """
    print(f"🚀 开始创建向量数据库: {db_name}")
    
    # 1. 读取和分割文档
    print("📖 读取和分割Markdown文档...")
    chunks = read_and_split_document(markdown_file, "###")
    
    if not chunks:
        raise ValueError("无法读取或分割文档")
    
    print(f"📄 成功分割出 {len(chunks)} 个文档块")
    
    # 2. 初始化向量存储管理器
    print("🔧 初始化向量存储管理器...")
    vector_manager = TencentIMVectorStore(
        secret_id=secret_id,
        secret_key=secret_key,
        db_name=db_name
    )
    
    # 3. 转换为Document格式
    print("📝 转换文档格式...")
    documents = vector_manager.chunks_to_documents(chunks)
    
    # 4. 存储到向量数据库
    print("💾 存储到向量数据库...")
    success = vector_manager.add_documents_to_vectorstore(documents, batch_size=3)
    
    if success:
        print(f"✅ 向量数据库 {db_name} 创建成功！")
    else:
        print(f"❌ 向量数据库 {db_name} 创建失败！")
    
    return vector_manager


def demo_vectorstore_operations():
    """
    演示向量数据库操作
    """
    print("🎯 腾讯云IM文档向量数据库演示")
    print("=" * 60)
    
    # 配置信息（需要替换为实际的密钥）
    SECRET_ID = "your_secret_id_here"  # 请替换为实际的密钥
    SECRET_KEY = "your_secret_key_here"  # 请替换为实际的密钥
    DB_NAME = "tencent.im.db"
    MARKDOWN_FILE = "/Users/zhangtianqi/git_root/agent_homework/ch8/腾讯云IM群组系统完整文档.md"
    
    # 检查是否需要替换密钥
    if SECRET_ID == "your_secret_id_here":
        print("⚠️ 请在代码中设置正确的腾讯云API密钥")
        print("💡 修改 SECRET_ID 和 SECRET_KEY 变量")
        return
    
    try:
        # 1. 创建向量数据库
        vector_manager = create_vectorstore_from_markdown(
            markdown_file=MARKDOWN_FILE,
            secret_id=SECRET_ID,
            secret_key=SECRET_KEY,
            db_name=DB_NAME
        )
        
        # 2. 显示数据库信息
        print("\n📊 数据库信息:")
        info = vector_manager.get_database_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        # 3. 演示搜索功能
        print("\n🔍 搜索演示:")
        test_queries = [
            "直播群有什么特点",
            "如何设置群组权限",
            "群成员管理功能",
            "社群Community的优势"
        ]
        
        for query in test_queries:
            print(f"\n查询: '{query}'")
            results = vector_manager.search_similar_documents(query, k=3)
            
            for i, result in enumerate(results):
                print(f"  {i+1}. {result['title']} (相似度: {result['similarity_score']:.4f})")
                print(f"     内容预览: {result['content'][:100]}...")
    
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")


if __name__ == "__main__":
    demo_vectorstore_operations()