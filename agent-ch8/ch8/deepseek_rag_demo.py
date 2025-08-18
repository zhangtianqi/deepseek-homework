#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云IM文档RAG系统 - 集成DeepSeek LLM
实现真正的检索增强生成，使用DeepSeek作为生成模型
"""

import json
import time
import os
from typing import List, Dict, Optional
from datetime import datetime

# 导入自定义模块
from document_splitter import read_and_split_document
from real_vector_store import TencentIMVectorDatabase
from tencent_embeddings import TencentLKEEmbeddings

# 导入OpenAI库（用于DeepSeek API）
try:
    from openai import OpenAI
except ImportError:
    print("❌ 请安装openai库: pip install openai>=1.0.0")
    exit(1)


class DeepSeekRAGSystem:
    """基于DeepSeek LLM的腾讯云IM文档RAG系统"""
    
    def __init__(self, config_file: str = "vector_store_config.json"):
        """
        初始化RAG系统
        
        Args:
            config_file (str): 配置文件路径
        """
        self.config = self._load_config(config_file)
        self.db_manager = None
        self.embeddings = None
        self.llm_client = None
        self._initialize_components()
    
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 成功加载配置文件: {config_file}")
            return config
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            # 使用默认配置
            return {
                "tencent_cloud": {
                    "secret_id": "your_secret_id_here",
                    "secret_key": "your_secret_key_here",
                    "region": "ap-guangzhou"
                },
                "vector_database": {
                    "name": "tencent.im.db",
                    "batch_size": 3
                },
                "documents": {
                    "source_file": "./腾讯云IM群组系统完整文档.md",
                    "split_level": "###"
                }
            }
    
    def _initialize_components(self):
        """初始化各个组件"""
        print("🔧 初始化DeepSeek RAG系统组件...")
        
        # 1. 设置DeepSeek API
        os.environ["OPENAI_API_KEY"] = "sk-97aa33f5e09f41bbb7a29def74ab334a"
        os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com"
        
        self.llm_client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ["OPENAI_BASE_URL"]
        )
        self.model_name = "deepseek-chat"
        
        print("✅ DeepSeek LLM客户端初始化完成")
        
        # 2. 检查API密钥
        secret_id = self.config['tencent_cloud']['secret_id']
        secret_key = self.config['tencent_cloud']['secret_key']
        
        if secret_id == "your_secret_id_here":
            print("⚠️ 检测到模板配置，使用内置API密钥")
            secret_id = ""
            secret_key = ""
        
        # 3. 初始化嵌入模型
        self.embeddings = TencentLKEEmbeddings(
            secret_id=secret_id,
            secret_key=secret_key
        )
        
        # 4. 初始化向量数据库管理器
        self.db_manager = TencentIMVectorDatabase(
            secret_id=secret_id,
            secret_key=secret_key,
            db_name=self.config['vector_database']['name']
        )
        
        print("✅ 向量数据库组件初始化完成")
    
    def setup_pipeline(self) -> bool:
        """
        设置完整的RAG流水线
        
        Returns:
            bool: 设置是否成功
        """
        print("🚀 开始设置DeepSeek RAG流水线")
        print("=" * 60)
        
        try:
            # 1. 测试DeepSeek API连接
            print("🧪 测试DeepSeek API连接...")
            test_response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            print(f"✅ DeepSeek API连接成功: {test_response.choices[0].message.content}")
            
            # 2. 检查源文档
            source_file = self.config['documents']['source_file']
            if not os.path.exists(source_file):
                print(f"❌ 源文档不存在: {source_file}")
                return False
            
            print(f"📄 找到源文档: {source_file}")
            
            # 3. 检查向量数据库
            if not self.db_manager.load_existing_database():
                print("📝 向量数据库不存在，开始创建...")
                
                # 创建新的向量数据库
                success = self.db_manager.create_database_from_markdown(
                    source_file,
                    batch_size=self.config['vector_database']['batch_size']
                )
                
                if not success:
                    print("❌ 向量数据库创建失败")
                    return False
            else:
                print("✅ 向量数据库加载成功")
            
            # 4. 显示数据库信息
            db_info = self.db_manager.get_database_info()
            print(f"\n📊 数据库信息:")
            for key, value in db_info.items():
                print(f"   {key}: {value}")
            
            print("\n✅ DeepSeek RAG流水线设置完成!")
            return True
            
        except Exception as e:
            print(f"❌ 设置流水线失败: {e}")
            return False
    
    def retrieve_documents(self, query: str, k: int = 5) -> List[Dict]:
        """
        检索相关文档
        
        Args:
            query (str): 查询文本
            k (int): 返回文档数量
            
        Returns:
            List[Dict]: 检索结果
        """
        if not self.db_manager:
            print("❌ 数据库管理器未初始化")
            return []
        
        print(f"🔍 检索查询: '{query}'")
        
        try:
            start_time = time.time()
            results = self.db_manager.search_documents(query, k=k)
            search_time = time.time() - start_time
            
            print(f"✅ 检索完成，用时 {search_time:.3f}秒，找到 {len(results)} 个相关文档")
            
            # 显示检索结果
            for i, result in enumerate(results):
                print(f"   {i+1}. 📄 {result['title']} (相似度: {result['similarity_score']:.4f})")
            
            return results
            
        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return []
    
    def build_context(self, results: List[Dict], max_tokens: int = 3000) -> str:
        """
        构建RAG上下文
        
        Args:
            results (List[Dict]): 检索结果
            max_tokens (int): 最大token数（估算）
            
        Returns:
            str: 构建的上下文
        """
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for result in results:
            title = result['title']
            content = result['full_content']
            
            # 格式化文档块
            section = f"【{title}】\n{content}\n\n"
            
            # 检查长度限制（粗略估算，1个中文字符≈1.5个token）
            section_tokens = len(section) * 1.5
            if current_length + section_tokens <= max_tokens:
                context_parts.append(section)
                current_length += section_tokens
            else:
                # 如果超出限制，截断最后一个文档
                remaining_tokens = max_tokens - current_length
                if remaining_tokens > 200:  # 至少保留200个token
                    remaining_chars = int(remaining_tokens / 1.5)
                    truncated = section[:remaining_chars] + "...\n\n"
                    context_parts.append(truncated)
                break
        
        context = "".join(context_parts)
        estimated_tokens = len(context) * 1.5
        print(f"📝 构建上下文完成，长度: {len(context)} 字符，预估: {estimated_tokens:.0f} tokens")
        
        return context
    
    def generate_answer_with_deepseek(self, query: str, context: str) -> Dict:
        """
        使用DeepSeek LLM生成答案
        
        Args:
            query (str): 用户查询
            context (str): 检索到的上下文
            
        Returns:
            Dict: 生成结果
        """
        print("🤖 使用DeepSeek生成答案...")
        
        # 构建专业的RAG提示词
#         system_prompt = """你是腾讯云即时通信IM的专业技术助手。请基于提供的文档内容回答用户问题。

# 回答要求：
# 1. 基于提供的文档内容回答，不要编造信息
# 2. 如果文档中没有相关信息，请明确说明
# 3. 回答要结构化、专业、准确
# 4. 使用表格、列表等格式提高可读性
# 5. 重点信息用**粗体**标注

# 文档内容：
# {context}"""

#         user_prompt = f"""基于上述腾讯云IM文档内容，请回答以下问题：

# {query}

# 请提供详细、准确的回答。"""

        try:
            start_time = time.time()
            
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt.format(context=context)},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.1,  # 较低的温度确保准确性
                stream=False
            )
            
            generation_time = time.time() - start_time
            
            answer = response.choices[0].message.content
            
            print(f"✅ DeepSeek答案生成完成，用时: {generation_time:.3f}秒")
            
            return {
                "answer": answer,
                "generation_time": generation_time,
                "model": self.model_name,
                "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            print(f"❌ DeepSeek答案生成失败: {e}")
            return {
                "answer": f"抱歉，生成答案时发生错误: {str(e)}",
                "generation_time": 0,
                "model": self.model_name,
                "error": str(e)
            }
    
    def run_deepseek_rag(self, query: str) -> Dict:
        """
        运行完整的DeepSeek RAG流程
        
        Args:
            query (str): 用户查询
            
        Returns:
            Dict: 完整的RAG结果
        """
        print(f"\n🎯 开始DeepSeek RAG流程处理")
        print(f"📝 用户查询: '{query}'")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            # 1. 文档检索
            print("🔍 步骤1: 向量检索")
            retrieved_docs = self.retrieve_documents(query, k=5)
            
            if not retrieved_docs:
                return {
                    'query': query,
                    'error': '未找到相关文档',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 2. 上下文构建
            print("\n📝 步骤2: 上下文构建")
            context = self.build_context(retrieved_docs, max_tokens=3000)
            
            # 3. DeepSeek答案生成
            print("\n🤖 步骤3: DeepSeek答案生成")
            generation_result = self.generate_answer_with_deepseek(query, context)
            
            total_time = time.time() - start_time
            
            # 4. 结果汇总
            result = {
                'query': query,
                'answer': generation_result['answer'],
                'llm_info': {
                    'model': generation_result['model'],
                    'generation_time': generation_result['generation_time'],
                    'prompt_tokens': generation_result.get('prompt_tokens', 0),
                    'completion_tokens': generation_result.get('completion_tokens', 0),
                    'total_tokens': generation_result.get('total_tokens', 0)
                },
                'retrieved_documents': [
                    {
                        'title': doc['title'],
                        'similarity_score': doc['similarity_score'],
                        'content_preview': doc['content_preview']
                    }
                    for doc in retrieved_docs
                ],
                'context_length': len(context),
                'total_processing_time': round(total_time, 3),
                'timestamp': datetime.now().isoformat()
            }
            
            if 'error' in generation_result:
                result['llm_error'] = generation_result['error']
            
            print(f"\n✅ DeepSeek RAG流程完成，总用时: {total_time:.3f}秒")
            return result
            
        except Exception as e:
            print(f"❌ DeepSeek RAG流程失败: {e}")
            return {
                'query': query,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_batch_demo(self) -> Dict:
        """
        运行批量DeepSeek RAG演示测试
        
        Returns:
            Dict: 批量测试结果
        """
        print("🚀 开始批量DeepSeek RAG演示测试")
        print("=" * 80)
        
        # 测试查询列表
        test_queries = [
            "直播群AVChatRoom有什么特点和限制？",
            "社群Community最多支持多少人？如何申请更大规模？",
            "如何设置群组权限？权限组功能是怎样的？",
            "Work群和Public群在功能上有什么主要区别？",
            "群成员资料包含哪些字段？自定义字段有什么特性？",
            "群组的自动回收规则是什么？不同类型群组有差异吗？"
        ]
        
        results = []
        total_start = time.time()
        
        for i, query in enumerate(test_queries):
            print(f"\n{'='*80}")
            print(f"测试 {i+1}/{len(test_queries)}")
            
            result = self.run_deepseek_rag(query)
            results.append(result)
            
            # 简要显示结果
            if 'error' not in result:
                print(f"\n📋 DeepSeek答案预览:")
                preview = result['answer'][:200] + "..." if len(result['answer']) > 200 else result['answer']
                print(f"   {preview}")
                
                if 'llm_info' in result:
                    llm_info = result['llm_info']
                    print(f"\n💬 LLM使用统计:")
                    print(f"   模型: {llm_info['model']}")
                    print(f"   生成时间: {llm_info['generation_time']:.3f}秒")
                    print(f"   Tokens: {llm_info.get('total_tokens', 0)} (输入: {llm_info.get('prompt_tokens', 0)}, 输出: {llm_info.get('completion_tokens', 0)})")
            
            # 避免API频率限制
            if i < len(test_queries) - 1:
                print("⏱️ 等待3秒...")
                time.sleep(3)
        
        total_time = time.time() - total_start
        
        # 生成测试总结
        successful_results = [r for r in results if 'error' not in r]
        
        summary = {
            'total_queries': len(test_queries),
            'successful_queries': len(successful_results),
            'failed_queries': len(test_queries) - len(successful_results),
            'total_time': round(total_time, 3),
            'avg_time_per_query': round(total_time / len(test_queries), 3)
        }
        
        # 计算LLM统计
        if successful_results:
            total_tokens = sum(r.get('llm_info', {}).get('total_tokens', 0) for r in successful_results)
            avg_generation_time = sum(r.get('llm_info', {}).get('generation_time', 0) for r in successful_results) / len(successful_results)
            
            summary.update({
                'total_tokens_used': total_tokens,
                'avg_generation_time': round(avg_generation_time, 3),
                'avg_tokens_per_query': round(total_tokens / len(successful_results), 1) if successful_results else 0
            })
        
        final_result = {
            'summary': summary,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存结果
        with open('deepseek_rag_demo_results.json', 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*80}")
        print(f"📊 DeepSeek RAG批量测试总结")
        print(f"{'='*80}")
        print(f"📝 总查询数: {summary['total_queries']}")
        print(f"✅ 成功查询: {summary['successful_queries']}")
        print(f"❌ 失败查询: {summary['failed_queries']}")
        print(f"⏱️ 总耗时: {summary['total_time']}秒")
        print(f"📈 平均耗时: {summary['avg_time_per_query']}秒/查询")
        
        if 'total_tokens_used' in summary:
            print(f"💬 总Token使用: {summary['total_tokens_used']}")
            print(f"📊 平均Token/查询: {summary['avg_tokens_per_query']}")
            print(f"🤖 平均生成时间: {summary['avg_generation_time']}秒")
        
        print(f"💾 结果已保存到: deepseek_rag_demo_results.json")
        
        return final_result


def main():
    """主函数"""
    print("🎯 腾讯云IM文档DeepSeek RAG系统演示")
    print("=" * 80)
    
    try:
        # 1. 初始化DeepSeek RAG系统
        rag_system = DeepSeekRAGSystem()
        
        # 2. 设置流水线
        if not rag_system.setup_pipeline():
            print("❌ DeepSeek RAG流水线设置失败")
            return
        
        # 3. 运行单个查询演示
        print(f"\n{'='*80}")
        print("🔍 单个DeepSeek RAG查询演示")
        print(f"{'='*80}")
        
        demo_query = "直播群AVChatRoom有什么特点和限制？"
        single_result = rag_system.run_deepseek_rag(demo_query)
        
        if 'error' not in single_result:
            print(f"\n📋 DeepSeek完整答案:")
            print(f"{single_result['answer']}")
            print(f"\n📊 检索到 {len(single_result['retrieved_documents'])} 个相关文档")
            print(f"⏱️ 总处理时间: {single_result['total_processing_time']}秒")
            if 'llm_info' in single_result:
                llm_info = single_result['llm_info']
                print(f"🤖 LLM信息: {llm_info['model']}, 生成时间: {llm_info['generation_time']:.3f}秒, Tokens: {llm_info.get('total_tokens', 0)}")
        
        # 4. 运行批量演示
        print(f"\n{'='*80}")
        print("🎛️ 批量DeepSeek RAG查询演示")
        print(f"{'='*80}")
        
        batch_results = rag_system.run_batch_demo()
        
        print(f"\n🎉 DeepSeek RAG演示完成!")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")


if __name__ == "__main__":
    main()
