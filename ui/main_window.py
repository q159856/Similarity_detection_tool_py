#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
提供文件名相似度检测的主界面
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any, Optional

from core import FileManager, SimilarityCalculator, get_all_matchers
from ui.styles import StyleManager
from ui.duplicate_manager import DuplicateManager


class MainWindow:
    """主窗口类"""
    
    def __init__(self, root: tk.Tk):
        """
        初始化主窗口
        
        Args:
            root: Tk根窗口
        """
        self.root = root
        self.root.title("文件名相似度检测工具")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        
        self.style_manager = StyleManager()
        self.style_manager.setup_styles(root)
        
        self.file_manager = FileManager()
        self.similarity_calculator = SimilarityCalculator(
            matcher_type='continuous',
            include_extension=False,
            threshold=0.6
        )
        
        self.similar_groups: List[Dict[str, Any]] = []
        self.folder_path: str = ""
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text="文件名相似度检测工具", style="Title.TLabel")
        title_label.pack(pady=(0, 10))
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        check_frame = ttk.Frame(notebook, padding="5")
        notebook.add(check_frame, text="  相似度检测  ")
        
        manage_frame = ttk.Frame(notebook, padding="5")
        notebook.add(manage_frame, text="  重复文件管理  ")
        
        self._create_check_tab(check_frame)
        self._create_manage_tab(manage_frame)
        
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame, variable=self.progress_var, maximum=100, mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=2)
        
        self.status_label = ttk.Label(status_frame, text="就绪", style="Normal.TLabel")
        self.status_label.pack(anchor=tk.W)
    
    def _create_check_tab(self, parent: ttk.Frame):
        """创建相似度检测标签页"""
        folder_frame = ttk.LabelFrame(parent, text="文件夹选择", padding="10")
        folder_frame.pack(fill=tk.X, pady=5)
        
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=70)
        self.folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(folder_frame, text="浏览", command=self._browse_folder)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        settings_frame = ttk.LabelFrame(parent, text="检测设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        left_settings = ttk.Frame(settings_frame)
        left_settings.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_settings = ttk.Frame(settings_frame)
        right_settings.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))
        
        self._create_left_settings(left_settings)
        self._create_right_settings(right_settings)
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="开始检测", command=self._start_check).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="清空结果", command=self._clear_results).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="导出结果", command=self._export_results).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="检测相同内容", command=self._check_content_similarity).pack(side=tk.LEFT, padx=10)
        
        result_frame = ttk.LabelFrame(parent, text="检测结果（点击文件名查看详细信息）", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self._create_result_display(result_frame)
    
    def _create_left_settings(self, parent: ttk.Frame):
        """创建设置面板左侧内容"""
        matcher_frame = ttk.LabelFrame(parent, text="匹配算法", padding="5")
        matcher_frame.pack(fill=tk.X, pady=5)
        
        all_matchers = get_all_matchers()
        
        matcher_label = ttk.Label(matcher_frame, text="选择匹配算法：", style="Normal.TLabel")
        matcher_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.matcher_type = tk.StringVar(value='continuous')
        
        matcher_combo = ttk.Combobox(
            matcher_frame, 
            textvariable=self.matcher_type,
            values=[m[0] for m in all_matchers],
            state='readonly',
            width=25
        )
        matcher_combo.pack(anchor=tk.W)
        
        self.matcher_desc_label = ttk.Label(
            matcher_frame, 
            text="", 
            style="Small.TLabel",
            foreground="#666666"
        )
        self.matcher_desc_label.pack(anchor=tk.W, pady=(5, 0))
        
        matcher_combo.bind('<<ComboboxSelected>>', self._on_matcher_changed)
        self._update_matcher_description()
        
        algorithm_frame = ttk.LabelFrame(parent, text="检测算法", padding="5")
        algorithm_frame.pack(fill=tk.X, pady=5)
        
        self.algorithm_mode = tk.StringVar(value='optimized')
        
        ttk.Radiobutton(
            algorithm_frame,
            text="优化算法（O(n log n)，推荐用于大量文件）",
            variable=self.algorithm_mode,
            value='optimized'
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            algorithm_frame,
            text="暴力算法（O(n²)，精确但较慢）",
            variable=self.algorithm_mode,
            value='brute'
        ).pack(anchor=tk.W, pady=2)
    
    def _create_right_settings(self, parent: ttk.Frame):
        """创建设置面板右侧内容"""
        threshold_frame = ttk.LabelFrame(parent, text="相似度阈值", padding="5")
        threshold_frame.pack(fill=tk.X, pady=5)
        
        self.threshold_var = tk.DoubleVar(value=0.6)
        
        threshold_label = ttk.Label(threshold_frame, text="相似度阈值：", style="Normal.TLabel")
        threshold_label.pack(anchor=tk.W)
        
        threshold_scale_frame = ttk.Frame(threshold_frame)
        threshold_scale_frame.pack(fill=tk.X, pady=5)
        
        self.threshold_scale = ttk.Scale(
            threshold_scale_frame,
            from_=0.1,
            to=1.0,
            variable=self.threshold_var,
            orient=tk.HORIZONTAL,
            command=self._update_threshold_label
        )
        self.threshold_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.threshold_value_label = ttk.Label(
            threshold_scale_frame, 
            text="60%", 
            style="Normal.TLabel",
            width=6
        )
        self.threshold_value_label.pack(side=tk.LEFT, padx=10)
        
        options_frame = ttk.LabelFrame(parent, text="其他选项", padding="5")
        options_frame.pack(fill=tk.X, pady=5)
        
        self.include_extension = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="包含文件扩展名进行比较",
            variable=self.include_extension
        ).pack(anchor=tk.W, pady=2)
        
        self.show_file_info = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="在结果中显示文件详细信息",
            variable=self.show_file_info
        ).pack(anchor=tk.W, pady=2)
    
    def _create_result_display(self, parent: ttk.Frame):
        """创建结果显示区域"""
        paned_window = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        result_left = ttk.Frame(paned_window)
        paned_window.add(result_left, weight=2)
        
        result_right = ttk.LabelFrame(paned_window, text="文件详细信息", padding="5")
        paned_window.add(result_right, weight=1)
        
        text_frame = ttk.Frame(result_left)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = tk.Text(text_frame, wrap=tk.WORD, relief=tk.SUNKEN, borderwidth=1)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.style_manager.configure_text_widget(self.result_text)
        
        self.result_text.bind('<Button-1>', self._on_text_click)
        
        self._create_file_info_panel(result_right)
    
    def _create_file_info_panel(self, parent: ttk.Frame):
        """创建文件信息面板"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.file_info_frame = ttk.Frame(canvas)
        
        self.file_info_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.file_info_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self._clear_file_info()
    
    def _clear_file_info(self):
        """清空文件信息面板"""
        for widget in self.file_info_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(
            self.file_info_frame, 
            text="点击左侧结果中的文件名\n查看文件详细信息", 
            style="Normal.TLabel",
            foreground="#666666"
        ).pack(pady=20)
    
    def _display_file_info(self, filename: str):
        """
        显示文件详细信息
        
        Args:
            filename: 文件名
        """
        if not self.folder_path:
            return
        
        file_path = os.path.join(self.folder_path, filename)
        info = self.file_manager.get_file_info(file_path)
        
        for widget in self.file_info_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(
            self.file_info_frame, 
            text=info['name'], 
            style="Heading.TLabel",
            foreground=self.style_manager.get_color('primary')
        ).pack(anchor=tk.W, pady=(0, 10))
        
        info_items = [
            ("文件路径", info['path']),
            ("文件大小", info['size_str']),
            ("扩展名", info['extension'] if info['extension'] else "无"),
            ("创建时间", info['created_time_str'] if info['created_time_str'] else "未知"),
            ("修改时间", info['modified_time_str'] if info['modified_time_str'] else "未知"),
        ]
        
        for label, value in info_items:
            item_frame = ttk.Frame(self.file_info_frame)
            item_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(
                item_frame, 
                text=f"{label}：", 
                style="Normal.TLabel",
                width=10
            ).pack(side=tk.LEFT)
            
            ttk.Label(
                item_frame, 
                text=str(value), 
                style="Normal.TLabel",
                foreground=self.style_manager.get_color('text_primary')
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Separator(self.file_info_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        btn_frame = ttk.Frame(self.file_info_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        def open_location():
            folder = os.path.dirname(file_path)
            self.file_manager.open_folder(folder)
        
        def open_file():
            if os.path.exists(file_path):
                try:
                    os.startfile(file_path)
                except:
                    pass
        
        ttk.Button(btn_frame, text="打开文件", command=open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="打开位置", command=open_location).pack(side=tk.LEFT, padx=2)
    
    def _create_manage_tab(self, parent: ttk.Frame):
        """创建重复文件管理标签页"""
        description = ttk.Label(
            parent,
            text="此功能用于管理相似度较高的文件，可以自动选择并删除重复文件。\n"
                 "请先在「相似度检测」标签页中选择文件夹并设置好参数。",
            style="Normal.TLabel"
        )
        description.pack(pady=20)
        
        settings_frame = ttk.LabelFrame(parent, text="管理设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=10, padx=20)
        
        threshold_frame = ttk.Frame(settings_frame)
        threshold_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(threshold_frame, text="管理阈值百分比：", style="Normal.TLabel").pack(side=tk.LEFT, padx=5)
        
        self.duplicate_percent_var = tk.DoubleVar(value=100.0)
        
        self.duplicate_percent_scale = ttk.Scale(
            threshold_frame,
            from_=0.0,
            to=100.0,
            variable=self.duplicate_percent_var,
            orient=tk.HORIZONTAL,
            length=300,
            command=self._update_duplicate_threshold_label
        )
        self.duplicate_percent_scale.pack(side=tk.LEFT, padx=10)
        
        self.duplicate_threshold_value_label = ttk.Label(
            threshold_frame, 
            text="实际：100% (100%)", 
            style="Normal.TLabel"
        )
        self.duplicate_threshold_value_label.pack(side=tk.LEFT, padx=5)
        
        info_label = ttk.Label(
            settings_frame,
            text="说明：实际阈值 = 基础相似度阈值 + (100% - 基础阈值) × 管理百分比\n"
                 "例如：基础阈值60% + 50% = 实际80%",
            style="Small.TLabel",
            foreground="#666666"
        )
        info_label.pack(anchor=tk.W, pady=10)
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=20)
        
        ttk.Button(
            btn_frame, 
            text="打开重复文件管理器", 
            command=self._open_duplicate_manager,
            width=25
        ).pack()
    
    def _update_matcher_description(self, event=None):
        """更新匹配算法描述"""
        matcher_type = self.matcher_type.get()
        all_matchers = get_all_matchers()
        
        for m in all_matchers:
            if m[0] == matcher_type:
                self.matcher_desc_label.configure(text=f"{m[1]}：{m[2]}")
                break
        
        self.similarity_calculator.set_matcher(matcher_type)
    
    def _on_matcher_changed(self, event=None):
        """匹配算法改变时的回调"""
        self._update_matcher_description()
    
    def _update_threshold_label(self, value):
        """更新阈值显示标签"""
        percentage = float(value) * 100
        self.threshold_value_label.configure(text=f"{percentage:.0f}%")
        self.similarity_calculator.threshold = float(value)
        self._update_duplicate_threshold_label(self.duplicate_percent_var.get())
    
    def _update_duplicate_threshold_label(self, value):
        """更新重复文件管理阈值显示"""
        percent_value = float(value)
        base_threshold = self.threshold_var.get() * 100
        
        actual_threshold = base_threshold + (100 - base_threshold) * (percent_value / 100)
        
        self.duplicate_threshold_value_label.configure(
            text=f"实际：{actual_threshold:.0f}% ({percent_value:.0f}%)"
        )
    
    def _browse_folder(self):
        """浏览选择文件夹"""
        folder_selected = filedialog.askdirectory(title="选择要检测的文件夹")
        if folder_selected:
            self.folder_path = folder_selected
            self.folder_var.set(folder_selected)
    
    def _progress_callback(self, progress: float):
        """
        进度回调函数
        
        Args:
            progress: 进度值 (0-100)
        """
        self.progress_var.set(progress)
        self.root.update()
    
    def _start_check(self):
        """开始检测"""
        if not self.folder_path or not os.path.exists(self.folder_path):
            messagebox.showwarning("警告", "请先选择一个有效的文件夹")
            return
        
        self.result_text.delete(1.0, tk.END)
        self._clear_file_info()
        self.progress_var.set(0)
        self.status_label.configure(text="正在读取文件...")
        self.root.update()
        
        self.similarity_calculator.include_extension = self.include_extension.get()
        
        try:
            files = self.file_manager.get_files_in_folder(self.folder_path)
        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.status_label.configure(text="就绪")
            return
        
        if len(files) < 2:
            messagebox.showinfo("提示", "文件夹中文件数量不足，无法进行相似度检测")
            self.status_label.configure(text="就绪")
            return
        
        self.status_label.configure(text=f"共发现 {len(files)} 个文件，正在检测相似度...")
        self.root.update()
        
        try:
            self.similar_groups = self.similarity_calculator.find_groups(
                files,
                algorithm=self.algorithm_mode.get(),
                progress_callback=self._progress_callback
            )
            
            self._display_results()
            
            self.progress_var.set(100)
            all_matchers = get_all_matchers()
            matcher_name = self.matcher_type.get()
            for m in all_matchers:
                if m[0] == matcher_name:
                    matcher_name = m[1]
                    break
            
            threshold_text = f"{self.threshold_var.get() * 100:.0f}%"
            self.status_label.configure(
                text=f"检测完成！发现 {len(self.similar_groups)} 组相似文件（{matcher_name}，阈值：{threshold_text}）"
            )
            
        except Exception as e:
            messagebox.showerror("错误", f"检测过程中发生错误：{str(e)}")
            self.status_label.configure(text="检测失败")
    
    def _check_content_similarity(self):
        """检测相同内容的文件"""
        if not self.folder_path or not os.path.exists(self.folder_path):
            messagebox.showwarning("警告", "请先选择一个有效的文件夹")
            return
        
        self.result_text.delete(1.0, tk.END)
        self._clear_file_info()
        self.progress_var.set(0)
        self.status_label.configure(text="正在读取文件内容并计算哈希...")
        self.root.update()
        
        try:
            files = self.file_manager.get_files_in_folder(self.folder_path)
        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.status_label.configure(text="就绪")
            return
        
        if len(files) < 2:
            messagebox.showinfo("提示", "文件夹中文件数量不足")
            self.status_label.configure(text="就绪")
            return
        
        try:
            self.similar_groups = self.similarity_calculator.find_groups_by_content(
                self.folder_path,
                files,
                progress_callback=self._progress_callback
            )
            
            self._display_content_results()
            
            self.progress_var.set(100)
            self.status_label.configure(
                text=f"内容检测完成！发现 {len(self.similar_groups)} 组内容相同的文件"
            )
            
        except Exception as e:
            messagebox.showerror("错误", f"检测过程中发生错误：{str(e)}")
            self.status_label.configure(text="检测失败")
    
    def _display_content_results(self):
        """显示内容检测结果"""
        self.result_text.delete(1.0, tk.END)
        
        if not self.similar_groups:
            self.result_text.insert(tk.END, "未发现内容相同的文件。\n", "summary")
            return
        
        total_files = sum(group['size'] for group in self.similar_groups)
        summary = f"检测完成！共发现 {len(self.similar_groups)} 组内容相同的文件，涉及 {total_files} 个文件。\n\n"
        self.result_text.insert(tk.END, summary, "summary")
        
        self.result_text.insert(tk.END, "=" * 80 + "\n\n", "separator")
        
        for idx, group in enumerate(self.similar_groups, 1):
            members = group['members']
            content_hash = group.get('content_hash', '')
            
            group_title = f"【第 {idx} 组】内容完全相同（共 {len(members)} 个文件）\n"
            self.result_text.insert(tk.END, group_title, "group_title")
            
            if content_hash:
                self.result_text.insert(tk.END, f"  内容哈希：{content_hash}\n", "file_info")
            
            for i, filename in enumerate(members, 1):
                if self.folder_path and self.show_file_info.get():
                    file_path = os.path.join(self.folder_path, filename)
                    info = self.file_manager.get_file_info(file_path)
                    info_str = f"（大小：{info['size_str']}）"
                else:
                    info_str = ""
                
                self.result_text.insert(tk.END, f"  {i}. {filename} ", "filename")
                if info_str:
                    self.result_text.insert(tk.END, f"{info_str}\n", "file_info")
                else:
                    self.result_text.insert(tk.END, "\n")
            
            self.result_text.insert(tk.END, "\n")
            self.result_text.insert(tk.END, "-" * 60 + "\n\n", "separator")
    
    def _display_results(self):
        """显示检测结果"""
        self.result_text.delete(1.0, tk.END)
        
        if not self.similar_groups:
            self.result_text.insert(tk.END, "未发现相似度高的文件组。\n", "summary")
            self.result_text.insert(tk.END, "建议降低相似度阈值后重新检测。\n")
            return
        
        total_files = sum(group['size'] for group in self.similar_groups)
        summary = f"检测完成！共发现 {len(self.similar_groups)} 组相似文件，涉及 {total_files} 个文件。\n\n"
        self.result_text.insert(tk.END, summary, "summary")
        
        all_matchers = get_all_matchers()
        matcher_name = self.matcher_type.get()
        for m in all_matchers:
            if m[0] == matcher_name:
                matcher_name = m[1]
                break
        
        threshold_text = f"{self.threshold_var.get() * 100:.0f}%"
        settings_info = f"匹配算法：{matcher_name}\n相似度阈值：{threshold_text}\n"
        self.result_text.insert(tk.END, settings_info)
        self.result_text.insert(tk.END, "=" * 80 + "\n\n", "separator")
        
        for idx, group in enumerate(self.similar_groups, 1):
            avg_sim = group['avg_similarity']
            members = group['members']
            
            group_title = f"【第 {idx} 组】平均相似度：{avg_sim * 100:.1f}% （共 {len(members)} 个文件）\n"
            self.result_text.insert(tk.END, group_title, "group_title")
            
            if members:
                first_file = members[0]
                sorted_members = sorted(
                    members[1:],
                    key=lambda x: self.similarity_calculator.calculate_pair(first_file, x),
                    reverse=True
                )
                sorted_members = [first_file] + sorted_members
            else:
                sorted_members = members
            
            for i, filename in enumerate(sorted_members, 1):
                if i == 1:
                    sim_text = "（基准文件）"
                    tag = "filename"
                else:
                    sim = self.similarity_calculator.calculate_pair(sorted_members[0], filename)
                    sim_text = f"（与基准相似度：{sim * 100:.1f}%）"
                    if sim >= 0.8:
                        tag = "similarity_high"
                    elif sim >= 0.6:
                        tag = "similarity_medium"
                    else:
                        tag = "filename"
                
                if self.folder_path and self.show_file_info.get():
                    file_path = os.path.join(self.folder_path, filename)
                    info = self.file_manager.get_file_info(file_path)
                    info_str = f" [大小：{info['size_str']}，修改：{info['modified_time_str']}]"
                else:
                    info_str = ""
                
                self.result_text.insert(tk.END, f"  {i}. {filename}", "filename")
                if info_str:
                    self.result_text.insert(tk.END, f"{info_str}", "file_info")
                self.result_text.insert(tk.END, f" {sim_text}\n", tag)
            
            self.result_text.insert(tk.END, "\n")
            self.result_text.insert(tk.END, "-" * 60 + "\n\n", "separator")
    
    def _on_text_click(self, event):
        """
        文本点击事件处理
        
        Args:
            event: 点击事件
        """
        if not self.folder_path or not self.show_file_info.get():
            return
        
        try:
            index = self.result_text.index("@%s,%s" % (event.x, event.y))
            line_start = self.result_text.index(f"{index} linestart")
            line_end = self.result_text.index(f"{index} lineend")
            line_text = self.result_text.get(line_start, line_end)
            
            import re
            match = re.search(r'\d+\.\s*([^\[\(]+)', line_text)
            if match:
                filename = match.group(1).strip()
                if filename:
                    self._display_file_info(filename)
        except:
            pass
    
    def _clear_results(self):
        """清空结果"""
        self.result_text.delete(1.0, tk.END)
        self._clear_file_info()
        self.similar_groups = []
        self.progress_var.set(0)
        self.status_label.configure(text="就绪")
    
    def _export_results(self):
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
                f.write("=" * 80 + "\n")
                f.write("文件名相似度检测结果报告\n")
                f.write("=" * 80 + "\n\n")
                
                all_matchers = get_all_matchers()
                matcher_name = self.matcher_type.get()
                for m in all_matchers:
                    if m[0] == matcher_name:
                        matcher_name = m[1]
                        break
                
                threshold_text = f"{self.threshold_var.get() * 100:.0f}%"
                f.write(f"检测文件夹：{self.folder_path}\n")
                f.write(f"匹配算法：{matcher_name}\n")
                f.write(f"相似度阈值：{threshold_text}\n")
                f.write(f"是否包含扩展名：{'是' if self.include_extension.get() else '否'}\n\n")
                
                total_files = sum(group['size'] for group in self.similar_groups)
                f.write(f"检测结果统计：\n")
                f.write(f"- 相似文件组数量：{len(self.similar_groups)}\n")
                f.write(f"- 涉及文件总数：{total_files}\n\n")
                
                f.write("=" * 80 + "\n\n")
                
                for idx, group in enumerate(self.similar_groups, 1):
                    avg_sim = group['avg_similarity']
                    members = group['members']
                    
                    f.write(f"【第 {idx} 组】平均相似度：{avg_sim * 100:.1f}% （共 {len(members)} 个文件）\n")
                    f.write("-" * 60 + "\n")
                    
                    if members:
                        first_file = members[0]
                        sorted_members = sorted(
                            members[1:],
                            key=lambda x: self.similarity_calculator.calculate_pair(first_file, x),
                            reverse=True
                        )
                        sorted_members = [first_file] + sorted_members
                    else:
                        sorted_members = members
                    
                    for i, filename in enumerate(sorted_members, 1):
                        if i == 1:
                            f.write(f"  {i}. {filename} （基准文件）\n")
                        else:
                            sim = self.similarity_calculator.calculate_pair(sorted_members[0], filename)
                            f.write(f"  {i}. {filename} （与基准相似度：{sim * 100:.1f}%）\n")
                    
                    f.write("\n")
                
                f.write("=" * 80 + "\n")
                f.write("检测报告结束\n")
                f.write("=" * 80 + "\n")
            
            messagebox.showinfo("成功", f"检测结果已成功导出到：\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出结果时发生错误：{str(e)}")
    
    def _open_duplicate_manager(self):
        """打开重复文件管理器"""
        if not self.folder_path or not os.path.exists(self.folder_path):
            messagebox.showwarning("警告", "请先在「相似度检测」标签页选择一个有效的文件夹")
            return
        
        base_threshold = self.threshold_var.get()
        percent_value = self.duplicate_percent_var.get() / 100.0
        actual_threshold = base_threshold + (1.0 - base_threshold) * percent_value
        
        manager = DuplicateManager(
            self.root,
            self.folder_path,
            actual_threshold,
            self.similarity_calculator,
            self.file_manager,
            self.style_manager
        )
        
        manager.show()
        
        if self.similar_groups:
            self._start_check()
