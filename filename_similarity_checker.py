#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名相似度检测工具
使用Python + Tkinter实现
功能：
1. 检测文件夹中文件名的相似度
2. 支持连续相似和非连续相似两种模式
3. 可自由调整相似度比例阈值
4. 将相似度高的文件进行分组展示
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
from difflib import SequenceMatcher
from collections import defaultdict


class FilenameSimilarityChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("文件名相似度检测工具")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 设置样式 - 使用通用字体避免中文名称问题
        self.style = ttk.Style()
        # 尝试设置中文字体，如果失败则使用默认字体
        try:
            self.style.configure("Title.TLabel", font=("Microsoft YaHei UI", 14, "bold"))
            self.style.configure("Heading.TLabel", font=("Microsoft YaHei UI", 11, "bold"))
            self.style.configure("Normal.TLabel", font=("Microsoft YaHei UI", 10))
            self.style.configure("Result.TLabel", font=("Microsoft YaHei UI", 9), foreground="#333333")
        except:
            # 如果中文不可用，使用默认字体
            self.style.configure("Title.TLabel", font=("TkDefaultFont", 14, "bold"))
            self.style.configure("Heading.TLabel", font=("TkDefaultFont", 11, "bold"))
            self.style.configure("Normal.TLabel", font=("TkDefaultFont", 10))
            self.style.configure("Result.TLabel", font=("TkDefaultFont", 9), foreground="#333333")
        
        # 存储检测结果
        self.similar_groups = []
        self.folder_path = ""
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="文件名相似度检测工具", style="Title.TLabel")
        title_label.pack(pady=(0, 10))
        
        # 文件夹选择区域
        folder_frame = ttk.LabelFrame(main_frame, text="文件夹选择", padding="10")
        folder_frame.pack(fill=tk.X, pady=5)
        
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=60)
        self.folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(folder_frame, text="浏览", command=self.browse_folder)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # 设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="检测设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # 相似度模式选择
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        mode_label = ttk.Label(mode_frame, text="相似度模式：", style="Normal.TLabel")
        mode_label.pack(side=tk.LEFT, padx=5)
        
        self.similarity_mode = tk.StringVar(value="continuous")
        continuous_radio = ttk.Radiobutton(
            mode_frame, 
            text="连续相似（最长公共子串）", 
            variable=self.similarity_mode, 
            value="continuous"
        )
        continuous_radio.pack(side=tk.LEFT, padx=20)
        
        non_continuous_radio = ttk.Radiobutton(
            mode_frame, 
            text="非连续相似（最长公共子序列）", 
            variable=self.similarity_mode, 
            value="non_continuous"
        )
        non_continuous_radio.pack(side=tk.LEFT, padx=20)
        
        # 相似度阈值设置
        threshold_frame = ttk.Frame(settings_frame)
        threshold_frame.pack(fill=tk.X, pady=10)
        
        threshold_label = ttk.Label(threshold_frame, text="相似度阈值：", style="Normal.TLabel")
        threshold_label.pack(side=tk.LEFT, padx=5)
        
        self.threshold_var = tk.DoubleVar(value=0.6)
        self.threshold_scale = ttk.Scale(
            threshold_frame, 
            from_=0.1, 
            to=1.0, 
            variable=self.threshold_var, 
            orient=tk.HORIZONTAL,
            length=400,
            command=self.update_threshold_label
        )
        self.threshold_scale.pack(side=tk.LEFT, padx=10)
        
        self.threshold_value_label = ttk.Label(threshold_frame, text="60%", style="Normal.TLabel")
        self.threshold_value_label.pack(side=tk.LEFT, padx=5)
        
        # 是否包含扩展名
        ext_frame = ttk.Frame(settings_frame)
        ext_frame.pack(fill=tk.X, pady=5)
        
        self.include_extension = tk.BooleanVar(value=False)
        ext_check = ttk.Checkbutton(
            ext_frame, 
            text="包含文件扩展名进行比较", 
            variable=self.include_extension
        )
        ext_check.pack(side=tk.LEFT, padx=5)
        
        # 算法选择
        algorithm_frame = ttk.Frame(settings_frame)
        algorithm_frame.pack(fill=tk.X, pady=5)
        
        algorithm_label = ttk.Label(algorithm_frame, text="匹配算法：", style="Normal.TLabel")
        algorithm_label.pack(side=tk.LEFT, padx=5)
        
        self.algorithm_mode = tk.StringVar(value="optimized")
        optimized_radio = ttk.Radiobutton(
            algorithm_frame, 
            text="优化算法（O(n log n)，推荐）", 
            variable=self.algorithm_mode, 
            value="optimized"
        )
        optimized_radio.pack(side=tk.LEFT, padx=20)
        
        brute_radio = ttk.Radiobutton(
            algorithm_frame, 
            text="暴力算法（O(n²)，精确）", 
            variable=self.algorithm_mode, 
            value="brute"
        )
        brute_radio.pack(side=tk.LEFT, padx=20)
        
        # 重复文件管理阈值百分比设置
        duplicate_threshold_frame = ttk.Frame(settings_frame)
        duplicate_threshold_frame.pack(fill=tk.X, pady=10)
        
        duplicate_threshold_label = ttk.Label(duplicate_threshold_frame, text="管理阈值百分比：", style="Normal.TLabel")
        duplicate_threshold_label.pack(side=tk.LEFT, padx=5)
        
        self.duplicate_percent_var = tk.DoubleVar(value=100.0)
        self.duplicate_percent_scale = ttk.Scale(
            duplicate_threshold_frame, 
            from_=0.0, 
            to=100.0, 
            variable=self.duplicate_percent_var, 
            orient=tk.HORIZONTAL,
            length=300,
            command=self.update_duplicate_threshold_label
        )
        self.duplicate_percent_scale.pack(side=tk.LEFT, padx=10)
        
        self.duplicate_threshold_value_label = ttk.Label(duplicate_threshold_frame, text="实际：100% (100%)", style="Normal.TLabel")
        self.duplicate_threshold_value_label.pack(side=tk.LEFT, padx=5)
        
        # 说明标签
        info_label = ttk.Label(
            duplicate_threshold_frame, 
            text="（在相似度阈值之上的百分比，如：阈值60%+50%=实际80%）", 
            style="Normal.TLabel",
            foreground="#666666"
        )
        info_label.pack(side=tk.LEFT, padx=10)
        
        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        check_btn = ttk.Button(btn_frame, text="开始检测", command=self.start_check)
        check_btn.pack(side=tk.LEFT, padx=10)
        
        clear_btn = ttk.Button(btn_frame, text="清空结果", command=self.clear_results)
        clear_btn.pack(side=tk.LEFT, padx=10)
        
        export_btn = ttk.Button(btn_frame, text="导出结果", command=self.export_results)
        export_btn.pack(side=tk.LEFT, padx=10)
        
        self.manage_duplicates_btn = ttk.Button(btn_frame, text="管理重复文件", command=self.manage_duplicates)
        self.manage_duplicates_btn.pack(side=tk.LEFT, padx=10)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(main_frame, text="就绪", style="Normal.TLabel")
        self.status_label.pack(anchor=tk.W)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="检测结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建带滚动条的文本区域
        text_frame = ttk.Frame(result_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 使用默认字体创建文本区域
        self.result_text = tk.Text(text_frame, wrap=tk.WORD, relief=tk.SUNKEN, borderwidth=1)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        # 配置文本标签样式 - 使用相对字体大小
        import tkinter.font as tkfont
        try:
            # 获取默认字体并设置合适的大小
            default_font = tkfont.nametofont("TkDefaultFont")
            # 创建不同大小的字体
            title_font = tkfont.Font(font=default_font)
            title_font.configure(size=11, weight="bold")
            
            bold_font = tkfont.Font(font=default_font)
            bold_font.configure(weight="bold")
            
            normal_font = tkfont.Font(font=default_font)
            normal_font.configure(size=9)
            
            summary_font = tkfont.Font(font=default_font)
            summary_font.configure(size=10, weight="bold")
        except:
            # 如果失败，使用简单的字体配置
            title_font = ("TkDefaultFont", 11, "bold")
            bold_font = ("TkDefaultFont", 9, "bold")
            normal_font = ("TkDefaultFont", 9)
            summary_font = ("TkDefaultFont", 10, "bold")
        
        self.result_text.tag_configure("group_title", font=title_font, foreground="#2c3e50", background="#ecf0f1")
        self.result_text.tag_configure("similarity_high", foreground="#e74c3c", font=bold_font)
        self.result_text.tag_configure("similarity_medium", foreground="#f39c12", font=normal_font)
        self.result_text.tag_configure("filename", foreground="#2980b9", font=normal_font)
        self.result_text.tag_configure("separator", foreground="#95a5a6")
        self.result_text.tag_configure("summary", font=summary_font, foreground="#27ae60")
        
    def update_threshold_label(self, value):
        """更新阈值显示标签"""
        percentage = float(value) * 100
        self.threshold_value_label.configure(text=f"{percentage:.0f}%")
        # 同时更新重复文件管理阈值的显示
        self.update_duplicate_threshold_label(self.duplicate_percent_var.get())
    
    def update_duplicate_threshold_label(self, value):
        """更新重复文件管理阈值显示标签"""
        percent_value = float(value)
        base_threshold = self.threshold_var.get() * 100
        
        # 计算实际阈值：base_threshold + (100 - base_threshold) * (percent_value / 100)
        actual_threshold = base_threshold + (100 - base_threshold) * (percent_value / 100)
        
        self.duplicate_threshold_value_label.configure(
            text=f"实际：{actual_threshold:.0f}% ({percent_value:.0f}%)"
        )
        
    def browse_folder(self):
        """浏览选择文件夹"""
        folder_selected = filedialog.askdirectory(title="选择要检测的文件夹")
        if folder_selected:
            self.folder_path = folder_selected
            self.folder_var.set(folder_selected)
            
    def get_files_in_folder(self, folder_path):
        """获取文件夹中的所有文件"""
        files = []
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    files.append(item)
        except Exception as e:
            messagebox.showerror("错误", f"读取文件夹时出错：{str(e)}")
        return files
    
    def clean_filename(self, filename):
        """预处理文件名，去除扩展名（可选）和特殊字符"""
        if not self.include_extension.get():
            # 去除文件扩展名
            filename = os.path.splitext(filename)[0]
        
        # 去除常见的特殊字符和空格，只保留字母、数字和中文
        filename = re.sub(r'[^\w\u4e00-\u9fa5]', '', filename)
        return filename.lower()
    
    def continuous_similarity(self, str1, str2):
        """
        连续字符串相似度检测 - 基于最长公共子串
        返回相似度比例 (0.0 - 1.0)
        """
        if not str1 or not str2:
            return 0.0
        
        # 使用SequenceMatcher计算最长公共子串
        matcher = SequenceMatcher(None, str1, str2)
        match = matcher.find_longest_match(0, len(str1), 0, len(str2))
        
        if match.size == 0:
            return 0.0
        
        # 计算相似度：最长公共子串长度 / 较短字符串长度
        min_length = min(len(str1), len(str2))
        if min_length == 0:
            return 0.0
        
        return match.size / min_length
    
    def non_continuous_similarity(self, str1, str2):
        """
        非连续字符串相似度检测 - 基于最长公共子序列 (LCS)
        返回相似度比例 (0.0 - 1.0)
        """
        if not str1 or not str2:
            return 0.0
        
        # 使用动态规划计算LCS
        m, n = len(str1), len(str2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if str1[i-1] == str2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        lcs_length = dp[m][n]
        
        # 计算相似度：LCS长度 / 较短字符串长度
        min_length = min(len(str1), len(str2))
        if min_length == 0:
            return 0.0
        
        return lcs_length / min_length
    
    def calculate_similarity(self, file1, file2):
        """根据选择的模式计算两个文件名的相似度"""
        clean1 = self.clean_filename(file1)
        clean2 = self.clean_filename(file2)
        
        if self.similarity_mode.get() == "continuous":
            return self.continuous_similarity(clean1, clean2)
        else:
            return self.non_continuous_similarity(clean1, clean2)
    
    def find_similar_groups(self, files):
        """
        找出相似度高的文件并分组
        根据选择的算法使用不同的匹配策略
        """
        if self.algorithm_mode.get() == "optimized":
            return self.find_similar_groups_optimized(files)
        else:
            return self.find_similar_groups_brute(files)
    
    def find_similar_groups_brute(self, files):
        """
        暴力算法：O(n²)，精确比较所有文件对
        """
        threshold = self.threshold_var.get()
        n = len(files)
        
        # 并查集数据结构
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
        
        # 存储所有相似度对
        similarity_pairs = []
        
        # 计算所有文件对的相似度
        total_pairs = n * (n - 1) // 2
        processed = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self.calculate_similarity(files[i], files[j])
                similarity_pairs.append((i, j, similarity))
                
                if similarity >= threshold:
                    union(i, j)
                
                processed += 1
                progress = (processed / total_pairs) * 100 if total_pairs > 0 else 0
                self.progress_var.set(progress)
                self.root.update()
        
        # 按根节点分组
        groups = defaultdict(list)
        for i in range(n):
            root = find(i)
            groups[root].append(files[i])
        
        # 筛选出大小>=2的组，并计算组内相似度
        result_groups = []
        for root, members in groups.items():
            if len(members) >= 2:
                # 计算组内所有文件对的平均相似度
                total_sim = 0
                count = 0
                for i in range(len(members)):
                    for j in range(i + 1, len(members)):
                        sim = self.calculate_similarity(members[i], members[j])
                        total_sim += sim
                        count += 1
                
                avg_similarity = total_sim / count if count > 0 else 0
                result_groups.append({
                    'members': members,
                    'avg_similarity': avg_similarity,
                    'size': len(members)
                })
        
        # 按平均相似度降序排序
        result_groups.sort(key=lambda x: x['avg_similarity'], reverse=True)
        
        return result_groups
    
    def find_similar_groups_optimized(self, files):
        """
        优化算法：使用排序 + 滑动窗口，复杂度接近O(n log n)
        原理：先对文件名排序，相似的文件名在排序后会相邻
        然后使用滑动窗口只比较相邻的文件，大大减少比较次数
        """
        threshold = self.threshold_var.get()
        n = len(files)
        
        # 滑动窗口大小：每个文件只比较前后window_size个文件
        # 动态调整窗口大小，文件越多窗口越大，但最多不超过20
        window_size = min(20, max(5, n // 5))
        
        # 并查集数据结构
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
        
        # 第一步：对文件按清理后的名称排序（O(n log n)）
        # 创建(原始文件名, 清理后文件名, 原始索引)的元组列表
        indexed_files = []
        for idx, filename in enumerate(files):
            clean_name = self.clean_filename(filename)
            indexed_files.append((filename, clean_name, idx))
        
        # 按清理后的名称排序
        indexed_files.sort(key=lambda x: x[1])
        
        # 第二步：使用滑动窗口比较相邻文件
        # 估算总比较次数：n * window_size
        total_pairs = n * window_size
        processed = 0
        
        for i in range(n):
            # 只比较当前文件与前后window_size范围内的文件
            start_j = max(0, i - window_size)
            end_j = min(n, i + window_size + 1)
            
            for j in range(start_j, end_j):
                if i >= j:
                    continue  # 避免重复比较
                
                # 获取原始索引
                orig_i = indexed_files[i][2]
                orig_j = indexed_files[j][2]
                
                # 计算相似度
                similarity = self.calculate_similarity(files[orig_i], files[orig_j])
                
                if similarity >= threshold:
                    union(orig_i, orig_j)
                
                processed += 1
                progress = (processed / total_pairs) * 100 if total_pairs > 0 else 0
                self.progress_var.set(progress)
                self.root.update()
        
        # 第三步：额外的n-gram分组策略，确保不会遗漏相似文件
        # 对于相似度可能较高的文件，使用n-gram进一步分组
        ngram_groups = self.group_by_ngrams(files, threshold)
        
        # 合并n-gram分组的结果到并查集
        for group in ngram_groups:
            if len(group) >= 2:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        union(group[i], group[j])
        
        # 按根节点分组
        groups = defaultdict(list)
        for i in range(n):
            root = find(i)
            groups[root].append(files[i])
        
        # 筛选出大小>=2的组，并计算组内相似度
        result_groups = []
        for root, members in groups.items():
            if len(members) >= 2:
                # 计算组内所有文件对的平均相似度
                total_sim = 0
                count = 0
                for i in range(len(members)):
                    for j in range(i + 1, len(members)):
                        sim = self.calculate_similarity(members[i], members[j])
                        total_sim += sim
                        count += 1
                
                avg_similarity = total_sim / count if count > 0 else 0
                result_groups.append({
                    'members': members,
                    'avg_similarity': avg_similarity,
                    'size': len(members)
                })
        
        # 按平均相似度降序排序
        result_groups.sort(key=lambda x: x['avg_similarity'], reverse=True)
        
        return result_groups
    
    def group_by_ngrams(self, files, threshold):
        """
        使用n-gram方法对文件进行分组
        这是优化算法的补充，用于捕获滑动窗口可能遗漏的相似文件
        返回：[[原始索引列表], ...]
        """
        n = len(files)
        if n < 2:
            return []
        
        # 选择n-gram的大小，对于短文件名使用2-gram，长文件名使用3-gram
        def get_ngrams(s, k):
            """获取字符串的所有k-gram"""
            if len(s) < k:
                return [s]
            return [s[i:i+k] for i in range(len(s) - k + 1)]
        
        # 为每个文件生成ngram索引
        ngram_index = defaultdict(set)  # ngram -> {文件索引}
        
        for idx, filename in enumerate(files):
            clean_name = self.clean_filename(filename)
            if not clean_name:
                continue
            
            # 选择合适的ngram大小
            k = 2 if len(clean_name) <= 5 else 3
            ngrams = get_ngrams(clean_name, k)
            
            for gram in ngrams:
                ngram_index[gram].add(idx)
        
        # 计算文件间的ngram重叠分数
        # 只处理那些共享足够多ngram的文件对
        candidates = set()
        
        for gram, file_indices in ngram_index.items():
            if len(file_indices) >= 2 and len(file_indices) <= 10:  # 只考虑中等大小的ngram组
                indices_list = list(file_indices)
                for i in range(len(indices_list)):
                    for j in range(i + 1, len(indices_list)):
                        candidates.add((indices_list[i], indices_list[j]))
        
        # 验证候选对的实际相似度
        result_groups = []
        for i, j in candidates:
            similarity = self.calculate_similarity(files[i], files[j])
            if similarity >= threshold:
                result_groups.append([i, j])
        
        return result_groups
    
    def start_check(self):
        """开始检测"""
        if not self.folder_path or not os.path.exists(self.folder_path):
            messagebox.showwarning("警告", "请先选择一个有效的文件夹")
            return
        
        # 清空之前的结果
        self.result_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.status_label.configure(text="正在读取文件...")
        self.root.update()
        
        # 获取文件列表
        files = self.get_files_in_folder(self.folder_path)
        
        if len(files) < 2:
            messagebox.showinfo("提示", "文件夹中文件数量不足，无法进行相似度检测")
            self.status_label.configure(text="就绪")
            return
        
        self.status_label.configure(text=f"共发现 {len(files)} 个文件，正在检测相似度...")
        self.root.update()
        
        # 检测相似度
        try:
            self.similar_groups = self.find_similar_groups(files)
            
            # 显示结果
            self.display_results()
            
            self.progress_var.set(100)
            mode_text = "连续相似" if self.similarity_mode.get() == "continuous" else "非连续相似"
            threshold_text = f"{self.threshold_var.get() * 100:.0f}%"
            self.status_label.configure(
                text=f"检测完成！发现 {len(self.similar_groups)} 组相似文件（{mode_text}，阈值：{threshold_text}）"
            )
            
        except Exception as e:
            messagebox.showerror("错误", f"检测过程中发生错误：{str(e)}")
            self.status_label.configure(text="检测失败")
    
    def display_results(self):
        """显示检测结果"""
        self.result_text.delete(1.0, tk.END)
        
        if not self.similar_groups:
            self.result_text.insert(tk.END, "未发现相似度高的文件组。\n", "summary")
            self.result_text.insert(tk.END, "建议降低相似度阈值后重新检测。\n")
            return
        
        # 显示统计信息
        total_files = sum(group['size'] for group in self.similar_groups)
        summary = f"检测完成！共发现 {len(self.similar_groups)} 组相似文件，涉及 {total_files} 个文件。\n\n"
        self.result_text.insert(tk.END, summary, "summary")
        
        mode_text = "连续相似（最长公共子串）" if self.similarity_mode.get() == "continuous" else "非连续相似（最长公共子序列）"
        threshold_text = f"{self.threshold_var.get() * 100:.0f}%"
        settings_info = f"检测模式：{mode_text}\n相似度阈值：{threshold_text}\n"
        self.result_text.insert(tk.END, settings_info)
        self.result_text.insert(tk.END, "=" * 80 + "\n\n", "separator")
        
        # 显示每个分组
        for idx, group in enumerate(self.similar_groups, 1):
            avg_sim = group['avg_similarity']
            members = group['members']
            
            # 组标题
            group_title = f"【第 {idx} 组】平均相似度：{avg_sim * 100:.1f}% （共 {len(members)} 个文件）\n"
            self.result_text.insert(tk.END, group_title, "group_title")
            
            # 对组成员按相似度与第一个文件的相似度排序
            if members:
                first_file = members[0]
                sorted_members = sorted(
                    members[1:],
                    key=lambda x: self.calculate_similarity(first_file, x),
                    reverse=True
                )
                sorted_members = [first_file] + sorted_members
            else:
                sorted_members = members
            
            # 显示文件列表
            for i, filename in enumerate(sorted_members, 1):
                # 计算与第一个文件的相似度
                if i == 1:
                    sim_text = "（基准文件）"
                    tag = "filename"
                else:
                    sim = self.calculate_similarity(sorted_members[0], filename)
                    sim_text = f"（与基准相似度：{sim * 100:.1f}%）"
                    # 根据相似度选择标签
                    if sim >= 0.8:
                        tag = "similarity_high"
                    elif sim >= 0.6:
                        tag = "similarity_medium"
                    else:
                        tag = "filename"
                
                self.result_text.insert(tk.END, f"  {i}. {filename} ", "filename")
                self.result_text.insert(tk.END, f"{sim_text}\n", tag)
            
            self.result_text.insert(tk.END, "\n")
            self.result_text.insert(tk.END, "-" * 60 + "\n\n", "separator")
    
    def clear_results(self):
        """清空结果"""
        self.result_text.delete(1.0, tk.END)
        self.similar_groups = []
        self.progress_var.set(0)
        self.status_label.configure(text="就绪")
    
    def export_results(self):
        """导出检测结果到文本文件"""
        if not self.similar_groups:
            messagebox.showwarning("警告", "没有可导出的检测结果")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存检测结果",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入标题
                f.write("=" * 80 + "\n")
                f.write("文件名相似度检测结果报告\n")
                f.write("=" * 80 + "\n\n")
                
                # 写入检测设置
                mode_text = "连续相似（最长公共子串）" if self.similarity_mode.get() == "continuous" else "非连续相似（最长公共子序列）"
                threshold_text = f"{self.threshold_var.get() * 100:.0f}%"
                f.write(f"检测文件夹：{self.folder_path}\n")
                f.write(f"检测模式：{mode_text}\n")
                f.write(f"相似度阈值：{threshold_text}\n")
                f.write(f"是否包含扩展名：{'是' if self.include_extension.get() else '否'}\n\n")
                
                # 写入统计信息
                total_files = sum(group['size'] for group in self.similar_groups)
                f.write(f"检测结果统计：\n")
                f.write(f"- 相似文件组数量：{len(self.similar_groups)}\n")
                f.write(f"- 涉及文件总数：{total_files}\n\n")
                
                f.write("=" * 80 + "\n\n")
                
                # 写入每个分组
                for idx, group in enumerate(self.similar_groups, 1):
                    avg_sim = group['avg_similarity']
                    members = group['members']
                    
                    f.write(f"【第 {idx} 组】平均相似度：{avg_sim * 100:.1f}% （共 {len(members)} 个文件）\n")
                    f.write("-" * 60 + "\n")
                    
                    # 对组成员排序
                    if members:
                        first_file = members[0]
                        sorted_members = sorted(
                            members[1:],
                            key=lambda x: self.calculate_similarity(first_file, x),
                            reverse=True
                        )
                        sorted_members = [first_file] + sorted_members
                    else:
                        sorted_members = members
                    
                    for i, filename in enumerate(sorted_members, 1):
                        if i == 1:
                            f.write(f"  {i}. {filename} （基准文件）\n")
                        else:
                            sim = self.calculate_similarity(sorted_members[0], filename)
                            f.write(f"  {i}. {filename} （与基准相似度：{sim * 100:.1f}%）\n")
                    
                    f.write("\n")
                
                f.write("=" * 80 + "\n")
                f.write("检测报告结束\n")
                f.write("=" * 80 + "\n")
            
            messagebox.showinfo("成功", f"检测结果已成功导出到：\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出结果时发生错误：{str(e)}")
    
    def find_duplicates_by_threshold(self, files, threshold):
        """
        找出相似度达到指定阈值的文件组
        参数：
            files: 文件列表
            threshold: 相似度阈值 (0.0 - 1.0)
        返回：[{'members': [文件名列表], 'clean_name': '清理后的文件名', 'avg_similarity': 平均相似度}, ...]
        """
        n = len(files)
        if n < 2:
            return []
        
        # 并查集数据结构
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
        
        # 第一步：使用优化策略查找相似文件
        # 1. 先按清理后的名称排序
        indexed_files = []
        for idx, filename in enumerate(files):
            clean_name = self.clean_filename(filename)
            indexed_files.append((filename, clean_name, idx))
        
        indexed_files.sort(key=lambda x: x[1])
        
        # 2. 滑动窗口比较
        window_size = min(20, max(5, n // 5))
        
        for i in range(n):
            start_j = max(0, i - window_size)
            end_j = min(n, i + window_size + 1)
            
            for j in range(start_j, end_j):
                if i >= j:
                    continue
                
                orig_i = indexed_files[i][2]
                orig_j = indexed_files[j][2]
                
                similarity = self.calculate_similarity(files[orig_i], files[orig_j])
                
                if similarity >= threshold:
                    union(orig_i, orig_j)
        
        # 3. 使用n-gram补充查找
        ngram_groups = self.group_by_ngrams(files, threshold)
        for group in ngram_groups:
            if len(group) >= 2:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        union(group[i], group[j])
        
        # 按根节点分组
        groups = defaultdict(list)
        for i in range(n):
            root = find(i)
            groups[root].append(files[i])
        
        # 筛选出大小>=2的组，并计算组内相似度
        result = []
        for root, members in groups.items():
            if len(members) >= 2:
                # 计算组内所有文件对的平均相似度
                total_sim = 0
                count = 0
                for i in range(len(members)):
                    for j in range(i + 1, len(members)):
                        sim = self.calculate_similarity(members[i], members[j])
                        total_sim += sim
                        count += 1
                
                avg_similarity = total_sim / count if count > 0 else 0
                
                # 使用第一个文件的清理名称作为组名
                clean_name = self.clean_filename(members[0]) if members else ""
                
                result.append({
                    'clean_name': clean_name,
                    'members': members,
                    'avg_similarity': avg_similarity,
                    'size': len(members)
                })
        
        # 按平均相似度降序排序，相似度相同则按文件数量降序
        result.sort(key=lambda x: (x['avg_similarity'], x['size']), reverse=True)
        
        return result
    
    def manage_duplicates(self):
        """管理重复文件（根据自定义阈值）"""
        if not self.folder_path or not os.path.exists(self.folder_path):
            messagebox.showwarning("警告", "请先选择一个有效的文件夹")
            return
        
        # 计算实际阈值
        base_threshold = self.threshold_var.get()
        percent_value = self.duplicate_percent_var.get() / 100.0
        
        # 实际阈值 = 基础阈值 + (1.0 - 基础阈值) * 百分比
        actual_threshold = base_threshold + (1.0 - base_threshold) * percent_value
        
        # 获取文件列表
        files = self.get_files_in_folder(self.folder_path)
        
        if len(files) < 2:
            messagebox.showinfo("提示", "文件夹中文件数量不足，无法检测重复文件")
            return
        
        # 找出达到阈值的相似文件
        self.status_label.configure(text=f"正在检测相似度 >= {actual_threshold * 100:.0f}% 的文件...")
        self.root.update()
        
        duplicate_groups = self.find_duplicates_by_threshold(files, actual_threshold)
        
        if not duplicate_groups:
            messagebox.showinfo("提示", f"未发现相似度 >= {actual_threshold * 100:.0f}% 的文件")
            self.status_label.configure(text="就绪")
            return
        
        # 创建重复文件管理窗口
        self.create_duplicate_manager_window(duplicate_groups, actual_threshold)
    
    def create_duplicate_manager_window(self, duplicate_groups, threshold):
        """创建重复文件管理窗口"""
        # 创建新窗口
        dup_window = tk.Toplevel(self.root)
        dup_window.title(f"重复文件管理器（相似度 >= {threshold * 100:.0f}%）")
        dup_window.geometry("800x600")
        dup_window.resizable(True, True)
        
        # 存储选中的文件
        selected_files = set()
        
        # 创建主框架
        main_frame = ttk.Frame(dup_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题和说明
        title_label = ttk.Label(main_frame, text=f"重复文件管理器（相似度 >= {threshold * 100:.0f}%）", style="Title.TLabel")
        title_label.pack(pady=(0, 5))
        
        info_text = f"共发现 {len(duplicate_groups)} 组相似文件，涉及 {sum(g['size'] for g in duplicate_groups)} 个文件。\n请勾选要删除的文件（每组至少保留一个文件）。"
        info_label = ttk.Label(main_frame, text=info_text, style="Normal.TLabel")
        info_label.pack(pady=(0, 10))
        
        # 创建带滚动条的画布和框架
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 存储每个组的复选框变量
        group_vars = []
        
        # 显示每个重复文件组
        for group_idx, group in enumerate(duplicate_groups, 1):
            members = group['members']
            clean_name = group['clean_name']
            avg_sim = group.get('avg_similarity', 1.0)
            
            # 组框架
            group_frame = ttk.LabelFrame(scrollable_frame, text=f"【第 {group_idx} 组】平均相似度：{avg_sim * 100:.1f}% （共 {len(members)} 个文件）", padding="10")
            group_frame.pack(fill=tk.X, pady=5, padx=5)
            
            # 存储该组的复选框变量
            file_vars = []
            
            # 显示每个文件的详细信息
            for file_idx, filename in enumerate(members):
                file_path = os.path.join(self.folder_path, filename)
                
                # 获取文件信息
                try:
                    file_size = os.path.getsize(file_path)
                    file_size_str = self.format_file_size(file_size)
                    mod_time = os.path.getmtime(file_path)
                    from datetime import datetime
                    mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    file_size_str = "未知"
                    mod_time_str = "未知"
                
                # 文件框架
                file_frame = ttk.Frame(group_frame)
                file_frame.pack(fill=tk.X, pady=2)
                
                # 复选框变量
                var = tk.BooleanVar(value=False)
                file_vars.append(var)
                
                # 复选框
                cb = ttk.Checkbutton(file_frame, variable=var)
                cb.pack(side=tk.LEFT, padx=5)
                
                # 文件名（突出显示）
                name_label = ttk.Label(file_frame, text=filename, foreground="#2980b9", font=("TkDefaultFont", 9, "bold"))
                name_label.pack(side=tk.LEFT, padx=5)
                
                # 文件信息
                info_str = f"大小：{file_size_str} | 修改时间：{mod_time_str}"
                info_label = ttk.Label(file_frame, text=info_str, foreground="#666666", font=("TkDefaultFont", 8))
                info_label.pack(side=tk.LEFT, padx=5)
                
                # 打开文件位置按钮
                def open_location(fp=file_path):
                    import subprocess
                    folder_path = os.path.dirname(fp)
                    if os.path.exists(folder_path):
                        try:
                            os.startfile(folder_path)
                        except:
                            subprocess.run(['explorer', folder_path])
                
                open_btn = ttk.Button(file_frame, text="打开位置", width=8, command=open_location)
                open_btn.pack(side=tk.RIGHT, padx=5)
            
            group_vars.append({
                'group': group,
                'file_vars': file_vars,
                'members': members
            })
            
            # 组操作按钮
            btn_frame = ttk.Frame(group_frame)
            btn_frame.pack(fill=tk.X, pady=5)
            
            # 自动选择辅助函数
            def select_by_criteria(group_vars_idx=group_idx-1, criteria=None):
                """根据条件选择文件"""
                gv = group_vars[group_vars_idx]
                members = gv['members']
                file_vars = gv['file_vars']
                
                if len(members) < 2:
                    return
                
                # 获取文件信息
                file_infos = []
                for idx, filename in enumerate(members):
                    file_path = os.path.join(self.folder_path, filename)
                    try:
                        file_size = os.path.getsize(file_path)
                        mod_time = os.path.getmtime(file_path)
                    except:
                        file_size = 0
                        mod_time = 0
                    file_infos.append({
                        'idx': idx,
                        'size': file_size,
                        'mod_time': mod_time,
                        'filename': filename
                    })
                
                # 根据条件排序
                if criteria == 'newest':
                    # 最新的保留，其他选中删除
                    file_infos.sort(key=lambda x: x['mod_time'], reverse=True)
                elif criteria == 'oldest':
                    # 最旧的保留，其他选中删除
                    file_infos.sort(key=lambda x: x['mod_time'])
                elif criteria == 'largest':
                    # 最大的保留，其他选中删除
                    file_infos.sort(key=lambda x: x['size'], reverse=True)
                elif criteria == 'smallest':
                    # 最小的保留，其他选中删除
                    file_infos.sort(key=lambda x: x['size'])
                else:
                    return
                
                # 第一个保留（不选中），其他选中删除
                for i, info in enumerate(file_infos):
                    if i == 0:
                        file_vars[info['idx']].set(False)
                    else:
                        file_vars[info['idx']].set(True)
            
            # 添加快速选择按钮
            ttk.Button(btn_frame, text="保留最新", width=8, 
                      command=lambda g=group_idx-1: select_by_criteria(g, 'newest')).pack(side=tk.LEFT, padx=2)
            ttk.Button(btn_frame, text="保留最旧", width=8,
                      command=lambda g=group_idx-1: select_by_criteria(g, 'oldest')).pack(side=tk.LEFT, padx=2)
            ttk.Button(btn_frame, text="保留最大", width=8,
                      command=lambda g=group_idx-1: select_by_criteria(g, 'largest')).pack(side=tk.LEFT, padx=2)
            ttk.Button(btn_frame, text="保留最小", width=8,
                      command=lambda g=group_idx-1: select_by_criteria(g, 'smallest')).pack(side=tk.LEFT, padx=2)
            ttk.Label(btn_frame, text="← 快速选择", foreground="#666666").pack(side=tk.LEFT, padx=10)
        
        # 底部按钮区域
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        def get_selected_files():
            """获取所有选中的文件"""
            selected = []
            for gv in group_vars:
                members = gv['members']
                file_vars = gv['file_vars']
                for idx, var in enumerate(file_vars):
                    if var.get():
                        selected.append(members[idx])
            return selected
        
        def validate_selection():
            """验证选择是否合法（每组至少保留一个）"""
            for gv in group_vars:
                file_vars = gv['file_vars']
                members = gv['members']
                selected_count = sum(1 for var in file_vars if var.get())
                if selected_count >= len(members):
                    return False, f"第 {group_vars.index(gv) + 1} 组选择了所有文件！每组至少需要保留一个文件。"
            return True, ""
        
        def delete_selected():
            """删除选中的文件"""
            # 验证选择
            valid, message = validate_selection()
            if not valid:
                messagebox.showwarning("警告", message)
                return
            
            # 获取选中的文件
            selected = get_selected_files()
            
            if not selected:
                messagebox.showinfo("提示", "没有选中任何文件")
                return
            
            # 确认删除
            confirm_msg = f"您确定要删除以下 {len(selected)} 个文件吗？\n此操作不可撤销！\n\n"
            for filename in selected[:10]:  # 只显示前10个
                confirm_msg += f"  - {filename}\n"
            if len(selected) > 10:
                confirm_msg += f"  ... 还有 {len(selected) - 10} 个文件\n"
            
            if not messagebox.askyesno("确认删除", confirm_msg):
                return
            
            # 执行删除
            deleted = []
            errors = []
            
            for filename in selected:
                file_path = os.path.join(self.folder_path, filename)
                try:
                    os.remove(file_path)
                    deleted.append(filename)
                except Exception as e:
                    errors.append(f"{filename}: {str(e)}")
            
            # 显示结果
            result_msg = ""
            if deleted:
                result_msg += f"成功删除 {len(deleted)} 个文件\n"
            if errors:
                result_msg += f"删除失败 {len(errors)} 个文件：\n"
                for err in errors[:5]:
                    result_msg += f"  - {err}\n"
                if len(errors) > 5:
                    result_msg += f"  ... 还有 {len(errors) - 5} 个错误\n"
            
            if errors:
                messagebox.showwarning("删除完成", result_msg)
            else:
                messagebox.showinfo("删除完成", result_msg)
            
            # 关闭窗口并刷新主界面
            dup_window.destroy()
            
            # 重新检测
            if self.similar_groups:
                self.start_check()
        
        def select_all_except_one():
            """全选（每组留一个）"""
            for gv in group_vars:
                file_vars = gv['file_vars']
                for idx, var in enumerate(file_vars):
                    if idx == 0:
                        var.set(False)  # 第一个不选
                    else:
                        var.set(True)
        
        def deselect_all():
            """取消全选"""
            for gv in group_vars:
                for var in gv['file_vars']:
                    var.set(False)
        
        # 底部按钮
        ttk.Button(bottom_frame, text="全选（每组留一个）", command=select_all_except_one).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="取消全选", command=deselect_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="删除选中的文件", command=delete_selected).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="关闭", command=dup_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 设置窗口在最前
        dup_window.transient(self.root)
        dup_window.grab_set()
        self.root.wait_window(dup_window)
    
    def format_file_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置中文字体支持 - 使用更兼容的方式
    try:
        # 尝试创建中文字体对象
        import tkinter.font as tkfont
        default_font = tkfont.nametofont("TkDefaultFont")
        # 检查系统是否有微软雅黑字体
        font_families = [f.lower() for f in tkfont.families()]
        if "microsoft yahei ui" in font_families:
            default_font.configure(family="Microsoft YaHei UI", size=9)
        elif "microsoft yahei" in font_families:
            default_font.configure(family="Microsoft YaHei", size=9)
    except:
        pass
    
    app = FilenameSimilarityChecker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
