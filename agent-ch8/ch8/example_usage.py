#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档分割工具使用示例
展示如何使用document_splitter模块的各种功能
"""

from document_splitter import (
    read_and_split_document,
    print_chunks_summary,
    save_chunks_to_json,
    get_chunk_by_title,
    search_chunks_by_keyword,
    filter_chunks_by_size
)


def basic_usage_example():
    """
    基础使用示例：读取和分割文档
    """
    print("🔥 基础使用示例")
    print("=" * 50)
    
    # 1. 读取和分割文档
    chunks = read_and_split_document("腾讯云IM群组系统完整文档.md", "###")
    
    if chunks:
        # 2. 显示摘要
        print_chunks_summary(chunks, show_details=False)
        
        # 3. 保存为JSON
        save_chunks_to_json(chunks, "example_output.json", {
            'description': '示例输出',
            'processor': 'example_usage.py'
        })
        
        return chunks
    
    return []


def search_examples(chunks):
    """
    搜索功能示例
    """
    print("\n🔍 搜索功能示例")
    print("=" * 50)
    
    # 1. 按关键词搜索
    print("1. 搜索包含'直播群'的文档块:")
    live_chunks = search_chunks_by_keyword(chunks, "直播群")
    for chunk in live_chunks:
        print(f"   ✅ {chunk['title']} ({chunk['char_count']} 字符)")
    
    # 2. 按标题查找
    print("\n2. 查找特定标题的文档块:")
    target_chunk = get_chunk_by_title(chunks, "消息能力差异")
    if target_chunk:
        print(f"   ✅ 找到: {target_chunk['title']}")
        print(f"   📄 内容长度: {target_chunk['char_count']} 字符")
        print(f"   📍 位置: 第{target_chunk['start_line']}-{target_chunk['end_line']}行")
    else:
        print("   ❌ 未找到")
    
    # 3. 多关键词搜索
    print("\n3. 搜索包含'权限'和'管理'的文档块:")
    permission_chunks = search_chunks_by_keyword(chunks, "权限")
    management_chunks = search_chunks_by_keyword(chunks, "管理")
    
    # 找到同时包含两个关键词的块
    common_chunks = []
    for chunk in permission_chunks:
        if chunk in management_chunks:
            common_chunks.append(chunk)
    
    print(f"   📊 包含'权限': {len(permission_chunks)} 个")
    print(f"   📊 包含'管理': {len(management_chunks)} 个") 
    print(f"   📊 同时包含两者: {len(common_chunks)} 个")
    
    for chunk in common_chunks:
        print(f"   ✅ {chunk['title']}")


def filtering_examples(chunks):
    """
    过滤功能示例
    """
    print("\n📏 过滤功能示例")
    print("=" * 50)
    
    # 1. 按大小过滤
    print("1. 按文档块大小过滤:")
    
    small_chunks = filter_chunks_by_size(chunks, max_chars=500)
    medium_chunks = filter_chunks_by_size(chunks, min_chars=500, max_chars=1500)
    large_chunks = filter_chunks_by_size(chunks, min_chars=1500)
    
    print(f"   📐 小块 (≤500字符): {len(small_chunks)} 个")
    print(f"   📏 中块 (500-1500字符): {len(medium_chunks)} 个")
    print(f"   📐 大块 (≥1500字符): {len(large_chunks)} 个")
    
    # 2. 显示每类的具体块
    print("\n   小块列表:")
    for chunk in small_chunks:
        print(f"     • {chunk['title']} ({chunk['char_count']} 字符)")
    
    print("\n   大块列表:")
    for chunk in large_chunks:
        print(f"     • {chunk['title']} ({chunk['char_count']} 字符)")


def content_analysis_example(chunks):
    """
    内容分析示例
    """
    print("\n📊 内容分析示例")
    print("=" * 50)
    
    # 1. 统计各类群组类型的提及次数
    group_types = ["Work", "Public", "Meeting", "AVChatRoom", "Community"]
    type_mentions = {}
    
    for group_type in group_types:
        mentions = 0
        for chunk in chunks:
            mentions += chunk['content'].count(group_type)
        type_mentions[group_type] = mentions
    
    print("1. 群组类型提及统计:")
    for group_type, count in sorted(type_mentions.items(), key=lambda x: x[1], reverse=True):
        print(f"   📈 {group_type}: {count} 次")
    
    # 2. 找出最长和最短的文档块
    longest_chunk = max(chunks, key=lambda x: x['char_count'])
    shortest_chunk = min(chunks, key=lambda x: x['char_count'])
    
    print(f"\n2. 文档块大小分析:")
    print(f"   📏 最长: {longest_chunk['title']} ({longest_chunk['char_count']} 字符)")
    print(f"   📐 最短: {shortest_chunk['title']} ({shortest_chunk['char_count']} 字符)")
    
    # 3. 内容密度分析（表格密集程度）
    print(f"\n3. 表格密度分析:")
    for chunk in chunks:
        table_lines = chunk['content'].count('|')
        if table_lines > 10:  # 包含较多表格的块
            density = table_lines / chunk['char_count'] * 1000  # 每1000字符的表格标记数
            print(f"   📊 {chunk['title']}: {table_lines} 个表格标记 (密度: {density:.1f}/1000字符)")


def rag_preparation_example(chunks):
    """
    RAG系统准备示例
    """
    print("\n🤖 RAG系统准备示例")
    print("=" * 50)
    
    # 1. 为每个块生成唯一ID和向量索引准备
    indexed_chunks = []
    for i, chunk in enumerate(chunks):
        indexed_chunk = chunk.copy()
        indexed_chunk['chunk_id'] = f"tencent_im_doc_{i:03d}"
        indexed_chunk['vector_ready'] = True
        indexed_chunk['embedding_text'] = f"{chunk['title']}\n{chunk['content']}"
        indexed_chunks.append(indexed_chunk)
    
    print(f"1. 已为 {len(indexed_chunks)} 个文档块生成索引ID")
    
    # 2. 根据内容类型分类
    categories = {
        'table_heavy': [],  # 表格密集的块
        'text_heavy': [],   # 文本密集的块
        'mixed': []         # 混合内容的块
    }
    
    for chunk in indexed_chunks:
        table_count = chunk['content'].count('|')
        text_lines = len([line for line in chunk['content'].split('\n') if line.strip() and not line.startswith('|')])
        
        if table_count > text_lines:
            categories['table_heavy'].append(chunk)
        elif text_lines > table_count * 2:
            categories['text_heavy'].append(chunk)
        else:
            categories['mixed'].append(chunk)
    
    print(f"\n2. 内容类型分类:")
    for category, chunks_list in categories.items():
        print(f"   📂 {category}: {len(chunks_list)} 个块")
        for chunk in chunks_list[:2]:  # 只显示前2个
            print(f"      • {chunk['title']}")
    
    # 3. 保存RAG准备就绪的数据
    rag_data = {
        'metadata': {
            'total_chunks': len(indexed_chunks),
            'categories': {k: len(v) for k, v in categories.items()},
            'ready_for_embedding': True,
            'suggested_embedding_model': 'text-embedding-ada-002'
        },
        'chunks': indexed_chunks
    }
    
    save_chunks_to_json(indexed_chunks, "rag_ready_chunks.json", rag_data['metadata'])
    print(f"\n✅ RAG准备就绪的数据已保存到: rag_ready_chunks.json")


def main():
    """
    主函数：运行所有示例
    """
    print("🚀 腾讯云IM文档分割工具 - 完整使用示例")
    print("=" * 80)
    
    # 1. 基础使用
    chunks = basic_usage_example()
    
    if not chunks:
        print("❌ 无法读取文档，示例终止")
        return
    
    # 2. 搜索示例
    search_examples(chunks)
    
    # 3. 过滤示例
    filtering_examples(chunks)
    
    # 4. 内容分析示例
    content_analysis_example(chunks)
    
    # 5. RAG准备示例
    rag_preparation_example(chunks)
    
    print(f"\n🎉 所有示例运行完成!")
    print(f"📁 生成的文件:")
    print(f"   • example_output.json - 基础输出")
    print(f"   • rag_ready_chunks.json - RAG准备就绪的数据")


if __name__ == "__main__":
    main()