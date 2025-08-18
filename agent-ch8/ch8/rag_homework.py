#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云文档URL保存为Markdown的工具
功能：从指定URL获取网页内容并转换为Markdown格式保存
"""

import requests
from bs4 import BeautifulSoup
import html2text
import os
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime


def fetch_url_content(url):
    """
    获取URL的网页内容
    
    Args:
        url (str): 目标URL
        
    Returns:
        tuple: (html_content, title, status_code)
    """
    try:
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        print(f"正在获取URL内容: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 确保正确的编码
        response.encoding = response.apparent_encoding or 'utf-8'
        
        # 解析HTML获取标题
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title')
        title = title.text.strip() if title else "无标题"
        
        print(f"成功获取内容，标题: {title}")
        return response.text, title, response.status_code
        
    except requests.exceptions.RequestException as e:
        print(f"获取URL内容失败: {e}")
        return None, None, None


def clean_html_content(html_content, base_url):
    """
    清理HTML内容，提取主要内容
    
    Args:
        html_content (str): 原始HTML内容
        base_url (str): 基础URL，用于处理相对链接
        
    Returns:
        str: 清理后的HTML内容
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除不需要的标签
    for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
        tag.decompose()
    
    # 移除广告和无关内容的div
    for div in soup.find_all('div', class_=re.compile(r'(ad|advertisement|sidebar|menu|nav)', re.I)):
        div.decompose()
    
    # 处理相对URL转为绝对URL
    for link in soup.find_all('a', href=True):
        link['href'] = urljoin(base_url, link['href'])
    
    for img in soup.find_all('img', src=True):
        img['src'] = urljoin(base_url, img['src'])
    
    return str(soup)


def html_to_markdown(html_content, title=""):
    """
    将HTML内容转换为Markdown格式
    
    Args:
        html_content (str): HTML内容
        title (str): 文档标题
        
    Returns:
        str: Markdown格式内容
    """
    # 配置html2text转换器
    h = html2text.HTML2Text()
    h.ignore_links = False  # 保留链接
    h.ignore_images = False  # 保留图片
    h.ignore_emphasis = False  # 保留强调格式
    h.body_width = 0  # 不限制行宽
    h.unicode_snob = True  # 处理Unicode字符
    h.escape_snob = True  # 转义特殊字符
    
    # 转换为Markdown
    markdown_content = h.handle(html_content)
    
    # 添加文档头部信息
    header = f"""# {title}

> 来源: [腾讯云文档](https://cloud.tencent.com/document/product/269/1502)
> 获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    
    return header + markdown_content


def clean_markdown(markdown_content):
    """
    清理Markdown内容，移除多余的空行和格式问题
    
    Args:
        markdown_content (str): 原始Markdown内容
        
    Returns:
        str: 清理后的Markdown内容
    """
    # 移除多余的空行
    lines = markdown_content.split('\n')
    cleaned_lines = []
    prev_empty = False
    
    for line in lines:
        line = line.rstrip()  # 移除行尾空格
        is_empty = len(line) == 0
        
        if is_empty and prev_empty:
            continue  # 跳过连续的空行
        
        cleaned_lines.append(line)
        prev_empty = is_empty
    
    return '\n'.join(cleaned_lines)


def save_to_file(content, filename):
    """
    保存内容到文件
    
    Args:
        content (str): 要保存的内容
        filename (str): 文件名
        
    Returns:
        bool: 保存是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"内容已保存到: {filename}")
        return True
        
    except Exception as e:
        print(f"保存文件失败: {e}")
        return False


def url_to_markdown(url, output_file=None):
    """
    将URL内容转换为Markdown并保存
    
    Args:
        url (str): 目标URL
        output_file (str): 输出文件名，如果为None则自动生成
        
    Returns:
        bool: 转换是否成功
    """
    # 获取网页内容
    html_content, title, status_code = fetch_url_content(url)
    
    if html_content is None:
        print("无法获取网页内容")
        return False
    
    print(f"HTTP状态码: {status_code}")
    
    # 清理HTML内容
    cleaned_html = clean_html_content(html_content, url)
    
    # 转换为Markdown
    markdown_content = html_to_markdown(cleaned_html, title)
    
    # 清理Markdown格式
    markdown_content = clean_markdown(markdown_content)
    
    # 生成输出文件名
    if output_file is None:
        # 从URL或标题生成文件名
        parsed_url = urlparse(url)
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:50]  # 限制长度并移除特殊字符
        if safe_title:
            output_file = f"{safe_title}.md"
        else:
            output_file = f"webpage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    # 保存到文件
    success = save_to_file(markdown_content, output_file)
    
    if success:
        print(f"转换完成! Markdown文件大小: {len(markdown_content.encode('utf-8'))} 字节")
    
    return success


def main():
    """
    主函数，处理命令行参数或直接运行
    """
    # 目标URL
    target_url = "https://cloud.tencent.com/document/product/269/1502"
    
    print("=" * 60)
    print("腾讯云文档转Markdown工具")
    print("=" * 60)
    
    # 执行转换
    success = url_to_markdown(target_url, "腾讯云IM群组系统文档.md")
    
    if success:
        print("\n✅ 转换成功完成!")
    else:
        print("\n❌ 转换失败!")


def read_and_split_document(file_path, split_level="###"):
    """
    读取Markdown文档并按指定标题级别进行分割
    
    Args:
        file_path (str): 文档文件路径
        split_level (str): 分割的标题级别，默认为"###"
        
    Returns:
        list: 分割后的文档块列表，每个块包含标题和内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"成功读取文档: {file_path}")
        print(f"文档总长度: {len(content)} 字符")
        
        # 按行分割内容
        lines = content.split('\n')
        
        # 存储分割后的文档块
        document_chunks = []
        current_chunk = {
            'title': '',
            'content': '',
            'level': 0,
            'start_line': 0,
            'end_line': 0
        }
        
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
        
        print(f"文档分割完成，共生成 {len(document_chunks)} 个块")
        return document_chunks
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        return []
    except Exception as e:
        print(f"读取文档时发生错误: {e}")
        return []


def analyze_document_chunks(chunks):
    """
    分析文档块的统计信息
    
    Args:
        chunks (list): 文档块列表
        
    Returns:
        dict: 统计信息
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


def print_chunks_summary(chunks):
    """
    打印文档块的摘要信息
    
    Args:
        chunks (list): 文档块列表
    """
    if not chunks:
        print("没有找到任何文档块")
        return
    
    print(f"\n{'='*60}")
    print(f"文档分割摘要")
    print(f"{'='*60}")
    
    stats = analyze_document_chunks(chunks)
    
    print(f"总块数: {stats['total_chunks']}")
    print(f"总字符数: {stats['total_characters']:,}")
    print(f"平均块大小: {stats['avg_chunk_size']:,} 字符")
    print(f"最小块大小: {stats['min_chunk_size']:,} 字符")
    print(f"最大块大小: {stats['max_chunk_size']:,} 字符")
    
    print(f"\n各块详细信息:")
    print(f"{'序号':<4} {'标题':<30} {'字符数':<8} {'行号范围':<10}")
    print("-" * 60)
    
    for info in stats['chunks_info']:
        title = info['title'][:27] + "..." if len(info['title']) > 30 else info['title']
        print(f"{info['index']:<4} {title:<30} {info['char_count']:<8} {info['lines']:<10}")


def save_chunks_to_json(chunks, output_file):
    """
    将文档块保存为JSON格式
    
    Args:
        chunks (list): 文档块列表
        output_file (str): 输出文件路径
        
    Returns:
        bool: 保存是否成功
    """
    try:
        import json
        
        # 添加元数据
        output_data = {
            'metadata': {
                'total_chunks': len(chunks),
                'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source_file': 'ch8/腾讯云IM群组系统完整文档.md'
            },
            'chunks': chunks
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"文档块已保存到: {output_file}")
        return True
        
    except Exception as e:
        print(f"保存JSON文件失败: {e}")
        return False


def demo_document_splitting():
    """
    演示文档分割功能
    """
    print("=" * 60)
    print("腾讯云IM文档分割演示")
    print("=" * 60)
    
    # 读取和分割文档
    file_path = "腾讯云IM群组系统完整文档.md"
    chunks = read_and_split_document(file_path, "###")
    
    if not chunks:
        print("文档分割失败")
        return
    
    # 打印摘要
    print_chunks_summary(chunks)
    
    # 显示前几个块的内容预览
    print(f"\n{'='*60}")
    print("前3个文档块内容预览:")
    print(f"{'='*60}")
    
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n📄 块 {i+1}: {chunk['title']}")
        print("-" * 40)
        # 显示前200个字符
        preview = chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content']
        print(preview)
    
    # 保存为JSON格式
    json_file = "腾讯云IM文档块.json"
    save_chunks_to_json(chunks, json_file)
    
    return chunks


if __name__ == "__main__":
    # 运行原有的URL转换功能
    # main()
    
    # 运行文档分割演示
    demo_document_splitting()
