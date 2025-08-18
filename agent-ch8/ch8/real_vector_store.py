#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实的腾讯云IM文档向量数据库
使用TencentLKEEmbeddings进行向量化存储
"""

import json
import os
import time
from typing import List, Dict
from langchain_core.documents import Document
from langchain_chroma import Chroma
from tencent_embeddings import TencentLKEEmbeddings
from document_splitter import read_and_split_document


class TencentIMVectorDatabase:
    """腾讯云IM文档向量数据库管理器"""
    
    def __init__(self, secret_id: str, secret_key: str, db_name: str = "tencent.im.db"):
        """
        初始化向量数据库管理器
        
        Args:
            secret_id (str): 腾讯云API密钥ID
            secret_key (str): 腾讯云API密钥Key
            db_name (str): 数据库名称
        """
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.db_name = db_name
        self.persist_directory = f"./{db_name}"
        
        # 初始化腾讯云嵌入模型
        print("🔧 初始化TencentLKEEmbeddings...")
        self.embeddings = TencentLKEEmbeddings(
            secret_id=secret_id,
            secret_key=secret_key,
            region="ap-guangzhou"
        )
        
        # 向量数据库实例
        self.vectorstore = None
    
    def create_database_from_markdown(self, markdown_file: str, batch_size: int = 3) -> bool:
        """
        从Markdown文件创建向量数据库
        
        Args:
            markdown_file (str): Markdown文件路径
            batch_size (int): 批处理大小（避免API频率限制）
            
        Returns:
            bool: 是否创建成功
        """
        try:
            print(f"🚀 开始创建向量数据库: {self.db_name}")
            
            # 1. 读取和分割文档
            print("📖 读取和分割Markdown文档...")
            chunks = read_and_split_document(markdown_file, "###")
            
            if not chunks:
                print("❌ 无法读取或分割文档")
                return False
            
            print(f"📄 成功分割出 {len(chunks)} 个文档块")
            
            # 2. 转换为Document格式
            print("📝 转换为Langchain Document格式...")
            documents = self._chunks_to_documents(chunks)
            print(f"✅ 转换了 {len(documents)} 个文档")
            
            # 3. 删除已存在的数据库
            if os.path.exists(self.persist_directory):
                import shutil
                shutil.rmtree(self.persist_directory)
                print(f"🗑️ 删除已存在的数据库: {self.db_name}")
            
            # 4. 分批创建向量数据库（避免API频率限制）
            print(f"💾 开始向量化并创建数据库（批次大小: {batch_size}）...")
            
            # 处理第一批，创建数据库
            first_batch = documents[:batch_size]
            print(f"🔄 处理第1批 ({len(first_batch)} 个文档)")
            
            self.vectorstore = Chroma.from_documents(
                documents=first_batch,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            # 处理剩余批次
            remaining_docs = documents[batch_size:]
            if remaining_docs:
                for i in range(0, len(remaining_docs), batch_size):
                    batch_num = i // batch_size + 2
                    batch = remaining_docs[i:i + batch_size]
                    
                    print(f"🔄 处理第{batch_num}批 ({len(batch)} 个文档)")
                    
                    # 添加到现有数据库
                    self.vectorstore.add_documents(batch)
                    
                    # 添加延迟避免API频率限制
                    if i + batch_size < len(remaining_docs):
                        print("⏱️ 等待3秒以避免API频率限制...")
                        time.sleep(3)
            
            print(f"✅ 向量数据库 {self.db_name} 创建成功！")
            return True
            
        except Exception as e:
            print(f"❌ 创建向量数据库失败: {e}")
            return False
    
    def load_existing_database(self) -> bool:
        """
        加载已存在的向量数据库
        
        Returns:
            bool: 是否加载成功
        """
        try:
            if not os.path.exists(self.persist_directory):
                print(f"❌ 数据库不存在: {self.db_name}")
                return False
            
            print(f"📂 加载已存在的向量数据库: {self.db_name}")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            
            print(f"✅ 数据库加载成功")
            return True
            
        except Exception as e:
            print(f"❌ 加载数据库失败: {e}")
            return False
    
    def search_documents(self, query: str, k: int = 5) -> List[Dict]:
        """
        搜索相似文档
        
        Args:
            query (str): 查询文本
            k (int): 返回文档数量
            
        Returns:
            List[Dict]: 搜索结果
        """
        if not self.vectorstore:
            print("❌ 向量数据库未初始化")
            return []
        
        try:
            print(f"🔍 搜索查询: '{query}'")
            
            # 执行相似性搜索
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            search_results = []
            for doc, score in results:
                result = {
                    'title': doc.metadata.get('title', 'Unknown'),
                    'content_preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    'full_content': doc.page_content,
                    'metadata': doc.metadata,
                    'similarity_score': float(1 - score),  # 转换为相似度
                    'distance_score': float(score)
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
            if not self.vectorstore:
                return {'error': '数据库未初始化'}
            
            all_docs = self.vectorstore.get()
            total_docs = len(all_docs['ids']) if all_docs['ids'] else 0
            
            # 计算数据库大小
            db_size = self._get_folder_size(self.persist_directory)
            
            info = {
                'database_name': self.db_name,
                'persist_directory': self.persist_directory,
                'total_documents': total_docs,
                'embedding_model': 'TencentLKEEmbeddings',
                'database_size_mb': round(db_size, 2),
                'database_exists': os.path.exists(self.persist_directory)
            }
            
            return info
            
        except Exception as e:
            return {'error': f'获取数据库信息失败: {e}'}
    
    def _chunks_to_documents(self, chunks: List[Dict]) -> List[Document]:
        """将文档块转换为Langchain Document格式"""
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
        
        return documents
    
    def _get_folder_size(self, folder_path: str) -> float:
        """获取文件夹大小（MB）"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(file_path)
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0


def demo_real_vector_store():
    """
    真实向量数据库演示
    """
    print("🎯 腾讯云IM文档向量数据库 (真实版本)")
    print("=" * 60)
    
    # 直接使用API密钥
    SECRET_ID = ""
    SECRET_KEY = ""
    DB_NAME = "tencent.im.db"
    MARKDOWN_FILE = "/Users/zhangtianqi/git_root/agent_homework/ch8/腾讯云IM群组系统完整文档.md"
    
    print(f"📖 使用API密钥: {SECRET_ID[:10]}...")
    
    # 检查API密钥配置
    if SECRET_ID == "your_secret_id_here" or SECRET_KEY == "your_secret_key_here":
        print("⚠️ 请配置真实的腾讯云API密钥")
        print("💡 修改SECRET_ID和SECRET_KEY变量")
        print("🔑 获取密钥: https://console.cloud.tencent.com/cam/capi")
        return
    
    try:
        # 1. 初始化向量数据库管理器
        db_manager = TencentIMVectorDatabase(
            secret_id=SECRET_ID,
            secret_key=SECRET_KEY,
            db_name=DB_NAME
        )
        
        # 2. 尝试加载已存在的数据库，如果不存在则创建
        if not db_manager.load_existing_database():
            print("📝 数据库不存在，开始创建...")
            success = db_manager.create_database_from_markdown(MARKDOWN_FILE, batch_size=2)
            
            if not success:
                print("❌ 数据库创建失败")
                return
        
        # 3. 显示数据库信息
        print("\n📊 数据库信息:")
        info = db_manager.get_database_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        # 4. 演示搜索功能
        print("\n🔍 搜索功能演示:")
        test_queries = [
            "直播群AVChatRoom的特点",
            "社群Community支持多少人",
            "如何设置群组权限",
            "群成员管理功能有哪些",
            "消息存储和漫游规则"
        ]
        
        search_results = {}
        
        for query in test_queries:
            print(f"\n🔎 查询: '{query}'")
            results = db_manager.search_documents(query, k=3)
            
            search_results[query] = results
            
            for i, result in enumerate(results):
                print(f"   {i+1}. 📄 {result['title']}")
                print(f"      🎯 相似度: {result['similarity_score']:.4f}")
                print(f"      📝 内容: {result['content_preview'][:80]}...")
        
        # 5. 保存搜索结果
        output_file = "real_vector_search_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'database_info': info,
                'search_results': search_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 搜索结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")


def create_config_template():
    """
    创建配置文件模板
    """
    config_template = {
        "tencent_cloud": {
            "secret_id": "your_secret_id_here",
            "secret_key": "your_secret_key_here",
            "region": "ap-guangzhou"
        },
        "vector_database": {
            "name": "tencent.im.db",
            "batch_size": 3,
            "embedding_model": "lke-text-embedding-v1"
        },
        "documents": {
            "source_file": "/Users/zhangtianqi/git_root/agent_homework/ch8/腾讯云IM群组系统完整文档.md",
            "split_level": "###"
        }
    }
    
    config_file = "vector_store_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_template, f, ensure_ascii=False, indent=2)
    
    print(f"📝 配置文件模板已创建: {config_file}")
    print("💡 请编辑配置文件并设置正确的API密钥")


if __name__ == "__main__":
    print("🚀 腾讯云IM文档向量数据库 - 真实版本")
    print("=" * 80)
    
    # 创建配置模板
    create_config_template()
    
    # 运行演示
    demo_real_vector_store()
