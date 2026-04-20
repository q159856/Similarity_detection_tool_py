#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重复文件管理器模块
提供重复文件的查看、选择和删除功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Set, Optional

from core import FileManager, SimilarityCalculator
from ui.styles import StyleManager


class DuplicateManager:
    """重复文件管理器"""
    
    def __init__(
        self,
        parent: tk.Tk,
        folder_path: str,
        threshold: float,
        similarity_calculator: SimilarityCalculator,
        file_manager: FileManager,
        style_manager: StyleManager
    ):
        """
        初始化重复文件管理器
        
        Args:
            parent: 父窗口
            folder_path: 文件夹路径
            threshold: 相似度阈值
            similarity_calculator: 相似度计算器
            file_manager: 文件管理器
            style_manager: 样式管理器
        """
        self.parent = parent
        self.folder_path = folder_path
        self.threshold = threshold
        self.similarity_calculator = similarity_calculator
        self.file_manager = file_manager
        self.style_manager = style_manager
        
        self.window: Optional[tk.Toplevel] = None
        self.duplicate_groups: List[Dict[str, Any]] = []
        self.group_vars: List[Dict[str, Any]] = []
    
    def show(self):
        """显示管理器窗口"""
        self._create_window()
        self._load_duplicates()
    
    def _create_window(self):
        """创建管理器窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"重复文件管理器（相似度 >= {self.threshold * 100:.0f}%）")
        self.window.geometry("950x700")
        self.window.resizable(True, True)
        
        self.window.transient(self.parent)
        self.window.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(
            main_frame, 
            text=f"重复文件管理器（相似度 >= {self.threshold * 100:.0f}%）", 
            style="Title.TLabel"
        )
        title_label.pack(pady=(0, 5))
        
        self.info_label = ttk.Label(main_frame, text="正在加载...", style="Normal.TLabel")
        self.info_label.pack(pady=(0, 10))
        
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        list_frame = ttk.Frame(paned_window)
        paned_window.add(list_frame, weight=3)
        
        detail_frame = ttk.LabelFrame(paned_window, text="文件详细信息", padding="5")
        paned_window.add(detail_frame, weight=1)
        
        self._create_list_area(list_frame)
        self._create_detail_area(detail_frame)
        
        self._create_bottom_buttons(main_frame)
    
    def _create_list_area(self, parent: ttk.Frame):
        """创建文件列表区域"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        mouse_wheel_support = True
        try:
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        except:
            pass
    
    def _create_detail_area(self, parent: ttk.Frame):
        """创建文件详情区域"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.detail_frame = ttk.Frame(canvas)
        
        self.detail_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.detail_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self._clear_detail()
    
    def _clear_detail(self):
        """清空详情面板"""
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(
            self.detail_frame,
            text="勾选文件复选框\n查看文件详细信息",
            style="Normal.TLabel",
            foreground="#666666"
        ).pack(pady=20)
    
    def _show_file_detail(self, filename: str):
        """
        显示文件详情
        
        Args:
            filename: 文件名
        """
        file_path = os.path.join(self.folder_path, filename)
        info = self.file_manager.get_file_info(file_path)
        
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(
            self.detail_frame,
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
            item_frame = ttk.Frame(self.detail_frame)
            item_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(
                item_frame,
                text=f"{label}：",
                style="Small.TLabel",
                width=10
            ).pack(side=tk.LEFT)
            
            value_label = ttk.Label(
                item_frame,
                text=str(value),
                style="Small.TLabel",
                foreground=self.style_manager.get_color('text_primary'),
                wraplength=200
            )
            value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Separator(self.detail_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        btn_frame = ttk.Frame(self.detail_frame)
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
    
    def _create_bottom_buttons(self, parent: ttk.Frame):
        """创建底部按钮"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            btn_frame, 
            text="全选（每组留一个）", 
            command=self._select_all_except_one
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="取消全选", 
            command=self._deselect_all
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="删除选中的文件", 
            command=self._delete_selected
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="关闭", 
            command=self._close
        ).pack(side=tk.RIGHT, padx=5)
    
    def _load_duplicates(self):
        """加载重复文件"""
        try:
            files = self.file_manager.get_files_in_folder(self.folder_path)
        except Exception as e:
            messagebox.showerror("错误", f"读取文件夹时出错：{str(e)}")
            self._close()
            return
        
        if len(files) < 2:
            messagebox.showinfo("提示", "文件夹中文件数量不足")
            self._close()
            return
        
        def progress_callback(progress: float):
            if self.window and self.window.winfo_exists():
                self.info_label.configure(text=f"正在检测... {progress:.0f}%")
                self.window.update()
        
        self.duplicate_groups = self.similarity_calculator.find_duplicates_by_threshold(
            files,
            self.threshold,
            progress_callback=progress_callback
        )
        
        if not self.duplicate_groups:
            messagebox.showinfo("提示", f"未发现相似度 >= {self.threshold * 100:.0f}% 的文件")
            self._close()
            return
        
        total_files = sum(g['size'] for g in self.duplicate_groups)
        self.info_label.configure(
            text=f"共发现 {len(self.duplicate_groups)} 组相似文件，涉及 {total_files} 个文件。\n请勾选要删除的文件（每组至少保留一个文件）。"
        )
        
        self._display_groups()
    
    def _display_groups(self):
        """显示重复文件组"""
        self.group_vars = []
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        for group_idx, group in enumerate(self.duplicate_groups, 1):
            members = group['members']
            clean_name = group.get('clean_name', '')
            avg_sim = group.get('avg_similarity', 1.0)
            
            group_frame = ttk.LabelFrame(
                self.scrollable_frame,
                text=f"【第 {group_idx} 组】平均相似度：{avg_sim * 100:.1f}% （共 {len(members)} 个文件）",
                padding="10"
            )
            group_frame.pack(fill=tk.X, pady=5, padx=5)
            
            file_vars = []
            file_checkboxes = []
            
            for file_idx, filename in enumerate(members):
                file_path = os.path.join(self.folder_path, filename)
                info = self.file_manager.get_file_info(file_path)
                
                file_frame = ttk.Frame(group_frame)
                file_frame.pack(fill=tk.X, pady=2)
                
                var = tk.BooleanVar(value=False)
                file_vars.append(var)
                
                def on_check(var=var, fn=filename):
                    if var.get():
                        self._show_file_detail(fn)
                
                cb = ttk.Checkbutton(file_frame, variable=var, command=on_check)
                cb.pack(side=tk.LEFT, padx=5)
                file_checkboxes.append(cb)
                
                name_label = ttk.Label(
                    file_frame,
                    text=filename,
                    foreground=self.style_manager.get_color('primary'),
                    font=self.style_manager.get_font('bold')
                )
                name_label.pack(side=tk.LEFT, padx=5)
                
                info_str = f"大小：{info['size_str']} | 修改：{info['modified_time_str']}"
                info_label = ttk.Label(
                    file_frame,
                    text=info_str,
                    foreground=self.style_manager.get_color('text_secondary'),
                    font=self.style_manager.get_font('small')
                )
                info_label.pack(side=tk.LEFT, padx=5)
                
                def make_open_location(fp=file_path):
                    def _open():
                        folder = os.path.dirname(fp)
                        self.file_manager.open_folder(folder)
                    return _open
                
                open_btn = ttk.Button(file_frame, text="打开位置", width=8, command=make_open_location())
                open_btn.pack(side=tk.RIGHT, padx=5)
            
            self.group_vars.append({
                'group': group,
                'file_vars': file_vars,
                'members': members,
                'file_checkboxes': file_checkboxes
            })
            
            btn_frame = ttk.Frame(group_frame)
            btn_frame.pack(fill=tk.X, pady=5)
            
            def make_select_by_criteria(g_idx=group_idx-1):
                def _select(criteria):
                    self._select_by_criteria(g_idx, criteria)
                return _select
            
            ttk.Button(
                btn_frame, 
                text="保留最新", 
                width=8,
                command=lambda g=group_idx-1: self._select_by_criteria(g, 'newest')
            ).pack(side=tk.LEFT, padx=2)
            
            ttk.Button(
                btn_frame,
                text="保留最旧",
                width=8,
                command=lambda g=group_idx-1: self._select_by_criteria(g, 'oldest')
            ).pack(side=tk.LEFT, padx=2)
            
            ttk.Button(
                btn_frame,
                text="保留最大",
                width=8,
                command=lambda g=group_idx-1: self._select_by_criteria(g, 'largest')
            ).pack(side=tk.LEFT, padx=2)
            
            ttk.Button(
                btn_frame,
                text="保留最小",
                width=8,
                command=lambda g=group_idx-1: self._select_by_criteria(g, 'smallest')
            ).pack(side=tk.LEFT, padx=2)
            
            ttk.Label(
                btn_frame,
                text="← 快速选择",
                foreground=self.style_manager.get_color('muted')
            ).pack(side=tk.LEFT, padx=10)
    
    def _select_by_criteria(self, group_vars_idx: int, criteria: str):
        """
        根据条件选择文件
        
        Args:
            group_vars_idx: 组索引
            criteria: 选择条件
        """
        if group_vars_idx >= len(self.group_vars):
            return
        
        gv = self.group_vars[group_vars_idx]
        members = gv['members']
        file_vars = gv['file_vars']
        
        if len(members) < 2:
            return
        
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
        
        if criteria == 'newest':
            file_infos.sort(key=lambda x: x['mod_time'], reverse=True)
        elif criteria == 'oldest':
            file_infos.sort(key=lambda x: x['mod_time'])
        elif criteria == 'largest':
            file_infos.sort(key=lambda x: x['size'], reverse=True)
        elif criteria == 'smallest':
            file_infos.sort(key=lambda x: x['size'])
        else:
            return
        
        for i, info in enumerate(file_infos):
            if i == 0:
                file_vars[info['idx']].set(False)
            else:
                file_vars[info['idx']].set(True)
    
    def _get_selected_files(self) -> List[str]:
        """
        获取所有选中的文件
        
        Returns:
            选中的文件列表
        """
        selected = []
        for gv in self.group_vars:
            members = gv['members']
            file_vars = gv['file_vars']
            for idx, var in enumerate(file_vars):
                if var.get():
                    selected.append(members[idx])
        return selected
    
    def _validate_selection(self) -> tuple:
        """
        验证选择是否合法
        
        Returns:
            (是否合法, 错误消息)
        """
        for gv in self.group_vars:
            file_vars = gv['file_vars']
            members = gv['members']
            selected_count = sum(1 for var in file_vars if var.get())
            if selected_count >= len(members):
                return False, f"第 {self.group_vars.index(gv) + 1} 组选择了所有文件！每组至少需要保留一个文件。"
        return True, ""
    
    def _select_all_except_one(self):
        """全选（每组留一个）"""
        for gv in self.group_vars:
            file_vars = gv['file_vars']
            for idx, var in enumerate(file_vars):
                if idx == 0:
                    var.set(False)
                else:
                    var.set(True)
    
    def _deselect_all(self):
        """取消全选"""
        for gv in self.group_vars:
            for var in gv['file_vars']:
                var.set(False)
        self._clear_detail()
    
    def _delete_selected(self):
        """删除选中的文件"""
        valid, message = self._validate_selection()
        if not valid:
            messagebox.showwarning("警告", message)
            return
        
        selected = self._get_selected_files()
        
        if not selected:
            messagebox.showinfo("提示", "没有选中任何文件")
            return
        
        confirm_msg = f"您确定要删除以下 {len(selected)} 个文件吗？\n此操作不可撤销！\n\n"
        for filename in selected[:10]:
            confirm_msg += f"  - {filename}\n"
        if len(selected) > 10:
            confirm_msg += f"  ... 还有 {len(selected) - 10} 个文件\n"
        
        if not messagebox.askyesno("确认删除", confirm_msg):
            return
        
        deleted = []
        errors = []
        
        for filename in selected:
            file_path = os.path.join(self.folder_path, filename)
            try:
                os.remove(file_path)
                deleted.append(filename)
            except Exception as e:
                errors.append(f"{filename}: {str(e)}")
        
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
        
        self._close()
    
    def _close(self):
        """关闭窗口"""
        if self.window and self.window.winfo_exists():
            self.window.destroy()
