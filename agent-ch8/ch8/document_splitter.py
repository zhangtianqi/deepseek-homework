#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档分割工具
专门用于将Markdown文档按标题级别分割，为RAG系统做准备
"""

import json
from datetime import datetime
from typing import List, Dict, Optional


def read_and_split_document(file_path: str, split_level: str = "###") -> List[Dict]:
    """
    读取Markdown文档并按指定标题级别进行分割
    
    Args:
        file_path (str): 文档文件路径
        split_level (str): 分割的标题级别，默认为"###"
        
    Returns:
        List[Dict]: 分割后的文档块列表，每个块包含以下字段：
            - title: 标题
            - content: 内容（包含标题行）
            - level: 标题级别
            - start_line: 起始行号
            - end_line: 结束行号
            - word_count: 字数
            - char_count: 字符数
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ 成功读取文档: {file_path}")
        print(f"📄 文档总长度: {len(content):,} 字符")
        
        # 按行分割内容
        lines = content.split('\n')
        
        # 存储分割后的文档块
        document_chunks = []
        chunk_lines = []
        current_title = ""
        chunk_start_line = 0
        
        for i, line in enumerate(lines):
            # 检查是否是指定级别的标题
            if line.startswith(split_level + " "):
                # 如果之前有积累的内容，保存为一个块
                if chunk_lines and current_title:
                    chunk_content = '\n'.join(chunk_lines).strip()
                    if chunk_content:  # 只保存非空内容
                        document_chunks.append({
                            'title': current_title,
                            'content': chunk_content,
                            'level': len(split_level),
                            'start_line': chunk_start_line + 1,
                            'end_line': i,
                            'word_count': len(chunk_content),
                            'char_count': len(chunk_content.encode('utf-8'))
                        })
                
                # 开始新的块
                current_title = line.replace(split_level + " ", "").strip()
                chunk_lines = [line]  # 包含标题行
                chunk_start_line = i
            else:
                # 添加到当前块
                chunk_lines.append(line)
        
        # 处理最后一个块
        if chunk_lines and current_title:
            chunk_content = '\n'.join(chunk_lines).strip()
            if chunk_content:
                document_chunks.append({
                    'title': current_title,
                    'content': chunk_content,
                    'level': len(split_level),
                    'start_line': chunk_start_line + 1,
                    'end_line': len(lines),
                    'word_count': len(chunk_content),
                    'char_count': len(chunk_content.encode('utf-8'))
                })
        
        print(f"✂️ 文档分割完成，共生成 {len(document_chunks)} 个块")
        return document_chunks
        
    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {file_path}")
        return []
    except Exception as e:
        print(f"❌ 读取文档时发生错误: {e}")
        return []


def analyze_document_chunks(chunks: List[Dict]) -> Dict:
    """
    分析文档块的统计信息
    
    Args:
        chunks (List[Dict]): 文档块列表
        
    Returns:
        Dict: 统计信息
    """
    if not chunks:
        return {}
    
    total_chars = sum(chunk['char_count'] for chunk in chunks)
    total_words = sum(chunk['word_count'] for chunk in chunks)
    
    stats = {
        'total_chunks': len(chunks),
        'total_characters': total_chars,
        'total_words': total_words,
        'avg_chunk_size': total_chars // len(chunks) if chunks else 0,
        'min_chunk_size': min(chunk['char_count'] for chunk in chunks),
        'max_chunk_size': max(chunk['char_count'] for chunk in chunks),
        'chunks_info': []
    }
    
    for i, chunk in enumerate(chunks):
        stats['chunks_info'].append({
            'index': i,
            'title': chunk['title'],
            'char_count': chunk['char_count'],
            'lines': f"{chunk['start_line']}-{chunk['end_line']}"
        })
    
    return stats


def print_chunks_summary(chunks: List[Dict], show_details: bool = True) -> None:
    """
    打印文档块的摘要信息
    
    Args:
        chunks (List[Dict]): 文档块列表
        show_details (bool): 是否显示详细信息
    """
    if not chunks:
        print("❌ 没有找到任何文档块")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 文档分割摘要")
    print(f"{'='*60}")
    
    stats = analyze_document_chunks(chunks)
    
    print(f"📦 总块数: {stats['total_chunks']}")
    print(f"📝 总字符数: {stats['total_characters']:,}")
    print(f"📏 平均块大小: {stats['avg_chunk_size']:,} 字符")
    print(f"📐 最小块大小: {stats['min_chunk_size']:,} 字符")
    print(f"📏 最大块大小: {stats['max_chunk_size']:,} 字符")
    
    if show_details:
        print(f"\n📋 各块详细信息:")
        print(f"{'序号':<4} {'标题':<35} {'字符数':<8} {'行号范围':<12}")
        print("-" * 70)
        
        for info in stats['chunks_info']:
            title = info['title'][:32] + "..." if len(info['title']) > 35 else info['title']
            print(f"{info['index']:<4} {title:<35} {info['char_count']:<8} {info['lines']:<12}")


def save_chunks_to_json(chunks: List[Dict], output_file: str, metadata: Optional[Dict] = None) -> bool:
    """
    将文档块保存为JSON格式
    
    Args:
        chunks (List[Dict]): 文档块列表
        output_file (str): 输出文件路径
        metadata (Optional[Dict]): 额外的元数据
        
    Returns:
        bool: 保存是否成功
    """
    try:
        # 默认元数据
        default_metadata = {
            'total_chunks': len(chunks),
            'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'split_method': 'markdown_heading_level_3'
        }
        
        # 合并用户提供的元数据
        if metadata:
            default_metadata.update(metadata)
        
        output_data = {
            'metadata': default_metadata,
            'chunks': chunks
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 文档块已保存到: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ 保存JSON文件失败: {e}")
        return False


def get_chunk_by_title(chunks: List[Dict], title: str) -> Optional[Dict]:
    """
    根据标题获取文档块
    
    Args:
        chunks (List[Dict]): 文档块列表
        title (str): 要查找的标题
        
    Returns:
        Optional[Dict]: 找到的文档块，如果没找到返回None
    """
    for chunk in chunks:
        if chunk['title'] == title:
            return chunk
    return None


def search_chunks_by_keyword(chunks: List[Dict], keyword: str, case_sensitive: bool = False) -> List[Dict]:
    """
    根据关键词搜索文档块
    
    Args:
        chunks (List[Dict]): 文档块列表
        keyword (str): 搜索关键词
        case_sensitive (bool): 是否区分大小写
        
    Returns:
        List[Dict]: 包含关键词的文档块列表
    """
    if not case_sensitive:
        keyword = keyword.lower()
    
    matching_chunks = []
    
    for chunk in chunks:
        search_text = chunk['content'] if case_sensitive else chunk['content'].lower()
        title_text = chunk['title'] if case_sensitive else chunk['title'].lower()
        
        if keyword in search_text or keyword in title_text:
            matching_chunks.append(chunk)
    
    return matching_chunks


def filter_chunks_by_size(chunks: List[Dict], min_chars: int = 0, max_chars: int = float('inf')) -> List[Dict]:
    """
    根据大小过滤文档块
    
    Args:
        chunks (List[Dict]): 文档块列表
        min_chars (int): 最小字符数
        max_chars (int): 最大字符数
        
    Returns:
        List[Dict]: 过滤后的文档块列表
    """
    return [chunk for chunk in chunks if min_chars <= chunk['char_count'] <= max_chars]


def main():
    """
    主函数 - 演示文档分割功能
    """
    print("🔧 腾讯云IM文档分割工具")
    print("=" * 60)
    
    # 读取和分割文档
    file_path = "/Users/zhangtianqi/git_root/agent_homework/ch8/腾讯云IM群组系统完整文档.md"
    chunks = read_and_split_document(file_path, "###")
    
    if not chunks:
        print("❌ 文档分割失败")
        return
    
    # 打印摘要
    print_chunks_summary(chunks)
    
    # 保存为JSON格式
    metadata = {
        'source_file': file_path,
        'description': '腾讯云IM群组系统文档，按三级标题分割'
    }
    json_file = "腾讯云IM文档块_处理后.json"
    save_chunks_to_json(chunks, json_file, metadata)
    
    # 演示搜索功能
    print(f"\n🔍 搜索演示：")
    print("-" * 30)
    
    # 搜索包含"权限"的块
    permission_chunks = search_chunks_by_keyword(chunks, "权限")
    print(f"包含'权限'的文档块: {len(permission_chunks)} 个")
    for chunk in permission_chunks:
        print(f"  - {chunk['title']}")
    
    # 按大小过滤
    large_chunks = filter_chunks_by_size(chunks, min_chars=1000)
    print(f"\n📏 大于1000字符的文档块: {len(large_chunks)} 个")
    for chunk in large_chunks:
        print(f"  - {chunk['title']} ({chunk['char_count']} 字符)")
    
    # 显示一个具体块的内容预览
    if chunks:
        print(f"\n📖 示例文档块内容预览:")
        print("-" * 40)
        sample_chunk = chunks[0]
        print(f"标题: {sample_chunk['title']}")
        print(f"字符数: {sample_chunk['char_count']}")
        print(f"内容预览:")
        preview = sample_chunk['content'][:300] + "..." if len(sample_chunk['content']) > 300 else sample_chunk['content']
        print(preview)
    
    return chunks


if __name__ == "__main__":
    main()