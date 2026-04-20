#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相似度计算模块
整合各种匹配算法，提供分组和批量计算功能
"""

import hashlib
from collections import defaultdict
from typing import List, Dict, Tuple, Any, Callable, Optional

from .file_manager import FileManager
from .matchers import (
    BaseMatcher, 
    get_matcher, 
    MATCHER_REGISTRY,
    ContentMatcher
)


class SimilarityCalculator:
    """相似度计算器"""
    
    def __init__(
        self,
        matcher_type: str = 'continuous',
        include_extension: bool = False,
        threshold: float = 0.6
    ):
        """
        初始化相似度计算器
        
        Args:
            matcher_type: 匹配算法类型
            include_extension: 是否包含扩展名进行比较
            threshold: 相似度阈值
        """
        self.matcher = get_matcher(matcher_type)
        self.matcher_type = matcher_type
        self.include_extension = include_extension
        self.threshold = threshold
        self.file_manager = FileManager()
    
    def set_matcher(self, matcher_type: str, **kwargs):
        """
        切换匹配算法
        
        Args:
            matcher_type: 匹配算法类型
            **kwargs: 传递给匹配器的参数
        """
        self.matcher = get_matcher(matcher_type, **kwargs)
        self.matcher_type = matcher_type
    
    def calculate_pair(self, file1: str, file2: str) -> float:
        """
        计算两个文件名的相似度
        
        Args:
            file1: 第一个文件名
            file2: 第二个文件名
            
        Returns:
            相似度值 (0.0 - 1.0)
        """
        clean1 = self.file_manager.clean_filename(file1, self.include_extension)
        clean2 = self.file_manager.clean_filename(file2, self.include_extension)
        
        return self.matcher.calculate(clean1, clean2)
    
    def calculate_file_content_hash(self, file_path: str) -> str:
        """
        计算文件内容的MD5哈希值
        
        Args:
            file_path: 文件完整路径
            
        Returns:
            MD5哈希值字符串
        """
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return ""
    
    def find_groups_brute(
        self,
        files: List[str],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        暴力算法：O(n²)，精确比较所有文件对
        
        Args:
            files: 文件列表
            progress_callback: 进度回调函数
            
        Returns:
            分组列表，每个分组包含成员文件和平均相似度
        """
        n = len(files)
        if n < 2:
            return []
        
        parent = list(range(n))
        
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[py] = px
        
        total_pairs = n * (n - 1) // 2
        processed = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self.calculate_pair(files[i], files[j])
                
                if similarity >= self.threshold:
                    union(i, j)
                
                processed += 1
                if progress_callback and total_pairs > 0:
                    progress = (processed / total_pairs) * 100
                    progress_callback(progress)
        
        return self._group_by_parent(files, parent)
    
    def find_groups_optimized(
        self,
        files: List[str],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        优化算法：使用排序 + 滑动窗口，复杂度接近O(n log n)
        
        Args:
            files: 文件列表
            progress_callback: 进度回调函数
            
        Returns:
            分组列表
        """
        n = len(files)
        if n < 2:
            return []
        
        window_size = min(20, max(5, n // 5))
        parent = list(range(n))
        
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[py] = px
        
        indexed_files = []
        for idx, filename in enumerate(files):
            clean_name = self.file_manager.clean_filename(filename, self.include_extension)
            indexed_files.append((filename, clean_name, idx))
        
        indexed_files.sort(key=lambda x: x[1])
        
        total_pairs = n * window_size
        processed = 0
        
        for i in range(n):
            start_j = max(0, i - window_size)
            end_j = min(n, i + window_size + 1)
            
            for j in range(start_j, end_j):
                if i >= j:
                    continue
                
                orig_i = indexed_files[i][2]
                orig_j = indexed_files[j][2]
                
                similarity = self.calculate_pair(files[orig_i], files[orig_j])
                
                if similarity >= self.threshold:
                    union(orig_i, orig_j)
                
                processed += 1
                if progress_callback and total_pairs > 0:
                    progress = (processed / total_pairs) * 100
                    progress_callback(progress)
        
        ngram_groups = self._group_by_ngrams(files)
        for group in ngram_groups:
            if len(group) >= 2:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        union(group[i], group[j])
        
        return self._group_by_parent(files, parent)
    
    def _group_by_ngrams(self, files: List[str]) -> List[List[int]]:
        """
        使用n-gram方法对文件进行分组（优化算法的补充）
        
        Args:
            files: 文件列表
            
        Returns:
            原始索引列表的列表
        """
        n = len(files)
        if n < 2:
            return []
        
        def get_ngrams(s, k):
            if len(s) < k:
                return [s]
            return [s[i:i+k] for i in range(len(s) - k + 1)]
        
        ngram_index = defaultdict(set)
        
        for idx, filename in enumerate(files):
            clean_name = self.file_manager.clean_filename(filename, self.include_extension)
            if not clean_name:
                continue
            
            k = 2 if len(clean_name) <= 5 else 3
            ngrams = get_ngrams(clean_name, k)
            
            for gram in ngrams:
                ngram_index[gram].add(idx)
        
        candidates = set()
        
        for gram, file_indices in ngram_index.items():
            if len(file_indices) >= 2 and len(file_indices) <= 10:
                indices_list = list(file_indices)
                for i in range(len(indices_list)):
                    for j in range(i + 1, len(indices_list)):
                        candidates.add((indices_list[i], indices_list[j]))
        
        result_groups = []
        for i, j in candidates:
            similarity = self.calculate_pair(files[i], files[j])
            if similarity >= self.threshold:
                result_groups.append([i, j])
        
        return result_groups
    
    def _group_by_parent(
        self,
        files: List[str],
        parent: List[int]
    ) -> List[Dict[str, Any]]:
        """
        根据并查集的父节点分组
        
        Args:
            files: 文件列表
            parent: 并查集父节点数组
            
        Returns:
            分组列表
        """
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        
        groups = defaultdict(list)
        for i in range(len(files)):
            root = find(i)
            groups[root].append(files[i])
        
        result_groups = []
        for root, members in groups.items():
            if len(members) >= 2:
                total_sim = 0
                count = 0
                for i in range(len(members)):
                    for j in range(i + 1, len(members)):
                        sim = self.calculate_pair(members[i], members[j])
                        total_sim += sim
                        count += 1
                
                avg_similarity = total_sim / count if count > 0 else 0
                result_groups.append({
                    'members': members,
                    'avg_similarity': avg_similarity,
                    'size': len(members)
                })
        
        result_groups.sort(key=lambda x: x['avg_similarity'], reverse=True)
        
        return result_groups
    
    def find_groups_by_content(
        self,
        folder_path: str,
        files: List[str],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        根据文件内容哈希分组（精确匹配相同内容的文件）
        
        Args:
            folder_path: 文件夹路径
            files: 文件列表
            progress_callback: 进度回调函数
            
        Returns:
            分组列表
        """
        hash_groups = defaultdict(list)
        
        total = len(files)
        for idx, filename in enumerate(files):
            file_path = f"{folder_path}/{filename}"
            file_hash = self.calculate_file_content_hash(file_path)
            
            if file_hash:
                hash_groups[file_hash].append(filename)
            
            if progress_callback:
                progress = ((idx + 1) / total) * 100
                progress_callback(progress)
        
        result_groups = []
        for file_hash, members in hash_groups.items():
            if len(members) >= 2:
                result_groups.append({
                    'members': members,
                    'avg_similarity': 1.0,
                    'size': len(members),
                    'content_hash': file_hash
                })
        
        result_groups.sort(key=lambda x: x['size'], reverse=True)
        
        return result_groups
    
    def find_groups(
        self,
        files: List[str],
        algorithm: str = 'optimized',
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        查找相似文件组
        
        Args:
            files: 文件列表
            algorithm: 算法类型 ('optimized' 或 'brute')
            progress_callback: 进度回调函数
            
        Returns:
            分组列表
        """
        if algorithm == 'brute':
            return self.find_groups_brute(files, progress_callback)
        return self.find_groups_optimized(files, progress_callback)
    
    def find_duplicates_by_threshold(
        self,
        files: List[str],
        threshold: float,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        根据自定义阈值查找重复文件组
        
        Args:
            files: 文件列表
            threshold: 相似度阈值
            progress_callback: 进度回调函数
            
        Returns:
            分组列表，包含清理后的名称作为组标识
        """
        original_threshold = self.threshold
        self.threshold = threshold
        
        try:
            groups = self.find_groups_optimized(files, progress_callback)
            
            for group in groups:
                if group['members']:
                    clean_name = self.file_manager.clean_filename(
                        group['members'][0], 
                        self.include_extension
                    )
                    group['clean_name'] = clean_name
            
            return groups
        finally:
            self.threshold = original_threshold
