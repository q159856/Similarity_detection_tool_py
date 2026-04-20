#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
匹配算法模块
提供多种文件匹配方式：
1. 连续相似（最长公共子串）
2. 非连续相似（最长公共子序列）
3. N-gram 匹配
4. 编辑距离（Levenshtein）
5. Jaccard 相似度
6. 余弦相似度
7. 模糊匹配
"""

from abc import ABC, abstractmethod
from difflib import SequenceMatcher as DifflibMatcher
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set, Any


class BaseMatcher(ABC):
    """匹配算法基类"""
    
    name: str = "Base Matcher"
    description: str = "基础匹配器"
    
    @abstractmethod
    def calculate(self, str1: str, str2: str) -> float:
        """
        计算两个字符串的相似度
        
        Args:
            str1: 第一个字符串
            str2: 第二个字符串
            
        Returns:
            相似度值 (0.0 - 1.0)
        """
        pass
    
    @classmethod
    def get_name(cls) -> str:
        """获取匹配器名称"""
        return cls.name
    
    @classmethod
    def get_description(cls) -> str:
        """获取匹配器描述"""
        return cls.description


class ContinuousMatcher(BaseMatcher):
    """连续相似匹配器 - 最长公共子串"""
    
    name = "连续相似"
    description = "基于最长公共子串(LCS)，适合查找名称中包含相同片段的文件"
    
    def calculate(self, str1: str, str2: str) -> float:
        if not str1 or not str2:
            return 0.0
        
        matcher = DifflibMatcher(None, str1, str2)
        match = matcher.find_longest_match(0, len(str1), 0, len(str2))
        
        if match.size == 0:
            return 0.0
        
        min_length = min(len(str1), len(str2))
        if min_length == 0:
            return 0.0
        
        return match.size / min_length


class NonContinuousMatcher(BaseMatcher):
    """非连续相似匹配器 - 最长公共子序列"""
    
    name = "非连续相似"
    description = "基于最长公共子序列，适合查找字符顺序相同但可能有间隔的文件"
    
    def calculate(self, str1: str, str2: str) -> float:
        if not str1 or not str2:
            return 0.0
        
        m, n = len(str1), len(str2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if str1[i-1] == str2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        lcs_length = dp[m][n]
        min_length = min(len(str1), len(str2))
        
        if min_length == 0:
            return 0.0
        
        return lcs_length / min_length


class NgramMatcher(BaseMatcher):
    """N-gram 匹配器"""
    
    name = "N-gram 匹配"
    description = "基于n元语法模型，适合查找有部分重叠的文件名"
    
    def __init__(self, n: int = 2):
        """
        初始化N-gram匹配器
        
        Args:
            n: n-gram的大小，默认为2（二元语法）
        """
        self.n = n
    
    def _get_ngrams(self, s: str) -> Set[str]:
        """获取字符串的所有n-gram"""
        if len(s) < self.n:
            return {s} if s else set()
        return {s[i:i+self.n] for i in range(len(s) - self.n + 1)}
    
    def calculate(self, str1: str, str2: str) -> float:
        if not str1 or not str2:
            return 0.0
        
        ngrams1 = self._get_ngrams(str1)
        ngrams2 = self._get_ngrams(str2)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = ngrams1 & ngrams2
        union = ngrams1 | ngrams2
        
        return len(intersection) / len(union) if union else 0.0


class LevenshteinMatcher(BaseMatcher):
    """编辑距离匹配器 - Levenshtein距离"""
    
    name = "编辑距离"
    description = "基于Levenshtein编辑距离，计算将一个字符串转换为另一个所需的最少操作次数"
    
    def calculate(self, str1: str, str2: str) -> float:
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0
        
        m, n = len(str1), len(str2)
        
        if m == 0:
            return 1.0 - (n / max(m, n))
        if n == 0:
            return 1.0 - (m / max(m, n))
        
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if str1[i-1] == str2[j-1] else 1
                dp[i][j] = min(
                    dp[i-1][j] + 1,
                    dp[i][j-1] + 1,
                    dp[i-1][j-1] + cost
                )
        
        distance = dp[m][n]
        max_length = max(m, n)
        
        return 1.0 - (distance / max_length) if max_length > 0 else 1.0


class JaccardMatcher(BaseMatcher):
    """Jaccard 相似度匹配器"""
    
    name = "Jaccard 相似度"
    description = "基于字符集合的Jaccard相似度，计算两个集合的交集与并集之比"
    
    def calculate(self, str1: str, str2: str) -> float:
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0
        
        set1 = set(str1)
        set2 = set(str2)
        
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union) if union else 0.0


class CosineMatcher(BaseMatcher):
    """余弦相似度匹配器"""
    
    name = "余弦相似度"
    description = "基于字符频率向量的余弦相似度，适合比较字符分布"
    
    def calculate(self, str1: str, str2: str) -> float:
        if not str1 or not str2:
            return 0.0
        
        counter1 = Counter(str1)
        counter2 = Counter(str2)
        
        all_chars = set(counter1.keys()) | set(counter2.keys())
        
        if not all_chars:
            return 0.0
        
        dot_product = sum(counter1.get(char, 0) * counter2.get(char, 0) for char in all_chars)
        
        magnitude1 = (sum(count ** 2 for count in counter1.values())) ** 0.5
        magnitude2 = (sum(count ** 2 for count in counter2.values())) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


class FuzzyMatcher(BaseMatcher):
    """模糊匹配器 - 综合多种算法"""
    
    name = "模糊匹配"
    description = "综合多种匹配算法的加权结果，提供更灵活的匹配"
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        初始化模糊匹配器
        
        Args:
            weights: 各算法的权重字典
        """
        self.matchers = {
            'continuous': ContinuousMatcher(),
            'levenshtein': LevenshteinMatcher(),
            'ngram': NgramMatcher(2),
            'jaccard': JaccardMatcher()
        }
        
        if weights is None:
            self.weights = {
                'continuous': 0.35,
                'levenshtein': 0.30,
                'ngram': 0.20,
                'jaccard': 0.15
            }
        else:
            self.weights = weights
    
    def calculate(self, str1: str, str2: str) -> float:
        if not str1 or not str2:
            return 0.0
        
        total = 0.0
        total_weight = 0.0
        
        for name, matcher in self.matchers.items():
            weight = self.weights.get(name, 0)
            if weight > 0:
                similarity = matcher.calculate(str1, str2)
                total += similarity * weight
                total_weight += weight
        
        return total / total_weight if total_weight > 0 else 0.0


class HashMatcher(BaseMatcher):
    """哈希匹配器 - 用于精确匹配"""
    
    name = "哈希匹配"
    description = "基于内容哈希，用于精确匹配相同内容的文件"
    
    def calculate(self, str1: str, str2: str) -> float:
        """
        注意：此方法仅比较字符串，实际文件内容哈希比较
        应该在 SimilarityCalculator 中实现
        """
        if str1 == str2:
            return 1.0
        return 0.0


class ContentMatcher(BaseMatcher):
    """内容匹配器 - 比较文件内容"""
    
    name = "内容匹配"
    description = "基于文件内容的相似度比较（需读取文件内容）"
    
    def calculate(self, str1: str, str2: str) -> float:
        """
        注意：此方法为占位符，实际文件内容比较
        应该在 SimilarityCalculator 中实现
        """
        if not str1 or not str2:
            return 0.0
        
        return DifflibMatcher(None, str1, str2).ratio()


MATCHER_REGISTRY: Dict[str, type] = {
    'continuous': ContinuousMatcher,
    'non_continuous': NonContinuousMatcher,
    'ngram': NgramMatcher,
    'levenshtein': LevenshteinMatcher,
    'jaccard': JaccardMatcher,
    'cosine': CosineMatcher,
    'fuzzy': FuzzyMatcher,
}


def get_matcher(matcher_type: str, **kwargs) -> BaseMatcher:
    """
    根据类型获取匹配器实例
    
    Args:
        matcher_type: 匹配器类型
        **kwargs: 传递给匹配器的参数
        
    Returns:
        匹配器实例
    """
    matcher_class = MATCHER_REGISTRY.get(matcher_type)
    if matcher_class:
        return matcher_class(**kwargs)
    return ContinuousMatcher()


def get_all_matchers() -> List[Tuple[str, str, str]]:
    """
    获取所有可用的匹配器信息
    
    Returns:
        [(类型标识, 名称, 描述), ...]
    """
    return [
        (key, cls.name, cls.description)
        for key, cls in MATCHER_REGISTRY.items()
    ]
