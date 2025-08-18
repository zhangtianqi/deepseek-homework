#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云IM文档向量数据库召回测试
测试向量搜索的召回效果和准确性
"""

import json
import time
from typing import List, Dict
from real_vector_store import TencentIMVectorDatabase


class RecallTester:
    """召回测试器"""
    
    def __init__(self, config_file: str = "vector_store_config.json"):
        """
        初始化召回测试器
        
        Args:
            config_file (str): 配置文件路径
        """
        self.config = self._load_config(config_file)
        self.db_manager = None
        self.test_queries = self._prepare_test_queries()
    
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 成功加载配置文件: {config_file}")
            return config
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            raise
    
    def _prepare_test_queries(self) -> List[Dict]:
        """准备测试查询"""
        return [
            {
                "query": "直播群AVChatRoom有什么特点",
                "expected_keywords": ["AVChatRoom", "直播群", "无上限", "历史消息"],
                "category": "群组类型查询"
            },
            {
                "query": "社群Community支持多少人",
                "expected_keywords": ["Community", "社群", "10万", "100万"],
                "category": "群组规模查询"
            },
            {
                "query": "如何设置群组权限",
                "expected_keywords": ["权限", "权限组", "按位", "管理"],
                "category": "权限配置查询"
            },
            {
                "query": "Work群和Public群的区别是什么",
                "expected_keywords": ["Work", "Public", "差异", "邀请", "申请"],
                "category": "群组对比查询"
            },
            {
                "query": "群成员资料包含哪些字段",
                "expected_keywords": ["成员资料", "Member_Account", "Role", "JoinTime"],
                "category": "数据结构查询"
            },
            {
                "query": "消息存储和漫游功能",
                "expected_keywords": ["消息", "存储", "漫游", "历史消息"],
                "category": "消息功能查询"
            },
            {
                "query": "自定义字段有什么特性",
                "expected_keywords": ["自定义字段", "Key-Value", "读权限", "写权限"],
                "category": "功能特性查询"
            },
            {
                "query": "群组自动回收规则",
                "expected_keywords": ["自动回收", "活跃成员", "40天", "解散"],
                "category": "规则查询"
            }
        ]
    
    def initialize_database(self) -> bool:
        """初始化数据库连接"""
        try:
            print("🔧 初始化向量数据库管理器...")
            
            # 直接使用API密钥（因为配置文件可能被重写）
            SECRET_ID = ""
            SECRET_KEY = ""
            
            self.db_manager = TencentIMVectorDatabase(
                secret_id=SECRET_ID,
                secret_key=SECRET_KEY,
                db_name="tencent.im.db"
            )
            
            # 尝试加载已存在的数据库
            if not self.db_manager.load_existing_database():
                print("📝 数据库不存在，开始创建...")
                success = self.db_manager.create_database_from_markdown(
                    self.config['documents']['source_file'],
                    batch_size=self.config['vector_database']['batch_size']
                )
                
                if not success:
                    print("❌ 数据库创建失败")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ 初始化数据库失败: {e}")
            return False
    
    def run_single_recall_test(self, test_case: Dict, k: int = 5) -> Dict:
        """
        运行单个召回测试
        
        Args:
            test_case (Dict): 测试用例
            k (int): 返回结果数量
            
        Returns:
            Dict: 测试结果
        """
        query = test_case['query']
        expected_keywords = test_case['expected_keywords']
        category = test_case['category']
        
        print(f"\n🔍 测试查询: '{query}'")
        print(f"📂 查询类别: {category}")
        
        try:
            # 执行搜索
            start_time = time.time()
            results = self.db_manager.search_documents(query, k=k)
            search_time = time.time() - start_time
            
            # 分析召回效果
            recall_analysis = self._analyze_recall(results, expected_keywords)
            
            test_result = {
                'query': query,
                'category': category,
                'expected_keywords': expected_keywords,
                'search_time': round(search_time, 3),
                'results_count': len(results),
                'recall_analysis': recall_analysis,
                'top_results': []
            }
            
            # 记录前3个结果
            for i, result in enumerate(results[:3]):
                test_result['top_results'].append({
                    'rank': i + 1,
                    'title': result['title'],
                    'similarity_score': round(result['similarity_score'], 4),
                    'char_count': result['metadata'].get('char_count', 0),
                    'content_preview': result['content_preview'][:100] + "..."
                })
                
                print(f"   {i+1}. 📄 {result['title']}")
                print(f"      🎯 相似度: {result['similarity_score']:.4f}")
                print(f"      📝 内容: {result['content_preview'][:80]}...")
            
            # 显示召回分析
            print(f"   📊 召回分析:")
            print(f"      ✅ 匹配关键词: {recall_analysis['matched_keywords']}")
            print(f"      📈 关键词覆盖率: {recall_analysis['keyword_coverage']:.2%}")
            print(f"      ⏱️ 搜索耗时: {search_time:.3f}秒")
            
            return test_result
            
        except Exception as e:
            print(f"❌ 测试查询失败: {e}")
            return {
                'query': query,
                'error': str(e)
            }
    
    def _analyze_recall(self, results: List[Dict], expected_keywords: List[str]) -> Dict:
        """
        分析召回效果
        
        Args:
            results (List[Dict]): 搜索结果
            expected_keywords (List[str]): 期望的关键词
            
        Returns:
            Dict: 召回分析结果
        """
        matched_keywords = []
        total_content = ""
        
        # 合并所有结果的内容
        for result in results:
            total_content += result['full_content'] + " "
        
        total_content = total_content.lower()
        
        # 检查关键词匹配
        for keyword in expected_keywords:
            if keyword.lower() in total_content:
                matched_keywords.append(keyword)
        
        keyword_coverage = len(matched_keywords) / len(expected_keywords) if expected_keywords else 0
        
        return {
            'matched_keywords': matched_keywords,
            'missing_keywords': [kw for kw in expected_keywords if kw not in matched_keywords],
            'keyword_coverage': keyword_coverage,
            'total_keywords': len(expected_keywords)
        }
    
    def run_comprehensive_test(self) -> Dict:
        """
        运行全面的召回测试
        
        Returns:
            Dict: 完整测试结果
        """
        print("🚀 开始全面召回测试")
        print("=" * 80)
        
        # 初始化数据库
        if not self.initialize_database():
            return {'error': '数据库初始化失败'}
        
        # 获取数据库信息
        db_info = self.db_manager.get_database_info()
        print(f"\n📊 数据库信息:")
        for key, value in db_info.items():
            print(f"   {key}: {value}")
        
        # 运行所有测试
        test_results = []
        total_start_time = time.time()
        
        for i, test_case in enumerate(self.test_queries):
            print(f"\n{'='*60}")
            print(f"测试 {i+1}/{len(self.test_queries)}")
            
            result = self.run_single_recall_test(test_case, k=5)
            test_results.append(result)
            
            # 避免API频率限制
            if i < len(self.test_queries) - 1:
                print("⏱️ 等待2秒避免API频率限制...")
                time.sleep(2)
        
        total_time = time.time() - total_start_time
        
        # 生成测试总结
        summary = self._generate_test_summary(test_results, total_time)
        
        final_result = {
            'database_info': db_info,
            'test_summary': summary,
            'test_results': test_results,
            'config': self.config
        }
        
        return final_result
    
    def _generate_test_summary(self, test_results: List[Dict], total_time: float) -> Dict:
        """生成测试总结"""
        successful_tests = [r for r in test_results if 'error' not in r]
        failed_tests = [r for r in test_results if 'error' in r]
        
        if not successful_tests:
            return {'error': '没有成功的测试'}
        
        avg_search_time = sum(r['search_time'] for r in successful_tests) / len(successful_tests)
        avg_keyword_coverage = sum(r['recall_analysis']['keyword_coverage'] for r in successful_tests) / len(successful_tests)
        
        # 按类别统计
        category_stats = {}
        for result in successful_tests:
            category = result['category']
            if category not in category_stats:
                category_stats[category] = []
            category_stats[category].append(result['recall_analysis']['keyword_coverage'])
        
        category_summary = {}
        for category, coverages in category_stats.items():
            category_summary[category] = {
                'avg_coverage': sum(coverages) / len(coverages),
                'test_count': len(coverages)
            }
        
        return {
            'total_tests': len(test_results),
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'avg_search_time': round(avg_search_time, 3),
            'avg_keyword_coverage': round(avg_keyword_coverage, 3),
            'total_test_time': round(total_time, 3),
            'category_summary': category_summary
        }
    
    def save_test_results(self, results: Dict, filename: str = "recall_test_results.json"):
        """保存测试结果"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"💾 测试结果已保存到: {filename}")
            return True
        except Exception as e:
            print(f"❌ 保存测试结果失败: {e}")
            return False


def main():
    """主函数"""
    print("🎯 腾讯云IM文档向量数据库召回测试")
    print("=" * 80)
    
    try:
        # 创建测试器
        tester = RecallTester()
        
        # 运行全面测试
        results = tester.run_comprehensive_test()
        
        if 'error' in results:
            print(f"❌ 测试失败: {results['error']}")
            return
        
        # 显示测试总结
        summary = results['test_summary']
        print(f"\n{'='*80}")
        print(f"📊 测试总结")
        print(f"{'='*80}")
        print(f"📋 总测试数: {summary['total_tests']}")
        print(f"✅ 成功测试: {summary['successful_tests']}")
        print(f"❌ 失败测试: {summary['failed_tests']}")
        print(f"⏱️ 平均搜索时间: {summary['avg_search_time']}秒")
        print(f"📈 平均关键词覆盖率: {summary['avg_keyword_coverage']:.2%}")
        print(f"🕒 总测试时间: {summary['total_test_time']}秒")
        
        print(f"\n📂 各类别测试结果:")
        for category, stats in summary['category_summary'].items():
            print(f"   {category}: {stats['avg_coverage']:.2%} (共{stats['test_count']}个测试)")
        
        # 保存结果
        tester.save_test_results(results)
        
        print(f"\n🎉 召回测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")


if __name__ == "__main__":
    main()
