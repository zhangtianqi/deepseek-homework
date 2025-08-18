#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试腾讯云LKE嵌入API
"""

import json
from tencent_embeddings import TencentLKEEmbeddings


def test_embedding_api():
    """测试嵌入API"""
    print("🧪 测试腾讯云LKE嵌入API")
    print("=" * 50)
    
    try:
        # 从配置文件读取密钥
        with open("vector_store_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        secret_id = config['tencent_cloud']['secret_id']
        secret_key = config['tencent_cloud']['secret_key']
        
        print(f"📖 使用API密钥: {secret_id[:10]}...")
        
        # 初始化嵌入模型
        embeddings = TencentLKEEmbeddings(
            secret_id=secret_id,
            secret_key=secret_key
        )
        
        # 测试单个文本嵌入
        test_text = "腾讯云即时通信IM群组系统"
        print(f"🔍 测试文本: '{test_text}'")
        
        print("⏳ 调用嵌入API...")
        vector = embeddings.embed_query(test_text)
        
        print(f"✅ 成功获取向量!")
        print(f"📏 向量维度: {len(vector)}")
        print(f"🔢 向量前5个值: {vector[:5]}")
        print(f"📊 向量范围: [{min(vector):.4f}, {max(vector):.4f}]")
        
        # 测试批量嵌入
        test_texts = [
            "直播群AVChatRoom特点",
            "社群Community功能",
            "群组权限管理"
        ]
        
        print(f"\n📋 测试批量嵌入 ({len(test_texts)} 个文本)...")
        vectors = embeddings.embed_documents(test_texts)
        
        print(f"✅ 批量嵌入成功!")
        print(f"📊 返回向量数: {len(vectors)}")
        for i, (text, vec) in enumerate(zip(test_texts, vectors)):
            print(f"   {i+1}. '{text}' -> {len(vec)}维向量")
        
        return True
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False


if __name__ == "__main__":
    test_embedding_api()