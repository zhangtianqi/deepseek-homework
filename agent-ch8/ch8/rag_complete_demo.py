#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云IM文档完整RAG演示
整合文档分割、向量存储、召回测试和答案生成的完整流程
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


class CompleteTencentIMRAG:
    """完整的腾讯云IM文档RAG系统"""
    
    def __init__(self, config_file: str = "vector_store_config.json"):
        """
        初始化RAG系统
        
        Args:
            config_file (str): 配置文件路径
        """
        self.config = self._load_config(config_file)
        self.db_manager = None
        self.embeddings = None
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
        print("🔧 初始化RAG系统组件...")
        
        # 检查API密钥
        secret_id = self.config['tencent_cloud']['secret_id']
        secret_key = self.config['tencent_cloud']['secret_key']
        
        if secret_id == "your_secret_id_here":
            print("⚠️ 检测到模板配置，使用内置API密钥")
            secret_id = ""
            secret_key = ""
        
        # 初始化嵌入模型
        self.embeddings = TencentLKEEmbeddings(
            secret_id=secret_id,
            secret_key=secret_key
        )
        
        # 初始化向量数据库管理器
        self.db_manager = TencentIMVectorDatabase(
            secret_id=secret_id,
            secret_key=secret_key,
            db_name=self.config['vector_database']['name']
        )
        
        print("✅ 组件初始化完成")
    
    def setup_pipeline(self) -> bool:
        """
        设置完整的RAG流水线
        
        Returns:
            bool: 设置是否成功
        """
        print("🚀 开始设置RAG流水线")
        print("=" * 60)
        
        try:
            # 1. 检查源文档
            source_file = self.config['documents']['source_file']
            if not os.path.exists(source_file):
                print(f"❌ 源文档不存在: {source_file}")
                return False
            
            print(f"📄 找到源文档: {source_file}")
            
            # 2. 检查向量数据库
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
            
            # 3. 显示数据库信息
            db_info = self.db_manager.get_database_info()
            print(f"\n📊 数据库信息:")
            for key, value in db_info.items():
                print(f"   {key}: {value}")
            
            print("\n✅ RAG流水线设置完成!")
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
    
    def build_context(self, results: List[Dict], max_tokens: int = 2000) -> str:
        """
        构建RAG上下文
        
        Args:
            results (List[Dict]): 检索结果
            max_tokens (int): 最大token数
            
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
            section = f"## {title}\n\n{content}\n\n"
            
            # 检查长度限制
            if current_length + len(section) <= max_tokens:
                context_parts.append(section)
                current_length += len(section)
            else:
                # 如果超出限制，截断最后一个文档
                remaining = max_tokens - current_length
                if remaining > 100:  # 至少保留100字符
                    truncated = section[:remaining] + "...\n\n"
                    context_parts.append(truncated)
                break
        
        context = "".join(context_parts)
        print(f"📝 构建上下文完成，长度: {len(context)} 字符")
        
        return context
    
    def generate_answer(self, query: str, context: str) -> str:
        """
        生成答案（模拟LLM响应）
        
        Args:
            query (str): 用户查询
            context (str): 检索到的上下文
            
        Returns:
            str: 生成的答案
        """
        # 这里模拟LLM的回答生成过程
        # 在实际应用中，这里会调用真实的LLM API
        
        print("🤖 生成答案中...")
        
        # 模拟处理时间
        time.sleep(0.5)
        
        # 分析查询类型
        query_lower = query.lower()
        
        if "直播群" in query or "avchatroom" in query_lower:
            answer = self._generate_avchatroom_answer(context)
        elif "社群" in query or "community" in query_lower:
            answer = self._generate_community_answer(context)
        elif "权限" in query:
            answer = self._generate_permission_answer(context)
        elif "区别" in query or "差异" in query:
            answer = self._generate_comparison_answer(context)
        elif "字段" in query or "资料" in query:
            answer = self._generate_fields_answer(context)
        else:
            answer = self._generate_general_answer(query, context)
        
        print("✅ 答案生成完成")
        return answer
    
    def _generate_avchatroom_answer(self, context: str) -> str:
        """生成直播群相关答案"""
        return """基于腾讯云IM文档，直播群（AVChatRoom）具有以下特点：

**核心特性：**
- 成员人数无上限，支持大规模直播场景
- 可随意进出群组，无需审批
- 支持以游客身份接收消息（Web端和小程序端）

**功能限制：**
- 不支持历史消息存储
- 不支持消息漫游功能
- 不支持离线推送
- 群组创建后40天内无人发言将被自动解散

**适用场景：**
适用于互动直播聊天室等场景，特别是需要大量用户同时在线互动的直播活动。

**注意事项：**
如果预期群成员会出现短时间内激增的场景（如大型在线活动），需要提前3天联系腾讯云客服进行服务资源报备。"""
    
    def _generate_community_answer(self, context: str) -> str:
        """生成社群相关答案"""
        return """基于腾讯云IM文档，社群（Community）的规模和特点如下：

**成员规模：**
- 常规支持：10万人
- 最大支持：100万人（企业版客户可提交工单申请）

**核心优势：**
- 支持分组和话题功能，实现分层级沟通
- 可容纳超大规模成员，共用一套好友关系
- 支持权限组管理，灵活控制成员权限

**功能特性：**
- 创建成功后可以随意进出
- 支持历史消息存储和漫游
- 支持消息回调和离线推送
- 可以设置不同的权限组管理成员

**适用场景：**
兴趣交友、游戏社交、粉丝运营、组织管理等需要大规模用户协作的场景。

**技术要求：**
需要终端SDK 5.8.1668增强版及以上版本，Web SDK 2.17.0及以上版本。"""
    
    def _generate_permission_answer(self, context: str) -> str:
        """生成权限相关答案"""
        return """基于腾讯云IM文档，群组权限设置说明如下：

**权限组功能：**
社群（Community）支持权限组功能，可以对不同成员设置不同权限。

**权限表示方式：**
权限采用按位的方式进行表示，主要权限包括：

**基础权限：**
- ModifyGroupInfo (1<<0): 修改群资料权限
- KickGroupMember (1<<1): 踢出群成员权限  
- BanGroupMember (1<<2): 禁言群成员权限
- GetOnlineMemberNum (1<<3): 获取群在线成员数权限

**话题权限：**
- ManageTopic (1<<0): 管理话题权限
- CreateTopic (1<<1): 创建话题权限
- SendTopicMessage (1<<2): 发送话题消息权限
- GetTopicMessage (1<<3): 拉取话题消息权限

**配置方法：**
可以通过即时通信IM控制台进行配置，支持灵活的权限组合管理。"""
    
    def _generate_comparison_answer(self, context: str) -> str:
        """生成对比类答案"""
        return """基于腾讯云IM文档，不同群组类型的主要区别如下：

**Work群（好友工作群）：**
- 适用于私密聊天场景，如企业内部员工群
- 成员上限：200人（可扩展至6000人）
- 只能由群成员邀请入群，不支持申请加群
- 无群主概念，所有成员均可管理群组

**Public群（陌生人社交群）：**
- 适用于公开群组，群主管理群组
- 成员上限：2000人（可扩展至6000人）
- 支持申请加群，需要群主或管理员审批
- 可以通过搜索群ID找到群组

**主要差异对比：**
- 加群方式：Work群仅支持邀请，Public群支持申请+邀请
- 管理权限：Work群所有成员可管理，Public群群主具备完整管理权限
- 群组搜索：Work群不支持搜索，Public群支持搜索
- 成员资料：Work群成员资料对外不可见，Public群支持对外展示"""
    
    def _generate_fields_answer(self, context: str) -> str:
        """生成字段相关答案"""
        return """基于腾讯云IM文档，群成员资料包含以下主要字段：

**基础字段：**
- Member_Account: 成员账号
- Role: 成员角色（Owner/Admin/Member）
- JoinTime: 入群时间
- NameCard: 群名片（最长50字节）

**消息相关：**
- MsgSeq: 成员消息序列号
- MsgFlag: 成员消息接收选项（AcceptAndNotify/AcceptNotNotify/Discard）
- LastSendMsgTime: 最后发言时间

**管理相关：**
- MuteUntil: 禁言到期时间
- AppMemberDefinedData: 群成员自定义字段

**自定义字段特性：**
- 支持Key-Value形式
- Key长度不超过16字节
- Value长度不超过64字节（群成员维度）
- 支持配置读写权限

这些字段为群组管理和成员信息维护提供了完整的数据结构支持。"""
    
    def _generate_general_answer(self, query: str, context: str) -> str:
        """生成通用答案"""
        return f"""基于腾讯云IM群组系统文档，针对您的问题"{query}"，提供以下信息：

根据检索到的相关文档内容，腾讯云即时通信IM提供了完整的群组系统功能，包括：

**群组类型：**
- 好友工作群（Work）
- 陌生人社交群（Public） 
- 临时会议群（Meeting）
- 直播群（AVChatRoom）
- 社群（Community）

**核心功能：**
- 完备的群组管理能力
- 稳定可靠的消息收发
- 权限控制和成员管理
- 自定义字段扩展
- 丰富的回调机制

如需了解更详细的信息，建议查看具体的功能模块文档或联系腾讯云技术支持。"""
    
    def run_complete_rag(self, query: str) -> Dict:
        """
        运行完整的RAG流程
        
        Args:
            query (str): 用户查询
            
        Returns:
            Dict: 完整的RAG结果
        """
        print(f"\n🎯 开始RAG流程处理")
        print(f"📝 用户查询: '{query}'")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 1. 文档检索
            print("🔍 步骤1: 文档检索")
            retrieved_docs = self.retrieve_documents(query, k=5)
            
            if not retrieved_docs:
                return {
                    'query': query,
                    'error': '未找到相关文档',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 2. 上下文构建
            print("\n📝 步骤2: 上下文构建")
            context = self.build_context(retrieved_docs, max_tokens=2000)
            
            # 3. 答案生成
            print("\n🤖 步骤3: 答案生成")
            answer = self.generate_answer(query, context)
            
            total_time = time.time() - start_time
            
            # 4. 结果汇总
            result = {
                'query': query,
                'answer': answer,
                'retrieved_documents': [
                    {
                        'title': doc['title'],
                        'similarity_score': doc['similarity_score'],
                        'content_preview': doc['content_preview']
                    }
                    for doc in retrieved_docs
                ],
                'context_length': len(context),
                'processing_time': round(total_time, 3),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"\n✅ RAG流程完成，总用时: {total_time:.3f}秒")
            return result
            
        except Exception as e:
            print(f"❌ RAG流程失败: {e}")
            return {
                'query': query,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_batch_demo(self) -> Dict:
        """
        运行批量演示测试
        
        Returns:
            Dict: 批量测试结果
        """
        print("🚀 开始批量RAG演示测试")
        print("=" * 80)
        
        # 测试查询列表
        test_queries = [
            "直播群AVChatRoom有什么特点？",
            "社群Community最多支持多少人？",
            "如何设置群组权限？",
            "Work群和Public群有什么区别？",
            "群成员资料包含哪些字段？",
            "消息存储和漫游是怎么工作的？",
            "自定义字段有什么特性？",
            "群组自动回收规则是什么？"
        ]
        
        results = []
        total_start = time.time()
        
        for i, query in enumerate(test_queries):
            print(f"\n{'='*60}")
            print(f"测试 {i+1}/{len(test_queries)}")
            
            result = self.run_complete_rag(query)
            results.append(result)
            
            # 简要显示结果
            if 'error' not in result:
                print(f"\n📋 答案预览:")
                preview = result['answer'][:150] + "..." if len(result['answer']) > 150 else result['answer']
                print(f"   {preview}")
            
            # 避免API频率限制
            if i < len(test_queries) - 1:
                print("⏱️ 等待2秒...")
                time.sleep(2)
        
        total_time = time.time() - total_start
        
        # 生成测试总结
        summary = {
            'total_queries': len(test_queries),
            'successful_queries': len([r for r in results if 'error' not in r]),
            'failed_queries': len([r for r in results if 'error' in r]),
            'total_time': round(total_time, 3),
            'avg_time_per_query': round(total_time / len(test_queries), 3)
        }
        
        final_result = {
            'summary': summary,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存结果
        with open('rag_demo_results.json', 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*80}")
        print(f"📊 批量测试总结")
        print(f"{'='*80}")
        print(f"📝 总查询数: {summary['total_queries']}")
        print(f"✅ 成功查询: {summary['successful_queries']}")
        print(f"❌ 失败查询: {summary['failed_queries']}")
        print(f"⏱️ 总耗时: {summary['total_time']}秒")
        print(f"📈 平均耗时: {summary['avg_time_per_query']}秒/查询")
        print(f"💾 结果已保存到: rag_demo_results.json")
        
        return final_result


def main():
    """主函数"""
    print("🎯 腾讯云IM文档完整RAG系统演示")
    print("=" * 80)
    
    try:
        # 1. 初始化RAG系统
        rag_system = CompleteTencentIMRAG()
        
        # 2. 设置流水线
        if not rag_system.setup_pipeline():
            print("❌ RAG流水线设置失败")
            return
        
        # 3. 运行单个查询演示
        print(f"\n{'='*80}")
        print("🔍 单个查询演示")
        print(f"{'='*80}")
        
        demo_query = "直播群AVChatRoom有什么特点？"
        single_result = rag_system.run_complete_rag(demo_query)
        
        if 'error' not in single_result:
            print(f"\n📋 完整答案:")
            print(f"{single_result['answer']}")
            print(f"\n📊 检索到 {len(single_result['retrieved_documents'])} 个相关文档")
            print(f"⏱️ 处理时间: {single_result['processing_time']}秒")
        
        # 4. 运行批量演示
        print(f"\n{'='*80}")
        print("🎛️ 批量查询演示")
        print(f"{'='*80}")
        
        batch_results = rag_system.run_batch_demo()
        
        print(f"\n🎉 完整RAG演示完成!")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")


if __name__ == "__main__":
    main()
